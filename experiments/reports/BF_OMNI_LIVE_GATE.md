# §9/§17 live delivery gate — Omni-MATH Bf, 1600/1600 rows

**Result: PASS.** 7608/7608 realized prompts hash-verified, 302/302
first-FAIL trajectories received the feedback. But the gate FAILED on its
first run, and the failure was in the instrument. That matters more than the
PASS, so it is recorded first.

## Cell integrity (checked before the gate)

| property | value |
|---|---|
| rows | 1600 / 1600 |
| distinct `problem_uid` | 1600 (0 duplicates) |
| arm / actor | all `Bf` / all `google/gemma-4-31B-it` |
| `config_version` | single value `25a04a554afcd006` |
| `visibility_policy` | single value, all three roles `[problem, shared_history, evaluator_feedback]` |
| `hard_failure` / `error` / `model_unavailable` | 0 / 0 / 0 |
| stopping conditions | 1475 `reviewer_agree_then_evaluator_pass`, 125 `max_rounds_exhausted_after_fail` |
| **UID set vs frozen A/B gemma-4 Omni cell** | **identical** (0 Bf-only, 0 frozen-only) |

## The first run said FAIL — and the gate was wrong, not the data

```
hash-verified 6504/7608 | first-FAIL 302 | delivered 293   GATE 9: FAIL
```

9 trajectories looked like delivery failures. That is exactly the defect this
control exists to find, so it was traced rather than explained away.

**Root cause: the gate advanced its evaluator-verdict index on every reviewer
turn.** The runner calls the evaluator only when the reviewer approves
(`if approve and current_answer is not None`, runner.py:898). A reviewer that
routes `continue` consumes no verdict. The gate's `ev_i += 1` fired
regardless, so from the first non-approving reviewer onward every verdict was
paired with the wrong turn.

`omni2_126` shows it exactly: reviewer turn 2 routes `continue`, and the
first evaluator timestamp (18:51:10) falls after reviewer turn 5 (18:51:05),
not turn 2. The runner's own `evaluator_feedback_in_prompt` flags turns 6-11.
The gate had the hint arriving three turns early, so the bytes diverged.

Two hypotheses were tested and rejected before this one: hint truncation
(`raw` is capped at 2000 chars in the log — but all 9 hints are 140-357 chars
and **0 of 791** FAIL verdicts in the cell hit the cap), and a divergence
between the gate's `hint_of()` and the runner's `parse_evaluator()` (they are
character-identical, runner.py:506-507).

**A second, independent instrument defect compounded it.** The gate does
`continue` on hash mismatch, which skips `shared.append`, so one mismatch
cascades into every later turn of that trajectory. Disabling only the cascade
— changing nothing else — already gives **302/302 delivered** and drops
mismatches from 1104 to 864. So the 9 "undelivered" trajectories were
manufactured by the gate twice over.

Fix: pair verdicts only on `route == "agree"`. After it, **7608/7608 prompts
hash-verify and mismatch is 0**, which makes the cascade moot.

## Proving the fixed gate can still fail

A gate edited until it passes is indistinguishable from a weakened one. Seven
controls, all against the *fixed* gate:

| control | expected | result |
|---|---|---|
| clean Bf cell | PASS | **PASS** |
| frozen Omni **arm B** (1600 rows, feedback never delivered) | FAIL | **FAIL** — 0/316 delivered, 0 prompts carry feedback |
| P1 `evaluator_feedback_in_prompt` flipped on 1 turn | FAIL | **FAIL** (metadata-vs-bytes) |
| P2 first FAIL verdict deleted | FAIL | **FAIL** (mismatch 3) |
| P3 one hint's text altered | FAIL | **FAIL** (mismatch 3) |
| P4b a **non-terminal** `agree` route flipped to `continue` | FAIL | **FAIL** (mismatch 3) |
| P5 two trajectories' hints swapped (right count, wrong content) | FAIL | **FAIL** (mismatch 6) |
| P6 one post-FAIL turn's `prompt_sha256_12` corrupted | FAIL | **FAIL** (mismatch 2) |

P5 is the one worth naming: a count-based check passes it, because the number
of hints delivered is unchanged and only their content is wrong. The gate
catches it because it compares bytes.

### A plant that passed, and why it is not a gap

The first version of P4 flipped the *first* `agree` route in the file to
`continue` and the gate still said PASS. The plant was weak, not the gate:
that reviewer was the **last turn** of its trajectory (turn 2 of 3), so the
verdict it pairs with is consumed after the final prompt was built. No
realized prompt changes, so no byte-checking instrument can see it — and
nothing about delivery is misreported either. Re-planted at a non-terminal
`agree` (P4b), the gate fails immediately. 1548 of 1600 trajectories end on
an agreeing reviewer, so the terminal case is the common one; a plant drawn
from it tests nothing. Recorded because "the plant passed" was briefly
indistinguishable from "the gate is blind".

## Scope

Omni only. §17 is **not** satisfied: `runner_xdomain.py` must be audited
separately on real SciBench Bf rows, which were still being generated when
this ran. The SciBench gate (`gate9_xdomain.py`) pairs verdicts by
**timestamp window** rather than a counter. That it does not share this
defect was initially only an argument, so it was **measured** on the Omni Bf
cell, where the runner's own `evaluator_feedback_in_prompt` flag supplies
ground truth for which turns carry feedback:

