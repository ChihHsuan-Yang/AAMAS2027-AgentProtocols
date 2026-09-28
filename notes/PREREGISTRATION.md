# Pre-registration — AAMAS 2027 controlled role-enforcement experiment

> **COMMITTED 2026-09-28, before any confirmatory result was inspected.**
> Git history is the timestamp of record. Amendments below this banner are
> additive and dated; primary tests may not be redefined after results.

## AMENDMENT 1 (2026-09-28 18:00) — actor panel

Live probes (Master, this session) found only **two** actors reliably serving on
the Sophia vLLM endpoint:

| model | status |
|---|---|
| openai/gpt-oss-120b | **serving** |
| google/gemma-4-31B-it | **serving** |
| meta-llama/Llama-3.3-70B-Instruct | served at 17:32, **503 by 17:47** (flapping) |
| google/gemma-3-27b-it | **503 throughout** ("online but not ready") |

**Decision:** the campaign is **actor-incremental**. It runs with the actors
that are live, writes per-(problem, arm, actor) rows, and resumes to add an
actor if its endpoint recovers. The design does not block on an unavailable model.

**Consequence for the central test, stated in advance.** P4 (actor x
intervention interaction) requires >=2 actors and is *stronger* with 3. With two
actors it is a single difference-of-differences and cannot separate a capability
ordering from a fidelity ordering. **If the campaign ends with two actors, P4 is
reported as an interaction between those two only, and the
capability-vs-fidelity dissociation (Amendment 2) is reported as UNRESOLVED.**

## AMENDMENT 2 (2026-09-28 18:00) — the discriminating contrast

The rival account (arXiv:2608.21747, "capability equalizer") predicts benefit
tracks **low capability**. Our account predicts benefit tracks **low realized
fidelity**. These are separable only if the panel's capability ordering differs
from its fidelity ordering.

**Pre-declared:** capability is measured in-campaign as Arm A accuracy per actor;
realized fidelity as Arm A P1a/E2v2 per actor. Both are read off the SAME run.
If the two orderings coincide across the available actors, **the contrast is not
identifiable and we say so** rather than reporting whichever fits.

## AMENDMENT 3 (2026-09-28 17:55) — enforcement-rate definition

Arm C rejections caused by **output formatting** (a bare string where the schema
wants an array) are coerced and logged as soft signals, NOT counted as
enforcement events. The enforcement rate reported in the paper is computed from
**role-boundary violations only** (`additional_property:answer`,
`answer_leak:*`, `missing_field:*`). Rationale in DECISION_LOG D4.

---


Frozen 2026-09-28. Metrics frozen in `VALIDATION-FINAL.md`; no metric may be
changed after launch without recording the change here and re-validating.

## Arms
A = soft-role PER (current prompts, control)
B = generic-role PER (role instructions removed; topology/budget identical)
C = hard architectural specialization (output-space enforcement)

## Units and pairing
Unit = (problem, actor, domain). All arms run on the **same** problems, so every
test is paired. Clustering: bootstrap by problem.

## PRIMARY tests — these determine whether the central claim survives

**P1. Intervention → functional fidelity.**
  H0: fidelity(C) = fidelity(A), per actor.
  Metric: P1a (Planner) and E2v2 (Executor), frozen definitions.
  Test: paired difference, bootstrap CI by problem.
  *This is also the manipulation check.* Arm C should drive P1a to ≈1.0 by
  construction. **If it does not, Arm C did not engage and every downstream
  result from it is void.**

**P2. Actor × intervention interaction on functional fidelity.**
  H0: [fid(C)−fid(A)] is equal across actors.
  Test: difference-in-differences across actor pairs, bootstrap CI.

**P3. Intervention → task outcome.**
  H0: accuracy(C) = accuracy(A), per actor. McNemar on discordant problems.

**P4. Actor × intervention interaction on task outcome.**
  H0: [acc(C)−acc(A)] is equal across actors.
  **This is THE test of the paper's thesis** — not P3. A main effect without an
  interaction is 2608.21747's result transplanted into MAS.

**P5. Relationship between Δfidelity and Δoutcome.**
  Per actor, across problems: does the change in realized fidelity track the
  change in correctness? Reported as association; **explicitly not causal**,
  because both are outcomes of the same intervention.

## SECONDARY / exploratory (labelled as such in the paper)
- A − B (role-instruction contribution; replication of a published null)
- per-domain breakdown
- rejection/regeneration event analysis in Arm C
- role distinguishability (r2) recomputed per arm
- influence rate and restate rate (adopted from 2609.04217 for comparability)
- Reviewer behaviour / R4 (requires annotating the deferred 30 messages first)

## Multiplicity
Five primary tests. Holm correction across P1-P5 for the headline claim.
Secondary analyses are not corrected and are labelled exploratory.

## Stopping and exclusions, fixed now
- Trajectories failing to parse are counted as incorrect (not dropped), matching
  the existing corpus convention.
- Arm C messages rejected-and-regenerated are logged; the regenerated message is
  the one analysed. **Rejection count per trajectory is reported.**
- No arm is dropped after seeing results. If an arm fails its manipulation
  check, that fact is reported as the result.

## Pre-declared interpretations (all five, none privileged)

| pattern | conclusion |
|---|---|
| C>A for the low-fidelity actor, C≈A for the high-fidelity one | **Thesis supported.** Enforcement substitutes for realized specialization; the value of role organization is actor-conditional. |
| C>A equally for all actors | Enforcement helps, specialization is not actor-conditional. Collides with 2602.03128 Principle 4 and 2608.21747. Weak paper; consider not submitting. |
| C≈A≈B for all | Functional specialization is not the source of PER's benefit. **Abandon the direction.** |
| C<A | Role overlap is load-bearing — the organization relies on agents exceeding their contracts. Interesting inversion; reframes the paper. |
| effects reverse across actors | Strongest form; requires all three actors to claim. |

## What would make us NOT submit
- Arm C fails its manipulation check (P1 null).
- C≈A≈B everywhere (pattern 3).
- The interaction (P4) is null AND the main effect matches 2608.21747's
  published direction — that is their result in a new setting, not ours.
