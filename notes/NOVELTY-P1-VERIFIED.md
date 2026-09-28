# P1 novelty verification — architectural enforcement × actor dependence

**Date 2026-09-28.** Answers Bella's four P1 questions. Everything below was
verified by fetching the paper; IDs confirmed by title match.

## CORRECTION to my previous report

I cited **2602.03128 Table 12** as "our Arm A vs Arm B, already run". Two errors:

1. **There is a v2** (17 Sep 2026) that rewrote the experiment. Table 12 is v1
   numbering; in v2 the specialization table is **Table 14** and adds a fourth
   condition (a dataset-profile tool). **Cite v2 or pin the version.** I confirmed
   both v1 and v2 exist on the abs page.
2. I implied it ignores model-dependence. **It does not.** Its §4.1.3 tests
   *schema-constrained planning* across **8 models** and reports a clean
   interaction (Qwen-7B 84.7% schema violations; GPT-5.6-Luna/Terra and
   Claude-Opus-5 never violate). That is structure × actor, verified across
   models — but on a **planning output schema**, not on division of labor
   between roles. The distinction must be made explicitly or a reviewer will
   conflate them.

## Q1 — Does 2602.03128 contain our soft-vs-generic comparison?

**Yes, and it is prompts only.** v2 Table 14: four conditioning strategies ×
five role labels (No Role, Data Scientist, Researcher, Data Analyst, Engineer).

Decisive quote: *"Conditioning is applied in the prompt, independent of any
framework, so this result is not tied to one implementation."*

Appendix C's "expert-guided" condition — its strongest arm — is a numbered prose
recipe, e.g. *"The classification report MUST be generated exactly using:
classification_report(y_test, y_pred, zero_division=0)."* **Capitalised prose
asking politely. No constrained decoding, no enforced schema, no removed field,
no restricted context or tool access in §4.1.4.** The one v2 condition touching
architecture (a dataset-profile tool) *grants* access rather than restricting it.

**One model (GPT-4o-mini).** The authors concede exactly our gap:
*"the effect may differ for models with stronger instruction following."*
Task is tabular ML pipeline generation; measurement is end-task F1 only, with
**no behavioural instrumentation** of the agents.

## Q2 — Does any prior work enforce role specialization architecturally?

**Partially, and in a different field.** The real prior art is governance, not
reasoning performance:

- **Skilder (2609.28693)** — verified. Enforces **role-scoped tool access
  deterministically at an MCP server**, built on our exact premise: *"system
  policies defined purely in prompts remain probabilistic advice rather than
  hard constraints."* Framed as least-privilege access control; makes no claim
  about reasoning performance or division of labor.
- **SERO (2605.28433)** — **not the threat I feared.** Its five "structural
  contracts" gate **which role-pool edits may be committed during evolution**
  (action mask + score gate), not what a running agent may emit. Its behavioural
  payload is still a *system prompt*. No planner is structurally prevented from
  emitting an answer.

**Not found**, after searching constrained decoding × multi-agent, grammar-
constrained × agent, role-conditioned schema, typed inter-agent interfaces,
JSON-schema × agent role, context isolation × multi-agent, interface contract ×
agent: **any paper that structurally removes a field from a role's output space
to create functional division of labor.** The planner-with-no-answer-field
construction appears open.

## Q3 — Has anyone run the same enforced architecture across actor models?

**This is where we are most at risk.** The *interaction shape* is already
published, under a name:

- **2608.21747 "Architecture as Capability Equalizer for Coding Agents"** —
  verified, abstract read in full. Six models, three vendor families, 90 trials,
  five spec formats **including TypeScript interface contracts**. Verbatim:
  *"specification format shows a strong format × model interaction. On the
  strongest models format barely matters (spread 0.17-0.92). On weaker models,
  format produces spreads of 0.83-2.42."* Thesis: *"Structured architecture
  specifications serve as a capability equalizer, with value inversely
  proportional to model strength."*
  **That is our predicted interaction, already named.** But: single-agent coding,
  spec-format as *input*, no multi-agent roles, n=3/cell, no significance tests.
- **2510.07614** — verified. Planner→Executor→Critic across 3 LLMs; the
  accountable-vs-simple delta is configuration-dependent (+36.22 for one config,
  0.00 and −0.78 for others) — our interaction, in their data, but never named
  or tested as such, and the "structured handoff" is a validated format with
  blame attribution, not output-space restriction.

## Q4 — 2609.04217: our strongest asset, not a threat

Verified in full text. **One backbone** (frozen Qwen2.5-7B). Roles are **prompts
only**: *"A role is the pair of g_θ and a natural-language role prompt."*

It asserts substrate-causation — *"not an optimizer failure but a property of the
substrate, a 7B with no headroom for a second distinct role"* — and then
explicitly disclaims it: *"we do not claim the conclusion transfers to larger or
heterogeneous backbones."* It **pre-registers our hypothesis as future work**
("Scale... Heterogeneity: distinct backbones per role") and hands us ready-made
behavioural instruments (influence rate: planner 0.14, critic 0.41; critic
restate-rate 0.00).

## Verdict

**The conjunction is open; each half is occupied.** Architectural enforcement of
role scope exists (Skilder) but as governance with no performance claim.
Architecture × actor interaction is actively being reported (2608.21747,
2602.03128 §4.1.3, 2510.07614). **Nobody has restricted what each role can
structurally emit to create division of labor, and run that across actor models.**

### Three binding framing requirements
1. Cite **2602.03128 v2** (Table 14, four conditions). Do **not** claim it
   ignores model-dependence — distinguish *output-schema* constraints (its
   §4.1.3, 8 models) from *role-division* constraints (ours).
2. **Position against 2608.21747 explicitly.** "Structure helps weak models more"
   is published. Our novelty must rest on **inter-agent division of labor**, not
   on the interaction shape itself.
3. Distinguish our enforcement from SERO's (gates pool *edits*) and from
   2510.07614's (format-validated handoff).

### Consequence for the paper
Add a **behavioural** measure alongside end-task metrics. Every paper above
except 2609.04217 reports end-task metrics only — that is a defensible second
axis, and it is what our validated fidelity suite already provides.
