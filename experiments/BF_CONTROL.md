# Arm Bf control: role-free with evaluator feedback delivered

Status: **LAUNCH APPROVED 2026-10-05 by X. Li** (co-author; Jane and Bella
informed, no reply before the deadline window — see DECISION_LOG.md D23).
Prepared 2026-10-03. Design and reading below are unchanged from 32b959a;
only the run commands were corrected (see "Run").

## The problem this control answers

The paper's headline is that, once told its answer is wrong, the
role-structured team (Arm A) revises while the role-free team (Arm B)
resubmits, and that this becomes a recovery gap (gemma-4, Omni-MATH:
0.222 vs 0.051; paired 37 vs 3, p = 2e-8).

**Arm B agents were never told.** In `runner.py` the evaluator's FAIL verdict
and repair hint are stored in `advice`. The Arm A and Arm C/C′ templates
interpolate `${advice}`. The Arm B template (`B_GENERIC_PREPEND`) has only
`${task_description}`, `${shared_history}` and `${slot_index}`;
`build_messages()` does not pass `advice` for Arm B; and `shared_history`
only ever receives `[Planner]`/`[Executor]`/`[Reviewer]` turns. This holds in
every committed version of `runner.py` and in `runner_xdomain.py`. The
`VISIBILITY` table listed `advice` for Arm B, which the template did not
honour.

So the A-vs-B recovery gap is confounded with feedback delivery, on both
benchmarks. First-pass results and the A-vs-C comparison are not affected.

`python3 experiments/test_bf_delivery.py` demonstrates this offline in a few
seconds (the check "Arm B prompts never contain evaluator feedback" passes
against the unmodified Arm B code path).

## The control

**Arm Bf** = Arm B + the evaluator feedback, and nothing else.

- Prompt templates are byte-identical to Arm B (`B_GENERIC_PREPEND`,
  `B_GENERIC_APPEND`); `prompts.py` is not changed.
- When the evaluator returns FAIL, the same string Arm A receives in
  `${advice}` (`Evaluator feedback: FAIL / Score: False\nRepair hint: …`) is
  shown to all three agents during the next cycle, as a trailing `[Evaluator]`
  entry of the shared-history block.
