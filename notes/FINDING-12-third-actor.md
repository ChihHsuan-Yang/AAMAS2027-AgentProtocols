# Finding 12 — Third actor (Llama-3.3-70B): PRELIMINARY, n≈45/arm

**Verified by Master from `actor3.jsonl` directly. Run is ~11% complete
(138/1200). These numbers WILL move. Recorded now because they already change
how the paper must be framed.**

## Llama-3.3-70B patterns with gemma-4, not gpt-oss

| actor | project-rule collapse (arm B) | **count-matched (first-pass)** | mean role msgs |
|---|---|---|---|
| gpt-oss-120b | 0.846 | **0.698** | 5.95 |
| gemma-4-31B | 0.177 | **0.000** | 5.75 |
| **Llama-3.3-70B** | 0.659 | **0.000** | 13.5 |

Under the raw project rule Llama-3.3 (0.659) looks like a high-collapse model
near gpt-oss (0.846). **Under the count-matched rule it is exactly 0.000** — its
apparent collapse is entirely long-trajectory repetition, since it emits 13.5
role messages against ~5.9 for the others.

**This is the count-matched rule earning its keep.** Reporting the raw number
would have placed Llama-3.3 beside gpt-oss and inverted the paper's conclusion.
The rule was adopted *before* this actor produced data, which is the right order.

Corroborating: Llama-3.3's project-rule collapse is *higher in Arm A* (0.867)
than in Arm B (0.659) — the manipulation is not driving it, so it cannot be the
role-identity collapse the paper is about.

## A problem the worker did not flag: this actor is failing the task

| arm | n | accuracy | mean actor calls |
|---|---|---|---|
| A | 45 | **0.222** | 15.9 |
| B | 44 | **0.318** | 13.5 |
| C | 49 | **0.347** | 11.9 |

Against ~0.83 for both other actors. I checked whether this is an
extraction/format artifact: **it is not** — 45/45, 44/44, 49/49 trajectories
produce a `final_answer`, and the dominant stopping condition is
`max_rounds_exhausted_after_fail` (62) rather than parse failure. Llama-3.3 is
genuinely weaker on Omni-MATH at this budget.

## What this means for the paper — two readings, and I will not pick yet

**Reading 1 (supports the thesis).** Three actors, three profiles: gpt-oss
collapses on the first pass and loses nothing; gemma-4 never first-pass
collapses and loses accuracy; Llama-3.3 never first-pass collapses either. So
**first-pass role collapse is a property of one actor**, not a general
consequence of removing role prompts. That makes the phenomenon *more*
actor-specific, not less.

**Reading 2 (threatens the thesis).** With Llama-3.3 at 0.22-0.35 accuracy, it
sits near the floor where neither collapse nor role-removal can show much. It
may simply be uninformative as a third point rather than a third regime. Its
B−A is +0.096 at n≈45, but that is nowhere near stable.

**Ruling:** do not use Llama-3.3 to claim a *relationship* between collapse and
role value. It can be reported as a third profile on the collapse axis, with
its low accuracy stated plainly as a scope limit. If the completed run keeps
accuracy near 0.3, the honest framing is: *the panel spans two actors that
perform the task and one that largely does not*, and the inverse relationship
rests on the two that do.

## Follow-ups
- recompute at run completion (~4.9 h) with CIs
- pair the B−A accuracy side, currently unmeasured
- check whether Llama's `max_rounds_exhausted` rate makes its collapse metric
  non-comparable even under the count-matched rule
