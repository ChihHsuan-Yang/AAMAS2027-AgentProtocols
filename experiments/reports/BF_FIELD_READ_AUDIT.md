# Field-read audit of the Bf analysis scripts — clean

Status: COMPLETE. **No defect found.** Written up anyway because the sweep
itself produced three false alarms, and the way it produced them is the same
error shape the sweep was looking for.

## Why this was run

`gate9.py` was found reading `reference` off the problems parquet, a column
that does not exist there (see `BF_OMNI_LIVE_GATE.md`). A guarded comparison
against `""` then reported a clean `leak: 0` that had never executed. Since
one wrong field read had already shipped, every field read in the scripts that
will produce the Sec.13-16 numbers was enumerated and checked against the data
they will actually be run on.

Scripts audited: `analysis/scripts/bf_control.py`, `analysis/scripts/bf_drift.py`,
`analysis/scripts/bf_verdict.py`, `experiments/bf_freeze.py`.

## Result

Every read resolves on the live Bf Omni cell (1,600 rows / 9,208 messages /
2,266 verdicts).

| level | fields read | all present? |
|---|---|---|
| trajectory row | `actor_model`, `arm`, `backend`, `benchmark_id`, `budget`, `config_version`, `correct`, `ended_at`, `evaluator_history`, `evaluator_model`, `inner_used`, `messages`, `problem_uid`, `request_timeout_s`, `started_at`, `stopping_condition` | **16/16, 1600/1600 each** |
| message | `role`, `text`, `route`, `evaluator_feedback_in_prompt`, `prompt_sha256_12` | yes — partials are role structure |
| verdict | `correctness`, `raw`, `timestamp` | **2266/2266 each** |

The message-level partials are by design, not loss:

| role | msgs | text | route | fb_flag | sha |
|---|---:|---:|---:|---:|---:|
| planner | 2536 | 2536 | 0 | 2536 | 2536 |
| executor | 2536 | 2536 | 0 | 2536 | 2536 |
| reviewer | 2536 | 2536 | 2536 | 2536 | 2536 |
| system | 1600 | 0 | 0 | 0 | 0 |

All three actor roles carry `text`/`fb_flag`/`sha` on 100% of turns; `route`
is reviewer-only; `system` turns are not actor turns and are never read as such.

One scoping fact worth recording: `evaluator_feedback_in_prompt` exists on
**0** frozen A and B messages — it is an addition of the Bf run. Block [0] of
`bf_control.py` is the only consumer and iterates `R["Bf"]` exclusively
(verified by parsing the block), so it is correctly scoped. A future reader
must not extend that block to A or B, where the field would read as absent.

## The sweep's own three false alarms

The first version of this audit reported `inner_used`, `final`, and
`evaluator_feedback_in_prompt` as ABSENT. All three were my errors:

| alarm | reality | cause |
|---|---|---|
| `inner_used` 0/9208 ABSENT | present **1600/1600 at row level** | I put a row field in the *message* field list and searched messages for it. Messages genuinely lack it, so it read as absent at a level it is never read from. |
| `final` 0/1600 ABSENT | not a data read at all | `bf_drift.py:143` uses `"final"` as a key in a dict **it constructs itself**. |
| 5 × `verdict.sha256` etc. ABSENT | not verdicts | my sweep assumed `v` means an evaluator verdict; in `bf_freeze.py:136` `v` is a **cells-manifest value** from `for k, v in cells.items()`. |

The consequence of alarm 1 is worth stating plainly. Had I trusted it, I would
have "fixed" `bf_control.py:240` — a line that is correct — on the evidence of
a check pointed at the wrong object. The printed `cycles` column is **4.08**,
not the `0.00` the false alarm implied, and `revisions = 4.08 - 3.21 = 0.87`
is positive and plausible. An independent derivation from the traces (reviewer
turns per first-pass-wrong trajectory) gives **4.08**, matching `inner_used`
exactly, which confirms the field means what the script assumes.

The repaired sweep resolves each read to the object level where it **actually
occurs**, by parsing the scripts with `ast` instead of hand-sorting field names
into guessed buckets.

## Caveat on scope

This audit proves the fields are *present*. It does not prove each field
*means* what its consumer assumes — that is a separate question, checked here
only for `inner_used` (independently re-derived, matches). Presence is the
weaker property, and it is the one the parquet defect violated.
