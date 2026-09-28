# 3-Arm Planner-Executor-Reviewer (PER) Experiment Runner

AAMAS 2027. Tests whether role differentiation in a multi-agent pipeline comes
from **prompting** or from **architecture**.

## The three arms

All three arms run the **same pipeline code** in `runner.py`. Only the
manipulated variable differs.

| | Arm A `soft` | Arm B `generic` | Arm C `hard` |
|---|---|---|---|
| Prompts | original PER prompts, **verbatim** from the source config | ONE identical generic prompt for all 3 agents | minimal declarative output contracts |
| Role differentiation | rhetorical (prompt tells each agent its job) | **none** (role names only route turns) | **architectural** (schemas + information routing) |
| Who may author the answer | anyone (measured, not prevented) | anyone | executor only, by construction |

Held **identical** across arms (asserted in code, logged per trajectory):
3 actors + 1 evaluator; order Planner -> Executor -> Reviewer; 3 outer rounds;
2 inner rounds; context-visibility policy; model-call budget (30 actor + 6
evaluator); retry budget (4 transport retries, 3 regenerations); stopping rule
(reviewer approval **and** evaluator PASS); temperature 0; max_tokens 4096;
backend `sophia_vllm`; grading by the same evaluator LLM.

The validate -> regenerate loop **exists in every arm**. Arms A and B use an
always-valid validator, so attempt 0 always passes. Only arm C has a
constraint that can fail. That is the manipulation.

### Arm C enforcement (in `schemas.py`)

* **Planner** must emit `{"subproblems":[str],"strategy":[str],"dependencies":[str],"required_quantities":[str]}`,
  `additionalProperties: false`, **no answer field**. Output containing
  `\boxed{}` or "Final Answer" is rejected. Max 3 regenerations, then a
  recorded hard failure.
* **Executor** receives **only the parsed plan object** and the problem --
  never the planner's raw text. Emits `{"derivation":str,"answer":str}`.
* **Reviewer** emits `{"verdict":"accept"|"revise_plan"|"revise_execution","target":str,"critique":str}`,
  **no answer field**. `accept` promotes the **executor's current answer
  verbatim, by reference** -- the reviewer keeps submission ownership but
  cannot author a new answer.

Two deliberate validator subtleties, both discovered by running it:

1. `target` may be empty **only** when `verdict == "accept"` (an accepted
   submission is not routed anywhere). A revise verdict without a target or
   critique is rejected -- it would carry no actionable information.
2. `\boxed{}` / "Final Answer" are **hard** constraints. The looser phrase
   "the answer is X" inside a critique is recorded as a *soft signal*
   (`soft_signals`) but does **not** reject: it is ordinary review prose and
   cannot hijack the submission, because `accept` promotes by reference.

## Files

* `runner.py` -- the runner (pipeline, backend, resume, CLI)
* `schemas.py` -- arm C validators + the schema documents
* `prompts.py` -- all prompt text; arm A and the evaluator are byte-verbatim
  from `IEEE-BigData-SciAgentTrace/code_staging/configs/paper/per_hint_llm/config.yaml`
  (verified by diff)
* `results/*.jsonl` -- one JSON line per completed trajectory

## Running

```bash
# validate the whole pipeline with ZERO API calls
python3 runner.py --dry-run --n 2 --arms A,B,C

# prove the arm-C hard-failure path fires (dry run only)
python3 runner.py --dry-run --n 1 --arms C --stub-hard-failure

# small real run: 1 problem x 3 arms, gpt-oss only
python3 runner.py --smoke --arms A,B,C --out results/smoke.jsonl

# full run
python3 runner.py --n 50 --arms A,B,C --out results/per_arms.jsonl \
  --concurrency 6 --actor-concurrency 3
```

### Flags

