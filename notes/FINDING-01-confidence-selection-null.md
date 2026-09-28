# Finding 01 — Confidence-gated speaker selection recovers none of the group's knowledge

**Status:** discovery-phase, statistically robust on labbench (MCQ, exact grader).
**Date:** 2026-09-28

## The mechanism as implemented

`agentverse/environments/tasksolving_env/rules/broadcast_deliberation.py:1190-1300`

Each discussion turn:
1. **All 3 deliberators are polled in parallel** (`asyncio.gather`) with *identical*
   context: same problem, same advice, same current candidate, same shared history.
   Each returns `{score: 1-100, reason, intent, candidate_answer}`.
2. `best_idx = argmax(score)`. **Only that agent speaks publicly.**
3. Agents with `score >= speak_threshold (65)` that were not selected get their
   intent written to a *private* note (`deferred_*`). Below 65: discarded entirely.
4. The public message updates the shared candidate.

Because every agent's `candidate_answer` is logged at every poll, the release
records **what each silenced agent would have said**. On MCQ benchmarks the
grader is exact (d3 calibration: 99.99% agreement with recorded labels on
labbench n=13,473; 100% on jeebench n=1,904). So the selection rule is
*counterfactually evaluable at the turn level*.

## Result

10,239 turns (4,438 trajectories) with >=2 gradable candidates.
Clustered bootstrap by trajectory.

| Selection rule | All turns | Disagreement turns |
|---|---|---|
| random agent | 0.5463 [.5346,.5579] | 0.3744 [.3625,.3864] |
| **argmax confidence (deployed)** | **0.5464** [.5341,.5588] | **0.3747** [.3589,.3912] |
| majority vote | 0.5511 [.5380,.5643] | 0.3881 [.3682,.4083] |
| best available (ceiling) | 0.6781 [.6651,.6908] | 0.7488 [.7267,.7697] |

- **argmax − random = +0.0001 [−0.0038, +0.0038]** pooled;
  **+0.0003 [−0.0102, +0.0110]** on disagreement turns.
- Survives every restriction: all-polls-parsed (n=3,529, delta −0.0003);
  unique argmax with spread>=5 (n=4,160, top−rest = +0.0010 [−0.0126,+0.0145]).
- **Anti-selection at large gaps:** conf spread >20 -> argmax 0.3322 vs random 0.3551.

## Why: the between/within decomposition

Confidence *is* informative — but not in the direction selection uses.

| component | share of variance | AUC -> correctness |
|---|---|---|
| between-turn (problem difficulty) | 68.8% | **0.5967** [.5855,.6084] |
| within-turn (which agent) | 31.2% | **0.4975** [.4921,.5027] |

The selection rule compares agents *facing the same problem*, so it can only
exploit the within-turn component — which is noise. Confidence tracks **how hard
the problem is**, not **who is right about it**.

Per benchmark, within-component AUC: jeebench .4819 [.4598,.5029],
labbench .4977 [.4922,.5034], mascqa .5181 [.4872,.5579]. None separable from 0.5.

## The cost

On disagreement turns the group's candidate set contains the correct answer
**74.9%** of the time; the deployed rule delivers **37.5%**. The gap is not a
knowledge deficit — it is an **aggregation failure**. Majority vote recovers only
a small part of it (+0.0134 [−0.0025,+0.0293]), so the headroom is real and
mostly unclaimed.

## Why an AAMAS reader cares

Confidence-gated / "speak only if you have something to add" communication is a
standard token-saving device in LLM MAS. This shows the gate can be *exactly
zero-value* while appearing principled, and gives the reason: self-reported
confidence is a problem-difficulty signal, not an inter-agent discriminator.
Any mechanism that compares confidence across agents on the same item inherits
this failure.

## Independent cross-check (2026-09-28)

The within-turn AUC was computed twice, by two separately-written implementations
(a per-turn loop with a resampled-turn-key bootstrap, and a vectorised
pair-aggregation with a trajectory-clustered bootstrap). They agree:

| feature | impl. A | impl. B |
|---|---|---|
| confidence (`score`) | 0.5013 [.4875,.5155] | 0.5013 [.4879,.5151] |
| peer `agreement` | 0.5296 [.5074,.5522] | 0.5296 [.5058,.5529] |
| `reason_len` | 0.4933 [.4779,.5094] | 0.4933 [.4772,.5111] |
| `intent_len` | 0.4992 [.4813,.5145] | 0.4992 [.4815,.5170] |

The point estimates are identical to 4 dp and the intervals differ only in the
bootstrap's third digit. The confidence null and the agreement signal are both
implementation-independent.

**Correction to the earlier table:** `has_candidate` is flagged "SIGNAL" by both
scripts, but this is a **bug in the flag logic, not a finding**. The feature is
constant (=1) on the gradable subset, so every pair ties, AUC is exactly 0.5000
with a zero-width interval, and the "does the CI exclude 0.5" test misfires on a
degenerate variable. It carries no information. Fixed interpretation: of the five
candidate within-turn features, **only peer agreement discriminates.**
