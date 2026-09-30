# Cross-domain replication — design, slice audit, and the prompt decision

**Worker: cross-domain experiment agent. 2026-09-30.**
**Nothing here is a paper claim. The Master Agent reviews and decides.**

Scope: Stage 1 = Arms A and B, actors `google/gemma-4-31B-it` and
`openai/gpt-oss-120b`, SciBench `text_only`, 574 problems, 2,296 trajectories.

---

## 1. Slice audit — I agree with SciBench, and the reasoning holds up

Every claim in the brief reproduces. Source:
`IEEE-BigData-SciAgentTrace/analysis/hf_cache/release/data/problems/part-00000.parquet`.

| claim | verdict | measured |
|---|---|---|
| SciBench `text_only` n = 574 | CONFIRMED | 574 (580 in `full`) |
| 100% free-response | CONFIRMED | `question_type` = `numeric_or_short_answer` for 574/574 |
| MIT, `evaluation_only_recommended` | CONFIRMED | `source_license_id`=MIT, `commercial_use_policy`=`allowed_with_upstream_terms` |
| LAB-Bench `llm_strict` = 741, 100% MCQ, 89% four-option | CONFIRMED | 741; 741/741 MCQ; 661/741 = **0.892** four-option |
| LAB-Bench is CC-BY-SA-4.0 + do-not-train | CONFIRMED | `training_use_policy` = `do_not_train_upstream_canary` |

**The `options_json` trap is real and I fell into the same hole the brief
warned about, in reverse.** For SciBench, `options_json.notna()` is TRUE for
all 580 rows — every row carries the *string* `"[]"`. Parsing it gives
`len(json.loads(...)) == 0` for **580/580**. So a `.notna()` test says "100%
MCQ" and the parse says "0% MCQ", and the parse is right. I applied the same
discipline in the runner's slice filter: `available_slices_json` is also a JSON
list, so membership is parsed, never truth-tested.

**The MCQ argument against LAB-Bench is sound and I'd keep it.** On a
4-option item under an oracle saying WRONG, emitting a distinct candidate is
worth 1/3 with no reasoning at all; 89% of the slice is four-option. That
makes the mechanism claim indistinguishable from guessing, and Stechly et al.
is the exact criticism a reviewer would reach for. SciBench's free-response
numeric answers keep the same grading contract as Omni-MATH.

### Two things the brief did not anticipate

**(a) SciBench ships no official solution.** `answer_text` is present for
**5 of 580 rows (0.9%)**, versus 4,181/4,181 (100%) for Omni-MATH. The
Omni-MATH evaluator prompt explicitly reasons about "the official solution".
The reference here is answer-only, and the adapted evaluator prompt says so.

**(b) SciBench is much easier than Omni-MATH, which costs Q2 power.** The
upstream released corpus already ran this exact slice with both our actors
(`registry/runs.parquet`, 8 runs, `coverage_status=target_complete`):

| protocol | gemma-4-31B | gpt-oss-120b |
|---|---|---|
| baseline | 0.706 | 0.624 |
| single_agent | 0.794 | 0.723 |
| broadcast | 0.878 | 0.897 |
| **per** | **0.913** | **0.875** |

Omni-MATH first-pass accuracy in our campaign was 0.802 / 0.710-0.762. If
SciBench first-pass lands near 0.85, the first-pass-wrong denominator is
~85-170 per arm instead of 316-463. Simulated power for the paired recovery
contrast:

| fpw rate | n_fpw/arm | gemma-size effect (0.222→0.051) | gpt-oss-size effect (0.324→0.247) |
|---|---|---|---|
| 0.15 | 86 | 0.95 | 0.20 |
| 0.20 | 114 | 0.98 | 0.27 |
| 0.30 | 172 | 1.00 | 0.39 |

**We are well powered for a gemma-sized effect and underpowered for a
gpt-oss-sized one.** A null on gpt-oss must therefore be reported as
inconclusive, not as a failure to replicate. Flagged for the Master before
any headline is written.

---

## 2. The prompt decision: option (b), adapt minimally

**Chosen: (b) — domain-adapt Arm A and the evaluator; carry Arm B
byte-identical.**

The deciding argument is that **(a) is not actually the cleaner comparison
here.** Arm B's generic prompt contains no domain language whatsoever — it is
already domain-neutral, so it transports unchanged by construction. Arm A's
prompt is saturated with math: "competition-level mathematics",
"olympiad-style", "For Omni-MATH, the boxed answer may be numeric, algebraic,
set-valued, functional, geometric", "MUST NOT carry out symbolic manipulation",
"Prefer exact symbolic forms over decimals".

