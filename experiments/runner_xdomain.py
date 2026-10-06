#!/usr/bin/env python3
"""CROSS-DOMAIN replication runner -- SciBench (AAMAS 2027).

Copy of runner.py with the benchmark swapped from Omni-MATH to the SciBench
`text_only` slice (574 free-response problems, MIT).  runner.py is untouched.

WHAT DIFFERS FROM runner.py, AND WHY (see notes/XDOMAIN-DESIGN.md):

  1. BENCHMARK_ID/SLICE_ID/DOMAIN -> scibench / text_only / science.
  2. load_problems() filters on the parsed `available_slices_json` list and
     builds an answer-only reference (SciBench ships no official solution:
     answer_text is present for 5 of 580 rows, 0.9%).
  3. The Arm A role prompts and the evaluator prompt are DOMAIN-ADAPTED
     (option (b) of the brief).  Arm B's prompt is carried over BYTE-IDENTICAL
     -- it is already domain-neutral, and that is asserted in code below.

Rationale for (b) rather than verbatim reuse: Arm B's generic prompt contains
no domain language at all, so leaving Arm A's math-specific wording in place
("competition-level mathematics", "olympiad-style", "For Omni-MATH") would
make the two arms differ in TWO ways -- role structure AND domain fit -- and
the domain-fit difference runs against Arm A.  Adapting A restores a
single-variable manipulation.  Every structural clause of A is preserved
(role separation, DELTA, required structure, Diagnosis/Fix Instruction,
answer ownership, routing tags); only domain nouns and the answer-form
enumeration change.

CONSEQUENCE, per the brief: P1a and every other clause-specific fidelity
metric are NOT transported across domains and are not computed here.

3-arm Planner-Executor-Reviewer experiment runner (AAMAS 2027).

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
# DOMAIN-ADAPTED PROMPT SET  (option (b) -- see module docstring)
#
# `P` below SHADOWS the imported Omni-MATH prompt module for the rest of this
# file, so every P.<NAME> reference in the pipeline resolves to the SciBench
# wording.  The Omni-MATH originals stay reachable as _OMNI for the
# byte-identity assertions.
# ==========================================================================

_OMNI = P


class _XDomainPrompts:
    """SciBench role + evaluator contracts.

    Structure is held identical to the Omni-MATH contracts clause for clause;
    only domain nouns and the answer-form enumeration differ.
    """

    # ---- ARM A: Planner -------------------------------------------------
    A_SOLVER_PREPEND = """You are the Planner in a Planner→Executor→Reviewer loop for college-level science problems (chemistry and physics).

Problem:
${task_description}

Previous plan you wrote (may be empty):
${previous_plan}

Reviewer / System feedback (may be empty):
${advice}

HARD ROLE SEPARATION (critical):
- You MUST NOT carry out algebraic manipulation or numerical calculation yourself.
- You MUST NOT write computed intermediate values.
- You MAY restate givens from the problem.
- Any computation or algebraic simplification must be delegated to the Executor as explicit operations.

REQUIRED STRUCTURE:
1) Givens / quantities / physical or chemical context
2) Target quantity, its units, and answer form
3) Key laws, relations, or equations to use
4) Ordered execution steps for the Executor

In "Target quantity and answer form", explicitly identify what the final answer should look like:
- a numeric value carrying physical units
- a dimensionless number or ratio
- a value in a specific unit requested by the problem
- a short symbolic expression
- a sign-bearing quantity (state the sign convention)

DELTA REQUIREMENT:
- Begin with "DELTA:" and list 2-4 concrete updates vs the previous plan.
- If reviewer feedback exists, address it explicitly."""

    A_SOLVER_APPEND = _OMNI.A_SOLVER_APPEND          # byte-identical

    # ---- ARM A: Executor ------------------------------------------------
    A_EXECUTOR_PREPEND = """You are the Executor.
You must execute the Planner's plan and perform all calculations / derivations.

Problem:
${task_description}

Planner plan:
${solution}

Reviewer feedback for Executor (may be empty):
${advice}

