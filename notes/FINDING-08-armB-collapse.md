# Finding 08 — Under generic prompts the organization collapses to N copies of one solver

**Status:** observed in smoke v3 (n=33 trajectories so far), verified by Master
against the wiring-fault hypothesis. **Preliminary — not yet powered.**

## What happens

In Arm B (generic role prompts, identical topology/budget/order), **6 of 14**
trajectories had two or more of the three agents emit a **byte-identical
response**. Arm A: 0/12. Arm C: 0/14.

A representative case — all three slots, same trajectory:

```
[planner]  \boxed{\dfrac{\sqrt{6}}{3}}\n\n[Agree]
[executor] \boxed{\dfrac{\sqrt{6}}{3}}\n\n[Agree]
[reviewer] \boxed{\dfrac{\sqrt{6}}{3}}\n\n[Agree]
```

All three answer, all three immediately agree, nobody plans and nobody reviews.

## It is NOT an A/A wiring fault — checked before believing it

The obvious failure mode is that the three slots are receiving the same prompt.
They are not. Per-role prompt hashes in that trajectory:

| role | prompt sha | prompt chars | response sha |
|---|---|---|---|
| planner | `bc089a427d10` | 539 | `c1847407881b` |
| executor | `a0d083ee40b2` | 585 | `c1847407881b` |
| reviewer | `28fb46503c83` | 634 | `c1847407881b` |

**Three distinct prompts, one identical response.** The convergence is
behavioural, not plumbing. (This check exists because a prior project shipped an
A/B that had silently collapsed to A/A; perfect row-wise agreement is the tell.)

## Why it matters for the paper

It is direct evidence for the central construct. The *specification* still
describes a three-role pipeline — same agents, same order, same budget. The
*realized organization* is three copies of a single solver. Specified and
realized organization come apart, visibly, in the control arm.

It also sharpens what Arm B controls for. Arm B is not "PER minus role words";
it is "the topology with no division of labor at all". That makes the A-vs-B
contrast a test of whether role *instructions* sustain differentiation, and the
A-vs-C contrast a test of whether *architecture* does.

## Caveats — do not overstate this yet
- n=14 Arm B trajectories. Preliminary.
- All smoke problems so far are solved by every arm (the 73.8% ceiling stratum),
  so collapse here costs nothing in accuracy. **Whether collapse is harmful is
  a different question and is unanswered.**
- temperature=0 is not deterministic on this endpoint, so identical outputs are
  not guaranteed by decoding — which makes the identity *more* notable, not less.

## Pre-registered follow-up
Collapse rate per arm per actor is a **secondary** endpoint (it was not in the
P1-P5 primary set and is not being promoted after the fact). It will be reported
with its own CI from the main campaign.
