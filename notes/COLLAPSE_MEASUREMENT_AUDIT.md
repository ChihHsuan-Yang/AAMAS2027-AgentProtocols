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

---

# AUDIT ROUND 2 (2026-09-29): a message-count confound, found and resolved

The third-actor worker flagged that the collapse rule ("any duplicate among all
role messages") gives longer trajectories more chances to collapse. **Verified
by the Master Agent — it is real, and resolving it makes the finding stronger.**

## The confound

Collapse by message-count stratum, Arm B:

| actor | nmsg=3 (one pass) | 4-9 | 10+ |
|---|---|---|---|
| **gpt-oss-120b** | **0.813** | 0.823 | 0.966 |
| **gemma-4-31B** | **0.000** | — | 0.978 |

gpt-oss collapses at 0.813 in *minimal three-message* trajectories. gemma-4's
headline 0.177 comes **entirely** from long trajectories — in a single pipeline
pass it collapses **never**.

## Count-matched rule: first three role messages only (one pipeline pass)

| actor | A | **B** | C | C' |
|---|---|---|---|---|
| gpt-oss-120b | 0.000 | **0.698** | 0.000 | 0.000 |
| gemma-4-31B | 0.000 | **0.000** | 0.002 | 0.002 |

**The contrast widens from 0.842 vs 0.177 to 0.698 vs 0.000.** Under a
count-matched definition gemma-4 shows *no* first-pass collapse at all, while
gpt-oss shows it in 70% of trajectories. This is cleaner than the raw number and
it is the version that belongs in the headline.

## Is gemma-4's long-trajectory collapse a different phenomenon?

I suspected retry stagnation (one agent repeating itself across rounds) rather
than role collapse. **Checked: it is not.** Among gemma-4's 231 long
trajectories, duplicate-hash groups are **436 across-role** vs **22
within-role**. So gemma-4 *does* genuinely collapse — but only after the outer
loop has failed repeatedly, i.e. collapse is a *symptom of being stuck*, not the
initial condition.

That is a substantively different story from gpt-oss, which collapses
immediately on the first pass, and it sharpens the paper: for gpt-oss collapse
is the *starting state* and costs nothing; for gemma-4 collapse *arrives with
failure* and coincides with the 0.406 → 0.018 accuracy destruction.

## Reporting rule adopted
Both definitions will be reported. The **count-matched (first-pass) rule is
primary** because it is not confounded with trajectory length; the all-message
rule is reported alongside it. No third actor may be compared on the raw rule
alone — Llama-3.3 emits ~2x more role messages, which would inflate it.
