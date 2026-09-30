# FINAL NUMBER AUDIT — independent recomputation of every headline number

**Auditor:** independent number auditor. **Date:** 2026-09-30.
**Subject:** `analysis/out/FINAL_TABLES_OUTPUT.txt` (mtime 2026-09-30 11:30),
produced by `analysis/scripts/FINAL_TABLES.py`.
**Instrument:** `analysis/scripts/INDEPENDENT_AUDIT.py`, written from the
written definitions and the raw frozen JSONL **before** `FINAL_TABLES.py` was
opened. Output: `analysis/out/INDEPENDENT_AUDIT_OUTPUT.txt`.

**Method note.** The audit script was written, run, and its numbers recorded
first. Only then was `FINAL_TABLES.py` read, and only to attribute each
disagreement to a line of code. That ordering is the reason four of the five
disagreements below were found at all: three of them are invisible unless you
compute the quantity a second time from the definition.

---

## 0. Hash verification

| file | manifest sha256 | computed | rows | bytes | verdict |
|---|---|---|---|---|---|
| `actor3.jsonl` | `fa22a446d5314bb6…` | `fa22a446d5314bb6…` | 1,200 | 46,037,025 | **MATCH** |
| `armCp.jsonl` | `038e08aec4d4aee1…` | `038e08aec4d4aee1…` | 800 | 23,627,781 | **MATCH** |
| `campaign_v2.jsonl` | `e4e53cb117d91129…` | `e4e53cb117d91129…` | 9,600 | 227,526,687 | **MATCH** |

All three match on **sha256 and byte count**. Rows loaded = 11,600 = manifest
`total_rows`. All 11 cells match their manifest counts. No duplicate
`(problem_uid, arm, actor_model)` key exists (asserted, not assumed).

`MAX_OUTER_ROUNDS=3 × INNER_ROUNDS=2 = 6` verified in `experiments/runner.py`
lines 62–63 and 798–801, **and** empirically: `max(inner_used)` over all
11,600 trajectories is exactly 6.

---

## 1. Headline numbers — mine vs `FINAL_TABLES.py`

### AGREE (recomputed independently, identical)

| quantity | FINAL_TABLES | audit | verdict |
|---|---|---|---|
| cell census (done/graded/ungraded/hardfail), all 11 cells | — | — | **AGREE** |
| first-pass accuracy, all 6 A/B cells | .802/.802/.710/.763/.307/.315 | .802/.802/.710/.762/.307/.315 | **AGREE** (≤.001, denominator identical in A/B) |
| final accuracy PREREG, all 11 cells | — | — | **AGREE** exactly |
| final accuracy AS-GRADED, all 11 cells | — | — | **AGREE** exactly |
| recovery PREREG, all 11 cells | .222/.051/.314/.378/.324/.247/.395/.316/.014/.015/.139 | identical | **AGREE** |
| n_fpw, all 11 cells | 316/316/344/74/463/380/357/98/276/268/251 | identical | **AGREE** |
| B−A and C−A, both scorings, all 12 contrasts | — | — | **AGREE** (point estimates exact; CI bounds ±0.0003 from bootstrap reps) |
| paired recovery transitions + exact McNemar, all 6 | p=1.95e-08 / 2.98e-01 / 2.08e-01 / 1.05e-01 / 3.75e-01 / 3.81e-06 | 1.947e-08 / 2.976e-01 / 2.082e-01 / 1.053e-01 / 3.750e-01 / 3.815e-06 | **AGREE** |
| cycles / submissions / revising, all 9 cells | 5.52/1.54/3.98 … | identical to 2dp | **AGREE** |
| attrition, all 11 cells | .000–.170 | identical | **AGREE** |
| P4 three difference-in-differences | +.0175 / +.0400 / +.0225 | −.0175 / −.0400 / −.0225 (sign convention reversed, same magnitudes/CIs) | **AGREE** |
| C′−C, both scorings | +.0450 / −.0125 / +.0196 / −.0089 | identical | **AGREE** |
| never-refuses, reviewer first-turn accept | .981/.051 etc. | identical on matching denominators | **AGREE** |
| frozen-answer, 6 A/B cells | .288/.845/.052/.208/.750/.806 | identical | **AGREE** |
| single-agent control, 4 published contrasts | −.0225/−.0563/+.0131/+.0294 | identical | **AGREE** |
| functional collapse by role (T8) | — | — | **AGREE** |

