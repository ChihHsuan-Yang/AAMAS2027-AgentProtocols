# Novelty audit — 2026-09-28

Commissioned adversarially ("tell me if we'd be scooped, don't reassure me").
**Verdict: partially anticipated, seriously.** Three of four sub-claims are
already in the literature. The framing in my first report is not viable.

## Method and its holes (state these when citing this file)

- WebSearch blocked by org policy. **Semantic Scholar returned HTTP 429 throughout
  — zero results.** DBLP bot-gated — zero results. **OpenAlex's AAMAS record stops
  at 2021**, so it could not answer the AAMAS question at all.
- What worked: arXiv Atom API (~35 scoped queries) + fetching rendered full text.
- AAMAS coverage came only from arXiv **comment-field** stamps (`co:"AAMAS"`),
  which finds 54 papers but **misses every AAMAS paper not posted to arXiv**.
  The AAMAS section is the weakest part of this audit. Check the proceedings.

## Verified by me directly (not taken from the subagent)

I fetched `arxiv.org/abs/<id>` for each of the four most damaging hits and
confirmed title, date, and abstract. All four are real.

| id | title | date |
|---|---|---|
| 2605.24299 | LLMs Show No Signs Of Individuated Metacognition | 2026-05-22 |
| 2605.22949 | MARGIN: Runtime Confidence Calibration for Multi-Agent FM Coordination | 2026-05-21 |
| 2607.28317 | One Human, N Agents: Audit-Budget Allocation ... Miscalibrated Confidence | 2026-07-30 |
| 2605.17292 | MetaCogAgent: Metacognitive Multi-Agent LLM Framework | 2026-05-17 |

## What is already published

**Our E2 (confidence has no within-item component) ≈ arXiv:2605.24299.**
20 models, 6 benchmarks, tetrachoric factor analysis: the cross-model confidence
matrix is ~rank-one — models share an item-difficulty axis and differ only in
threshold. Pairwise calibration τ=0.037 (SQuAD), 0.025 (OmniMath), vanishing
under base-rate control. Their intro names the casualty explicitly:
*"the individuation assumption underlying confidence-weighted routing fails."*
**This is our mechanism, found independently, and published first.**

**Our E1 (confidence-argmax ≈ random) ≈ arXiv:2605.22949 §8.1 and 2607.28317.**
MARGIN's Table 9, pairwise resolution vs a 50% random baseline: MBPP 48.9,
LiveCodeBench 45.2, CodeContests 50.0, BigCodeBench 43.4 — *"at or below a coin
flip."* 2607.28317 derives a threshold δ* past which confidence-ranked selection
is provably worse than random, and measures real models past it (AUROC ≈ .50-.52).

**Our F02 (oracle-feedback confound) = Kamoi et al., TACL 2024 (2406.01297).**
Formalizes "unrealistic self-correction" using ground-truth answers, with a
named-offender table (RCI, Reflexion, Self-Refine). **Do not claim this.** Inherit
it as methodology and apply it to the multi-agent gating setting.

**Our "debate ≈ majority voting"** — arXiv:2508.17536, NeurIPS 2025 Spotlight.
Background, never a finding.

## What survives — verified by me

**The self-vs-peer head-to-head has not been run.** I checked the one paper the
audit flagged as a possible closer, MetaCogAgent (2605.17292), in **full text**:

- Its six baselines are Single-Agent, Round-Robin, **Random-Routing**,
  Skill-Fixed, Majority-Vote, AutoGen. **No confidence-argmax arm.**
- Full-text keyword counts: `random` 1, `Random` 2, `peer` 1, `cross-agent` 1,
  `within-item` 0, `coin` 0. It reports the *combined* system (82.4% vs
  Random-Routing 63.5%) and never isolates self-report from cross-agent evaluation.

So the three-arm contrast — **self-report gate / peer-assessment gate / random
speaker, same items, same system** — remains open. 2606.15419 (JAMIA 2026) ran
peer-selection vs majority vote; 2601.17152 ran peer-selection vs random. Neither
ran it against self-report.

**Also open:** protocol-level measurement inside a *live multi-agent dialogue*.
2605.24299 is a static model-pool study (`multi-agent` 0 occurrences, `peer` 0,
`debate` 0). MARGIN is a coordinator over a model pool. Nobody has measured a
deployed speaker gate against a random-speaker control inside a running protocol.

## The counterexamples we must explain, not ignore

**SID (2510.06843)** uses confidence to let high-confidence agents exit early and
reports it works. **DebUnc (2407.06426)** reports confidence-conveying helps
debate. A reviewer will read these as contradicting E1.

Our decomposition supplies the reconciliation: SID's gate is **within-agent over
rounds** (temporal); ours is **between-agent within-item** (cross-sectional).
E2 predicts exactly that difference — the between-problem component is real
(AUC .597) and is what a temporal gate rides on. This converts two apparent
counterexamples into support. It must be stated explicitly in the paper.

**CONCAT (2605.29612)** used confidence to select cluster leaders and was
**WITHDRAWN in Sept 2026** over prompt overlap across runs. Cite as a cautionary
case, not a competitor.

## AAMAS positioning (subject to the coverage hole above)

Nothing at AAMAS combines LLM confidence with a communication gate. The
venue-appropriate frame already exists and we should adopt it:
- **Reputation as a Solution to Cooperation Collapse in LLM MAS** (2505.05029,
  AAMAS 2026) — reputation *is* a peer-assessment signal fixing a coordination
  failure. Structurally our thesis in another task. A reviewer will expect it.
- **Robust Knowledge Extraction using Social Choice Theory** (2312.14877, AAMAS 2024).
- **GroupDebate** (2409.14051, AAMAS 2026) — communication efficiency in LLM debate.
- Framing to adopt: **impartial peer selection applied to LLM speaker gating.**

## Consequence for our claim

The claim as written in my first report is **not publishable as novel**. Revised
position, in priority order:
1. Do **not** lead with the between/within decomposition (that's 2605.24299).
2. Lead with the **coordination consequence measured inside a live protocol**, and
   make the **three-arm self/peer/random contrast** the headline.
3. Explain SID and DebUnc via the temporal-vs-cross-sectional distinction.
4. Cite 2605.24299 / 2605.22949 / 2607.28317 in the intro as converging prior
   evidence, then state the delta in one sentence. Burying them is the worst
   option — the same queries find them in minutes.

## Two holes to close before submission
- Rerun with a Semantic Scholar API key (429'd throughout here).
- Check AAMAS 2025/2026 proceedings directly; arXiv stamps are not coverage.
