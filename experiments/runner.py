#!/usr/bin/env python3
"""3-arm Planner-Executor-Reviewer experiment runner (AAMAS 2027).

Three arms share ONE pipeline implementation.  Everything except the
manipulated variable is held identical by construction:

  agents            3 actors (Planner/Executor/Reviewer slots) + 1 evaluator
  order             Planner-slot -> Executor-slot -> Reviewer-slot
  outer rounds      3 (MAX_OUTER_ROUNDS)
  inner rounds      2 (INNER_ROUNDS)
  visibility        each arm's policy is declared in VISIBILITY and is the
                    SAME SHAPE: each actor sees the problem + the accumulated
                    shared history produced by the pipeline so far
  model-call budget MAX_ACTOR_CALLS actor calls + MAX_EVALUATOR_CALLS
                    evaluator calls, enforced by a hard counter in every arm
  retry budget      MAX_TRANSPORT_RETRIES transport retries per call,
                    MAX_REGENERATIONS validation regenerations per turn
                    (the regeneration path EXISTS in all arms; only arm C has
                    a constraint that can fail, which is the manipulation)
  stopping rule     reviewer approval ([Agree] / verdict=="accept")
                    OR evaluator PASS
  decoding          temperature 0, max_tokens 4096
  backend           sophia_vllm
  grading           evaluator LLM, openai/gpt-oss-120b, sees ground truth

The manipulated variable is ONLY: the prompt text (A vs B) and the presence of
architectural enforcement (C).
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import random
import re
import string
import sys
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import prompts as P  # noqa: E402
import schemas as S  # noqa: E402

# ==========================================================================
# Held-constant experiment constants (identical across all three arms)
# ==========================================================================

BACKEND = "sophia_vllm"
BASE_URL = "https://inference-api.alcf.anl.gov/resource_server/sophia/vllm/v1"
AUTH_SCRIPT_DIR = "/Users/bellayang/work/agent-e/mas-eval"

MAX_OUTER_ROUNDS = 3
INNER_ROUNDS = 2
TEMPERATURE = 0.0
MAX_TOKENS = 8192  # raised from 4096: 74% of Arm C rejections were finish_reason=length (master, 19:20)

# Model-call budget. 3 outer rounds x 2 inner rounds x 3 actors = 18, plus a
# regeneration allowance.  Enforced identically in every arm.
MAX_ACTOR_CALLS = 30
MAX_EVALUATOR_CALLS = 6
MAX_REGENERATIONS = 3          # per turn; arm C spec
MAX_TRANSPORT_RETRIES = 4      # per call, 429/503/timeout
REQUEST_TIMEOUT_S = 300.0

ROLE_ORDER = ["planner", "executor", "reviewer"]

# Context-visibility policy, declared per arm so the paper can assert it is
# the same.  "shared_history" = the running transcript of actor turns.
VISIBILITY = {
    "A": {"planner": ["problem", "shared_history", "advice"],
          "executor": ["problem", "shared_history", "advice"],
          "reviewer": ["problem", "shared_history", "advice"]},
    "B": {"planner": ["problem", "shared_history", "advice"],
          "executor": ["problem", "shared_history", "advice"],
          "reviewer": ["problem", "shared_history", "advice"]},
    # Arm C is the manipulation: the executor's view of the planner is the
    # PARSED PLAN OBJECT, never the planner's raw text.
    "C": {"planner": ["problem", "shared_history", "advice"],
          "executor": ["problem", "parsed_plan", "advice"],
          "reviewer": ["problem", "parsed_plan", "parsed_execution", "advice"]},
}

PROBLEMS_PARQUET = (
    "/Users/bellayang/Documents/note/projects/IEEE-BigData-SciAgentTrace/"
    "analysis/hf_cache/release/data/problems/part-00000.parquet"
)
BENCHMARK_ID = "omnimath2"
DOMAIN = "math"

DEFAULT_ACTORS = [
    "openai/gpt-oss-120b",
    "google/gemma-4-31B-it",
    "meta-llama/Llama-3.3-70B-Instruct",
]
EVALUATOR_MODEL = "openai/gpt-oss-120b"


def config_version_hash() -> str:
    """Hash of every prompt + schema + held-constant knob.

    Any change to the experimental setup changes this string, so trajectories
    from different setups can never be silently pooled.
    """
    h = hashlib.sha256()
    for k in sorted(P.ALL_PROMPTS):
        h.update(k.encode())
        h.update(P.ALL_PROMPTS[k].encode())
    h.update(json.dumps(S.SCHEMAS, sort_keys=True).encode())
    h.update(
        json.dumps(
            {
                "backend": BACKEND,
                "base_url": BASE_URL,
                "max_outer_rounds": MAX_OUTER_ROUNDS,
                "inner_rounds": INNER_ROUNDS,
                "temperature": TEMPERATURE,
                "max_tokens": MAX_TOKENS,
                "max_actor_calls": MAX_ACTOR_CALLS,
                "max_evaluator_calls": MAX_EVALUATOR_CALLS,
                "max_regenerations": MAX_REGENERATIONS,
                "max_transport_retries": MAX_TRANSPORT_RETRIES,
                "role_order": ROLE_ORDER,
                "visibility": VISIBILITY,
                "evaluator_model": EVALUATOR_MODEL,
                "benchmark_id": BENCHMARK_ID,
            },
            sort_keys=True,
        ).encode()
    )
    return h.hexdigest()[:16]


CONFIG_VERSION = config_version_hash()

# ==========================================================================
# Token handling -- NEVER logged, NEVER written to any output file.
# ==========================================================================


class TokenProvider:
    """Fetch/refresh the bearer token. The value is kept in memory only."""

    def __init__(self, dry_run: bool = False):
        self._token: Optional[str] = None
        self._fetched_at = 0.0
        self._lock = asyncio.Lock()
        self.dry_run = dry_run

    def _fetch_sync(self) -> str:
        if self.dry_run:
            return "DRY-RUN-NO-TOKEN"
        sys.path.insert(0, AUTH_SCRIPT_DIR)
        import inference_auth_token  # noqa: PLC0415

        return inference_auth_token.get_access_token()

    async def get(self, force: bool = False) -> str:
        async with self._lock:
            if force or self._token is None or (time.time() - self._fetched_at) > 1800:
                self._token = await asyncio.get_event_loop().run_in_executor(
                    None, self._fetch_sync
                )
                self._fetched_at = time.time()
            return self._token


def scrub(text: str, token: Optional[str]) -> str:
    """Defence in depth: strip any token substring from anything we log."""
    if not text:
        return text
    if token and len(token) > 12 and token in text:
        text = text.replace(token, "<REDACTED>")
    # Also kill any Bearer header that leaks into an error string.
    text = re.sub(r"(?i)bearer\s+[A-Za-z0-9._\-]{12,}", "Bearer <REDACTED>", text)
    return text


# ==========================================================================
# Backend client
# ==========================================================================


class ModelUnavailable(Exception):
    """The model is reachable but not serving (e.g. 503 'not ready').

    Carries the retry/latency spent before the determination so those calls
    are not lost from the trajectory's instrumentation.
    """

    def __init__(self, message: str, retries: int = 0, latency_s: float = 0.0):
        super().__init__(message)
        self.retries = retries
        self.latency_s = latency_s


class CallBudgetExceeded(Exception):
    pass


@dataclass
class CallResult:
    text: str
    latency_s: float
    retries: int
    ok: bool
    error: Optional[str] = None
    status: Optional[int] = None
    finish_reason: Optional[str] = None
    used_reasoning_fallback: bool = False


class Backend:
    def __init__(self, tokens: TokenProvider, dry_run: bool = False,
                 stub: Optional["StubResponder"] = None):
        self.tokens = tokens
        self.dry_run = dry_run
        self.stub = stub
        self._client = None
        self.unavailable_models: Dict[str, str] = {}

    async def _get_client(self):
        if self._client is None:
            import httpx  # noqa: PLC0415

            self._client = httpx.AsyncClient(timeout=REQUEST_TIMEOUT_S)
        return self._client

    async def aclose(self):
        if self._client is not None:
            await self._client.aclose()

    async def chat(self, model: str, messages: List[Dict[str, str]],
                   tag: str = "") -> CallResult:
        if self.dry_run:
            return self.stub.respond(model, messages, tag)

        if model in self.unavailable_models:
            raise ModelUnavailable(
                "{}: {}".format(model, self.unavailable_models[model])
            )

        import httpx  # noqa: PLC0415

        client = await self._get_client()
        payload = {
            "model": model,
            "messages": messages,
            "temperature": TEMPERATURE,
            "max_tokens": MAX_TOKENS,
        }
        retries = 0
        t0 = time.time()
        last_err = "unknown"
        last_status: Optional[int] = None
        token = await self.tokens.get()

        while retries <= MAX_TRANSPORT_RETRIES:
            try:
                resp = await client.post(
                    BASE_URL + "/chat/completions",
                    json=payload,
                    headers={"Authorization": "Bearer " + token},
                )
                last_status = resp.status_code
                if resp.status_code == 200:
                    data = resp.json()
                    choice = data["choices"][0]
                    msg = choice.get("message", {})
                    txt = (msg.get("content") or "")
                    if not txt.strip():
                        # gpt-oss puts chain-of-thought in "reasoning" and can
                        # spend the whole budget there, leaving content empty.
                        # Fall back so the turn is not silently lost.
                        txt = (msg.get("reasoning")
                               or msg.get("reasoning_content") or "")
                    return CallResult(
                        text=txt, latency_s=time.time() - t0, retries=retries,
                        ok=True, status=200,
                        finish_reason=choice.get("finish_reason"),
                        used_reasoning_fallback=not (msg.get("content") or "").strip(),
                    )
                body = scrub(resp.text[:600], token)
                if resp.status_code == 401:
                    token = await self.tokens.get(force=True)
                    last_err = "401 re-auth"
                    retries += 1
                    continue
                if resp.status_code == 503 and (
                    "not ready" in body.lower() or "online but not ready" in body.lower()
                ):
                    # Per-model unavailability: record and skip, do not crash
                    # and do not burn the retry budget spinning.
                    self.unavailable_models[model] = "503 " + body[:200]
                    raise ModelUnavailable(
                        "{}: 503 {}".format(model, body[:200]),
                        retries=retries, latency_s=time.time() - t0,
                    )
                if resp.status_code in (408, 409, 425, 429, 500, 502, 503, 504):
                    last_err = "HTTP {}: {}".format(resp.status_code, body[:200])
                    retries += 1
                    if retries > MAX_TRANSPORT_RETRIES:
                        break
                    await asyncio.sleep(min(2.0 * (2 ** (retries - 1)), 30.0)
                                        + random.uniform(0, 1.0))
                    continue
                # Non-retryable.
                return CallResult(
                    text="", latency_s=time.time() - t0, retries=retries, ok=False,
                    error="HTTP {}: {}".format(resp.status_code, body[:300]),
                    status=resp.status_code,
                )
            except ModelUnavailable:
                raise
            except (httpx.TimeoutException, httpx.TransportError) as exc:
                last_err = scrub("{}: {}".format(type(exc).__name__, exc), token)
                retries += 1
                if retries > MAX_TRANSPORT_RETRIES:
                    break
                await asyncio.sleep(min(2.0 * (2 ** (retries - 1)), 30.0)
                                    + random.uniform(0, 1.0))
            except Exception as exc:  # noqa: BLE001
                return CallResult(
                    text="", latency_s=time.time() - t0, retries=retries, ok=False,
                    error=scrub("{}: {}".format(type(exc).__name__, exc), token),
                    status=last_status,
                )

        return CallResult(
            text="", latency_s=time.time() - t0, retries=retries, ok=False,
            error="retries exhausted: " + last_err, status=last_status,
        )


# ==========================================================================
# Dry-run stub responder (zero API calls)
# ==========================================================================


class StubResponder:
    """Deterministic canned responses exercising every code path.

    For arm C the planner stub deliberately emits an INVALID first attempt
    (a boxed answer) so the dry run proves the regeneration/validation path
    actually fires and is logged.
    """

    def __init__(self, force_hard_failure: bool = False):
        self.counts: Dict[str, int] = {}
        self.force_hard_failure = force_hard_failure

    def respond(self, model: str, messages: List[Dict[str, str]], tag: str) -> CallResult:
        self.counts[tag] = self.counts.get(tag, 0) + 1
        n = self.counts[tag]
        parts = tag.split("|")
        # tag == "<traj_tag>|<arm>|<role>"
        arm = parts[-2] if len(parts) >= 2 else ""
        role = parts[-1] if parts else ""
        text = ""
        if role == "evaluator":
            # First submission FAILs, later ones PASS: exercises the outer loop.
            if n <= 1:
                text = ("Verdict: FAIL\nCorrectness: 0\n"
                        "Response: answer-shape mismatch; give a general family.")
            else:
                text = "Verdict: PASS\nCorrectness: 1\nResponse: equivalent."
        elif arm == "C":
            if role == "planner":
                if self.force_hard_failure:
                    text = "I refuse to emit JSON. \\boxed{42}"
                elif n == 1:
                    text = ('Plan: first compute the bound.\n'
                            'Final Answer: \\boxed{42}')          # INVALID
                elif n == 2:
                    text = ('{"subproblems":["s1"],"strategy":["st1"],'
                            '"dependencies":["d1"],"required_quantities":["q1"],'
                            '"answer":"42"}')                      # INVALID
                else:
                    text = ('{"subproblems":["bound the max count"],'
                            '"strategy":["construct then verify"],'
                            '"dependencies":["subproblem 1 before 2"],'
                            '"required_quantities":["m as a function of n"]}')
            elif role == "executor":
                text = ('{"derivation":"stub derivation step by step",'
                        '"answer":"1 + \\\\lceil n/2 \\\\rceil"}')
            else:
                text = ('{"verdict":"accept","target":"executor",'
                        '"critique":"stub critique: derivation supports the form"}')
        elif arm == "B":
            text = ("Continuing the shared work on the problem.\n"
                    "\\boxed{1 + \\lceil n/2 \\rceil}\n"
                    + ("[Agree]" if role == "reviewer" else "[Continue]"))
        else:  # arm A
            if role == "planner":
                text = "DELTA: 1) restate givens 2) set target form\n1) Givens ...\n2) Target quantity: a formula in n"
            elif role == "executor":
                text = "Derivation: stub steps.\n\\boxed{1 + \\lceil n/2 \\rceil}"
            else:
                text = ("Diagnosis:\n- looks complete\nFix Instruction:\n- none\n"
                        "Final Answer For Evaluator:\n\\boxed{1 + \\lceil n/2 \\rceil}\n[Agree]")
        return CallResult(text=text, latency_s=0.001, retries=0, ok=True, status=200)


# ==========================================================================
# Output parsing (arms A and B)
# ==========================================================================

_BOXED_FIND = re.compile(r"\\boxed\s*\{")


def extract_boxed(text: str) -> Optional[str]:
    """Return the LAST \\boxed{...} content, brace-balanced."""
    if not text:
        return None
    out = None
    for m in _BOXED_FIND.finditer(text):
        i = m.end() - 1  # at '{'
        depth = 0
        for j in range(i, len(text)):
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    out = text[i + 1 : j].strip()
                    break
    return out


def parse_route(text: str) -> str:
    """Arm A/B reviewer routing tag. Returns 'agree'|'planner'|'executor'|'continue'."""
    if not text:
        return "continue"
    tail = text.strip()[-400:]
    if re.search(r"\[Agree\]", tail, re.IGNORECASE):
        return "agree"
    if re.search(r"\[Route:\s*Planner\]", tail, re.IGNORECASE):
        return "planner"
    if re.search(r"\[Route:\s*Executor\]", tail, re.IGNORECASE):
        return "executor"
    if re.search(r"\[Continue\]", tail, re.IGNORECASE):
        return "continue"
    # Fall back to whole-text search once.
    if re.search(r"\[Agree\]", text, re.IGNORECASE):
        return "agree"
    return "continue"


def parse_evaluator(text: str) -> Tuple[Optional[int], str]:
    """Return (correctness 0/1/None, hint text)."""
    if not text:
        return None, ""
    m = re.search(r"Correctness\s*[:=]\s*([01])", text)
    c = int(m.group(1)) if m else None
    if c is None:
        v = re.search(r"Verdict\s*[:=]\s*(PASS|FAIL)", text, re.IGNORECASE)
        if v:
            c = 1 if v.group(1).upper() == "PASS" else 0
    h = re.search(r"Response\s*[:=]\s*(.*)", text, re.DOTALL)
    return c, (h.group(1).strip() if h else text.strip())[:1500]


def fill(template: str, **kw) -> str:
    """${var} substitution that tolerates unknown placeholders and $ in LaTeX."""
    out = template
    for k, v in kw.items():
        out = out.replace("${" + k + "}", "" if v is None else str(v))
    return out


# ==========================================================================
# Trajectory record
# ==========================================================================


@dataclass
class Trajectory:
    problem_uid: str
    arm: str
    actor_model: str
    domain: str
    run_id: str
    backend: str = BACKEND
    config_version: str = CONFIG_VERSION
    actor_calls: int = 0
    evaluator_calls: int = 0
    retries: int = 0
    regeneration_events: List[Dict[str, Any]] = field(default_factory=list)
    messages: List[Dict[str, Any]] = field(default_factory=list)
    evaluator_history: List[Dict[str, Any]] = field(default_factory=list)
    stopping_condition: str = "unset"
    final_answer: Optional[str] = None
    correct: Optional[int] = None
    hard_failure: Optional[str] = None
    wall_time_s: float = 0.0
    started_at: str = ""
    ended_at: str = ""
    rounds_used: int = 0
    inner_used: int = 0
    error: Optional[str] = None
    unavailable_wait_s: Optional[float] = None

    def key(self) -> Tuple[str, str, str]:
        return (self.problem_uid, self.arm, self.actor_model)

    def to_json(self) -> str:
        d = {
            "problem_uid": self.problem_uid,
            "arm": self.arm,
            "actor_model": self.actor_model,
            "evaluator_model": EVALUATOR_MODEL,
            "domain": self.domain,
            "benchmark_id": BENCHMARK_ID,
            "run_id": self.run_id,
            "backend": self.backend,
            "config_version": self.config_version,
            "actor_calls": self.actor_calls,
            "evaluator_calls": self.evaluator_calls,
            "retries": self.retries,
            "regeneration_events": self.regeneration_events,
            "stopping_condition": self.stopping_condition,
            "final_answer": self.final_answer,
            "correct": self.correct,
            "hard_failure": self.hard_failure,
            "wall_time_s": round(self.wall_time_s, 3),
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "rounds_used": self.rounds_used,
            "inner_used": self.inner_used,
            "error": self.error,
            "unavailable_wait_s": self.unavailable_wait_s,
            "request_timeout_s": REQUEST_TIMEOUT_S,
            "budget": {
                "max_actor_calls": MAX_ACTOR_CALLS,
                "max_evaluator_calls": MAX_EVALUATOR_CALLS,
                "max_regenerations": MAX_REGENERATIONS,
                "max_transport_retries": MAX_TRANSPORT_RETRIES,
                "max_outer_rounds": MAX_OUTER_ROUNDS,
                "inner_rounds": INNER_ROUNDS,
                "temperature": TEMPERATURE,
                "max_tokens": MAX_TOKENS,
            },
            "visibility_policy": VISIBILITY[self.arm],
            "messages": self.messages,
            "evaluator_history": self.evaluator_history,
        }
        return json.dumps(d, ensure_ascii=False)


# ==========================================================================
# The pipeline -- one implementation, three arms
# ==========================================================================


class BudgetCounter:
    def __init__(self, traj: Trajectory):
        self.traj = traj

    def actor(self):
        if self.traj.actor_calls >= MAX_ACTOR_CALLS:
            raise CallBudgetExceeded("actor call budget exhausted")
        self.traj.actor_calls += 1

    def evaluator(self):
        if self.traj.evaluator_calls >= MAX_EVALUATOR_CALLS:
            raise CallBudgetExceeded("evaluator call budget exhausted")
        self.traj.evaluator_calls += 1


async def run_trajectory(problem: Dict[str, Any], arm: str, actor_model: str,
                         backend: Backend, run_id: str) -> Trajectory:
    t0 = time.time()
    traj = Trajectory(
        problem_uid=problem["problem_uid"], arm=arm, actor_model=actor_model,
        domain=DOMAIN, run_id=run_id,
        started_at=datetime.now(timezone.utc).isoformat(),
    )
    budget = BudgetCounter(traj)
    traj_tag = "{}::{}::{}".format(problem["problem_uid"], arm, actor_model)
    task = problem["problem_text"]
    gold = problem.get("reference", "")

    # Shared state, identical fields in all arms.
    shared_history: List[str] = []
    advice = ""
    previous_plan = ""
    plan_obj: Optional[Dict[str, Any]] = None
    exec_obj: Optional[Dict[str, Any]] = None
    current_answer: Optional[str] = None     # owned by the pipeline, not a role
    answer_owner = "none"
    last_executor_text = ""

    async def actor_call(role: str, msgs: List[Dict[str, str]]) -> CallResult:
        budget.actor()
        r = await backend.chat(
            actor_model, msgs,
            tag="{}|{}|{}".format(traj_tag, arm, role))
        traj.retries += r.retries
        return r

    def log_msg(role: str, rnd: int, inner: int, text: str, attempt: int = 0,
                extra: Optional[Dict[str, Any]] = None):
        m = {
            "role": role, "outer_round": rnd, "inner_round": inner,
            "attempt_index": attempt,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "text": text,
        }
        if extra:
            m.update(extra)
        traj.messages.append(m)

    def build_messages(role: str, rnd: int, inner: int) -> List[Dict[str, str]]:
        hist = "\n\n".join(shared_history[-8:])
        if arm == "A":
            if role == "planner":
                pre = fill(P.A_SOLVER_PREPEND, task_description=task,
                           previous_plan=previous_plan, advice=advice)
                app = fill(P.A_SOLVER_APPEND, role_description="Planner")
            elif role == "executor":
                pre = fill(P.A_EXECUTOR_PREPEND, task_description=task,
                           solution=previous_plan, advice=advice)
                app = P.A_EXECUTOR_APPEND
            else:
                pre = fill(P.A_CRITIC_PREPEND, task_description=task,
                           previous_plan=previous_plan,
                           preliminary_solution=last_executor_text, advice=advice)
                app = P.A_CRITIC_APPEND
            return [{"role": "user", "content": pre + "\n\n" + hist + "\n\n" + app}]
        if arm == "B":
            slot = ROLE_ORDER.index(role) + 1
            pre = fill(P.B_GENERIC_PREPEND, task_description=task,
                       shared_history=hist, slot_index=slot)
            return [{"role": "user", "content": pre + "\n\n" + P.B_GENERIC_APPEND}]
        # Arm C
        if role == "planner":
            pre = fill(P.C_PLANNER_PREPEND, task_description=task,
                       previous_plan=(json.dumps(plan_obj) if plan_obj else ""),
                       advice=advice)
            app = P.C_PLANNER_APPEND
        elif role == "executor":
            # ARCHITECTURAL: only the PARSED plan object crosses this boundary.
            pre = fill(P.C_EXECUTOR_PREPEND, task_description=task,
                       plan_json=json.dumps(plan_obj, indent=2, ensure_ascii=False),
                       advice=advice)
            app = P.C_EXECUTOR_APPEND
        else:
            pre = fill(P.C_REVIEWER_PREPEND, task_description=task,
                       plan_json=json.dumps(plan_obj, indent=2, ensure_ascii=False),
                       execution_json=json.dumps(exec_obj, indent=2, ensure_ascii=False),
                       advice=advice)
            app = P.C_REVIEWER_APPEND
        return [{"role": "user", "content": pre + "\n\n" + app}]

    async def turn(role: str, rnd: int, inner: int) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """Run one actor turn with the validate -> regenerate loop.

        The loop structure is IDENTICAL in all arms; only the validator differs
        (arms A/B use the always-valid validator, so attempt 0 always passes).
        Returns (raw_text, parsed_obj_or_None).  Raises on hard failure.
        """
        validator = S.VALIDATORS[role] if arm == "C" else (lambda t: S.always_valid(t))
        last_raw = ""
        prev_violation = None
        prev_violations: List[str] = []
        for attempt in range(MAX_REGENERATIONS + 1):
            msgs = build_messages(role, rnd, inner)
            if attempt > 0:
                # Regeneration feedback is MECHANICAL: the full list of
                # violated constraints plus the schema-derived contract.  No
                # rhetorical role-pressure (that would contaminate the
                # architecture-vs-prompting contrast the arms are testing).
                msgs[0]["content"] += (
                    "\n\nYour previous output was rejected by the output "
                    "validator.\nViolated constraints: {}\n{}\n"
                    "Return only the JSON object.".format(
                        ", ".join(prev_violations) or prev_violation,
                        S.schema_contract_text(role) if arm == "C" else "",
                    )
                )
            prompt_text = msgs[0]["content"]
            prompt_sha = hashlib.sha256(prompt_text.encode()).hexdigest()[:12]
            r = await actor_call(role, msgs)
            last_raw = r.text
            if not r.ok:
                raise RuntimeError("call failed: {}".format(r.error))
            vr = validator(r.text)
            if attempt > 0 or arm == "C":
                # Log every arm-C attempt (including the accepted one) plus any
                # regeneration in any arm, so the manipulation check has the
                # full per-attempt series.
                traj.regeneration_events.append({
                    "role": role,
                    "outer_round": rnd,
                    "inner_round": inner,
                    "attempt_index": attempt,
                    "raw_output_truncated_2000chars": r.text[:2000],
                    "validation_result": vr.as_log(),
                    "violated_constraint": vr.violated_constraint,
                    "latency_s": round(r.latency_s, 3),
                    "prompt_sha256_12": prompt_sha,
                    "prompt_chars": len(prompt_text),
                    "finish_reason": r.finish_reason,
                    "used_reasoning_fallback": r.used_reasoning_fallback,
                    "regenerated": (not vr.ok) and attempt < MAX_REGENERATIONS,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
            if vr.ok:
                log_msg(role, rnd, inner, r.text, attempt,
                        {"validation": vr.as_log(),
                         "latency_s": round(r.latency_s, 3),
                         "prompt_sha256_12": prompt_sha,
                         "prompt_chars": len(prompt_text),
                         "response_sha256_12": hashlib.sha256(
                             r.text.encode()).hexdigest()[:12],
                         "finish_reason": r.finish_reason,
                         "used_reasoning_fallback": r.used_reasoning_fallback})
                return r.text, vr.obj
            prev_violation = vr.violated_constraint
            prev_violations = list(vr.all_violations)
            log_msg(role, rnd, inner, r.text, attempt,
                    {"validation": vr.as_log(), "latency_s": round(r.latency_s, 3),
                     "prompt_sha256_12": prompt_sha,
                     "prompt_chars": len(prompt_text),
                     "response_sha256_12": hashlib.sha256(
                         r.text.encode()).hexdigest()[:12],
                     "rejected": True})
        # Exhausted regenerations.
        traj.hard_failure = "regeneration_exhausted:{}:{}".format(role, prev_violation)
        raise RuntimeError(traj.hard_failure)

    async def evaluate(candidate: str) -> Tuple[Optional[int], str, str]:
        budget.evaluator()
        pre = fill(P.EVALUATOR_PREPEND, task_description=task,
                   solution=candidate, result=gold)
        msgs = [{"role": "user", "content": pre + "\n\n" + P.EVALUATOR_APPEND}]
        r = await backend.chat(
            EVALUATOR_MODEL, msgs,
            tag="{}|{}|evaluator".format(traj_tag, arm))
        traj.retries += r.retries
        if not r.ok:
            raise RuntimeError("evaluator call failed: {}".format(r.error))
        c, hint = parse_evaluator(r.text)
        traj.evaluator_history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "candidate": candidate[:2000],
            "raw": r.text[:2000],
            "correctness": c,
            "latency_s": round(r.latency_s, 3),
            "finish_reason": r.finish_reason,
        })
        return c, hint, r.text

    try:
        stop = False
        stop_reason = "max_rounds_exhausted"
        last_correct: Optional[int] = None
        for rnd in range(1, MAX_OUTER_ROUNDS + 1):
            traj.rounds_used = rnd
            for inner in range(1, INNER_ROUNDS + 1):
                traj.inner_used += 1

                # ---- Planner slot ----
                raw, obj = await turn("planner", rnd, inner)
                if arm == "C":
                    plan_obj = obj
                    previous_plan = json.dumps(obj, ensure_ascii=False)
                    shared_history.append("[Planner]\n" + previous_plan)
                else:
                    previous_plan = raw
                    shared_history.append("[Planner]\n" + raw)
                    # Arms A/B: an answer authored here is simply accepted --
                    # nothing architectural prevents it.  Record ownership so
                    # role leakage is measurable.
                    b = extract_boxed(raw)
                    if b is not None:
                        current_answer, answer_owner = b, "planner"

                # ---- Executor slot ----
                raw, obj = await turn("executor", rnd, inner)
                last_executor_text = raw
                if arm == "C":
                    exec_obj = obj
                    current_answer = obj.get("answer")
                    answer_owner = "executor"
                    shared_history.append(
                        "[Executor]\n" + json.dumps(obj, ensure_ascii=False))
                else:
                    shared_history.append("[Executor]\n" + raw)
                    b = extract_boxed(raw)
                    if b is not None:
                        current_answer, answer_owner = b, "executor"

                # ---- Reviewer slot ----
                raw, obj = await turn("reviewer", rnd, inner)
                if arm == "C":
                    shared_history.append(
                        "[Reviewer]\n" + json.dumps(obj, ensure_ascii=False))
                    verdict = obj["verdict"]
                    reviewer_advice = obj["critique"]
                    # "accept" promotes the EXECUTOR'S CURRENT ANSWER VERBATIM
                    # BY REFERENCE.  The reviewer owns the submission decision
                    # but never authors answer text.
                    approve = (verdict == "accept")
                    route = {"accept": "agree", "revise_plan": "planner",
                             "revise_execution": "executor"}[verdict]
                    if approve:
                        answer_owner = "executor(promoted_by_reviewer_by_reference)"
                else:
                    shared_history.append("[Reviewer]\n" + raw)
                    route = parse_route(raw)
                    approve = (route == "agree")
                    reviewer_advice = raw[-1500:]
                    # Arms A/B: the reviewer MAY author a new answer.  If it
                    # does, it takes ownership -- the leak arm C forbids.
                    b = extract_boxed(raw)
                    if b is not None:
                        current_answer, answer_owner = b, "reviewer"

                traj.messages[-1]["route"] = route
                traj.messages[-1]["answer_owner_after_turn"] = answer_owner
                advice = reviewer_advice

                # ---- Evaluator, INSIDE the loop (config stop_on_agree=true,
                # reviewer_feedback_mode=hint).  Identical in every arm.
                if approve and current_answer is not None:
                    c, hint, _ = await evaluate(current_answer)
                    last_correct = c
                    if c == 1:
                        stop = True
                        stop_reason = "reviewer_agree_then_evaluator_pass"
                        break
                    # FAIL: the non-leaking hint becomes the next advice,
                    # exactly as reviewer_feedback_mode: hint prescribes.
                    advice = ("Evaluator feedback: FAIL / Score: False\n"
                              "Repair hint: {}".format(hint))
                    stop_reason = "reviewer_agree_evaluator_fail"
                elif approve and current_answer is None:
                    advice = ("Evaluator feedback: FAIL / Score: False\n"
                              "Repair hint: no final answer was produced; "
                              "produce a properly formed final answer.")
                    stop_reason = "agree_without_answer"
            if stop:
                break

        traj.final_answer = current_answer
        traj.correct = last_correct
        if current_answer is None:
            traj.stopping_condition = "no_answer_produced"
        elif stop:
            traj.stopping_condition = stop_reason
        else:
            # Rounds exhausted without a PASS. Grade the final candidate once
            # if it was never submitted, so every trajectory has a grade.
            if last_correct is None:
                c, _hint, _ = await evaluate(current_answer)
                traj.correct = c
                traj.stopping_condition = ("max_rounds_then_evaluator_pass"
                                           if c == 1 else "max_rounds_exhausted")
            else:
                traj.stopping_condition = "max_rounds_exhausted_after_fail"

        traj.messages.append({"role": "system", "answer_owner_final": answer_owner,
                              "timestamp": datetime.now(timezone.utc).isoformat()})

    except ModelUnavailable as exc:
        traj.stopping_condition = "model_unavailable"
        traj.error = str(exc)[:500]
        # Preserve the transport work spent before the determination.
        traj.retries += getattr(exc, "retries", 0)
        traj.unavailable_wait_s = round(getattr(exc, "latency_s", 0.0), 3)
    except CallBudgetExceeded as exc:
        traj.stopping_condition = "budget_exceeded"
        traj.error = str(exc)[:500]
        traj.final_answer = current_answer
    except Exception as exc:  # noqa: BLE001
        traj.stopping_condition = ("hard_failure" if traj.hard_failure
                                   else "runtime_error")
        traj.error = scrub("{}: {}".format(type(exc).__name__, exc), None)[:800]
        traj.final_answer = current_answer

    traj.wall_time_s = time.time() - t0
    traj.ended_at = datetime.now(timezone.utc).isoformat()
    return traj


# ==========================================================================
# Problem selection -- deterministic, identical for every arm and actor
# ==========================================================================


def load_problems(n: int, seed: int) -> List[Dict[str, Any]]:
    import pandas as pd  # noqa: PLC0415

    df = pd.read_parquet(PROBLEMS_PARQUET)
    df = df[df["benchmark_id"] == BENCHMARK_ID]
    df = df[df["problem_text"].notna() & df["answer"].notna()]
    df = df.sort_values("problem_uid", kind="mergesort").reset_index(drop=True)
    idx = list(range(len(df)))
    random.Random(seed).shuffle(idx)
    picked = sorted(idx[:n])
    out = []
    for i in picked:
        r = df.iloc[i]
        ref = "Final answer: {}".format(r["answer"])
        at = r.get("answer_text")
        if isinstance(at, str) and at.strip():
            ref += "\n\nOfficial solution:\n{}".format(at[:6000])
        out.append({
            "problem_uid": str(r["problem_uid"]),
            "problem_text": str(r["problem_text"]),
            "answer": str(r["answer"]),
            "reference": ref,
        })
    out.sort(key=lambda d: d["problem_uid"])
    return out


STUB_PROBLEMS = [
    {"problem_uid": "STUB_1",
     "problem_text": "Let n >= 2. Find the minimum m such that ...",
     "answer": "1 + \\lceil n/2 \\rceil",
     "reference": "Final answer: 1 + \\lceil n/2 \\rceil"},
    {"problem_uid": "STUB_2",
     "problem_text": "Compute the number of ways to ...",
     "answer": "561",
     "reference": "Final answer: 561"},
]


# ==========================================================================
# Resume support
# ==========================================================================


def load_done(path: Path) -> set:
    done = set()
    if not path.exists():
        return done
    with path.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                d = json.loads(line)
            except Exception:  # noqa: BLE001
                continue
            # A trajectory that died on an unavailable model is NOT complete --
            # retry it on the next run rather than baking in the outage.
            if d.get("stopping_condition") == "model_unavailable":
                continue
            done.add((d.get("problem_uid"), d.get("arm"), d.get("actor_model")))
    return done


# ==========================================================================
# Main
# ==========================================================================


async def amain(args) -> int:
    run_id = args.run_id or datetime.now(timezone.utc).strftime("run-%Y%m%dT%H%M%SZ")
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    arms = [a.strip().upper() for a in args.arms.split(",") if a.strip()]
    actors = [m.strip() for m in args.actors.split(",") if m.strip()]

    if args.dry_run:
        problems = STUB_PROBLEMS[: max(1, args.n)]
    else:
        problems = load_problems(args.n, args.seed)

    done = load_done(out_path)
    work = []
    for p in problems:
        for arm in arms:
            for actor in actors:
                if (p["problem_uid"], arm, actor) in done:
                    continue
                work.append((p, arm, actor))

    print("[runner] run_id={} config_version={} backend={}".format(
        run_id, CONFIG_VERSION, BACKEND))
    print("[runner] problems={} arms={} actors={}".format(
        len(problems), arms, actors))
    print("[runner] already complete (skipped): {}".format(
        len(problems) * len(arms) * len(actors) - len(work)))
    print("[runner] trajectories to run: {}".format(len(work)))
    print("[runner] out={}".format(out_path))
    if args.dry_run:
        print("[runner] DRY RUN: zero API calls, stub responses")

    tokens = TokenProvider(dry_run=args.dry_run)
    backend = Backend(tokens, dry_run=args.dry_run,
                      stub=StubResponder(
                          force_hard_failure=getattr(
                              args, "stub_hard_failure", False))
                      if args.dry_run else None)

    # Per-actor concurrency: one semaphore per actor model.
    sems = {a: asyncio.Semaphore(args.actor_concurrency) for a in actors}
    gsem = asyncio.Semaphore(args.concurrency)
    write_lock = asyncio.Lock()
    fh = out_path.open("a")
    counters = {"done": 0, "correct": 0, "error": 0, "unavailable": 0}

    async def one(p, arm, actor):
        async with gsem, sems[actor]:
            if not args.dry_run and actor in backend.unavailable_models:
                print("[skip] {} unavailable: {}".format(
                    actor, backend.unavailable_models[actor][:80]))
                counters["unavailable"] += 1
                # Still record the skip so the run is auditable.
                t = Trajectory(problem_uid=p["problem_uid"], arm=arm,
                               actor_model=actor, domain=DOMAIN, run_id=run_id,
                               stopping_condition="model_unavailable",
                               error=backend.unavailable_models[actor][:300],
                               started_at=datetime.now(timezone.utc).isoformat(),
                               ended_at=datetime.now(timezone.utc).isoformat())
            else:
                try:
                    t = await run_trajectory(p, arm, actor, backend, run_id)
                except Exception as exc:  # noqa: BLE001
                    t = Trajectory(problem_uid=p["problem_uid"], arm=arm,
                                   actor_model=actor, domain=DOMAIN, run_id=run_id,
                                   stopping_condition="runtime_error",
                                   error=scrub(traceback.format_exc()[-800:], None),
                                   started_at=datetime.now(timezone.utc).isoformat(),
                                   ended_at=datetime.now(timezone.utc).isoformat())
            async with write_lock:
                fh.write(t.to_json() + "\n")
                fh.flush()
                os.fsync(fh.fileno())
            counters["done"] += 1
            if t.correct == 1:
                counters["correct"] += 1
            if t.error:
                counters["error"] += 1
            print("[done {}/{}] {} arm={} actor={} stop={} correct={} "
                  "actor_calls={} eval_calls={} regen_events={} {:.1f}s".format(
                      counters["done"], len(work), t.problem_uid, t.arm,
                      t.actor_model.split("/")[-1], t.stopping_condition, t.correct,
                      t.actor_calls, t.evaluator_calls,
                      len(t.regeneration_events), t.wall_time_s))

    await asyncio.gather(*(one(*w) for w in work))
    fh.close()
    await backend.aclose()

    print("[runner] FINISHED done={} correct={} errors={} unavailable_skips={}".format(
        counters["done"], counters["correct"], counters["error"],
        counters["unavailable"]))
    if backend.unavailable_models:
        print("[runner] models recorded unavailable: {}".format(
            list(backend.unavailable_models)))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="3-arm PER experiment runner")
    ap.add_argument("--out", default=str(HERE / "results" / "per_arms.jsonl"),
                    help="JSONL output path (appended; used for resume)")
    ap.add_argument("--n", type=int, default=50, help="number of problems")
    ap.add_argument("--seed", type=int, default=20270101,
                    help="problem-selection seed (same problems for all arms)")
    ap.add_argument("--arms", default="A,B,C")
    ap.add_argument("--actors", default=",".join(DEFAULT_ACTORS))
    ap.add_argument("--concurrency", type=int, default=6, help="global concurrency")
    ap.add_argument("--actor-concurrency", type=int, default=3,
                    dest="actor_concurrency", help="concurrency per actor model")
    ap.add_argument("--dry-run", action="store_true",
                    help="zero API calls; stub responses validate the pipeline")
    ap.add_argument("--smoke", action="store_true",
                    help="small N (1 problem, gpt-oss only)")
    ap.add_argument("--run-id", default=None, dest="run_id")
    ap.add_argument("--stub-hard-failure", action="store_true",
                    dest="stub_hard_failure",
                    help="dry-run only: planner stub never satisfies the arm-C "
                         "schema, proving the hard-failure path")
    args = ap.parse_args()

    if args.smoke:
        args.n = min(args.n, 1)
        args.actors = "openai/gpt-oss-120b"
        args.concurrency = min(args.concurrency, 3)

    return asyncio.run(amain(args))


if __name__ == "__main__":
    raise SystemExit(main())