### DISAGREE — five, each investigated to root cause

| # | quantity | FINAL_TABLES | audit | who is right |
|---|---|---|---|---|
| **D1** | first-pass accuracy, arms C/Cp | gemma C **0.822**, gpt-oss C **0.788**, Llama C **0.295**, gemma Cp **0.825**, gpt-oss Cp **0.773** | **0.779 / 0.761 / 0.281 / 0.810 / 0.740** | **AUDIT** |
| **D2** | grader noise floor (group-level) | **0.0086** (24/2,791) | **0.0072** (20/2,790) | **AUDIT** |
| **D3** | `SIG` verdict on gpt-oss B−A | **SIG**, `[+0.0000,+0.0331]` | **not resolvable**; verdict is seed-dependent | **AUDIT** |
| **D4** | frozen-answer, arms C/Cp | gemma C 0.119, Llama C 0.072 | 0.125 / 0.076 (accepted messages only) | **FINAL_TABLES** (minor), see below |
| **D5** | "first three role messages" = one pipeline pass | assumed | false for 857 trajectories | **AUDIT** (latent; does not move a published number) |

---

## D1 — first-pass accuracy in Arm C is computed on a survivorship denominator

**This is the same defect the STATISTICAL_AUDIT just fixed in the recovery
column, left unfixed one column to its left.**

`FINAL_TABLES.py` line ~152:

```python
g  = [r for r in s if graded(r)]          # correct is not None
f1 = np.mean([fp(r) for r in g]) if g else np.nan     # <-- first-pass
...
fpw = [r for r in s if is_fpw(r)]         # <-- CORRECTED denominator
```

`is_fpw()` carries an explicit comment saying the denominator must be drawn
from all trajectories because "a trajectory can receive a first verdict and
then die in regeneration." That is exactly right — and `f1`, three lines
above, does the thing the comment warns against.

**Scale and direction.** 178 trajectories receive a first evaluator verdict and
then end with `correct=None`. **178 of 178 are first-pass WRONG** — necessarily,
because a first-pass PASS ends the loop. So the drop is perfectly one-sided and
inflates first-pass accuracy in precisely the arm that attrits:

| cell | n_judged | fp (correct) | n_graded | fp (published) | inflation |
|---|---|---|---|---|---|
| gemma-4 C | 1,554 | **0.779** | 1,472 | 0.822 | **+0.0434** |
| gpt-oss C | 1,493 | **0.761** | 1,442 | 0.788 | **+0.0269** |
| gpt-oss Cp | 377 | **0.740** | 361 | 0.773 | **+0.0328** |
| gemma-4 Cp | 389 | **0.810** | 382 | 0.825 | +0.0148 |
| Llama-3.3 C | 349 | **0.281** | 332 | 0.295 | +0.0144 |
| all A/B cells | — | — | — | — | ≤ +0.0014 |

**A reader can catch this from the published table alone.** If `firstpass` is
computed on `n_graded` but `n_fpw` on `n_judged`, then
`(1 − firstpass) × n_graded ≠ n_fpw`. Applied to T1 as printed:

| cell | (1−fp)×n_graded | printed n_fpw | |
|---|---|---|---|
| gemma-4 C | 262 | **344** | **inconsistent** |
| gpt-oss C | 306 | **357** | **inconsistent** |
| gemma-4 Cp | 67 | **74** | **inconsistent** |
| gpt-oss Cp | 82 | **98** | **inconsistent** |
| Llama-3.3 C | 234 | **251** | **inconsistent** |
| gemma-4 A/B, gpt-oss A | exact | exact | ok |

