# Controlled experiment — three arms (NOT YET APPROVED, NOT YET LAUNCHED)

## The causal question

> Does **architecturally enforcing** the intended division of labor change the
> effectiveness of the same multi-agent organization, and is that effect
> actor-dependent?

## Arms

All three share: 3 agents, same interaction order (Planner→Executor→Reviewer),
same message-passing graph, same context visibility, same call budget, same
verifier, same retry budget, same stopping rule, same decoding, same grading.

**Arm A — soft-role PER (reproduction).** Current prompts, unchanged. Control.

**Arm B — generic-role PER.** Identical topology and budget; all three agents
receive the *same* generic prompt ("You are one of three agents solving this
problem collaboratively; continue the work"). Role *names* retained for routing
only — the pipeline must still run. Isolates: does functional role *instruction*
contribute anything over the bare pipeline?

**Arm C — hard architectural specialization.** Specialization enforced by the
*interface*, not by stronger wording:

| agent | enforcement (structural, not textual) |
|---|---|
| Planner | emits **JSON conforming to a schema with no answer field** — `{givens[], target_form, lemmas[], steps[]}`. A final answer is *unrepresentable*. Free-text prose is rejected by the parser and regenerated. |
| Executor | receives **only the parsed plan object + the problem**, never the Planner's raw text; emits `{derivation, answer}`. |
| Reviewer | emits **`{verdict ∈ {accept, revise_plan, revise_execution}, target_span, critique}`**. It retains **submission ownership** — `accept` promotes the Executor's current answer **verbatim, by reference** — but has no field in which to *author* a new answer. |

**Design risk caught in the offline smoke test, and fixed.** The PER config
grants the Reviewer "FINAL ANSWER OWNERSHIP", and it is observed to emit the
submitted answer in **41-42%** of messages (gpt_oss 0.421, gemma_4 0.411). A
naive Arm C that simply removes the Reviewer's answer field would change
**who submits**, not only who may author — confounding enforcement with a
changed submission path. Submit-by-reference preserves the submission path and
isolates authorship, which is the variable of interest.

**Why this is not a handicap** (Bella's explicit concern): Arm C removes no
*capability* from the system as a whole — every function (planning, computing,
answering, critiquing) is still performed, by exactly one agent, with the same
total call budget. What changes is only *which agent can emit which kind of
output*. To verify this is not a handicap, the pre-registered check is that
Arm C's **total answer-bearing calls equal Arm A's**; if C simply produces fewer
answers, that is a budget artifact and the arm is void.

**Arm D (role/function shuffle) — DROPPED.** It would test whether role-to-
position mapping matters, which is a different question from whether enforcement
matters, and with 2 actors × 2 domains it would halve the power available to the
A/B/C contrast. Not necessary to isolate the claim.

## Controls (Bella §11) — all fixed across arms

task set (identical matched problems) · actor model · decoding (temp 0,
max_tokens) · topology and interaction order · context visibility policy (same
rule, different *content* only in C by construction) · endpoint/backend ·
**total call budget** · verifier model and prompt · **oracle-feedback exposure
(identical retry budget)** · stopping criteria · answer grading.

Note: the legacy corpus confounds organization with oracle budget (F02). This
design fixes retry budget explicitly and logs `evaluator_calls` per trajectory,
which PER currently does not record — **an instrumentation fix required before
launch.**

## Pre-registered analyses (Bella §P4) — written before any data

Primary endpoints, all paired on identical problems, McNemar / clustered bootstrap:

1. **Main effect of enforcement:** C − A, per actor, per domain.
2. **Actor × intervention interaction:** (C−A)|gpt_oss − (C−A)|gemma_4.
   *This is the primary test of the paper's thesis*, not the main effect.
3. **Does fidelity actually move?** P1a and E2v2 measured in every arm.
   Arm C should force P1a → ~1.0 by construction (a manipulation check: if it
   does not, the enforcement failed and the arm is void).
4. **Does fidelity change accompany outcome change?** Per-actor correlation
   between Δfidelity and Δaccuracy across problems; reported as association only.
5. **Role-instruction contribution:** A − B.

## What we conclude under each outcome (predefined, all five)

| pattern | conclusion |
|---|---|
| **C > A for the low-fidelity actor, C ≈ A for the high-fidelity actor** | Thesis supported: enforcement substitutes for realized specialization; the value of role organization is actor-conditional. Strongest outcome. |
| **C > A for both actors equally** | Enforcement helps, but specialization is *not* actor-conditional. Still publishable as "architectural enforcement beats prompted roles", but the AAMAS-novel interaction is gone and it collides with 2602.03128's Principle 4. Weaker paper. |
| **C ≈ A ≈ B for both** | Functional specialization is not the source of PER's benefit. **Direction abandoned** — report as a negative result or do not submit. |
| **C < A (enforcement hurts)** | Role overlap is *load-bearing*: the organization relies on agents exceeding their contracts. This would be a genuinely interesting inversion and is publishable, but it reframes the paper entirely. |
| **Effects reverse across actors** (C helps one, hurts the other) | Strongest form of actor-conditionality. Requires a third actor before claiming. |

**Explicitly:** patterns 3 and 4 are publishable or abandonment-triggering
outcomes, not failures to be re-analysed. The design is not built so that only
the hoped-for result is reportable.

## Sizing — three options, wall-clock from real logs

Means (not medians) from observed PER trajectories; PER is right-skewed
(omnimath2/gemma mean 514s vs median 118s).

| option | n/cell | domains | trajectories | calls | tokens | wall @conc32 | power (large / moderate) |
|---|---|---|---|---|---|---|---|
| **1 smoke** | 25 | omnimath2 | 150 | 1.3k | 1.5M | **0.5 h** | 0.14 / 0.06 — *instrumentation only, not a test* |
| **2 min defensible** | 400 | omnimath2 + labbench | 4,800 | 54k | 55M | **16.3 h** | 0.96 / 0.50 |
| **3 stronger** | 800 | omnimath2 + labbench | 9,600 | 109k | 110M | **32.6 h** | 1.00 / 0.79 |

### The n=200 pilot is strictly dominated

| plan | calls | wall @conc32 | power (moderate) |
|---|---|---|---|
| n=200 pilot **then** n=400 rerun | 81,453 | 24.5 h | 0.51 |
| **n=400 once** | 54,302 | 16.3 h | 0.51 |
| n=800 once | 108,604 | 32.6 h | 0.78 |

The pilot-then-rerun path costs **50% more calls and 8 more hours for identical
power**. Recommendation: **smoke test (0.5 h) → option 2 or 3 directly.**

Given Oct 8, option 3 at concurrency 32 is 1.4 days of endpoint time and is
affordable if the endpoints are healthy. **Recommend option 3**, falling back to
option 2 if throughput disappoints.

## Blocking prerequisite
PER does not log `evaluator_calls` (coverage 0.000 in the existing corpus). The
oracle-exposure control cannot be *verified* without it. Instrument before launch;
this is part of what the smoke test checks.


---

# Design amendments forced by the verified novelty audit (2026-09-28)

## 1. Arm B is now a REPLICATION, not a contribution

2602.03128 v2 Table 14 already runs role-label vs prompt-conditioning with
everything else fixed, and concludes role prompts do not induce specialization.
Arm B therefore serves only as (a) the control that makes A-vs-C interpretable
and (b) a replication of a published result in a *reasoning* setting on
*multi-agent roles* rather than tabular ML with a single agent. Keep it; do not
sell it.

## 2. Arm C must be visibly NOT a prompt

The audit's decisive finding: every prior "strong specialization" condition,
including 2602.03128's expert-guided arm, is **natural-language prose**
("The classification report MUST be generated exactly using..."). Our claim dies
if Arm C reads as a stronger prompt.

Enforcement must therefore be demonstrably structural, and the paper must be
able to state it in one sentence a reviewer can check:

> In Arm C the Planner's output is parsed against a schema with no answer field;
> a message containing a final answer is **rejected by the parser and
> regenerated**, so contract violation is unrepresentable rather than discouraged.

**Required instrumentation:** log every rejected-and-regenerated emission. The
rejection count is the evidence that enforcement bound at all — the analogue of
"prove the limit binds". An Arm C with zero rejections is an arm where the
constraint never engaged, and its result is uninterpretable.

## 3. Third actor model becomes near-mandatory

2608.21747 ("capability equalizer") already publishes "structure helps weaker
models more" across six models in single-agent coding. With only two actors we
cannot distinguish our interaction from theirs generalised, and our sign-reversal
framing is already retracted (FINDING-07 correction). A third actor is what
separates "an interaction" from "an anecdote about gemma3".

**Constraint:** gemma3_27b has first-pass coverage but only 833 omnimath2
problems; gemma_4_31b has **zero** first-pass coverage. In the new run we
generate first-pass labels ourselves, so this constraint disappears — but only
if the third actor is included in the run itself.

## 4. Add a behavioural endpoint, not just accuracy

Every competitor except 2609.04217 reports end-task metrics only. Our validated
fidelity suite (P1a, E2v2, agreement 0.967/0.923) is a second axis of
contribution. 2609.04217 also supplies ready-made instruments we should adopt
for comparability: **influence rate** and **restate rate**.

## 5. Revised arm set

| arm | what changes | status |
|---|---|---|
| A soft-role PER | nothing (control) | keep |
| B generic-role PER | role instructions removed | keep, as control + replication |
| C hard architectural | schema enforcement, submit-by-reference | **the contribution** |
| D shuffle | — | dropped |

## 6. Revised sizing with the third actor (verified against real logs)

| actors | n/cell | trajectories | calls | wall @conc32 | wall @conc64 |
|---|---|---|---|---|---|
| 2 | 400 | 4,800 | 54,302 | 16.3 h | 8.2 h |
| 2 | 800 | 9,600 | 108,604 | 32.6 h | 16.3 h |
| **3** | **400** | **7,200** | **81,453** | **24.5 h** | **12.2 h** |
| 3 | 800 | 14,400 | 162,906 | 48.9 h | 24.5 h |

**Recommendation changed: 3 actors × n=400 (24.5 h @conc32) over 2 actors ×
n=800 (32.6 h).** It is *cheaper in wall-clock* and buys the third actor, which
the novelty audit makes near-mandatory. The power cost is real — moderate-effect
power drops from 0.79 (n=800) to 0.50 (n=400) per cell — but the paper's primary
test is the **interaction across actors**, and a third actor contributes more to
that than extra n on two actors does. If throughput allows, 3 × 800 at conc64
(24.5 h) dominates everything.
