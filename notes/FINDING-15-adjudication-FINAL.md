# Finding 15 FINAL — Blinded Opus-5 adjudication, complete (171 items × 3 reps)

**513 calls, 0 errors. Supersedes the interim version.**
Protocol/rubric/audit trail: `adjudication/`. Rubric sha `4f624de5b1073940`,
frozen before the first judgement.

## Judge stability across independent reps

| item | all-reps-agree |
|---|---|
| Q1 semantic redundancy | 162/171 = 0.947 |
| Q2 functional redundancy | 164/171 = 0.959 |
| Q3 new information | 163/171 = 0.953 |
| Q4 answer influence | 153/171 = 0.895 |
| **Q5 division of labour** | **163/171 = 0.953** |

The headline judgement is stable at 0.953 across independent calls. (The
interim 1.000 was on 35 items; the full run is the number to report.)

## The result, per cell — a blinded judge reproduces it in all three actors

| actor / arm | n | Q1 sem | Q2 fun | **Q5 division of labour** |
|---|---|---|---|---|
| gemma-4 / A | 14 | 0.071 | 0.000 | **1.000** |
| gpt-oss / A | 14 | 0.071 | 0.000 | **1.000** |
| Llama-3.3 / A | 14 | 0.214 | 0.000 | **1.000** |
| **gemma-4 / B** | 14 | **1.000** | 0.857 | **0.143** |
| **gpt-oss / B** | 28 | 0.929 | **1.000** | **0.000** |
| **Llama-3.3 / B** | 14 | 0.929 | **1.000** | **0.000** |
| gemma-4 / C | 16 | 0.188 | 0.188 | 0.812 |
| gpt-oss / C | 14 | 0.929 | 0.143 | 0.857 |
| Llama-3.3 / C | 14 | 0.071 | 0.000 | **0.929** |
| gemma-4 / C′ | 15 | 0.267 | 0.067 | 0.933 |
| gpt-oss / C′ | 14 | 0.714 | 0.214 | 0.714 |

**Arm A: division of labour 1.000 in all three actors.
Arm B: 0.000-0.143. Arm C/C′: 0.714-0.933 — enforcement restores it.**

This is the central result, reproduced by a judge that never saw the actor, the
arm, the automated label, the correctness, or the hypothesis.

## Validating the byte metric

| scope | n | agreement | precision | recall | kappa |
|---|---|---|---|---|---|
| pooled | 171 | 0.719 | **1.000** | 0.262 | 0.305 |
| arm A | 42 | **1.000** | — | — | — |
| arm B | 56 | 0.286 | **1.000** | 0.259 | 0.024 |

**Zero false positives in 17 firings, and zero disagreement cases of the form
"flag says collapse, judge says division exists".** Recall 0.262.

So: a **sound but severely conservative** detector. Everything it flags is real
collapse; it misses roughly three quarters of it.

## Terminology ruling (Bella §8) — CONFIRMED

The word **"collapse" is justified**, for the *functional* measure:
Arm B is judged 0.929-1.000 semantically redundant with division of labour at
0.000-0.143, in every actor. The **byte** rate must be called **"exact output
duplication"** and reported as a lower bound with precision 1.000 / recall 0.26.
No byte-based rate may compare actors — recall differs by actor.

## Limitations carried into the paper
- Model-based adjudication is **not** ground truth. Judge, protocol, rubric,
  stability, and this limitation are all stated in the paper.
- Precision is estimable only where the flag fires: gpt-oss 14 positives,
  gemma-4 3, Llama-3.3 0. Reported per actor with n.
- Single judge family. A second frontier model as robustness judge was not run.
- The Arm C reading is partly mechanical: its validator forbids `\boxed`, so
  some restored "division of labour" is the constraint by construction.