Five of eleven rows of T1 are internally inconsistent with themselves. The
"262" is not a coincidence: it is the `n_fpw` the **previous** version of the
table printed, before the STATISTICAL_AUDIT fix. The fix was applied to
`recovery` and not to `firstpass`, and the two columns now disagree about
which trajectories exist.

**Verdict: the audit is right.** A trajectory with a first evaluator verdict
*is* judged on its first pass; whether it later died in regeneration is a
property of its *final* state and cannot retroactively unjudge its first
submission. Conditioning on it is survivorship selection of exactly the kind
`FINDING-24` was written about.

**Claim impact.** A2 and the paper's R2 (§`subsec:firstpass`) quote the
*paired A-vs-B* first-pass numbers, which are computed in T3 on a different
path and are **unaffected** (gemma +0.0000, gpt-oss +0.0502, Llama +0.0077 on
the corrected judged pairing — matching the published +0.0000/+0.0503/+0.0077).
**No approved claim changes.** What changes is T1's Arm C first-pass column,
which is where a reviewer looks to see whether enforcement hurt the first
answer, and it currently reads 0.043 too generous for gemma-4.

---

## D2 — the grader noise floor folds non-identical prompts

The definition is *"repeated **identical** prompts at temperature 0."*
`FINAL_TABLES.py` groups by `(problem_uid, nrm(candidate))` where
`nrm` = strip **all** whitespace and strip `$`. The evaluator prompt
interpolates the candidate **verbatim** (`prompts.EVALUATOR_PREPEND`:
`Submitted candidate:\n${solution}`), so two candidates differing by
whitespace produce **two different prompts**. Their disagreement is format
sensitivity, not nondeterminism, and does not belong in a nondeterminism floor.

| grouping | discordant / repeated | floor | groups folding >1 raw string |
|---|---|---|---|
| exact bytes (the literal unit) | 20 / 2,790 | **0.0072** | 0 |
| NFKC + collapse whitespace (audit) | 20 / 2,790 | **0.0072** | 0 |
| strip all whitespace + `$` (published) | 24 / 2,791 | 0.0086 | **6** |

Six of the published 24 discordant groups fold more than one distinct raw
candidate string. Two examples:

- `omni2_3708`: `'(2014, 0, 0)'` graded **1**, `'(2014,0,0)'` graded **0**.
- `omni2_526`: `'NNYYY Y'` graded **0**, `'NNYYYY'` graded **1** (×5).

These are real and worth reporting — as *grader format sensitivity* — but they
are not the same measurement. The exact-bytes grouping and my NFKC grouping
agree to the row (20/2,790), which is the confirmation that 0.0072 is the
robust number and 0.0086 is the artifact of one specific normalization.

**Verdict: the audit is right**, and note the direction — the published floor
is **19% too high**, which is the *conservative* direction for the paper's own
"clears the floor" argument. Correcting it makes gemma-4's margin 4.7× rather
than 3.9×.

**Claim impact.** A8 and two paper passages (`results.tex` ~193,
`limitations.tex` ~43) quote "24 of 2,791 … 0.0086 … 3.9×". All three
numbers change to 20 / 2,790 / 0.0072 / 4.7×. **The verdicts do not change**:
gemma-4 still clears, gpt-oss and Llama-3.3 still do not. Note also that
`APPROVED_CLAIMS.md` A8 has just been amended to say the ratio should not be
reported at all — that instruction and this correction agree on the outcome
and disagree on the reason, so the floor itself still needs fixing wherever
it is quoted as a count.

---

## D3 — one published `SIG` is decided by the bootstrap seed, not the data

T2 prints `gpt-oss B−A +0.0163 [+0.0000,+0.0331] SIG`. A lower bound printed
as exactly `+0.0000` is the signature of a CI sitting **on** the decision
boundary. Resampling the same 1,600 paired differences under 40 different RNG
seeds:

