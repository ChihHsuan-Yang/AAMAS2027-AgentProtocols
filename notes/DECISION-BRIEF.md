# Decision brief — 2026-09-28

## The situation in one paragraph

Our strongest, best-replicated results (confidence gate ≈ random; no within-item
component) were **published by others in May-July 2026**. Our one genuinely open
contribution (self-report vs peer-assessment vs random, head-to-head in a live
protocol) is the one that **failed held-out confirmation offline** — the best
oracle-free fix we can measure is +0.011 [−0.006,+0.028] and collapses into
majority voting. So: what is solid is not novel, and what is novel is not solid.

## Three honest options

### Option 1 — Run the 3-arm experiment and let it decide (recommended)
The contrast is verified open: MetaCogAgent's baselines are Single-Agent,
Round-Robin, Random-Routing, Skill-Fixed, Majority-Vote, AutoGen — **no
confidence-argmax arm** (checked in full text). 2606.15419 ran peer-vs-majority;
2601.17152 ran peer-vs-random. Nobody ran self-vs-peer-vs-random.

- **If peer > self**: a real positive result, in a live protocol, against the
  right control, framed as *impartial peer selection for LLM speaker gating* —
  an AAMAS-native contribution.
- **If peer ≈ self ≈ random**: we have shown that **no locally observable signal
  works**, extending 2605.24299 from static model pools to running protocols and
  closing the fix they never tested. Weaker, still a paper, honest.
- Cost: 3 arms × 800 labbench problems × 1 model ≈ 70k calls / ~265M tokens.
  ~1-2 days on our allocation. **This is small.** It fits before Oct 8.

### Option 2 — Pivot to the measurement-validity paper
Lead with E5 (stop-on-PASS censors destructive revision → "collaboration rarely
harms" is unfalsifiable on this class of benchmark) + E4 applied to MAS. Needs
the blind-verifier arm (P1) to be more than a critique. Risk: Kamoi et al. owns
the single-agent version, so the delta is "same argument, multi-agent setting" —
thin for 8 pages.

### Option 3 — Don't submit to AAMAS 2027
The honest option. Our novel-and-solid intersection is currently close to empty.
There is a May 2027 IJCAI and the AAMAS 2028 cycle. Not my recommendation — the
experiment in Option 1 is cheap and decisive — but it belongs on the list.

## What I'd do

**Option 1.** It is the only path where a ~2-day run converts an
already-scooped diagnostic into an owned result, and it is decisive either way:
both outcomes are writable. Everything else we have becomes supporting material
(protocol reconstruction, the oracle decomposition, the role-compliance finding).

## What I need from you

1. Approve or reject the 3-arm run (~70k calls, labbench, 1 model).
2. A view on whether a null outcome is acceptable to you as the paper. If it
   isn't, say so now — that makes Option 3 the right call and saves the compute.

## Not done yet (flagging, not hiding)
- E7 (role separation) was **not** covered by the novelty audit. Needs its own
  search before it goes in any paper.
- The audit's Semantic Scholar leg 429'd throughout and its AAMAS coverage came
  only from arXiv comment stamps. Both holes need closing before submission.