- Lifetime is one cycle, as `${advice}` has in Arm A (there it is overwritten
  by the Reviewer's text at the end of the following cycle).
- The feedback is not stored in `shared_history`, so it does not consume one
  of the 8 history slots and the agents' view of each other is the same as in
  Arm B.
- Until the first FAIL, an Arm Bf prompt is byte-identical to the Arm B
  prompt. Removing the `[Evaluator]` block from any Arm Bf prompt yields the
  Arm B prompt. Both are asserted by `test_bf_delivery.py`.
- Bf adds **no instruction** about what to do with the feedback. Arm A's
  Reviewer contract does ("If `${advice}` contains … FAIL … you MUST NOT
  output `[Agree]`"). That is deliberate: Bf isolates *information*, and what
  remains between Bf and A is the role contracts.
- Every actor message in an Arm Bf trajectory logs
  `evaluator_feedback_in_prompt` (true/false), so delivery is measured per
  message rather than declared.

Other changes in the same patch:

- `VISIBILITY["B"]` corrected to `["problem", "shared_history"]`; `"Bf"`
  added. This changes `CONFIG_VERSION` (Omni-MATH `25a04a554afcd006`,
  SciBench `d311904cee36c21b`), so new rows can never be silently pooled with
  the frozen ones. The frozen rows keep their recorded hashes.
- `AAMAS_PROBLEMS_PARQUET` and `AAMAS_AUTH_SCRIPT_DIR` environment variables
  override the two machine-specific paths. Defaults are unchanged.

## Scope

gemma-4 only (`google/gemma-4-31B-it`), the one actor carrying the recovery
result:

| run | problems | trajectories |
|---|---|---|
| Omni-MATH, `runner.py`, seed 20270101, n = 1600 | the frozen 1,600 | 1,600 |
| SciBench, `runner_xdomain.py`, n = 574 | the frozen 574 | 574 |

All 1,600 / 574 problems are run, not only the first-pass-wrong ones:
temperature 0 is not bit-deterministic on this endpoint, so which problems
fail first has to be observed in the Bf run itself. The Bf first-pass rate is
also a free replicate of Arm B's (same prompts up to the first verdict).

Rough cost, from the frozen campaign's rate (9,600 rows in about 8 h): a few
hours in total at the same per-actor concurrency. This is an estimate.

## Prerequisites

1. Access to the ALCF inference endpoint in `PROJECT_PATHS.md`, and the Globus
   auth helper (`inference_auth_token.py`). Point `AAMAS_AUTH_SCRIPT_DIR` at
   its directory if it is not at the default path. Re-auth is interactive.
2. The problems parquet used by the frozen runs
   (`…/hf_cache/release/data/problems/part-00000.parquet`). Point
   `AAMAS_PROBLEMS_PARQUET` at it if it is not at the default path.
3. `google/gemma-4-31B-it` and the evaluator `openai/gpt-oss-120b` both being
   served.
4. The frozen A/B rows for the analysis: `campaign_v2.jsonl` (Omni-MATH) and
   the SciBench JSONL, from `experiments/results/FROZEN/`,
   `experiments/results/xdomain/FROZEN_SCIBENCH/`, or the private HF artifact.

## Run

```bash
# 0. offline checks, zero API calls
python3 experiments/test_bf_delivery.py                       # must print ALL PASS
python3 experiments/runner.py --dry-run --n 2 --arms Bf

# 1. smoke: 5 problems, then look at one trajectory by hand
python3 experiments/runner.py --n 5 --arms Bf \
    --actors google/gemma-4-31B-it \
    --out experiments/results/bf/smoke.jsonl --run-id bf-smoke

# 2. Omni-MATH
python3 experiments/runner.py --n 1600 --arms Bf \
    --actors google/gemma-4-31B-it \
    --out experiments/results/bf/bf_omnimath_gemma4.jsonl \
    --run-id bf-gemma4-n1600 --concurrency 24

# 3. SciBench
python3 experiments/runner_xdomain.py --n 574 --arms Bf \
    --actors google/gemma-4-31B-it \
    --out experiments/results/bf/bf_scibench_gemma4.jsonl \
    --run-id bf-gemma4-scibench --concurrency 24
```

**Correction (2026-10-05).** The commands above omit `--actor-concurrency`,
whose default is 3: a single-actor run would then have at most 3 trajectories
in flight (about 15 h for 1,600). The launch uses
`--concurrency 20 --actor-concurrency 20` (gemma-4 was measured stable at 25
concurrent requests, `infra/throughput_ledger.md`). The actual launch is
`experiments/run_bf.sh`, which runs, in order, Omni-MATH Bf (n=1600),
SciBench Bf (n=574) and an Omni-MATH Arm A bridge (n=400, the prefix subset
of the 1,600; a drift check on the endpoint since 2026-09-30, never pooled
into any table).

Pre-launch gate: `experiments/bf_preflight.py` (frozen files match their
committed MANIFEST sha256; the parquet selects exactly the frozen problem
set; the auth helper returns a token). Monitoring and completion:
`experiments/bf_status.py`.

**Infrastructure failures (rule fixed before launch).** `runner.load_done()`
treats only `model_unavailable` as not done; a `runtime_error` row (a call
that failed after all transport retries, a failed evaluator call, an
unexpected exception) would be counted complete and, under the
pre-registered scoring, as incorrect. `experiments/bf_requeue.py` moves
`model_unavailable` and `runtime_error` rows to `*.infra_failed.jsonl` and
the identical command re-runs them. Every other stopping condition is a
protocol outcome and is never touched. A problem whose `runtime_error`
recurs 3 times keeps its last row (counted incorrect) and is reported.

Resume is automatic: re-run the identical command until every problem has a
row that is not `model_unavailable`. The run is complete when the cell is
full, not when the process exits.

Same problems as the frozen cells: problem selection is deterministic in
`--n` and `--seed` (default 20270101) given the same parquet. It is checked
after the run rather than assumed: `bf_control.py` prints how many problems
are common to A, B and Bf, and that number must be 1,600 (574 for SciBench).

Smoke gate before step 2: in `smoke.jsonl`, find a trajectory whose first
evaluator verdict is FAIL and confirm that the three actor messages of the
following cycle have `evaluator_feedback_in_prompt: true` and that their
`prompt_chars` grew accordingly.

## Analyse

```bash
python3 analysis/scripts/bf_control.py \
    --frozen experiments/results/FROZEN/campaign_v2.jsonl \
    --bf experiments/results/bf/bf_omnimath_gemma4.jsonl

python3 analysis/scripts/bf_control.py \
    --frozen experiments/results/xdomain/FROZEN_SCIBENCH/<frozen file>.jsonl \
    --bf experiments/results/bf/bf_scibench_gemma4.jsonl
```

Positive control: the script's A-vs-B lines must reproduce the paper
(Omni-MATH gemma-4: recovery 70/316 vs 16/316; paired n = 237, 37 vs 3;
SciBench: paired n = 99, 21 vs 2). If they do not, the wrong frozen file was
loaded; stop.

## How the result will be read (fixed before the run)

Primary comparison: paired recovery, A vs Bf, on problems first-pass-wrong
under both, exact McNemar; and final accuracy A vs Bf on all problems.

| outcome | reading |
|---|---|
| Bf recovers about as rarely as B; A vs Bf still clearly favours A | The role contrast survives feedback delivery. Bf replaces (or sits beside) B as the role-free condition and the storyline stands on a sound comparison. |
| Bf recovers about as often as A; A vs Bf not resolved | The A-vs-B gap was feedback delivery. The headline as written does not hold. |
| in between | Both contribute. Report the decomposition B → Bf → A. |

The behavioural measures (submissions vs revisions per cycle, Reviewer never
declining, one distinct answer) are reported for Bf beside A and B whatever
the outcome.

## Do not

- Do not modify, move or re-freeze anything under `FROZEN/` or the HF artifact.
- Do not pool Bf rows into the frozen files or into `FINAL_TABLES.py` inputs.
- Do not change `prompts.py`, the evaluator prompt, or any budget constant.
- Do not edit the manuscript from the result. Report the script output to
  Jane and Bella; what the paper says is their decision.
