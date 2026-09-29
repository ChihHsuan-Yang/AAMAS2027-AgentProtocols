# CLAIM_STATUS — live board (2026-09-29, post-pivot)

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


---

# 2026-09-29 — post-pivot board

## The claim ladder Bella specified (§21)

| level | claim | status |
|---|---|---|
| **A** descriptive | removing role instructions can cause extreme organizational collapse | **SUPPORTED** — first-pass collapse 0.698 (gpt-oss) vs 0.000 (Arm A); audited against determinism, normalization, retry convergence, difficulty |
| **B** actor-specific surprise | the actor with the largest collapse loses the least | **SUPPORTED** — and it runs both ways: gpt-oss collapses 0.698 and loses nothing; gemma-4 collapses 0.000 and loses 0.029 |
| **C** structural dissociation | enforcement restores structure without restoring capability | **SUPPORTED** — P2 → 1.000, collapse → ~0, C−A null both actors, C′ rules out context |
| **D** functional dissociation | structural compliance ≠ cognitive division of labor | **SUPPORTED** — Planner computation persists at or above soft-role density; the pre-registered P1a objective **failed** (see PREREGISTRATION-PROVENANCE.md) |
| **E** broad | visible specialization is neither necessary nor sufficient | **NOT CLAIMED** — needs human validation (in flight) and the third actor |

## Mechanism (F11) — SUPPORTED, and it is what lifts this above an anecdote

> Role differentiation is load-bearing for **error recovery**, not for
> **first-pass solving**, and only for the actor that cannot otherwise escape a
> wrong consensus.

gemma-4 first-pass **0.809 → 0.809** (unchanged); recovery **0.490 → 0.045**.
Without roles it reaches unanimity 0.954, is wrong in 0.436 of those, escapes
only 0.638. gpt-oss stays split 0.251 and escapes 0.772.

## Corrections logged this session
- gpt-oss **whole-arm** B−A is **+0.0078 [−0.0102,+0.0259]** — null. The +0.0171
  is the differentiated→collapsed **subset**. Never conflate.
- Mechanism A ("first agent already solved it") is **REFUTED**: gpt-oss first
  agent correct 0.481, 38% of finals rescued from a wrong start.
- gemma-4's raw 0.177 collapse was a trajectory-length artifact; count-matched
  it is **0.000**.

## Provenance rulings (binding on the manuscript)
- **P4 (pre-registered primary) is NULL.** Reported as Pattern E.
- **B−A is POST-HOC.** It was secondary/exploratory in the committed file. It
  must be labelled post-hoc however important it is.
- **The P1a manipulation objective FAILED.** Reported as a failed objective
  first, an insight second.
