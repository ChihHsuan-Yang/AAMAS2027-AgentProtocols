# §11 — infra-failure handling, fixed BEFORE any Bf result is read

Directive §11: the policy is fixed before results; *"Do not change failure
handling after seeing the result. Keep all displaced infra-failure rows for
audit."*

Written while both cells contain **zero** infra failures, so the rule cannot
have been chosen to favour an outcome. No Bf recovery, paired, delta or
p-value figure is read in this file.

## Current state (structural counts only)

| cell | rows | `hard_failure` | `error` | `model_unavailable` |
|---|---:|---:|---:|---:|
| Omni Bf (complete) | 1600 | **0** | **0** | **0** |
| SciBench Bf (in progress) | 429 | **0** | **0** | **0** |

Stopping conditions observed, both cells: `reviewer_agree_then_evaluator_pass`
and `max_rounds_exhausted_after_fail`. Neither is an infra failure —
`max_rounds_exhausted_after_fail` is a **scientific** outcome (the team used
its cycles and never passed) and must never be dropped. No
`.infra_failed.jsonl` sidecar exists for either cell.

The policy below is therefore currently **vacuous**. It is declared anyway,
because a rule written after a failure appears is a rule chosen with knowledge
of which rows it would remove.

## The policy

1. **Only `stopping_condition == "model_unavailable"` counts as an infra
   failure.** This is the one condition `bf_control.py:150` drops, and it means
   the endpoint did not serve the request — no deliberation happened.
2. **`hard_failure` and `error` rows are NOT auto-dropped.** `hard_failure` is
   set by `regeneration_exhausted` (runner.py:798), which is a property of the
   arm's own constraint handling, not of the infrastructure. If any appears, it
   is reported and adjudicated explicitly in the final report, not silently
   removed.
3. **`max_rounds_exhausted_after_fail` is never dropped.** It is the outcome
   the recovery metric exists to measure.
4. **Every displaced row is retained**, written to the cell's
   `.infra_failed.jsonl` sidecar, counted in the freeze manifest as
   `infra_failed_rows_retained` (`bf_freeze.py:100`), and reported. Nothing is
   deleted.
5. **A displaced row is re-run at most once**, under the same frozen config and
   the same model. If it fails again it stays displaced and is reported as
   such. Re-running is never conditional on the row's outcome.
6. **If displaced rows exceed 1% of a cell (16 Omni / 6 SciBench), the cell is
   reported as degraded** and the shortfall stated in the final report rather
   than absorbed into a denominator.

## The drop path was proven to bind

A rule nobody has shown to fire is not known to work. Planted into a **copy**
(nothing committed, source untouched): 7 Omni Bf rows re-marked
`stopping_condition = "model_unavailable"`.

| quantity | baseline | after planting 7 |
|---|---:|---:|
| common problems | 1600 | **1593** |
| actor messages scanned | 7608 | 7587 |
| `reviewer_agree_then_evaluator_pass` | 1475 | 1468 |
| first-FAIL delivery | 302/302 | 302/302 |

Exactly 7 problems left the denominator. **The drop binds.**

A detail that matters for reading future output: the baseline run prints **no**
NOTE line, because `bf_control.py:164` emits it only when
`len(common) < len(cells["A"])`. Silence means the cell is at full n. The NOTE
appearing at all is a signal that rows are missing — from infra drops, or from
an incomplete run (the invocation hazard recorded in `BF_S13_GATE.md`).

### A false negative this test produced first

My first binding test reported "NO CHANGE: drop did not bind" — wrong on two
counts. I passed `--actor google/gemma-4-31B-it`, but `bf_control.py:58`
defines `actor()` as `r["actor_model"].split("/")[-1]`, so the flag wants the
bare `gemma-4-31B-it`. **Both** runs exited immediately with `no rows for arm
A`, produced no output, and my regex found nothing in either — identical empty
results read as "no difference". The comparison was between two failures.

Recorded because the failure mode is the point: a control that errors out in
both conditions looks exactly like a clean null. The fix was to assert the
baseline produced parseable output *before* comparing it to anything.

## Not done

No row dropped, re-run or deleted. `bf_control.py` unmodified. No Bf outcome
read. The plant existed only in `/tmp` and was removed.