If I reuse Arm A verbatim, A and B differ in **two** ways at once: role
structure (the manipulation) *and* domain fit (a confound that runs
**against** Arm A, since only A is told it is doing mathematics while solving
chemistry). A reviewer would be right to say the replication was rigged
against the arm the paper credits. Adapting A restores the single-variable
manipulation.

What is preserved in the adapted Arm A, clause for clause: hard role
separation + the MUST NOT compute prohibition, the 4-part required structure,
the target-quantity/answer-form section, the DELTA requirement,
Diagnosis/Fix Instruction with the 2-bullet caps, final-answer ownership,
the post-FAIL routing constraint, and the three routing tags. What changed:
domain nouns, and the answer-form enumeration (math forms → units, sign,
significant figures).

`A_SOLVER_APPEND`, `A_EXECUTOR_APPEND` and `EVALUATOR_APPEND` were already
domain-neutral and are carried **byte-identical**; this is asserted in code.

**Arm B is asserted byte-identical to Omni-MATH's at import time**
(`assert P.B_GENERIC_PREPEND == _OMNI.B_GENERIC_PREPEND`). If that ever
fails, the A-vs-B contrast is no longer the same manipulation.

The evaluator prompt is **common mode** — byte-identical across A and B — so
it cannot manufacture an A-vs-B difference; it only sets the difficulty
floor. Its unit/tolerance clauses follow the upstream `science_qa` evaluator
preset rather than being invented here.

### The consequence, which the brief demanded and I am honouring

**P1a and every clause-specific role-fidelity metric are NOT computed for
SciBench and NOT compared to Omni-MATH's.** This is not a caveat, it is an
exclusion: the analysis script does not implement them. This is the same
error class already documented in
`notes/DEFECT-prompt-varies-by-domain.md` — that note found P1a reading
0.925/0.947 on labbench vs 0.111/0.042 on omnimath2 purely because
multiple-choice biology has nothing to compute. Cross-domain fidelity
comparisons get dropped, not caveated.

---

## 3. Held constant (verified in code against `runner.py`)

`MAX_OUTER_ROUNDS`=3, `INNER_ROUNDS`=2, `TEMPERATURE`=0.0, `MAX_TOKENS`=8192,
`MAX_ACTOR_CALLS`=30, `MAX_EVALUATOR_CALLS`=6, `MAX_REGENERATIONS`=3,
`MAX_TRANSPORT_RETRIES`=4, `REQUEST_TIMEOUT_S`=300, `ROLE_ORDER`,
`VISIBILITY[A]`, `VISIBILITY[B]`, `EVALUATOR_MODEL`, `BACKEND`, `BASE_URL`
— all asserted SAME. Stopping rule unchanged.

`config_version` = `aed89f28ab338bdb`, which **differs** from the Omni-MATH
hash by construction (`slice_id` was added to the hashed config), so SciBench
and Omni-MATH trajectories can never be silently pooled.

`experiments/runner.py` is byte-unmodified (md5 `27511610b4ef6d0e4e554cbc402d4a12`,
clean in `git status`).

---

## 4. Grading check — the artifact risk the brief flagged

Two probes, both against the **exact** evaluator prompt and model the runner
uses, imported from `runner_xdomain.py` rather than retyped.

### Probe 1 — `xdom_grader_check.py`: 20 positive / 20 negative

Positives are **not my judgement**: they are real model answers from the
upstream released SciBench run, labelled correct by an independent scoring
pass, joined to gold by `problem_uid`. Negatives are machine-perturbed golds
in the shapes that matter.

|  | graded CORRECT | graded WRONG |
|---|---|---|
| **truly correct** | **20** | 0 |
| **truly wrong** | 0 | **20** |

Sensitivity 1.000, specificity 1.000, 0 unparsed. Per kind, all 5/5:
`power_of_ten`, `wrong_value`, `wrong_sign`, `incompatible_unit`.

### Probe 2 — `xdom_grader_hard.py`, because 40/40 is weak evidence

A check that only ever passes proves little, and probe 1's positives were
already written in gold's unit — the unit-equivalence machinery was never
exercised. The hazard that would actually corrupt this experiment is the
**false negative**: a correct answer in a different-but-equivalent form
graded wrong, which would depress accuracy, inflate the fpw denominator, and
could differ by arm if the arms write answers in different styles. So I
generated equivalence cases that *must* pass, plus near-misses that *must*
fail (a grader that accepts everything is broken, not lenient, and only the
negatives separate those).

|  | graded CORRECT | graded WRONG |
|---|---|---|
| **truly correct** (equivalent restatements) | **22** | 0 |
| **truly wrong** (25% off) | 0 | **8** |

Per kind: `unit_conversion` 10/10 (atm→kPa, kJ→J, dm³→m³, g→kg),
`extra_precision` 10/10, `sci_notation` 2/2, `near_miss_25pct` 8/8.