| Flag | Meaning |
|---|---|
| `--out PATH` | JSONL output, **appended**; also the resume ledger |
| `--n N` | number of problems (default 50) |
| `--seed S` | problem-selection seed; same problems for every arm/actor |
| `--arms A,B,C` | which arms to run |
| `--actors "m1,m2"` | actor models (evaluator is always `openai/gpt-oss-120b`) |
| `--concurrency N` | global in-flight trajectory limit |
| `--actor-concurrency N` | per-actor-model in-flight limit |
| `--dry-run` | **zero API calls**; stub responses exercise every path |
| `--smoke` | 1 problem, gpt-oss only |
| `--stub-hard-failure` | dry-run only: planner stub never validates |
| `--run-id ID` | label for the run (default: UTC timestamp) |

## Resuming

Write is incremental: one `fsync`ed line per completed trajectory. On restart
the runner reads the output file and skips every completed
`(problem_uid, arm, actor_model)` key. Just re-run the same command.

Trajectories recorded as `model_unavailable` are **not** treated as complete --
they are retried on the next run, so a backend outage is not baked into the
dataset.

## Problem selection

`omnimath2` rows from the released parquet, filtered to rows with both
`problem_text` and `answer`, sorted by `problem_uid`, then a seeded shuffle.
Deterministic: every arm and actor sees **the same problems**.

## Instrumentation (per JSONL line)

`problem_uid`, `arm`, `actor_model`, `evaluator_model`, `domain`,
`benchmark_id`, `run_id`, `backend`, `config_version`, `actor_calls`,
**`evaluator_calls`** (logged explicitly -- the historical corpus omitted this
and it is a known confound), `retries`, `regeneration_events`,
`stopping_condition`, `final_answer`, `correct`, `hard_failure`,
`wall_time_s`, `started_at`/`ended_at`, `rounds_used`, `inner_used`, `budget`,
`visibility_policy`, `messages` (per-role text + timestamps),
`evaluator_history`.

Each entry in `regeneration_events` carries: `role`, `attempt_index`,
`raw_output_truncated_2000chars`, `validation_result` (incl. `all_violations`
and `soft_signals`), `violated_constraint`, `latency_s`, `prompt_sha256_12`,
`prompt_chars`, `finish_reason`, `regenerated`, `timestamp`.

**Validity probe.** Every turn logs a hash of the exact prompt sent and of the
response. If two roles ever produce identical output, the prompt hashes show
whether that is real convergence or an A/A bug (identical inputs). This caught
a real question on the first live run: in arm B the executor and reviewer
returned byte-identical text, and the differing prompt hashes confirmed it was
genuine convergence, not a wiring fault.

`config_version` hashes every prompt, schema, and held-constant knob, so
trajectories from different setups can never be silently pooled.

## Robustness

* Per-model unavailability (503 "online but not ready") is **recorded and
  skipped**, never crashed on. The model is marked unavailable for the rest of
  the run so the remaining work is not spent retrying a dead endpoint.
* Exponential backoff with jitter on 429/500/502/503/504/timeouts, capped at
  `MAX_TRANSPORT_RETRIES`; the loop is bounded and cannot spin on a dead backend.
* 401 triggers exactly one token refresh per retry slot.
* **The bearer token is never logged or written to any output file.** It is
  held in memory only, and every error string is scrubbed for it plus any
  `Bearer ...` header shape.

## Known limitations

* `gpt-oss-120b` returns chain-of-thought in a `reasoning` field and can spend
  the whole token budget there, leaving `content` empty. The client falls back
  to `reasoning` and sets `used_reasoning_fallback` so affected turns are
  identifiable. At `max_tokens: 4096` this was not observed in practice.
* `google/gemma-3-27b-it` and `meta-llama/Llama-3.3-70B-Instruct` were both
  returning 503 "online but not ready" at the time of writing. Only
  `openai/gpt-oss-120b` and `google/gemma-4-31B-it` were confirmed serving.
* Grading is a single LLM evaluator call at temperature 0. The evaluator is
  known to be nondeterministic on byte-identical inputs in this corpus, so
  treat single-trajectory grades accordingly.
