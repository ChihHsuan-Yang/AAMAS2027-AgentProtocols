# Claim ladder — evidence required vs evidence held (2026-09-28)

## Claim 1 — "Nominal LLM roles do not reliably imply distinct functional behaviors"

**Evidence required:** behavioural measurement showing role-prompted agents are
functionally similar, on matched prompts, with a validated instrument.

**Status: FALSIFIED IN ITS STRONG FORM, by our own data.** Roles are highly
distinguishable — 0.896 balanced accuracy (3-way) and AUC 0.995 (Planner vs
Executor) from function-only features, trajectory-grouped CV. We must not make
this claim.

**Weak form that survives:** distinguishability is carried by *output format and
answer commitment*, not by the governed cognitive division — computation-only
features give AUC 0.714, barely above the length-only nuisance control (0.768).
Plus component-wise contract violation: Planner abstains from answering 0.540
but from computing 0.042.

**Novelty: LOW.** MAST FM-1.2 "Disobey role specification"; role-overstepping
already published at 46.4%/43.4% (2604.02770); effective rank 2.17/3.0
(2604.03809); "role drift" named and instrumented (2607.21627). **Cannot lead
with this.**

---

## Claim 2 — "Functional role realization varies systematically across actor models"

**Evidence required:** same organization, same prompt, different actors, with
CIs, within-domain (so the contract is constant).

**Status: HELD, strongly.** omnimath2, byte-identical prompts:

| actor | Planner no-computation | Executor uses-plan |
|---|---|---|
| gemma3_27b | 0.266 [.252,.281] | 0.833 [.821,.845] |
| gemma_4_31b | 0.111 [.104,.118] | 0.441 [.431,.450] |
| gpt_oss_120b | 0.042 [.038,.045] | 0.164 [.157,.170] |

All pairwise differences exclude zero. n = 3,501-22,808 messages per cell.

**Novelty: MODERATE.** 2604.27228 reports 28pp model-dependent role fidelity in
a different (advocacy) setting. Ours is on a functional pipeline with a much
larger corpus, but the *type* of claim exists.

---

## Claim 3 — "Realized specialization predicts when role-based organization is beneficial"

**Evidence required:** measured specialization per (organization, actor) cell,
formally mediating the organization × actor interaction. Needs ≥3 actors with
first-pass coverage and a real mediation estimate, not two findings side by side.

**Status: NOT HELD. This is the gap.**
- The interaction is real: paired on 828 common problems,
  **+0.1522 [+0.1135, +0.1896]**.
- But only **one arm is significant** (gemma3 −0.1365; gpt_oss +0.0157, n.s.),
  so "sign reversal" is not supported.
- Mediation cannot be estimated: **N = 3 actors**, and only 2 have both fidelity
  and first-pass coverage on omnimath2. gemma_4_31b has **zero** first-pass
  coverage.
- The suggestive ordering (highest fidelity ↔ PER preferred) rests on 2 usable
  points. That is not a finding.

**Novelty if obtained: HIGH.** 2609.14570 manipulates specialization without
measuring it; 2604.27228 measures it without linking to organization choice.
Nobody closes the loop.

---

## Claim 4 — "Manipulating functional specialization causally changes the effectiveness of role-based organization"

**Evidence required:** controlled arms at fixed topology/budget/verifier, ≥2
actors, with the interaction moving as specialization is manipulated.

**Status: NOT ATTEMPTED (no experiment run).**

**Novelty warning:** the *generic-vs-prompted* contrast is already published —
2602.03128 (SIGMOD 2027) Principle 4, verified verbatim: *"Role-based
conditioning fails to induce specialization... Role naming or lightweight prompt
modifications are insufficient."* And 2609.04217 runs the ablation on
Planner-Executor-Critic at equal inference cost, coining "role-differentiation
collapse."

**What is still open:** a **hard/architectural** enforcement arm where violation
is impossible (not a stronger prompt), *crossed with actor model*. 2602.03128's
strongest arm is still a prompt and uses one model for that table; 2609.04217
uses one 7B backbone and explicitly says it cannot test whether collapse is a
substrate property.

---

## Where this leaves us

The ladder's bottom rung is falsified, the second is held but only moderately
novel, and **the rungs that would make the paper (3 and 4) are exactly the ones
not yet supported.** Claim 3 is blocked by data (2 usable actors) and Claim 4 by
not having run anything.

The honest summary: *we have a well-measured instrument and a real interaction,
and no mediation.* Whether that becomes an AAMAS paper depends entirely on the
controlled run.