**Conclusion: the grading path handles unit equivalence sanely in both
directions.** A measured A-vs-B difference on SciBench will not be a unit
artifact.

---

## 5. Smoke run — 12 live trajectories

`run_id=smoke-scibench-01`, 3 problems × 2 arms × 2 actors.

- both arms produced answers in 12/12; 0 errors; 0 transport retries
- evaluator fired in 12/12 (`evaluator_history` non-empty)
- retry loop verified: the hard problem ran to `max_rounds_exhausted_after_fail`
  with 18 actor calls / up to 6 evaluator calls, exactly at budget
- messages logged with prompt/response hashes and `prompt_chars`
- `used_reasoning_fallback` fired 0/96 messages — correct, not broken:
  every call returned real `content`, and the F13 fix records
  `reasoning_chars` separately
- answers extracted correctly in both arms via `\boxed{}`
- Q4 signal already visible at n=3: collapse A 0.000/0.333 vs B 1.000/1.000

### One smoke trajectory exposed a real, already-known defect

`scibench:atkins:e1.19(a)(b)`, gemma-4 Arm A: recorded `correct=0`, but the
held `final_answer` was `1.18e-10 m` and gold is `0.118 nm` — **the same
value**. The evaluator was not wrong: it graded `1.48e-10 m`, the last answer
actually *submitted*, which is genuinely 25% off. The team then revised to the
correct value and ran out of cycles before resubmitting.

This is **FINDING-18** (`notes/FINDING-18-UNSUBMITTED-ANSWER-DEFECT.md`)
reproducing in the new domain: `correct` is the grade of the last *submitted*
answer while `final_answer` is the last answer *held*. It is inherited
unchanged from `runner.py` — deliberately, since changing it would break
comparability with the frozen Omni-MATH campaign. As in the main campaign it
is concentrated in the arm that revises (Arm A), so it works **against** the
paper's headline. `xdom_analyze.py` reports the exposure both ways (`[X2]`),
using the same conservative exact-match floor.

---

## 6. Analysis — definitions are executed, not reimplemented

`xdom_analyze.py` `exec`s `FINAL_TABLES.py` with stdout suppressed and lifts
its function objects, so `judged`, `is_fpw`, `fp`, `fin_prereg`, `ansseq`,
`nrm`, `first3`, `routes`, `func_collapse`, `unanimous` are the **same code
objects** the Omni-MATH tables use. Verified by `inspect.getsourcefile`:
each resolves to `FINAL_TABLES.py` at its original line. `FINAL_TABLES.py` is
imported, never edited.

This matters most for the recovery denominator: `judged(r)` is
`bool(ev(r))` — first evaluator verdict exists — which **includes**
trajectories that later died in regeneration. That is the FATAL-1 fix, and
reimplementing it from memory as `is_fpw`-with-`graded` is exactly the bug it
corrects.

Every contrast is reported with a **paired bootstrap CI and a seed-free exact
McNemar** on discordant pairs, because a bootstrap bound sitting at zero gives
a seed-dependent significance label.

---

## 7. Interpretation rules — pre-registered by the Master, acknowledged here

The Master Agent fixed the reading of this result in
`notes/XDOMAIN-POWER-PREREG.md` (commit `4ac8e3b`) at 761/2,296 rows, before
any recovery contrast existed. **I am bound by those rules and my analysis
script already conforms to them.** Restating the ones that constrain my
reporting:

1. A **gemma-4 null IS informative** (power 0.95 vs the Omni-MATH effect) and
   is reported as a real boundary condition.
2. A **gpt-oss null is NOT informative** (power 0.21). It must be reported as
   "cannot detect an effect of the size seen in Omni-MATH", never as a
   non-replication, and never counted as one of two actors failing.
3. **No pooling of the two actors** to manufacture power. `xdom_analyze.py`
   reports every contrast per actor and never pools.
4. **No P1a or clause-specific fidelity metric across domains** — already
   excluded from the script, not merely caveated.
5. A mixed result is **supplement/rebuttal material**, not a second headline.
   That is the Master's call, not mine.

My independent power simulation, run before launch and from a different
starting point (the upstream released corpus: PER 0.913 gemma / 0.875
gpt-oss across 8 `target_complete` runs), agrees with the Master's: ~0.95
power for a gemma-sized effect, ~0.20-0.27 for a gpt-oss-sized one. The
measured first-pass-wrong rate on landed rows (0.167-0.208, projecting
~96-120 per cell) confirms it a third way.

**Consequence I will honour in the final report:** if gpt-oss comes back
null I will say the study cannot resolve it, and I will not describe the
overall result as a partial replication on that basis.