| contrast | fraction of seeds returning SIG | exact McNemar |
|---|---|---|
| gemma-4 B−A | **1.00** (stable) | p = 2e-08, reject |
| **gpt-oss B−A** | **0.12** | **p = 0.0621, do not reject** |
| Llama-3.3 B−A | 0.00 (stable) | p = 1.000 |
| gemma-4 C−A | **1.00** (stable) | p = 0.0078, reject |
| gpt-oss C−A | 0.00 (stable) | p = 0.604 |
| Llama-3.3 C−A | 0.00 (stable) | p = 0.427 |

The 2.5% bound ranges over `[−0.00063, +0.00063]` across seeds and is exactly
`0.0` for 65% of them. **Exactly one contrast in the study has a seed-dependent
verdict, and it is the one the table labels SIG.** The seed-free adjudicator on
the same discordant pairs (103 vs 77) gives p = 0.062.

This is the defect class named in my brief — "one contrast flipped
significant/not-significant across four runs of the same script" — surviving
in a different form. `FINAL_TABLES.py` uses a module-level `RNG`, so its runs
reproduce each other; that makes the instability invisible without varying the
seed on purpose.

**Verdict: the audit is right.** The honest label is "not resolvable", and it
happens to agree with the treatment the paper already gives gpt-oss elsewhere:
A8 and `results.tex` both say gpt-oss's B−A is *not resolvable above grader
noise*. So the paper currently calls the same contrast SIG in T2 and
not-resolvable two paragraphs later. Removing the SIG makes the manuscript
self-consistent.

---

## D4 — frozen-answer in Arm C: rejected attempts count as answers

`ansseq()` walks **all** role messages including ones the validator rejected.
A rejected arm-C executor attempt often still carries an `"answer"` field, so
a trajectory whose only "second answer" was a rejected attempt is scored as
having moved.

| cell | published (incl. rejected) | audit (accepted only) |
|---|---|---|
| gemma-4 C | 0.119 | 0.125 |
| Llama-3.3 C | 0.072 | 0.076 |
| all other cells | — | identical |

**Verdict: FINAL_TABLES is defensible and I am not claiming it is wrong.** The
question "did the team produce a distinct second candidate?" can reasonably be
answered over everything the actor generated. But it should be *stated*: a
rejected message never entered the shared history and was never submitted, so
under the stricter reading the frozen-answer rate for Arm C is 0.006 higher.
The effect is far too small to move A5 or A6. Recorded for completeness, and
because it is the only place the two implementations disagree in the direction
that flatters Arm C.

**A note on the extractor, which I expected to be the bug and was not.** The
brief warned that an arm-blind `\boxed`-only extractor reads Arm C as maximally
frozen. `FINAL_TABLES.py` handles this correctly. My positive control PC6
confirms the hazard is real and large: on gemma-4 Arm C the arm-aware rate is
**0.125** and the arm-blind rate is **1.000** — the blind extractor would call
Arm C the most frozen arm in the study when it is the least. Both
implementations avoid it.

---

## D5 — "the first three role messages" are not one pipeline pass

`first3(r)` takes the first three planner/executor/reviewer messages in
document order, including **rejected** attempts. For **857 of 11,600**
trajectories those three messages are not one pass:

| shape | count |
|---|---|
| `(planner, planner, executor)` | 190 |
| `(planner, executor, executor)` | 201 |
| `(planner, planner, planner)` | 25 |
| fewer than 3 role messages | 56 |
| first3 contains ≥1 rejected attempt | **857** |

All 857 are in arms C/Cp. Because collapse and unanimity are `n/a`/`nan` for
C/Cp in the published tables, **no printed number moves**: recomputing T8's
`all3` on strictly-pass-1 accepted messages reproduces every published value
(gemma B 0.976, gpt-oss B 0.846, Llama B 0.872, all A/C values). 

