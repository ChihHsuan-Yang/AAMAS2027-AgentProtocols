# Collapse measurement audit (2026-09-29)

The 84% figure is now the headline, so it must survive the most skeptical audit.
Every number below was computed by the Master Agent directly from campaign JSONL.

## What exactly is compared

`response_sha256_12 = sha256(r.text)[:12]` where `r.text` is the **raw model
completion**. It is taken *before* parsing, *before* JSON extraction, and
contains **no** role wrapper, no system header, no scaffold field — the runner
adds role tags only when appending to `shared_history`, never to the hashed
text. Verified at `runner.py:744,755`. So the measure compares what the model
actually emitted, which is the right subject.

## Q5 — Could deterministic decoding mechanically produce equality?

**No. This is the decisive check.**

| collapsed groups with **identical** prompt | **0** |
|---|---|
| collapsed groups with **different** prompts | **1,364** |

Every collapsed group arose from *different* inputs. Same-input determinism
cannot explain any of it. (Reinforced by the endpoint's measured
nondeterminism: gpt-oss returned 3 distinct outputs to 3 identical requests.)

## Q8 — Does it survive normalization?

| measure | Arm B / gpt-oss |
|---|---|
| exact (byte-identical) | **0.842** |
| normalized (whitespace/case/LaTeX/punct stripped) | **0.927** |

Normalization *raises* the rate. The exact measure is therefore **conservative**
— it undercounts. The 8.5-point gap is near-exact collapse.

## Q9/Q10 — When does it occur?

1,079 collapse events in outer round 1 vs 591 later. It happens on the **first
pass**, not only after evaluator feedback, so it is not an artifact of retry
convergence.

## THE REVIEWER'S BEST ATTACK: "collapse only happens on easy problems"

**Refuted for gpt-oss — and the pattern inverts between actors.**
Difficulty proxy = historical one-shot baseline accuracy on the same problem.

| stratum | gpt-oss collapse | gemma-4 collapse |
|---|---|---|
| HARD (baseline ≤1/3) | **0.827** | 0.567 |
| MED | 0.709 | 0.094 |
| EASY (baseline >2/3) | 0.900 | **0.008** |

gpt-oss collapses at 0.827 **on the hardest problems**. It is not an
easy-problem artifact. gemma-4's collapse is concentrated on hard problems and
essentially absent on easy ones (0.008) — a different phenomenon in the same
metric, which is itself worth reporting.

## THE DECISIVE TABLE: same problem, organization lost, what happened to accuracy

Matched within problem, A vs B, the transition **differentiated → collapsed**:

| actor | n | acc under A | acc under B | B−A |
|---|---|---|---|---|
| **gpt-oss-120b** | **1,024** | 0.823 | 0.819 | **−0.0039 [−0.0225,+0.0146]** |
| **gemma-4-31B** | 165 | 0.406 | 0.018 | **−0.3879 [−0.4606,−0.3152]** |

**The same organizational transition costs gemma-4 39 accuracy points and costs
gpt-oss nothing**, on 1,024 matched problems. This is the paper.

Note the gemma-4 A_diff→B_coll cell is *catastrophic* (0.406 → 0.018): when
gemma-4's organization collapses, the system essentially stops working. For
gpt-oss the identical transition is free.

## Status of the levels Bella asked for

- **Level 1 exact redundancy** — DONE, audited above, conservative.
- **Level 2 semantic redundancy** — normalized collapse (0.927) is a first cut;
  embedding/edit-distance work dispatched.
- **Level 3 functional contribution** — NOT YET DONE. Required before claiming
  "no material contribution". Dispatched.
- **Human validation** — NOT YET DONE. Required before the headline is final.

## Verdict so far

The exact-collapse measure is **sound, conservative, and not explainable** by
determinism, normalization, retry convergence, or problem easiness. The headline
survives this audit. It is **not yet** licensed to claim *functional* redundancy
— that needs Level 3 plus human validation.
