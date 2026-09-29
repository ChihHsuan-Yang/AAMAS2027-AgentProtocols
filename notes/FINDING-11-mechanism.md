# Finding 11 — WHY the two actors differ: roles are load-bearing for RECOVERY, not for solving

**2026-09-29. This is the mechanism analysis (Bella's §9, risk #5).**
Tested seven candidate mechanisms; two are refuted, one is strongly supported.

## REFUTED — Mechanism A: "gpt-oss's first agent already solved it"

Arm B, first planner message graded against gold:

| actor | first-agent correct | final | rescued (first wrong → final right) |
|---|---|---|---|
| gpt-oss-120b | **0.481** | 0.856 | **0.380** |
| gemma-4-31B | 0.527 | 0.831 | 0.304 |

gpt-oss's first agent is correct **less than half the time**, and 38% of its
final answers are rescued from a wrong first answer. Collapse is **not** "the
work was already done". This was the most obvious explanation and it is dead.

## SUPPORTED — the gap is entirely in RECOVERY, not in solving

Decomposing each actor's B−A into first-submission success vs recovery after a
failed submission, paired on the same problems:

| actor | n | first-pass A→B | **recovery A→B** |
|---|---|---|---|
| **gemma-4-31B** | 1,280 | 0.809 → 0.809 (**Δ −0.001**) | **0.490 → 0.045 (Δ −0.445)** |
| gpt-oss-120b | 1,274 | 0.729 → 0.775 (Δ +0.046) | 0.431 → 0.249 (Δ −0.182) |

**Gemma-4's first-pass rate is unchanged to three decimals.** Removing roles
costs it *nothing* on problems it solves outright. Its entire −0.029 loss comes
from recovery collapsing from 0.490 to **0.045** — when gemma-4 without roles
gets it wrong the first time, it essentially never recovers.

gpt-oss also loses recovery (0.431 → 0.249) but *gains* first-pass (+0.046),
and the two roughly cancel.

## The redundancy mechanism: consensus and escape from it

In Arm B all three agents answer. Do they agree, and does it matter?

| | gpt-oss-120b | gemma-4-31B |
|---|---|---|
| unanimous | 0.749 | **0.954** |
| unanimous and **all wrong** | 0.312 | **0.436** |
| **recovered from unanimous-but-wrong** | **0.772** | **0.638** |
| split (disagreement) | 0.251 | 0.046 |

gemma-4 without roles reaches **near-total consensus (0.954)**, is wrong in
43.6% of those cases, and escapes that state only 63.8% of the time. gpt-oss
retains disagreement 5x more often (0.251 vs 0.046) and escapes wrong consensus
77.2% of the time.

## The synthesis

> **Role differentiation is load-bearing for error recovery, not for first-pass
> solving — and only for the actor that cannot otherwise escape a wrong
> consensus.**

For gemma-4, role prompts are what keep the three agents from locking onto the
same wrong answer. Remove them and the team agrees 95% of the time, is wrong
in 44% of those, and cannot get out: recovery drops to 0.045.

For gpt-oss, enough residual disagreement survives role removal that the
evaluator loop still has something to work with.

This also explains why **Arm C does not help**: enforcing *answer-authorship*
boundaries does not restore *disagreement*. It restores who may speak, not
whether they differ.

## Caveats
- Recovery is conditioned on needing a retry, which is post-treatment. The
  first-pass/recovery split is a **decomposition**, not a causal mediation.
- The retry loop is oracle-gated (the evaluator sees gold), so "recovery" here
  means recovery *with* an oracle signal. This is a property of the protocol
  family, documented since F02, and bounds the external validity of the
  mechanism claim.
