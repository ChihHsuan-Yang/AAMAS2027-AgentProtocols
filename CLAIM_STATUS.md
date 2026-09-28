# CLAIM_STATUS — live board (2026-09-28 21:00)

Labels: OBSERVED · SUPPORTED · TENTATIVE · FALSIFIED · UNTESTED · DROPPED.
**Paper prose must never outrun this file.**

## FALSIFIED — do not resurrect

| claim | evidence |
|---|---|
| "Role labels do not produce distinguishable behavior" | 0.896 balanced accuracy, function-only features, trajectory-grouped CV. Killed by our own data. |
| "Arm C enforces the division of cognitive labor" | **Arm C leaves P1a at 0.034-0.231 and eq-density at 2.66-4.27/1k.** It does not touch computation. (D9, F09) |
| "All arms share the same context-visibility policy" | Measured: Arm C planner 1,530 chars vs Arm A 14,186. The logged VISIBILITY was false; corrected. (D9) |

## SUPPORTED — measured, validated, robust

| claim | evidence |
|---|---|
| Role distinguishability rests on format, not the governed function | 0.896 full vs **0.714** computation-only vs **0.768** length-only control |
| Per-clause compliance varies enormously inside one contract | 0.961 (decomposes) to 0.042 (abstains from computing) |
| Realized fidelity is actor-dependent under byte-identical prompts | all 6 pairwise differences significant; frozen metrics, human-validated κ 0.806/0.843 |
| **Arm C enforces ANSWER AUTHORSHIP** | **P2 = 1.000 in every Arm C cell**, vs Arm A 0.562 (gpt-oss) / 1.000 (gemma-4). This is the redesignated manipulation check and it passes. |
| Architectural enforcement engages and is discriminating | boundary rejections observed live; 4/4 planted violations caught, incl. `\boxed` smuggled in prose outside the JSON |

## OBSERVED — real but preliminary / needs stratification

| claim | status |
|---|---|
| Arm B collapses to N copies of one solver | 6/14 smoke, reproduced in campaign; prompt hashes distinct so not an A/A fault. **Needs: per-actor + informative-vs-ceiling stratification** (R-13) |
| Removing the answer field does not stop computing | the **second dissociation**, and now the paper's most on-thesis intervention result. Needs final-n confirmation. |
| Attrition is Arm-C-specific and actor-differential | C 6.2-8.3% vs A/B 0.0%; prereg Nones→0 moves Arm C/gpt-oss by **0.164**. Must be reported both ways. |

## UNTESTED — campaign in flight

- P3/P4 accuracy effects and the actor × intervention interaction (n too small yet)
- C′ − C context effect (arm launched, 5 rows)
- replicate noise floor (R-9)
- evaluator independence — gpt-oss grades itself (R-10)

## DROPPED_WITH_REASON

| claim | reason |
|---|---|
| Three-actor ordering claim (G1) | only 2 actors serving; gemma-3-27b and Llama-3.3-70B both 503. Amendment 1 fires. |
| Capability-vs-fidelity dissociation | the actor carrying it (gemma3) never came up; gemma_4_31b has **zero** baseline first-pass rows. **Amendment 2 fires: report UNRESOLVED.** |
| Two-domain claim | runner pins omnimath2; lab-bench's Planner contract has no computation clause anyway |
| Full n=4181 stretch | marginal power not worth risking C′ and the noise floor |

## The paper's honest one-line contribution, as of now

> Prompted roles are behaviorally distinguishable yet differ sharply in which
> clauses of their contract they realize; architectural enforcement of the
> **answer-authorship** boundary succeeds completely (P2 → 1.000) while leaving
> the **cognitive division of labor** untouched (computation density unchanged
> or higher) — a dissociation between specifying who *may answer* and who
> actually *does the work*.

That is narrower than the launch hypothesis and it is what the evidence supports.