**Verdict: the audit is right about the code, but this is a latent defect, not
a wrong number.** It is worth fixing because it is a trap for the next person
who extends a first-pass metric to Arm C — which is exactly what the frozen
collapse rubric (`COLLAPSE_ANNOTATION_RUBRIC.md`) defines its unit as.

---

## 2. Single-agent control — located, provenance audited, soundness assessed

**Not in the frozen snapshot.** Source:
`…/IEEE-BigData-SciAgentTrace/analysis/hf_cache/release/data/trajectories/part-00000.parquet`,
`protocol_id='single_agent'`, `benchmark_id='omnimath2'`, 9,195 rows.
File sha256 `d56dc5bdab0134fdf5b8ae383c061be7da3ca8039fe1d886c3ca1cec18fdb619`
(matches the `d56dc5bdab0134fd…` recorded in `RESULT_PROVENANCE.md`).

The four published contrasts **reproduce exactly** (gemma A −0.0225, gemma B
−0.0563, gpt-oss A +0.0131, gpt-oss B +0.0294), and coverage is complete: all
1,600 of our problems are present in both single-agent actor cells, so no
problem was silently scored 0 for being absent. I assert this rather than
assume it, and the audit reports a shortfall if one appears.

**Is the comparison sound? Partly, and the caveats are not all currently stated.**

