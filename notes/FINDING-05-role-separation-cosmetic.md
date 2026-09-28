# Finding 05 — PER's "hard role separation" is instructed, not obeyed

**Status:** descriptive, exact, 145,411 role messages across 17,223 trajectories.

## The instruction

The PER config gives the Planner an unusually explicit contract, in capitals:

> HARD ROLE SEPARATION (critical):
> - You MUST NOT carry out symbolic manipulation or arithmetic yourself.
> - You MUST NOT write computed intermediate values.
> - Any computation ... must be delegated to the Executor.

and separately: "Do NOT provide the final answer."

## What the agents actually did

Share of messages containing each behavioural marker:

| marker | Planner | Executor | Reviewer |
|---|---|---|---|
| numeric equation (`= <number>`) | **0.587** | 0.610 | 0.346 |
| explicit arithmetic (`a * b`) | **0.105** | 0.191 | 0.079 |
| `\boxed` answer | **0.150** | 0.564 | 0.496 |
| numeric approximation | 0.072 | 0.117 | 0.040 |

A compliant Planner scores ~0 on all four. It scores 0.587 on numeric equations
— within 0.023 [0.018, 0.030] of the Executor, the agent whose *job* that is.

Role separation holds for *answer commitment* (boxed: 0.150 vs 0.564, a
−0.414 [−0.420,−0.408] gap) but essentially fails for *computation*.

So the division of labour is asymmetric: the Planner respects the part of the
contract about who **announces** the answer, and ignores the part about who
**derives** it. Roles here are closer to output-format conventions than to a
functional decomposition.

## Reviewer routing

`[Agree]` 42.5% · `[Route:Executor]` 26.6% · `[Route:Planner]` 15.1%.
The Reviewer does exercise its routing authority — it is not a rubber stamp —
and it prefers repairing execution over re-planning by ~1.8:1.

## A Simpson's reversal in the outcome table (recorded as a warning)

Pooled, trajectories whose Planner computed look **better**: first-pass 0.645
(n=4,968) vs 0.500 (n=2,324). Within every cell the sign **flips**:

| benchmark | actor | planner computed | first-pass acc | n |
|---|---|---|---|---|
| labbench | gpt_oss_120b | no | **0.429** | 1,994 |
| labbench | gpt_oss_120b | yes | 0.125 | 289 |
| omnimath2 | gemma3_27b | no | **0.870** | 169 |
| omnimath2 | gemma3_27b | yes | 0.431 | 664 |
| omnimath2 | gpt_oss_120b | no | **0.988** | 161 |
| omnimath2 | gpt_oss_120b | yes | 0.718 | 4,015 |

The pooled direction is an artifact of composition: omnimath2 is both easier for
these models and far more likely to make a planner compute, so it dominates the
"yes" cell. **Report only the stratified version.**

Even stratified this is observational and confounded — a planner computes when
the problem invites computation, so difficulty drives both. It is not evidence
that computing *causes* failure. Usable claim: *role compliance is not constant
across problems, so "PER" denotes a family of behaviours rather than one
protocol.*

## Why it matters for the paper

It undercuts the standard reading of PER's gain. If the Planner computes 58.7%
of the time, PER's +14.6-point oracle-free advantage cannot be attributed to
*specialization* without further evidence — it may simply be three sequential
attempts with critique. A controlled arm (same 3 calls, no role labels) would
separate these, and is cheap. Logged as a candidate P2.
