# Overlap boundary — arXiv:2609.27822 (VERIFIED 2026-09-28)

**"What Confidence Routing Is Actually Doing: Auditing Routing, Calibration,
and Commitment in Multi-Agent Deliberation"** — posted 2026-08-18.

**Authors: Jingyan Jiang, Huihuo Zheng, Rajeev Thakur, Chih-Hsuan Yang.**

## This is OUR OWN GROUP'S paper, not an external competitor

That changes the nature of the constraint. It is not a scooping risk — it is a
**self-overlap / thin-slicing risk**, which is the thing AAMAS polices most
directly ("substantially similar concurrent archival submissions", "thin-sliced
submissions whose contribution is too incremental relative to another
overlapping paper"). A reviewer who finds both will be asking whether the AAMAS
paper is a second slice of one project.

It also explains the previous session's novelty problem: my F01/F03 findings
(confidence-argmax ≈ random; the between/within dissociation) were not merely
anticipated by strangers — **they are substantially this paper**, on the same
corpus.

## What 2609.27822 claims (from its abstract, fetched and read)

Same corpus, same protocol: 4,181 gpt-oss-120b olympiad-math traces (= our
omnimath2), repeated on a 2x2 actor x benchmark grid adding gemma-4-31B-it and a
biology MCQ benchmark (= our labbench).

It separates three trace-level questions about the **confidence-routed broadcast**
protocol:
1. **Routing** — does argmax-confidence select the right candidate?
   Fixed routers differ by ≤1.1 pp on gpt-oss/math; **raw-confidence argmax is
   5.6 and 11.2 points BELOW random-valid selection in the Gemma cells.**
2. **Calibration** — AUROC 0.72 primary cell but 79% stated vs 52% actual;
   isotonic recalibration cuts ECE 0.278 → 0.008 but cannot create missing
   discrimination (raw AUROC 0.537 / 0.440 in Gemma cells).
3. **Commitment** — poll and spoken answers diverge in 20.4% of valid pairs.

## Everything now FORBIDDEN for the AAMAS paper

- confidence routing, confidence-vs-random selection
- verbal confidence calibration
- peer-vs-self speaker gating
- poll-to-speak commitment / divergence
- any further audit of the **broadcast** protocol

## Consequence for our prior findings

| prior finding | status now |
|---|---|
| F01 confidence-argmax ≈ random | **RETIRED** — inside 2609.27822's scope, and it reports a stronger version (below random in Gemma cells) |
| F03 peer approval vs self-report | **RETIRED** — "peer-vs-self speaker gating" explicitly excluded |
| F04 effect sizing for a selection fix | **RETIRED** with F01/F03 |
| F02 oracle-feedback confound | **KEPT as methodology only** — not a claim (Kamoi et al. TACL 2024 owns it), but it constrains our experimental design |
| F05 PER role separation not obeyed | **KEPT — this is the new seed.** Different protocol (PER, not broadcast), different question. |
| F06 organization x actor interaction | **KEPT** — note 2609.27822 also reports actor-dependence, but *of confidence routing inside broadcast*. Ours is about *which organization wins*, which is a different quantity. Must be stated carefully. |

## Distinctness of the new direction

| axis | 2609.27822 | proposed AAMAS |
|---|---|---|
| protocol | Broadcast Deliberation | **PER** (+ broadcast only as the comparison organization) |
| object | one scalar (confidence) and its three uses | **functional division of labor** across heterogeneous roles |
| unit | poll/turn, candidate selection | **role-message behavior**, trajectory-level specialization |
| question | is the router picking correctly? | do prompted roles instantiate distinct functions at all? |
| intervention | recalibration / alternative routers | **generic-role vs soft-role vs hard-enforced-role** |

The one real adjacency is F06 (actor-dependence). 2609.27822 already shows
actor-dependence *of a routing mechanism*. We must not present "things vary by
actor model" as our novelty — our claim has to be specifically about **realized
role specialization** as the mediator of **organization choice**.