REQUIREMENTS:
- Carry out the needed derivations and numerical work.
- Keep the reasoning readable and concise.
- Infer the required answer shape and units from the problem statement before finishing.
- The final answer is normally a numeric value with units; it may also be a dimensionless number or a short symbolic expression.
- Include units whenever the quantity has them, and use the unit the problem asks for.
- Carry enough precision through intermediate steps, and report the final value to a sensible number of significant figures.
- Preserve the sign of the quantity where the sign is physically meaningful.
- Your LAST line must be EXACTLY: \\boxed{<answer>}
- The boxed answer may be a number with units, a plain number, or a concise symbolic form.
- No punctuation after the final box."""

    A_EXECUTOR_APPEND = _OMNI.A_EXECUTOR_APPEND      # byte-identical

    # ---- ARM A: Reviewer ------------------------------------------------
    A_CRITIC_PREPEND = """You are the Reviewer in a Planner→Executor→Reviewer pipeline for college-level science problems.

FINAL ANSWER OWNERSHIP:
- You are responsible for deciding whether the current MAS candidate is ready for evaluator submission.
- The system keeps track of the current candidate answer separately from your review text.
- Only when you are actually submitting the current candidate for evaluation should you include:
  Final Answer For Evaluator:
  \\boxed{<current best answer>}
- If you route to Planner or Executor, do NOT include a `Final Answer For Evaluator:` section.
- Infer the required answer shape and units from the problem statement before judging correctness.
- For this benchmark, the boxed answer is normally a numeric value carrying physical units; it may also be a dimensionless number or a short symbolic expression.
- Check the unit, the magnitude, the sign, and the number of significant figures, not only the digits.
- An answer with the right number in the wrong unit, or off by a power of ten, is incorrect.
- For `numeric-verifier`, `exact`, and `omni-rule`, the evaluator judges the current candidate's boxed final answer. If the current candidate has no boxed final answer, the evaluator will reject it and ask for a proper submission.
- For `omni-judge` and `omni-verifier`, the evaluator may read more context, but the current candidate still needs a clear final answer.
- The final line of your response must still be exactly one route tag.
- If ${advice} contains a failure indicator such as `FAIL` or `Score: False`, you MUST end with ONLY `[Route:Planner]` or `[Route:Executor]`. You MUST NOT output `[Agree]`.
- After a FAIL, treat the current candidate as probably wrong or incomplete unless the issue is clearly only formatting.
- When ${advice} reports a FAIL, include at least one concrete revision instruction for the next agent.
- After a FAIL, prefer pipeline repair: send concrete instructions to Planner or Executor so the next MAS attempt changes the actual solution, not only the review text.
- Do NOT approve an answer only because the derivation sounds coherent; check the physical or chemical setup, the equation used, unit consistency, and the arithmetic.
- Do not repeat your previous reviewer message verbatim after a FAIL.
- Keep the review concise. Do NOT restate the full derivation.
- Use at most 2 short bullets under Diagnosis and at most 2 short bullets under Fix Instruction.
- Keep the total reviewer text before the final boxed answer brief.

Inputs you see:
- Problem
- Previous Planner plan
- Executor output
- System/Evaluator feedback in ${advice}

Problem:
${task_description}

Previous Planner plan:
${previous_plan}

Current submission to review:
${preliminary_solution}

System/Evaluator feedback:
${advice}"""

    A_CRITIC_APPEND = """Routing rules:
- Review the current submission and decide whether the current candidate is ready to submit.
- Approve only if the derivation supports the exact answer shape and unit requested by the problem.
- Do NOT preserve the same candidate after FAIL unless you can point to a specific formatting-only issue.
- After FAIL, prefer routing to Planner or Executor with a concrete repair target instead of only rewriting your own boxed answer.
- If the setup, the governing relation, or the interpretation is wrong, route to Planner.
- If the setup is sound but the derivation, arithmetic, unit conversion, or boxing is flawed, route to Executor.
- Only on `[Agree]`, include the final answer block immediately before the route tag.
- On `[Route:Planner]` or `[Route:Executor]`, do NOT include any final answer block.

Output format (STRICT):
Diagnosis:
- bullet 1
- bullet 2
Fix Instruction:
- bullet 1
If and only if you are submitting now, add:
Final Answer For Evaluator:
\\boxed{<current best answer>}
End with EXACTLY ONE tag on the last line:
  [Route:Planner] OR [Route:Executor] OR [Agree]"""

    # ---- ARM B: byte-identical to Omni-MATH -----------------------------
    # Asserted below.  Arm B carries no domain language, so there is nothing
    # to adapt; keeping the bytes identical makes that checkable.
    B_GENERIC_PREPEND = _OMNI.B_GENERIC_PREPEND
    B_GENERIC_APPEND = _OMNI.B_GENERIC_APPEND

    # ---- EVALUATOR: identical in every arm ------------------------------
    # Adapted for units / significant figures / scientific notation.  This is
    # COMMON MODE: byte-identical across arms A and B, so it cannot manufacture
    # an A-vs-B difference; it only sets the difficulty floor.  The unit and
    # tolerance clauses follow the upstream science_qa evaluator preset
    # (code_staging/configs/paper/prompt_presets/science_qa/per_hint_llm.yaml).
    EVALUATOR_PREPEND = """You are the Evaluator in a Planner→Executor→Reviewer loop for college-level science problems.

