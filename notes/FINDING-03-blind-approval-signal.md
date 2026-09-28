# Finding 03 — The group HAS a reliable internal signal; the gate uses a different, useless one

**Status:** robust. 74,235 gradable blind peer reviews, 13,354 panels, 5,796 trajectories.

## Two signals inside the same protocol

Broadcast Deliberation produces two distinct agent-generated assessments:

| signal | what it is | ground truth? | used for |
|---|---|---|---|
| **poll confidence** | each agent self-reports 1-100 on its own answer | no | **selecting who speaks** (argmax) |
| **approval vote** | each agent reviews the *current candidate* and returns approve / needs_revision / propose_correction, stamped "peer review/suggestion (not evaluator feedback; not system proof)" | no | terminating the approval phase (unanimity) |

Both are oracle-free. They differ in **direction**: confidence is *self*-directed
and *within-agent*; approval is *other*-directed and *about a shared object*.

## The dissociation

| signal | AUC -> candidate correctness |
|---|---|
| self-reported confidence, **within turn** (what selection uses) | **0.4975** [.4921, .5027] |
| blind peer approval fraction | **0.6307** |

Per-review base rates: approve 0.5915 (n=32,043), needs_revision 0.4660
(n=27,084), propose_correction 0.4214 (n=15,108).

Panel-level unanimity is strongly informative:

| | accuracy | n |
|---|---|---|
| unanimous approval | **0.7342** | 4,447 |
| any dissent | 0.4640 | 8,907 |
| **difference** | **+0.2702 [+0.2535, +0.2873]** | |

Holds in every benchmark: jeebench .905 vs .666, labbench .653 vs .452,
mascqa .960 vs .583.

## Why this matters

The same three agents, in the same protocol, on the same problem, produce:
- a **self**-assessment that cannot discriminate who is right (AUC .4975), and
- a **peer** assessment that can (AUC .631, +27 pts at unanimity).

The deployed communication gate is wired to the first. This is not "LLMs are
badly calibrated" — confidence *is* calibrated to problem difficulty
(between-problem AUC .597). It is a **structural mismatch between what the signal
measures and what the mechanism asks of it**: selection needs a *relative,
inter-agent* comparison, and self-confidence has no inter-agent component.

## The generalizable claim for AAMAS

> In LLM multi-agent systems, an agent's assessment of **itself** and agents'
> assessments of **each other** are not interchangeable sources for coordination
> decisions. Self-report varies with the task; peer report varies with the
> proposal. Any gate, router, or selector that compares self-reports across
> agents on one item is reading a channel with no signal in it.

This is testable, mechanistic, and prescribes a fix (route the gate through peer
assessment), which is exactly the shape of an AAMAS contribution.

## Caveats to resolve before claiming
- Approval reviews occur *after* discussion, so a reviewed candidate has already
  survived selection: the comparison is not a clean A/B of the two signals at the
  same decision point. **A controlled arm is required** — poll both signals at the
  same turn and select on each.
- Unanimity is partly endogenous to problem easiness (like confidence). Needs the
  same between/within decomposition applied to approval.

---

## CORRECTION (2026-09-28, d10) — the headline AUC comparison was not like-for-like

The comparison "peer approval AUC 0.631 vs confidence AUC 0.4975" above is
**invalid as stated**, and I am recording it rather than deleting it because the
error shape matters for the paper.

Approval panels all review **one** candidate, so correctness is constant within a
panel: the 0.631 is a **between-problem** quantity. Confidence's 0.4975 is a
**within-turn** quantity. Different contrasts. Comparing them is the same mistake
as comparing a protocol's accuracy to another protocol's first-pass accuracy.

### The like-for-like test (d10)

Restrict to **the same problem with ≥2 distinct candidates reviewed and mixed
correctness**, then ask whether peer approval ranks the right candidate above the
wrong one:

| signal | contrast | AUC |
|---|---|---|
| self-confidence | within turn, between agents, same problem | **0.4975** [.4921, .5027] |
| peer approval | within problem, between candidates | **0.5297** [.5080, .5519] |

1,209 problems, 2,206 pairs (labbench 2,089).

### What survives

The qualitative claim **survives, and is now properly supported**: peer
assessment has a within-item component that self-report does not. Both intervals
are narrow and they do not overlap 0.5 in the same direction — confidence's
straddles it, approval's excludes it.

The quantitative claim **shrinks a lot**. The usable peer signal is AUC ≈ 0.53,
not 0.63. That is the same magnitude as raw peer *agreement* (0.5296, d7) —
which raises the live possibility that peer *judgement* adds nothing over peer
*agreement*. Both are ≈0.53 and their intervals are nearly identical.

### Consequence for the experiment design

This makes arm A4 (`plurality`, agreement without judgement) **not optional** —
it is now the primary rival hypothesis, not a secondary control. If A3 ≈ A4, the
paper's mechanism is "peers agreeing", not "peers judging", and the framing must
change accordingly.

It also sets realistic expectations: a selector built on an AUC-0.53 channel
recovers a modest slice of the 37.5% → 74.9% headroom, not most of it. Any
projected effect size in the proposal must be computed from 0.53, not 0.63.