| axis | status |
|---|---|
| evaluator model | **matched** (`gpt_oss_120b` both sides) |
| benchmark, problem set | **matched** (same 1,600 `problem_uid`s) |
| oracle exposure | control gets **more** (1.66/1.69 evaluator calls vs our Arm A's 1.11/1.35) — conservative for the claim |
| actor calls | control gets **fewer** (3.16/3.40 vs 5.87–7.54) — generous for the claim |
| `source_commit` | **DIFFERENT PER ACTOR**: gemma `7c975354…`, gpt-oss `be9c47c9…` |
| `release_status` | `candidate`, not `released` |
| Llama-3.3 | **no single-agent cell exists** |
| byte pinning | no manifest in this repo pins this file |

The **per-actor source_commit split is the one I would flag**. A9 requires
quoting gpt-oss and gemma-4 *together* and reads the two as a contrast
("collapsed team beats its single agent" vs "team is worse than its single
agent"). Those two control arms were built from **different commits**, so the
contrast between them is cross-version in a way no within-snapshot contrast
is. The existing "not in the frozen snapshot" caveat does not cover this.
The comparison is sound enough for the directional guard A9 makes; it is not
sound enough to support any statement about the *size* of the gap differing
between the two actors.

---

## 3. Positive controls — 11 planted defects, 11 detections

Each corrupts a copy of the data or the input in the shape of the defect
feared, and confirms the check fires. Run every time the script runs.

| control | planted defect | fired | evidence |
|---|---|---|---|
| PC1 | one byte flipped in `armCp.jsonl` | **YES** | sha256 MISMATCH reported on that file |
| PC2 | lookup key absent from a manifest | **YES** | naive `.get(p,0)` scores it 0 with n=3; guarded path uses n=2 and reports the shortfall |
| PC3 | blanked `evaluator_history` on 1,284 first-pass-correct rows | **YES** | n_judged 1600→316, accuracy 0.8025→0.0000; a defect scoring unjudged as 0 would have kept n=1600 |
| PC4 | nulled `correct` on every correct row in gemma/A | **YES** | PREREG n=1600 all→0; AS-GRADED n=246. Proven to be different code paths |
| PC5 | injected one discordant grading group | **YES** | discordant 20→21, repeated 2790→2791, exactly +1 each |
| PC5b | injected one *concordant* repeat | **YES** | discordant unchanged at 20, denominator 2790→2791 — the check does not over-fire |
| PC6 | arm-blind `\boxed`-only extractor | **YES** | gemma/C frozen 0.125 (aware) vs **1.000** (blind) — reproduces the exact backwards reading the brief warned about |
| PC7 | silent-empty JSON parse on arm C | **YES** | 500/500 sampled accepted arm-C executors yield an answer (100%) |
| PC8 | duplicate `(problem,arm,actor)` row | **YES** | AssertionError raised, naming the key |
| PC9 | McNemar on a symmetric table | **YES** | b=c=10 → p=1.000; b=37,c=3 → p=1.9e-08 — discriminates both ways |
| PC10 | degenerate bootstrap | **YES** | all-zero → [0,0]; 5% ones → [0.0370,0.0640] |

**11 / 11 fired.** PC5b and PC9 are the two that test for *over*-firing;
both behaved.

---

## 4. Determinism

`INDEPENDENT_AUDIT.py` run 5 times:

```
PYTHONHASHSEED=0       ced5e0d9d6cd6c752604e0f7cec8e4d4
PYTHONHASHSEED=1       ced5e0d9d6cd6c752604e0f7cec8e4d4
PYTHONHASHSEED=random  ced5e0d9d6cd6c752604e0f7cec8e4d4
PYTHONHASHSEED=random  ced5e0d9d6cd6c752604e0f7cec8e4d4
PYTHONHASHSEED=random  ced5e0d9d6cd6c752604e0f7cec8e4d4
```

**Byte-identical, all five.** Achieved by: sorting every aggregation key before
iterating (`sorted(set(ca) & set(cb))`, never bare set iteration); seeding every
`np.random.default_rng` from `sha256(contrast_name)` rather than `hash()`; and
fixing the file read order. No value reaching stdout depends on dict or set
iteration order.

---

## 5. What I checked and found clean

So the clean parts are not mistaken for parts I skipped:

- Every cell count against `MANIFEST.json`; duplicate keys asserted absent.
- The 6-cycle cap, verified in source **and** empirically (`max(inner_used)=6`).
- Both scoring rules implemented independently and shown to be distinct code
  paths by a positive control.
- All 12 paired contrasts, both scorings, independent bootstrap.
- All 6 paired recovery transition tables and exact McNemar p-values.
- The three P4 difference-in-differences (sign convention differs, magnitudes
  and intervals agree).
- Attrition, rejects/trajectory, cycles/submissions/revising, reviewer
  first-turn accept, never-refuses, unanimity (both denominators reproduced),
  functional collapse by role.
- Gold-answer coverage: `FINAL_TABLES.py` T19 now hard-asserts `_missing == 0`,
  which is the correct repair for defect class #3; I confirmed the assert is
  live and passes.
- Candidate-string truncation at 2,000 chars: only 3 of 17,486 gradings reach
  the cap and **none** of them sits in a repeated group, so truncation cannot
  be folding two different answers into one noise-floor group.

---

## 6. Recommended repairs, in priority order

1. **D1** — change `f1 = np.mean([fp(r) for r in g])` to use the same
   all-trajectories denominator `is_fpw()` already documents. Five of eleven
   T1 rows are currently self-inconsistent. Add the
   `(1−firstpass)×n_graded == n_fpw` identity as a runtime assert so this
   cannot recur.
2. **D3** — drop the `SIG` on gpt-oss B−A, or report exact McNemar
   (p = 0.062) beside every bootstrap verdict. As printed, T2 contradicts A8
   and `results.tex` about the same contrast.
3. **D2** — regroup the noise floor on exact candidate bytes: 20 / 2,790 =
   0.0072. Update `results.tex` ~193 and `limitations.tex` ~43. Report the six
   whitespace-folded pairs separately as grader format sensitivity — they are
   a finding, in a different table.
4. **D5** — make `first3()` select accepted, outer_round-1, inner_round-1
   messages. No published number moves; the trap does.
5. **A9 provenance** — add "the two single-agent arms come from different
   source commits" wherever the gpt-oss/gemma-4 contrast is drawn.
