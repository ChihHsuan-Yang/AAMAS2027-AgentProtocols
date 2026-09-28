# Measurement validation report (P0) — 2026-09-28

Definitions were frozen in `ANNOTATION_DEFINITIONS.md` **before** annotating.
Sample rebuilt (`r10`) because the v1 sheet left only 23 P1a-annotatable
messages; v2 is balanced on actor × automated-label so precision AND recall are
estimable. Adjudications with per-item reasons: `analysis/results/r11_annotations.csv`.

## Agreement

| measure | n | agreement | Cohen's κ | precision | recall | confusion |
|---|---|---|---|---|---|---|
| **P1a** Planner does not compute | 30 | **0.967** | **0.933** | 1.000 | 0.941 | TP16 FP0 FN1 TN13 |
| **E2** Executor uses the plan | 13 | **0.923** | **0.843** | 0.833 | 1.000 | TP5 FP1 FN0 TN7 |

Both clear the 0.8 go/no-go threshold.

## Error analysis — what kind of errors, not just how many

Bella's condition: a high aggregate is not enough if errors systematically
confuse solving with planning, or critique with re-solving. Examined:

**P1a — 1 error, conservative, not systematic.** [ann 1] has `n_eq=1`: a single
incidental numeral matched the evaluated-equation pattern in a message that is
otherwise a pure plan (DELTA + four required sections, explicit delegation).
The measure therefore **under-credits compliance**; it never over-credits
(precision 1.000, FP 0). For a claim of the form "planners frequently violate
the no-computation clause", a conservative measure biases *against* our own
hypothesis, which is the safe direction.

**E2 — 1 error, and it IS systematic.** [ann 19] contains **zero** occurrences
of "plan"/"Planner". The v1 measure fired on `f_ref_step` matching "Step 0" and
"Inductive step" — phrases inside the Executor's *own* construction. This is
precisely the solving-vs-following confusion Bella warned about, so the metric
was rebuilt (v2: explicit plan/Planner reference required, bare step numbering
dropped).

## Consequence of the fix — and it matters

| actor | E2 v1 | **E2 v2 (corrected)** |
|---|---|---|
| gemma3_27b | 0.833 | **0.112** |
| gemma_4_31b | 0.441 | **0.243** |
| gpt_oss_120b | 0.164 | **0.062** |

Decomposition shows why: gemma3's `f_ref_step` is **0.818** while its
`f_ref_plan` is only 0.105. It writes "Step N:" constantly in its own working.
v1 read that as plan consumption. **The actor ordering on E2 flipped**
(gemma3 → gemma_4_31b at rank 1). All pairwise v2 differences remain
significant, so the *actor effect* survives; its *direction* on this component
did not.

## Gate outcome (Bella's P0)

> "After validation, rerun the actor ordering and verify that the major
> actor-dependent fidelity differences remain. If that collapses, stop."

**It does not collapse — but one component reordered.**

- **P1a survives unchanged and still orders gemma3 (0.266) > gemma_4 (0.111) >
  gpt_oss (0.042)**, all pairwise differences excluding zero. This ordering
  still aligns with the PER advantage (gemma3 strongly prefers PER; gpt_oss
  does not).
- **E2v2 orders gemma_4 (0.243) > gemma3 (0.112) > gpt_oss (0.062)** — it no
  longer aligns.

**So the two fidelity components disagree about which actor is most faithful.**
A single collapsed "fidelity" scalar would have concealed that, which is the
strongest vindication of reporting components separately.

## What this does to the mediation story

It weakens it. The suggestive chain (higher fidelity ↔ PER preferred) holds for
the Planner-abstention component and **fails** for the Executor plan-consumption
component. Any mediation claim must now specify *which* aspect of realized
specialization is supposed to mediate, and defend that choice in advance rather
than after seeing which one fits.

## Frozen definitions

`P1a` = zero evaluated numeric results in a Planner message (omnimath2 only,
the sole domain imposing the clause).
`E2v2` = explicit reference to the plan or Planner; bare step numbering
excluded.
**Functional specialization** = between-role behavioural separability on
function-only features (r2).
**Role fidelity** = per-clause compliance with the contract the agent's own
domain prompt imposes, reported component-wise, never averaged across domains.

## Remaining gap
R4 (Reviewer re-solving) is **not yet annotated** — 30 messages are in the sheet.
It is not on the critical path for the mediator, so it is deferred, not skipped.
