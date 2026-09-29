# Go / conditional-go / no-go — 2026-09-28

## Recommendation: **CONDITIONAL GO**, with two hard gates before the main run

The direction survived validation and the novelty audit. The compute is
feasible but **2-3x more expensive in wall-clock than I told you earlier**, and
the schedule is now the binding risk rather than the science.

## What is now established (and validated)

- Actor-dependence of realized fidelity: **all six pairwise differences
  significant** under adjudicator-validated, frozen metrics (κ 0.81 / 0.84).
- Organization × actor interaction, paired on 828 common problems:
  **+0.1522 [+0.1135, +0.1896]**.
- A **discriminating prediction** that separates us from 2608.21747: capability
  and realized fidelity are *anti-correlated* on the one pair where both are
  measurable (gpt_oss: capability .568 / P1a .042; gemma3: .425 / .266). A
  capability-equalizer account and a fidelity account predict **opposite**
  things for gpt_oss. The experiment can falsify our framing.

## Gate 1 — smoke test (2.4 h sequential / 1.1 h parallel, ~1,650 calls)

Must all pass before the main run:
1. **Arm C engages**: non-zero rejection/regeneration events, with reasons logged.
2. **Arm C manipulation check**: P1a → ≈1.0.
3. **Answer-bearing calls equal across arms** (the non-handicap check).
4. **`evaluator_calls` is now logged** — PER currently records it at 0.000
   coverage, so the oracle-exposure control is unverifiable without this fix.
5. **Concurrency ladder re-run on the live endpoint.** conc 32-64 has no
   precedent in this project; tested-clean is 25 (OSS) and 8-10 (Gemma).
6. **Backend pinned and logged per trajectory.** The same cell has shown 9.6x
   sec-per-ktok and .72 vs .93 accuracy differences between backends —
   unpinned, this confounds the actor contrast outright.

## Gate 2 — scale decision, from Gate 1's measured throughput

| option | n | domains | trajectories | actor calls | tokens | wall (seq / parallel) | power |
|---|---|---|---|---|---|---|---|
| smoke | 25 | omni | 225 | 1.7k | 2.1M | **2.4 h / 1.1 h** | none (instrumentation) |
| **minimum defensible** | 400 | omni | 3,600 | 26.4k | 33.6M | **38.1 h / 17.1 h** | .96 large, .49 moderate |
| **preferred** | 400 | omni+lab | 7,200 | 70.9k | 78.7M | **63.5 h / 26.6 h** | as above, ×2 domains |
| stretch | 800 | omni+lab | 14,400 | 141.8k | 157.3M | 127 h / 53.3 h | .79 moderate |

Concurrency: gpt_oss 25, gemma family 10 (validated levels, not assumed ones).
Gemma-4 is **4-5× slower per call** than gpt-oss, which is why the gemma arms
dominate wall-clock.

**Recommend PREFERRED (63.5 h sequential, 26.6 h if actors run in parallel).**
**Stretch is not feasible** before Oct 8 — 127 h sequential leaves no margin for
a single endpoint failure, and this project has documented three distinct
backend outages.

## Honest statement of the power limit
At n=400 the per-cell main effect is well powered for large effects (.96) but
the **interaction** — which is the paper's primary test (P4) — needs roughly
twice the n for equal power. **At n=400 the interaction is powered only for
large effects.** I will state this as a limitation rather than promise moderate
ones. If the interaction returns null at this size, that is "no large
interaction detected", not "no interaction".

## What would make me say NO-GO
- Arm C shows zero rejection events in the smoke test (constraint never bound).
- Measured throughput at validated concurrency puts PREFERRED past ~72 h.
- Globus high-assurance re-auth cannot be kept alive for an unattended multi-day
  run (it returns 401 on a valid token and needs an interactive browser login).

## Residual scientific risk, stated plainly
Even a clean result gives a **narrow** paper: structurally enforced inter-agent
division of labor, three actors, two domains, one organization. Its defensibility
rests on the capability-vs-fidelity dissociation holding up — and that currently
rests on **a single actor pair**. The third actor is what turns it from an
anecdote into an ordering claim. That is why gemma3_27b is in the design for a
scientific reason, not a convenience one.
