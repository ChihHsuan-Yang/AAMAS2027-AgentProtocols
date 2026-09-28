# Stress test: is the distinction from 2608.21747 strong enough? (2026-09-28)

Bella's instruction: the distinction must not be "they study single agents and
we study multiple agents." I argue it both ways and then judge.

## What 2608.21747 actually establishes (verified from its abstract)

Five *informationally equivalent* specification formats (prose, Mermaid,
OpenAPI, C4 DSL, TypeScript interface contracts) given to **one** coding agent,
six models, 90 trials. Result: *"specification format shows a strong format ×
model interaction... On the strongest models format barely matters (0.17-0.92
spread). On weaker models, 0.83-2.42."* Framing: *"Structured architecture
specifications serve as a capability equalizer, with value inversely
proportional to model strength."*

Their independent variable is **the representation of a task given to one
agent**. The constraint is on the **input**. Nothing in their design concerns
how work is divided between agents, because there is only one.

## The case FOR our distinction

| axis | 2608.21747 | ours |
|---|---|---|
| what is constrained | the **input specification** handed to an agent | the **output space** of each agent (a field is unrepresentable) |
| who is constrained | one agent | **three agents, differently** — the constraint is *asymmetric by role* |
| what the constraint is about | how a task is described | **who is allowed to do which part of the work** |
| the dependent construct | code quality | **realized organization** — measured behaviourally, not inferred from the score |
| what could fail | the agent misreads a format | **the division of labor fails to materialise even though each agent is individually capable** |

The substantive difference is that **our constraint has no single-agent
analogue**. "The Planner may not emit an answer" is only meaningful because
another agent exists to emit it. A format constraint is a property of a message;
a division-of-labor constraint is a property of a *relation between agents*.
That is an organizational object, not a formatting object.

Second: we measure the **mediator**. 2608.21747 observes outcome × model and
infers that structure compensates for capability. It never measures whether the
model's *behaviour* changed — only whether its score did. Our fidelity suite
(validated, κ 0.81-0.84) lets us ask whether enforcement changed **what the
agents actually did**, and whether that change is what moved the outcome. Every
paper in the audit except 2609.04217 reports end-task metrics only.

## The case AGAINST (the skeptical reviewer)

A hostile reviewer says: *"Strip the vocabulary. You constrain output formats
per agent; they constrain input formats per task. Both find structure helps
weaker models more. 'Distributed across agents' is an implementation detail of
where the constraint sits. The capability-equalizer mechanism — structure
substitutes for what the model can't supply itself — predicts your result
without any organizational theory. You have transplanted a known interaction."*

This is a serious objection and it is not fully answerable in advance.

## What actually defeats it — and it is empirical, not rhetorical

The objection predicts a specific thing: **enforcement should help the weaker
model more, monotonically in capability.** Our claim predicts something
different: **enforcement should help the actor whose realized fidelity is low,
which need not be the weakest model.**

These come apart in our own data. Measured on the **same omnimath2 problems**,
using one-shot baseline first-pass accuracy as the capability proxy:

| actor | capability | P1a | E2v2 |
|---|---|---|---|
| gemma3_27b | 0.425 | **0.266** | **0.112** |
| gpt_oss_120b | **0.568** | 0.042 | 0.062 |

The *more capable* model is the *less faithful* one on both frozen metrics.
**Important limit: only these two actors have baseline first-pass coverage**
(gemma_4_31b has none), so the dissociation currently rests on a **single
pair**. It is a hypothesis-generating observation, not an established
anti-correlation — a Spearman on 2-3 points is meaningless and is not reported.
This is precisely why the third actor is load-bearing rather than
nice-to-have. So:

- If C helps gpt_oss most → that is the **low-fidelity** actor but the
  **high-capability** one. The capability-equalizer story predicts the opposite.
  **This dissociates us from 2608.21747 empirically.**
- If C helps gemma3 most → capability-equalizer wins and we should say so.

**This is a real risk, and it is the right kind:** the design can return the
answer that makes our framing wrong. That is what makes the distinction
testable rather than semantic.

## Verdict

The distinction survives, **conditionally**. It is strong enough to defend if
and only if:
1. we measure the mediator (we can — validated), and
2. the intervention's benefit tracks **realized fidelity rather than model
   capability**, which in our panel are anti-correlated and therefore separable.

If the benefit tracks capability instead, we have replicated 2608.21747 in a MAS
setting and should say so rather than dress it up. **Pre-registered as P4 +
the capability-vs-fidelity contrast.**

## Required in the paper
- Cite 2608.21747 in the introduction, state its result accurately, and name the
  dissociating prediction **before** presenting our result.
- Never describe our contribution as "the multi-agent version of" anything.
- Lead with **realized organization** as the object; the outcome is evidence
  about it, not the claim.