Problem:
${task_description}

Submitted candidate:
${solution}

Ground truth / evaluator-only reference material:
${result}

Requirements:
  - Decide whether the submitted candidate final answer is scientifically equivalent to the ground truth.
  - Focus on the final answer, not stylistic wording.
  - The reference material is the final answer for this problem. It is normally a numeric value with units.
  - Treat the following as EQUIVALENT (correct):
      * the same value written in a different but compatible unit (for example 1.0 dm^3 and 1.0e-3 m^3, or 1 atm and 101.325 kPa)
      * the same value in scientific, decimal, or engineering notation (for example 2.26e-5, 0.0000226, 22.6e-6)
      * LaTeX and plain-text renderings of the same unit (for example \\mathrm{atm}, \\text{atm}, atm)
      * a value agreeing with the reference to the precision the reference itself carries; judge agreement at the reference's number of significant figures, and allow a relative difference of about 1% to absorb rounding and constant choices
      * a value that differs only by including or omitting a unit that the problem clearly fixes
  - Treat the following as NOT equivalent (incorrect):
      * a different physical quantity, or the right number in an incompatible unit
      * a value off by a power of ten
      * a wrong sign where the sign is physically meaningful
      * a missing, placeholder, or non-numeric answer where a number is required
  - Do not reveal, quote, restate, or hint at the ground truth in your response.
  - Output a clear verdict label: `Verdict: PASS` or `Verdict: FAIL`.
  - If the answer is equivalent, output `Correctness: 1`.
  - Otherwise output `Correctness: 0` and give a short non-leaking repair hint that names the kind of mismatch without revealing the ground truth, for example: wrong unit, off by a power of ten, wrong sign, wrong quantity computed, insufficient precision, or formatting/boxing issue."""

    EVALUATOR_APPEND = _OMNI.EVALUATOR_APPEND        # byte-identical

    # ---- ARM C / C-prime: carried over verbatim -------------------------
    # Not run in this stage.  Carried so build_messages() cannot NameError if
    # arm C is later enabled, and so the config hash covers them.
    C_PLANNER_PREPEND = _OMNI.C_PLANNER_PREPEND
    C_PLANNER_APPEND = _OMNI.C_PLANNER_APPEND
    C_EXECUTOR_PREPEND = _OMNI.C_EXECUTOR_PREPEND
    C_EXECUTOR_APPEND = _OMNI.C_EXECUTOR_APPEND
    C_REVIEWER_PREPEND = _OMNI.C_REVIEWER_PREPEND
    C_REVIEWER_APPEND = _OMNI.C_REVIEWER_APPEND
    CP_PLANNER_PREPEND = _OMNI.CP_PLANNER_PREPEND
    CP_PLANNER_APPEND = _OMNI.CP_PLANNER_APPEND
    CP_EXECUTOR_PREPEND = _OMNI.CP_EXECUTOR_PREPEND
    CP_EXECUTOR_APPEND = _OMNI.CP_EXECUTOR_APPEND
    CP_REVIEWER_PREPEND = _OMNI.CP_REVIEWER_PREPEND
    CP_REVIEWER_APPEND = _OMNI.CP_REVIEWER_APPEND


P = _XDomainPrompts()

# The Arm B manipulation must be carried across domains unchanged.  If this
# ever fails, the A-vs-B contrast is no longer the same manipulation.
assert P.B_GENERIC_PREPEND == _OMNI.B_GENERIC_PREPEND
assert P.B_GENERIC_APPEND == _OMNI.B_GENERIC_APPEND

P.ALL_PROMPTS = {
    k: getattr(P, k) for k in (
        "A_SOLVER_PREPEND", "A_SOLVER_APPEND",
        "A_EXECUTOR_PREPEND", "A_EXECUTOR_APPEND",
        "A_CRITIC_PREPEND", "A_CRITIC_APPEND",
        "B_GENERIC_PREPEND", "B_GENERIC_APPEND",
        "C_PLANNER_PREPEND", "C_PLANNER_APPEND",
        "C_EXECUTOR_PREPEND", "C_EXECUTOR_APPEND",
        "C_REVIEWER_PREPEND", "C_REVIEWER_APPEND",
        "EVALUATOR_PREPEND", "EVALUATOR_APPEND",
    )
}


# ==========================================================================
# Held-constant experiment constants (identical across all three arms)
# ==========================================================================

BACKEND = "sophia_vllm"
BASE_URL = "https://inference-api.alcf.anl.gov/resource_server/sophia/vllm/v1"
# Machine-specific; override with AAMAS_AUTH_SCRIPT_DIR when running elsewhere.
AUTH_SCRIPT_DIR = os.environ.get(
    "AAMAS_AUTH_SCRIPT_DIR", "/Users/bellayang/work/agent-e/mas-eval")

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
    # CORRECTED 2026-10-03: the Arm B template never interpolates ${advice},
    # build_messages() never passes it, and shared_history only ever receives
    # [Planner]/[Executor]/[Reviewer] turns -- so Arm B agents never saw the
    # evaluator's FAIL verdict or repair hint. The previous entry listed
    # "advice" for B and was logged per trajectory as ground truth. Same class
    # of error as the Arm C entry below.
    "B": {"planner": ["problem", "shared_history"],
          "executor": ["problem", "shared_history"],
          "reviewer": ["problem", "shared_history"]},
    # Arm Bf (added 2026-10-03): Arm B with the evaluator's feedback DELIVERED.
    # Prompt templates are byte-identical to Arm B. When the evaluator returns
    # FAIL, the same advice string Arm A receives in ${advice} is shown to all
    # three agents for the next cycle, as a trailing "[Evaluator]" entry of the
    # shared-history block -- the same one-cycle lifetime ${advice} has in A.
    # Until the first FAIL, an Arm Bf prompt is byte-identical to Arm B's.
    "Bf": {"planner": ["problem", "shared_history", "evaluator_feedback"],
           "executor": ["problem", "shared_history", "evaluator_feedback"],
           "reviewer": ["problem", "shared_history", "evaluator_feedback"]},
    # Arm C is the manipulation: the executor's view of the planner is the
    # PARSED PLAN OBJECT, never the planner's raw text.
    # CORRECTED 2026-09-28 (master, D9-R3): the Arm C templates never
    # interpolate ${shared_history}; the previous entry claimed they did and was
    # logged per trajectory as ground truth. A false provenance field is worse
    # than an absent one. Measured: Arm C planner prompts average 1,530 chars vs
    # Arm A's 14,186.
    "C": {"planner": ["problem", "previous_plan", "advice"],
          "executor": ["problem", "parsed_plan", "advice"],
          "reviewer": ["problem", "parsed_plan", "parsed_execution", "advice"]},
    # Arm C-prime: C with shared_history restored -- the context control.
    "Cp": {"planner": ["problem", "shared_history", "previous_plan", "advice"],
           "executor": ["problem", "shared_history", "parsed_plan", "advice"],
           "reviewer": ["problem", "shared_history", "parsed_plan",
                        "parsed_execution", "advice"]},
}

# Machine-specific; override with AAMAS_PROBLEMS_PARQUET when running elsewhere.
PROBLEMS_PARQUET = os.environ.get("AAMAS_PROBLEMS_PARQUET", (
    "/Users/bellayang/Documents/note/projects/IEEE-BigData-SciAgentTrace/"
    "analysis/hf_cache/release/data/problems/part-00000.parquet"
))
BENCHMARK_ID = "scibench"
SLICE_ID = "text_only"
DOMAIN = "science"

DEFAULT_ACTORS = [
    "openai/gpt-oss-120b",
    "google/gemma-4-31B-it",
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
                "slice_id": SLICE_ID,
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
    reasoning_chars: int = 0   # F13: always record hidden-reasoning size


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
                    # DEFECT FIXED 2026-09-29 (F13): previously `reasoning` was
                    # captured ONLY when content was empty, so a short content
                    # with a long hidden reasoning trace silently discarded the
                    # reasoning. 81.8% of gpt-oss Arm B messages were affected
                    # and the old `used_reasoning_fallback` flag caught 5.7%.
                    # Always preserve the reasoning trace alongside content.
                    reasoning_txt = (msg.get("reasoning")
                                     or msg.get("reasoning_content") or "")
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
                        reasoning_chars=len(reasoning_txt),
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
                        '"answer":"24 atm"}')
            else:
                text = ('{"verdict":"accept","target":"executor",'
                        '"critique":"stub critique: derivation supports the form"}')
        elif arm in ("B", "Bf"):
            text = ("Continuing the shared work on the problem.\n"
                    "\\boxed{24 atm}\n"
                    + ("[Agree]" if role == "reviewer" else "[Continue]"))
        else:  # arm A
            if role == "planner":
                text = "DELTA: 1) restate givens 2) set target form\n1) Givens ...\n2) Target quantity: a pressure in atm"
            elif role == "executor":
                text = "Derivation: stub steps.\n\\boxed{24 atm}"
            else:
                text = ("Diagnosis:\n- looks complete\nFix Instruction:\n- none\n"
                        "Final Answer For Evaluator:\n\\boxed{24 atm}\n[Agree]")
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
    # Arm Bf only: evaluator feedback pending delivery in the NEXT cycle. Set
    # when the evaluator returns FAIL, cleared at the end of the following
    # cycle -- the lifetime ${advice} has in Arm A.
    evaluator_feedback = ""
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
        if arm == "Bf":
            # Measured, not declared: was evaluator feedback in THIS prompt?
            m["evaluator_feedback_in_prompt"] = bool(evaluator_feedback)
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
        if arm in ("B", "Bf"):
            slot = ROLE_ORDER.index(role) + 1
            if arm == "Bf" and evaluator_feedback:
                # Same string Arm A gets in ${advice}; template unchanged.
                hist = ((hist + "\n\n") if hist else "") + \
                    "[Evaluator]\n" + evaluator_feedback
            pre = fill(P.B_GENERIC_PREPEND, task_description=task,
                       shared_history=hist, slot_index=slot)
            return [{"role": "user", "content": pre + "\n\n" + P.B_GENERIC_APPEND}]
        # Arm C and Arm C-prime. Identical except C' restores shared_history
        # (the context control added after measuring a ~6x context gap vs A).
        cp = (arm == "Cp")
        if role == "planner":
            tmpl = P.CP_PLANNER_PREPEND if cp else P.C_PLANNER_PREPEND
            kw = dict(task_description=task,
                      previous_plan=(json.dumps(plan_obj) if plan_obj else ""),
                      advice=advice)
            if cp: kw["shared_history"] = hist
            pre = fill(tmpl, **kw)
            app = P.CP_PLANNER_APPEND if cp else P.C_PLANNER_APPEND
        elif role == "executor":
            # ARCHITECTURAL: only the PARSED plan object crosses this boundary.
            tmpl = P.CP_EXECUTOR_PREPEND if cp else P.C_EXECUTOR_PREPEND
            kw = dict(task_description=task,
                      plan_json=json.dumps(plan_obj, indent=2, ensure_ascii=False),
                      advice=advice)
            if cp: kw["shared_history"] = hist
            pre = fill(tmpl, **kw)
            app = P.CP_EXECUTOR_APPEND if cp else P.C_EXECUTOR_APPEND
        else:
            tmpl = P.CP_REVIEWER_PREPEND if cp else P.C_REVIEWER_PREPEND
            kw = dict(task_description=task,
                      plan_json=json.dumps(plan_obj, indent=2, ensure_ascii=False),
                      execution_json=json.dumps(exec_obj, indent=2, ensure_ascii=False),
                      advice=advice)
            if cp: kw["shared_history"] = hist
            pre = fill(tmpl, **kw)
            app = P.CP_REVIEWER_APPEND if cp else P.C_REVIEWER_APPEND
        return [{"role": "user", "content": pre + "\n\n" + app}]

    async def turn(role: str, rnd: int, inner: int) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """Run one actor turn with the validate -> regenerate loop.

        The loop structure is IDENTICAL in all arms; only the validator differs
        (arms A/B use the always-valid validator, so attempt 0 always passes).
        Returns (raw_text, parsed_obj_or_None).  Raises on hard failure.
        """
        validator = S.VALIDATORS[role] if arm in ("C", "Cp") else (lambda t: S.always_valid(t))
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
                        S.schema_contract_text(role) if arm in ("C", "Cp") else "",
                    )
                )
            prompt_text = msgs[0]["content"]
            prompt_sha = hashlib.sha256(prompt_text.encode()).hexdigest()[:12]
            r = await actor_call(role, msgs)
            last_raw = r.text
            if not r.ok:
                raise RuntimeError("call failed: {}".format(r.error))
            vr = validator(r.text)
            if attempt > 0 or arm in ("C", "Cp"):
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
                if arm in ("C", "Cp"):
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
                if arm in ("C", "Cp"):
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
                if arm in ("C", "Cp"):
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
                evaluator_feedback = ""   # one-cycle lifetime, as ${advice} in A

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
                    evaluator_feedback = advice
                    stop_reason = "reviewer_agree_evaluator_fail"
                elif approve and current_answer is None:
                    advice = ("Evaluator feedback: FAIL / Score: False\n"
                              "Repair hint: no final answer was produced; "
                              "produce a properly formed final answer.")
                    evaluator_feedback = advice
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
    # Slice membership is a JSON LIST, not a scalar.  `.notna()` is TRUE for an
    # empty list, so it must be parsed, not truth-tested -- the same trap that
    # makes SciBench's `options_json` look like every row is multiple choice.
    df = df[df["available_slices_json"].apply(
        lambda s: SLICE_ID in (json.loads(s) if isinstance(s, str) else (s or [])))]
    df = df[df["problem_text"].notna() & df["answer"].notna()]
    df = df.sort_values("problem_uid", kind="mergesort").reset_index(drop=True)
    idx = list(range(len(df)))
    random.Random(seed).shuffle(idx)
    picked = sorted(idx[:n])
    out = []
    for i in picked:
        r = df.iloc[i]
        # SciBench ships no official solution (answer_text present for 5 of
        # 580 rows, 0.9%), so the reference is answer-only for all but those.
        # The evaluator prompt is written for an answer-only reference.
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
     "problem_text": "What pressure would 131 g of xenon in 1.0 dm^3 exert at 25 C as a perfect gas?",
     "answer": "24 $\\mathrm{atm}$",
     "reference": "Final answer: 24 $\\mathrm{atm}$"},
    {"problem_uid": "STUB_2",
     "problem_text": "Calculate the molar mass of a gas given rho = 1.23 kg m^-3 ...",
     "answer": "169 $\\mathrm{g} \\mathrm{mol}^{-1}$",
     "reference": "Final answer: 169 $\\mathrm{g} \\mathrm{mol}^{-1}$"},
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

    # normalize arm names: A/B/C uppercase, Cp keeps its lowercase suffix
    def _norm_arm(a):
        a = a.strip()
        if a.upper() == "BF":
            return "Bf"
        return "Cp" if a.upper() in ("CP", "C'", "CPRIME") else a.upper()
    arms = [_norm_arm(a) for a in args.arms.split(",") if a.strip()]
    actors = [m.strip() for m in args.actors.split(",") if m.strip()]

    if args.dry_run:
        problems = STUB_PROBLEMS[: max(1, args.n)]
    else:
        problems = load_problems(args.n, args.seed)
        if args.limit_uids:
            keep = {u.strip() for u in args.limit_uids.split(",") if u.strip()}
            problems = [p for p in problems if p["problem_uid"] in keep]

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
    ap = argparse.ArgumentParser(
        description="cross-domain (SciBench) PER experiment runner")
    ap.add_argument("--out", default=str(HERE / "results" / "xdomain" / "scibench_AB.jsonl"),
                    help="JSONL output path (appended; used for resume)")
    ap.add_argument("--n", type=int, default=574, help="number of problems")
    ap.add_argument("--seed", type=int, default=20270101,
                    help="problem-selection seed (same problems for all arms)")
    ap.add_argument("--arms", default="A,B")
    ap.add_argument("--actors", default=",".join(DEFAULT_ACTORS))
    ap.add_argument("--concurrency", type=int, default=6, help="global concurrency")
    ap.add_argument("--actor-concurrency", type=int, default=3,
                    dest="actor_concurrency", help="concurrency per actor model")
    ap.add_argument("--dry-run", action="store_true",
                    help="zero API calls; stub responses validate the pipeline")
    ap.add_argument("--smoke", action="store_true",
                    help="small N (1 problem, gpt-oss only)")
    ap.add_argument("--run-id", default=None, dest="run_id")
    ap.add_argument("--limit-uids", default=None, dest="limit_uids",
                    help="comma-separated problem_uids; overrides --n (smoke use)")
    ap.add_argument("--stub-hard-failure", action="store_true",
                    dest="stub_hard_failure",
                    help="dry-run only: planner stub never satisfies the arm-C "
                         "schema, proving the hard-failure path")
    args = ap.parse_args()

    if args.smoke:
        args.n = min(args.n, 3)
        args.concurrency = min(args.concurrency, 6)

    return asyncio.run(amain(args))


if __name__ == "__main__":
    raise SystemExit(main())
