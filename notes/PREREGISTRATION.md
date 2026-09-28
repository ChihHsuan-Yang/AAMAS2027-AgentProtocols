# Pre-registration — written BEFORE any data from the intervention exists

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
