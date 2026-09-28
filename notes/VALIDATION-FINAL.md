# Measurement validation — FINAL (2026-09-28)

Definitions frozen in `ANNOTATION_DEFINITIONS.md` before annotating.
72 P1a + 13 E2 messages adjudicated by hand, each with a recorded reason
(`analysis/results/r11_annotations.csv`).

## Final agreement

| measure | n | agreement | Cohen's κ | precision | recall | confusion |
|---|---|---|---|---|---|---|
| **P1a** Planner abstains from computing | 72 | **0.903** | **0.806** | 0.943 | 0.868 | TP33 FP2 FN3 TN34 |
| **E2v2** Executor consumes the plan | 13 | **0.923** | **0.843** | 0.833 | 1.000 | TP5 FP1 FN0 TN7 |

Both clear the 0.8 go/no-go threshold. Note P1a fell from 0.967 (n=30) to 0.903
(n=72) as annotation continued — the early figure was optimistic, which is the
normal direction and the reason for finishing the sheet.

## Error categories (the part that matters)

**P1a false positives (2) — symbolic results with no digits.** [61] asserts an
inradius of `s/2` and a ratio `pi/(4 sqrt3)` while *stating* it performs no
arithmetic; [85] states the expected final answer `4^{n-2}+2^{n+1}`. The
digit-based pattern cannot see these. **Consequence: P1a slightly
over-credits compliance**, i.e. true violation rates are marginally higher than
reported.

**P1a false negatives (3) — permitted content.** The pattern fires on restated
givens and on search instructions to the Executor ("Step 1: Execute setting
n=1"), both of which the contract explicitly allows.

The two classes point in **opposite** directions, so they do not bias the
actor comparison in a consistent way.

**Two of the five apparent FNs were MY annotation errors, not metric errors** —
[118] genuinely computes `2024 = 2^3·11·23` and a divisor count `(3+1)(1+1)(1+1)=16`.
Corrected in place.

**E2 false positive (1) — systematic, and fixed.** v1's `f_ref_step` matched
"Step 0"/"Inductive step" in the Executor's *own* construction. This is exactly
the solving-vs-following confusion to worry about. Metric rebuilt (v2: explicit
plan/Planner reference required).

## A rejected "improvement" — recorded because it is instructive

I built a P1a v3 adding (a) an instruction/given exclusion and (b) a symbolic-
result detector. **It made agreement worse: 0.903 → 0.694, recall 0.868 → 0.421.**
The symbolic detector fired on **9 of 9** messages judged compliant, including
on the phrase *"The answer should be a single integer"* — which is the contract's
**required answer-form section**. It penalised compliance.

**v3 rejected. P1a is frozen at v1**, with the FP limitation documented rather
than "fixed" into something worse.

## FROZEN definitions

- **P1a** = a Planner message containing zero evaluated numeric equalities
  (`= <number>`). omnimath2 only — the sole domain whose prompt imposes the
  clause. Known limitation: blind to digit-free symbolic results (~2/72).
- **E2v2** = an Executor message containing an explicit reference to the plan or
  Planner (`the plan`, `Planner`, `per the plan`, `as planned`, `planned steps`,
  `structured plan`). Bare step numbering excluded.
- **Functional specialization** = between-role behavioural separability on
  function-only features (r2).
- **Role fidelity** = per-clause compliance with the contract that agent's own
  domain prompt imposes; reported component-wise, never averaged across domains.

## GATE RESULT: actor ordering after freezing

| actor | P1a | E2v2 |
|---|---|---|
| gemma3_27b | **0.2662** [.2519,.2811] | 0.1123 [.1023,.1223] |
| gemma_4_31b | 0.1113 [.1046,.1179] | **0.2425** [.2340,.2509] |
| gpt_oss_120b | 0.0417 [.0379,.0454] | 0.0623 [.0581,.0667] |

**All six pairwise differences significant.** Actor-dependence of realized
fidelity is confirmed under the frozen metrics.

**But the two components order the top two actors differently** (P1a: gemma3 >
gemma_4; E2v2: gemma_4 > gemma3). `gpt_oss_120b` is last on both. Reported, not
reconciled — a single fidelity scalar would have hidden this, and any mediation
claim must name its component in advance.

## Does any current claim change?
- Claim 2 (actor-dependent realization): **unchanged, now validated.**
- Claim 3 (mediation): **weakened** — the two components disagree on the ranking,
  so "higher fidelity ↔ PER preferred" holds only for P1a.
- Nothing else moves.

## R4 — DEFERRED, not dropped
30 Reviewer messages are in the sheet, unannotated. R4 ("does not re-solve") is
off the mediator path: the mediation hypothesis concerns the plan→execute
handoff, not reviewer behaviour. **Needed for the final paper?** Only if the
paper characterises all three roles — which the 8-page limit may not permit. If
Arm C's constrained critique interface is reported, R4 must be annotated first,
because it is that arm's manipulation check. **Decision point, not an oversight.**
