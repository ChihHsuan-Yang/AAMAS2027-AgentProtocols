# Campaign results — n≈8,140 trajectories (2026-09-29)

Run `main-n1600-v2` (still filling) + `armCp-n400` (complete, 800).
Quarantined runs excluded. All contrasts paired by problem, bootstrap by problem,
pre-registered Nones→0 rule applied.

## The pre-registered outcome: PATTERN E, with one exception

`PREREGISTRATION.md` defined five patterns. The accuracy result is **Pattern E
("Soft ≈ Generic ≈ Hard")** for the *enforcement* contrast, and the
pre-registration says: *"The central causal theory fails. Do not force it."*

### P3/P4 — accuracy

| contrast | gemma-4-31B | gpt-oss-120b |
|---|---|---|
| **C − A** (enforcement) | −0.0098 [−0.0278,+0.0082] | −0.0025 [−0.0205,+0.0155] |
| **B − A** (generic roles) | **−0.0303 [−0.0466,−0.0139]** | +0.0147 [−0.0025,+0.0327] |
| C′ − A | +0.0199 [−0.0099,+0.0497] | −0.0066 [−0.0464,+0.0331] |

**P4 (central test), C vs A: interaction −0.0073 [−0.0335,+0.0180] — NULL.**
Architectural enforcement of answer authorship changes accuracy for neither
actor, and there is no actor × intervention interaction.

**But B−A IS significantly actor-dependent: interaction −0.0450
[−0.0687,−0.0221].** Removing role instructions *hurts* gemma-4 (−3.0 pts) and
does not hurt gpt-oss (+1.5 pts). On the informative stratum this is large:
gemma-4 **−0.230 [−0.348,−0.106]**, gpt-oss +0.105 [−0.017,+0.227].

## What DID work: the manipulation, and the mechanism

### Manipulation check (redesignated to P2) — PASSES decisively
| arm / actor | P1a (computation) | **P2 (answer authorship)** |
|---|---|---|
| A / gemma-4-31B | 0.119 | 0.981 |
| A / gpt-oss-120b | 0.053 | **0.617** |
| **C / both** | 0.117–0.253 | **1.000** |
| **C′ / both** | 0.100–0.247 | **1.000** |

557–811 boundary rejections per Arm C cell. Enforcement is real and bites.

### The dissociation (the paper's finding)
Enforcement drives answer authorship to 1.000 while leaving computation
untouched — density 2.70/3.47 eq per 1k chars in Arm C vs 2.55/2.08 in Arm A,
i.e. **unchanged or higher**. *You can structurally stop an agent from
answering without making it stop doing the work.*

### Context confound — RULED OUT empirically
C′ restores context (planner 6,811 vs C's 1,898 chars; A is 14,489).
**C′ − C = +0.0179 [−0.0071,+0.0429] (gemma-4), −0.0115 [−0.0420,+0.0191]
(gpt-oss) — null in both.** The Arm C result is not a context artifact.

### Role collapse (F08) — large, and strongly actor-dependent
| arm | gemma-4-31B | gpt-oss-120b |
|---|---|---|
| A | 0.074 | 0.025 |
| **B** | **0.173** | **0.846** |
| C | 0.045 | 0.022 |
| C′ | 0.072 | 0.074 |

Under generic prompts **84.6% of gpt-oss trajectories** collapse to byte-identical
agent outputs. Architectural enforcement *prevents* collapse (0.022) — it holds
the organization apart even though it does not improve accuracy.

## Attrition — must be reported, it is Arm-C-specific
| arm | actor | hard-fail | acc (drop None) | acc (prereg None→0) | Δ |
|---|---|---|---|---|---|
| A/B | both | **0.000** | — | — | 0 |
| C | gemma-4 | 0.065 | 0.904 | 0.846 | 0.058 |
| C | gpt-oss | 0.054 | 0.902 | 0.824 | **0.078** |

Arm C looks *better* than A if you drop failures and *the same* if you follow
the pre-registered rule. We follow the rule.

## Honest headline

> Architecturally enforcing the answer-authorship boundary works perfectly as a
> mechanism (P2 → 1.000), prevents organizational collapse (2.2% vs 84.6%), and
> **changes task accuracy not at all** — while leaving the cognitive division of
> labor untouched. What role *instructions* buy is actor-dependent
> (interaction −0.045, significant); what architectural *enforcement* buys, in
> accuracy terms, is nothing.
