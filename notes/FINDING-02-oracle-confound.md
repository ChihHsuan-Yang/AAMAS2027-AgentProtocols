# Finding 02 — The protocol ladder is half an artifact of oracle feedback

**Status:** robust, paired, n=6,551 problems x 4 protocols.

## The confound nobody named

All four protocols run inside the SAME outer loop. The `Evaluator` agent
**sees the ground-truth answer** (`${result}` in every config) and returns
`Verdict: PASS/FAIL` plus a "non-leaking repair hint" that names the *mismatch
category* (wrong value / incomplete list / wrong answer shape / missing cases /
insufficient generality). That hint goes back to the agents.

So the loop is not self-contained deliberation: it is **deliberation with an
oracle that says "you're wrong, and wrong in THIS way"**, repeated until PASS or
budget exhaustion.

The four arms consume different amounts of this oracle signal:

| protocol | submissions | mean evaluator_calls | structure |
|---|---|---|---|
| baseline_llm | 1 | 0.80 | 1 agent |
| single_agent | up to 3 | 1.44 | 1 agent |
| per | 3 outer x 2 inner | *not logged* | 3 roles |
| broadcast | 3 outer x (4 disc + 2 appr) | 1.78 | 3 peers |

Agent count, attempt budget, and oracle-feedback budget increase **together**.
The published ordering baseline < single < PER < broadcast is monotone in all
three at once. AI4S R3 praised the design for "controlling for protocol, actor,
and problem-level confounders" — the oracle-budget asymmetry was not caught by
any reviewer, and the SC26 supplement mentions bundling only as a one-paragraph
limitation.

## Decomposition

`first_pass_correct` = verdict on the FIRST submission, i.e. **before any oracle
bit has reached the agents**. That gives a zero-feedback comparison at equal
oracle exposure.

| protocol | total gain vs baseline | structure (oracle-free) | oracle retry | % from oracle |
|---|---|---|---|---|
| single_agent | +0.2216 | **+0.0023** [−0.0064,+0.0108] | +0.2194 | **99.0%** |
| per | +0.2832 | +0.1459 [+0.1352,+0.1566] | +0.1372 | 48.5% |
| broadcast | +0.3473 | +0.1696 [+0.1586,+0.1807] | +0.1777 | 51.2% |

**Single-Agent Iterative has no oracle-free effect at all.** Its entire +22-point
advantage is the ground-truth retry loop. "Self-refinement helps" is, here,
"being told you are wrong helps."

Multi-agent structure *does* carry a real oracle-free effect (+14.6 / +17.0
points), so the multi-agent claim survives — but at half the advertised size.

## Second artifact: destructive revision is unobservable by construction

`right_to_wrong` transitions = **exactly 0.0000** in all four protocols
(d1_transitions.csv). Not "rare" — structurally impossible: the loop halts the
moment the evaluator says PASS, so a correct answer is never exposed to further
revision. Any "collaboration rarely hurts" claim from this corpus is circular.

The SC26 project's own unused `e2_paired_accuracy_effects.csv` reports 234
right-to-wrong flips *across protocols* (baseline right, arm wrong) — a different
and legitimate quantity — but *within*-protocol destructive revision is censored.

## Consequence for the AAMAS paper

A clean study of multi-agent mechanism on this corpus must either
(a) restrict to the first submission (oracle-free), or
(b) run a new arm with a **verifier that does not see ground truth**.