| pairing strategy | turns | wrong turns | wrong trajectories |
|---|---|---|---|
| counter (the defect) | 7608 | **621** | **124** |
| `route == "agree"` (the fix) | 7608 | **0** | **0** |
| timestamp window (xdomain's) | 7608 | **0** | **0** |

The counter row is the positive control: a comparison that could not detect
the known defect would prove nothing about the other two. Both the fix and
the window strategy reproduce the runner's own flags exactly.

Timestamp pairing has its own failure mode — a window containing more than
one verdict makes the result order-dependent, since the gate takes the first.
Measured: **0** such windows in Omni Bf (2536 reviewer turns) and **0** in the
partial SciBench Bf cell (165 turns), with no non-monotonic trajectories in
either. Windows containing *zero* verdicts (270 and 17) are the expected
non-approving reviewers.

This still does not satisfy §17: the SciBench gate must run on the completed
SciBench cell with its own domain-adapted prompts and evaluator wording.

No Bf result has been interpreted. This file is about delivery only.

## Correction: the `leak` counter was vacuous, then wrongly scoped

Two successive defects in the same check. Recorded in full because the first
one produced a clean-looking `leak: 0` in the PASS above.

### Defect 1 — the gate read a column that does not exist

`gate9.py` derived gold as `df.loc[uid].get("reference","")` from the raw
problems parquet. **That parquet has no `reference` column.** Its gold field is
`answer`; the runner *constructs* `reference` itself in `load_problems()`:

```python
ref = "Final answer: {}".format(r["answer"])      # experiments/runner.py:977
```

So `gold` was `""` for all 1,600 problems and the test `gold.strip() and
len(gold.strip())>1 and gold.strip() in pr` was short-circuited by its own
guard on every one of the 7,608 prompts. The reported `leak: 0` was **not a
measured null** — the check never executed its comparison. Confirmed directly:
1600/1600 golds had `len <= 1` under the guard, which is impossible for real
Omni-MATH answers.

Fixed to read `df.loc[uid,"answer"]`.

`gate9_xdomain.py` does **not** share this defect and needed no change. It
calls `runner_xdomain.load_problems()` rather than reading the parquet, and
that function builds `reference` the same way the runner does — verified
574/574 populated, e.g. `'Final answer: 24 $\mathrm{atm}$'`. Checked
separately per Sec.17 rather than inferred from the Omni fix.

### Defect 2 — the repaired check measured the wrong channel

With gold live, the gate reported **2,226 leaking prompts (29%)** and FAILed.
That rate is not credible, so the hits were attributed to their source:

| where the gold string came from | prompts | share |
|---|---:|---:|
| agent-authored history (the actors' own text) | 2,046 | 91.9% |
| the task statement itself | 177 | 8.0% |
| **the evaluator block — the only text Bf adds** | **3** | **0.1%** |

99.9% of the hits were the arm writing or reading the answer in its own
reasoning, which Bf does not cause and which is present identically in Arm B.
The check was scoped to the evaluator block.

### Why `leak` is now reported and not gated

Gating on `leak == 0` would fail the paper's own published Arm A. Measured on
the frozen `campaign_v2.jsonl` (sha256 `e4e53cb1…` verified against
`FROZEN/MANIFEST.json` before reading; file not modified), Omni / gemma-4,
first evaluator FAIL hint, using the word-form detector from
`BF_HINT_DISCLOSURE.md` rather than a substring test:

| cell | first-FAIL rows | disclosed | rate |
|---|---:|---:|---:|
| frozen A — hint delivered | 316 | 9 | 2.85% |
| frozen B — hint withheld | 316 | 5 | 1.58% |
| **Bf — hint delivered** | **302** | **4** | **1.32%** |

Fisher exact, A vs Bf: **p = 0.2634**. Bf's disclosure rate is not elevated
relative to the arm it is matched to; it is numerically lower. Arm B's 1.58%
is a property of the evaluator alone — those hints were generated but never
placed in any prompt.

Disclosure is therefore a property of the **shared evaluator signal**, which
Sec.4 holds constant between A and Bf by construction, not an artifact of
delivery. A gate that rejected it would reject the control for a property the
control is designed to preserve.

One related fact worth stating, because it bears on Sec.6: **A and Bf do not
receive the same hint bytes.** Of 241 uids that first-fail in both, only 15
(6.2%) have a byte-identical first hint. The evaluator is re-run per campaign
and is not deterministic. A and Bf share the *evaluator and its prompt*, not
the realized string.

### Control for the repaired detector

The obvious positive control — planting a gold answer into a hint — is
**invalid here and initially misled me**. Editing `evaluator_history[*].raw`
changes the reconstructed prompt, so its sha stops matching
`prompt_sha256_12`, the gate `continue`s past the row, and the leak count goes
*down* (2226 → 2223). A content check downstream of a hash guard cannot be
controlled by editing hashed content. The detector was instead controlled by
varying the **gold**, which is not hashed:

| control | result | expected |
|---|---|---|
| L1 gold := `"Score: False"` (in every evaluator block) | 2,154 hits = exactly the prompts carrying feedback | fires on all |
| L2 gold := `"ZZQX_NOT_PRESENT_ANYWHERE_42"` | 0 hits | silent |
| L3 gold[omni2_100] := a word from that trajectory's own hint | 36 prompts / 10 trajectories = baseline 33/9 **+ exactly 3/1** | +1 trajectory |

L1 and L2 bracket the detector; L3 shows it attributes a hit to the right
trajectory. Clean-input control (L2) included, per the rule that a detector
must be shown to stay silent as well as to fire.

### Effect on the PASS verdict: none

The PASS is carried by `mismatch == 0` (7,608/7,608 hash-verified), `multi == 0`,
`early == 0`, `flag_bad == 0`, `append_bad == 0`, and
`delivered_traj == traj_fail` (302/302). Each was independently positive-
controlled by a plant that must break it, and all plants still fail the amended
gate: P1 flag flipped, P2 first verdict deleted, P5 hints swapped between
trajectories, P6 sha corrupted — plus P3/P4b from the earlier pass. `leak` was
never a load-bearing component of those six, and is now reported rather than
gated. **GATE 9: PASS stands.**
