# Finding 04 — Effect-size reality check: the fix is much weaker than the failure

**Date:** 2026-09-28. This revises the P0 proposal's expected outcome.

## The asymmetry

Two facts now sit side by side, and only one of them is large:

| | estimate | interval |
|---|---|---|
| **The failure** — argmax-confidence minus random | +0.0001 | [−0.0038, +0.0038] |
| **The headroom** — oracle minus deployed, disagreement turns | +0.374 | (0.7475 vs 0.3738) |
| **The best available fix** — agreement-select minus confidence-select | **+0.0109** | **[−0.0057, +0.0277]** |

labbench disagreement turns, n=3,438, clustered by trajectory.

Selection by peer agreement and by plurality are **identical to 4 dp** (0.3847 vs
0.3847). That is not a coincidence — on a 3-agent panel, "the agent with most
peers holding its answer" and "the modal answer" are nearly the same function.

## What this means for the paper

**The negative result is the strong result.** The confidence gate is worth
nothing, and that is measured tightly (interval width ±0.004). The ceiling is
enormous (+37 points unclaimed). Those two facts are the paper.

**The constructive half is weak and may not survive.** The best oracle-free fix
I can find offline is +0.011 per turn with an interval that includes zero, and
it collapses to majority voting. Two consequences:

1. **P0's framing must change.** It is no longer "peer-rank beats confidence"
   (I would be pre-committing to a +0.011 effect). It is: *is there ANY
   oracle-free within-item channel, and is peer judgement separable from peer
   agreement?* A3-vs-A4 is the whole question, not a control.
2. **A trajectory-level effect will be smaller still.** Only 37.6% of turns show
   disagreement, so a per-turn +0.011 dilutes further end-to-end. A pilot powered
   to detect it needs to be sized off the per-turn figure on disagreement turns
   only, with turn-level outcomes as the primary endpoint — not final accuracy.

## Honest framing options

**(a) Mechanism-and-limit paper (recommended).** Claim: the standard confidence
gate reads a channel with no within-item component; we localize the failure
(between/within decomposition), bound what any local selector can recover, and
show the best oracle-free alternative recovers ~3% of the gap. Contribution is
a *negative result with a mechanism and a ceiling* — genuinely useful to anyone
building confidence-gated MAS, and it does not overclaim.

**(b) Hold out for a stronger fix.** Only worth it if a channel with materially
better within-item AUC exists. Nothing in the existing traces has one: the five
features tested are 0.4933-0.5296. I would not bet the deadline on finding one.

I recommend (a), with P0 reframed as the falsification test rather than the
method demonstration.

## Discovery/confirmation discipline

Every number above was found on the same data. The between/within decomposition,
the feature sweep, and the effect sizing all used labbench. **jeebench, mascqa,
omnimath2, and the second actor model (gemma_4_31b) must be held out** as the
confirmation set for whichever claim we commit to. I have deliberately not tuned
anything on them.

---

## Held-out confirmation (d11) — one prediction failed

Pre-registered before looking at gemma_4_31b (a different actor model on
different hardware; 14,559 polls, 1,989 trajectories, never used in d1-d10 tuning).

| prediction | gpt_oss_120b (discovery) | gemma_4_31b (held out) | verdict |
|---|---|---|---|
| **P1** confidence within-turn AUC ≈ 0.5 | 0.5181 [.4919,.5437] | **0.4944 [.4774,.5115]** | **replicates** |
| **P3** argmax-conf − random ≈ 0 | +0.0049 [−0.0130,+0.0234] | **−0.0012 [−0.0152,+0.0135]** | **replicates** |
| **P2** agreement within-turn AUC > 0.5 | 0.5258 [.4916,.5591] | 0.5259 [.4931,.5568] | **FAILS** |

### P2 failed, and I am not going to rescue it

The pooled agreement result (0.5296 [.5058,.5529], d7) excluded 0.5. Split by
actor, **neither arm does** — both intervals straddle it, despite point estimates
that are near-identical (.5258 / .5259) and consistent with the pooled value.

This is a power split, not a contradiction: the pooled test had ~4,992 pairs, each
arm ~1,549 and ~3,209. The effect is plausibly real and simply under-powered per
arm. **But "plausibly real and under-powered" is not a finding**, and I will not
report agreement as an established signal on this evidence. Selecting the pooled
analysis because it clears significance, when the pre-registered per-arm split
does not, is exactly the post-hoc move that makes a result unreplicable.

Likewise `agree_minus_conf`: +0.0057 [−0.0159,+0.0267] and +0.0139
[−0.0096,+0.0371]. Both include zero. The +0.0109 pooled figure in the table
above is the *only* version that looked non-trivial, and it too includes zero.

### Where this leaves the paper

**Strengthened:** the negative result. The confidence gate is worth nothing, and
this now replicates across two actor models, two hardware sites, with tight
intervals (gemma: −0.0012 [−0.0152,+0.0135]). The between/within mechanism
replicates too. This is the most solid thing in the project.

**Weakened to the point of removal:** every constructive claim. No oracle-free
within-item channel I have tested survives held-out confirmation. The honest
statement is now:

> Self-reported confidence carries no within-item signal; we searched five
> observable alternatives and **found none that replicates across actor models
> either**. The group's knowledge (74.9% ceiling) is not recoverable by any local
> selection rule we could identify from the traces.

That is a stronger and more surprising claim than "use peer agreement instead",
and it is the one the data actually supports. It also makes P0's A3-vs-A4 arms
genuinely open rather than a formality — the experiment is now a real test with a
real chance of returning null, which is the right reason to run it.
