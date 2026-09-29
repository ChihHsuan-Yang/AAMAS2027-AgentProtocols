# Finding 15 — Blinded Opus-5 adjudication: INTERIM at 137/513 calls (101 items)

**2026-09-29. Run continuing; these are the interim numbers and they are already
decisive on the questions the adjudication was commissioned to answer.**
Protocol, rubric hash, blinding audit and audit trail: `adjudication/`.

## Judge stability — the thing repeated reps were for

| item | all-reps-agree |
|---|---|
| Q1 semantic redundancy | 34/35 = 0.971 |
| Q2 functional redundancy | **35/35 = 1.000** |
| Q3 new information | 33/35 = 0.943 |
| Q4 answer influence | 34/35 = 0.971 |
| **Q5 division of labour** | **35/35 = 1.000** |

The headline judgement is perfectly stable across independent calls.

## Rubric rates per cell — the result, by a fourth independent route

| actor / arm | n | Q1 sem | Q2 fun | Q3 new | Q4 infl | **Q5 division** |
|---|---|---|---|---|---|---|
| gemma-4 / A | 11 | 0.091 | 0.000 | 1.000 | 0.364 | **1.000** |
| gpt-oss / A | 8 | 0.125 | 0.000 | 1.000 | 0.500 | **0.875** |
| Llama-3.3 / A | 8 | 0.125 | 0.000 | 1.000 | 0.750 | **1.000** |
| **gemma-4 / B** | 10 | **1.000** | **1.000** | 0.300 | 0.000 | **0.000** |
| **gpt-oss / B** | 15 | **1.000** | **1.000** | 0.000 | 0.000 | **0.000** |
| **Llama-3.3 / B** | 8 | **1.000** | **1.000** | 0.375 | 0.250 | **0.000** |
| gemma-4 / C | 12 | 0.250 | 0.250 | 0.833 | 0.333 | 0.750 |
| gpt-oss / C | 7 | 0.857 | 0.143 | 0.857 | 0.286 | 0.857 |

**Every Arm A cell: division of labour in 0.875-1.000 of trajectories.
Every Arm B cell: 0.000. In all three actors.** Semantic and functional
redundancy are both 1.000 in every Arm B cell.

This is the fourth independent route to F14, and the sharpest: a blinded judge
that never saw the actor, the arm, or the hypothesis reproduces the result
exactly. Arm C largely restores the division of labour (0.750-0.857),
consistent with the enforcement working structurally.

## Validating the byte metric — what it is and is not good for

| scope | n | agreement | precision | recall | kappa |
|---|---|---|---|---|---|
| pooled | 101 | 0.693 | **1.000** | 0.279 | 0.308 |
| arm A | 25 | 0.960 | — | 0.000 | 0.000 |
| **arm B** | 33 | 0.273 | **1.000** | **0.273** | 0.000 |
| arm C | 28 | 0.893 | 1.000 | 0.400 | 0.523 |

**Precision is 1.000 in every cell where the flag fires — zero false positives
in 12 firings, and zero disagreement cases of the form "flag says collapse,
judge says division exists".** Recall is 0.273-0.400.

So the byte metric is a **sound but severely conservative detector**: what it
flags is genuinely collapsed, and it misses roughly three quarters of it.

## Terminology ruling (Bella §8)

The word **"collapse" is justified** — but for the *functional* measure, not
the byte one. Specifically:
- "collapse" may describe the Arm B state, which the judge finds is
  **1.000 semantically and functionally redundant with 0.000 division of
  labour** in all three actors.
- the byte rate must be called **"exact output duplication"** and reported as a
  conservative lower bound with precision 1.000 / recall ≈0.28.
- no byte-based *rate* may be used to compare actors (recall differs by actor).

## Caveats carried into the paper
- Interim (101 of 171 items); final numbers on completion.
- Precision is estimable only where positives exist: gpt-oss 14, gemma-4 3,
  Llama-3.3 0. Report per actor with the n.
- Model-based adjudication is **not** ground truth. The paper states judge,
  protocol, rubric, stability, and this limitation.
- The Arm C reading is partly mechanical: its validator forbids `\boxed`, so
  some of the restored "division of labour" is the constraint by construction.
