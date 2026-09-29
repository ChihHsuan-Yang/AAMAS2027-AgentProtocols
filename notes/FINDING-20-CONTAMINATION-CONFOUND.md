# Finding 20 — The context-contamination confound, tested rather than argued

**2026-09-29. Closes the objection the novelty audit flagged from
2605.08563 ("Why Retrying Fails: Context Contamination"), which reports that
leaving failed attempts in context raises per-step error ~7.1x.**

## The objection

Arm B accumulates 5.8 failed submissions in `shared_history`; Arm A
accumulates 1.5. An objector says: **Arm B recovers less because its context
is dirtier, not because it lacks roles.** If true, our mechanism is wrong and
the paper is about prompt hygiene.

In H28 I said Arm C answers this. **That answer was too quick** — Arm C also
changes the output schema, so it varies two things at once. Here is the test
that varies one.

## Test 1 — the gradient exists inside every arm

Recovery by tercile of accumulated actor-message characters, first-pass-wrong:

| actor / arm | low ctx | mid ctx | high ctx |
|---|---|---|---|
| gemma-4 / A | 0.505 | 0.054 | 0.066 |
| gemma-4 / B | 0.132 | 0.011 | 0.011 |
| gpt-oss / A | 0.702 | 0.261 | 0.061 |
| gpt-oss / B | 0.324 | 0.191 | 0.213 |

**The contamination effect is real and large** — inside Arm A, recovery falls
0.702 → 0.061 with context volume. We should not dismiss it. So the question
is whether it *accounts for* the arm gap.

## Test 2 — match the arms on context volume

Recovery by pooled context quartile:

| actor | quartile | Arm A | Arm B |
|---|---|---|---|
| gemma-4 | Q1 | **0.649** (n=57) | **0.148** (n=81) |
| gemma-4 | Q2 | **0.244** (n=41) | **0.010** (n=96) |
| gemma-4 | Q3 | 0.053 (n=76) | 0.016 (n=61) |
| gemma-4 | Q4 | 0.059 (n=101) | 0.000 (n=37) |
| gpt-oss | Q1 | 0.923 (n=13) | 0.268 (n=168) |
| gpt-oss | Q2 | **0.694** (n=108) | **0.236** (n=72) |
| gpt-oss | Q3 | 0.279 (n=136) | 0.227 (n=44) |
| gpt-oss | Q4 | **0.072** (n=139) | **0.167** (n=42) |

**The arm gap survives context matching in Q1-Q2 for both actors** — gemma-4
0.649 vs 0.148 and 0.244 vs 0.010; gpt-oss 0.694 vs 0.236. Contamination does
not explain it at comparable context volume.

**But report Q4 honestly: gpt-oss REVERSES** (A 0.072 vs B 0.167). At the
highest context volumes Arm A's own contamination costs it more than the role
labels buy. That is a real limit on the claim and it goes in the text.

## A caveat on Test 2 that I nearly skipped

Context volume is itself downstream of treatment, so this is post-treatment
conditioning like everything else in the mechanism section. I checked whether
it is merely "cycles used" renamed: **it is not** — corr(context, cycles) is
0.695 / 0.575 in Arm A but only 0.243 / 0.140 in Arm B. They are distinct
variables, so the context-matched test carries information the cycle-matched
test does not. Both are reported; neither is causal.

## What separates the arms at matched full spend

At 6 cycles — identical budget, identical realized spend:

| actor | contrast | Arm A | Arm B | ratio |
|---|---|---|---|---|
| gemma-4 | recovery | 0.031 | 0.004 | 8.2x |
| gemma-4 | **P(frozen answer)** | 0.360 | 0.863 | **2.4x** |
| gpt-oss | recovery | 0.071 | 0.035 | 2.0x |
| gpt-oss | **P(frozen answer)** | 0.071 | 0.272 | **3.8x** |

The frozen-answer gap is present in both actors and in the same direction; it
is the more stable of the two contrasts at matched spend.

## Verdict

**The contamination objection is answered but not dismissed.** Contamination
is a real driver of recovery within every arm; it does not account for the
arm gap at matched context in the lower three quartiles; and in the top
quartile for gpt-oss it dominates and reverses the sign. All three statements
go in the discussion, with the 2605.08563 citation.
