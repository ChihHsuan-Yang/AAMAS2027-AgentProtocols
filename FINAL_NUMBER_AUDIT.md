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

---
---

# SECOND INDEPENDENT NUMBER AUDIT — PDF vs canonical output

**Auditor:** second independent number auditor (distinct instrument from the
first audit above). **Date:** 2026-09-30.
**Subject:** `paper/main.pdf` (mtime 17:05, 9 pages) checked **against**
`analysis/out/FINAL_TABLES_OUTPUT.txt` (mtime 14:49), regenerated from
`experiments/results/FROZEN/`.
**Scope difference from audit #1:** audit #1 checked script-vs-script. This
one checks **PDF-vs-script**: every numeric literal in the manuscript traced
to the table that produces it.

## 0. Preconditions — all pass

| check | result |
|---|---|
| sha256 + byte count, all 3 frozen files vs `MANIFEST.json` | **MATCH** (3/3) |
| rows loaded = `total_rows` | 11,600 = 11,600 |
| `FINAL_TABLES.py` rerun vs committed `FINAL_TABLES_OUTPUT.txt` | **byte-identical** |
| PDF numeric literals vs `main.tex` + `sections/*.tex` | PDF is **current** with the sources (no stale build) |
| `figures/` and `paper/figures/` copies of Fig. 1 | identical sha256 |
| working tree clean at audit start | yes |

**Determinism.** `PYTHONHASHSEED` 0 / 1 / random, three full runs:

```
a2cffe46609bef6f2bb6bb4fd584244421b5e79d08a4a27204368157fe5c62cb  run_0
a2cffe46609bef6f2bb6bb4fd584244421b5e79d08a4a27204368157fe5c62cb  run_1
a2cffe46609bef6f2bb6bb4fd584244421b5e79d08a4a27204368157fe5c62cb  run_random
```

Byte-identical, and each run reproduces the committed canonical file exactly.
`FIGDATA.json` sha256 `da87298b4dbf19fd` before and after — unchanged by the
rerun, so the committed figure data is the current figure data.

## 1. Disagreements — three, each traced to root cause

| # | where | paper / canonical | what is right | severity |
|---|---|---|---|---|
| **E1** | `results.tex:249`, PDF p.6 | paper **61.8%**; canonical T5 **0.616** | **canonical** — 61.8% is the pre-fix survivorship value | published number is wrong |
| **E2** | T14, canonical output | T14 labels a DiD **SIG**; T29 and the paper call it null | **T29 / the paper** — T14's label is seed-dependent | script label wrong; no published number affected |
| **E3** | `results.tex:288–290`, PDF p.7 | the sentence's stated **direction is inverted** | **the numbers**, not the sentence | prose wrong, values right |

### E1 — the paper's 61.8% is the survivorship denominator the D1 fix removed

`results.tex:247–249`, reproduced verbatim in the PDF:

> in $98.1\%$ of gemma-4's Arm B first-pass-wrong trajectories the Reviewer
> never declines to submit, against $5.1\%$ in Arm A (**$61.8\%$** vs $4.3\%$
> for gpt-oss).

Canonical `[T5]` prints gpt-oss Arm B `neverrefuse` = **0.616**. Recomputed
from the frozen rows:

| denominator | count | rate |
|---|---|---|
| `judged()` — first verdict received (canonical, post-D1-fix) | 234 / **380** | **0.6158** → 61.6% |
| `graded()` — final grade obtained (pre-fix, survivorship) | 233 / **377** | **0.6180** → 61.8% |

The paper's figure reproduces the **graded** denominator to four decimals.
It is the D1 survivorship defect — the one `is_fpw()` was introduced to fix —
surviving in the manuscript at a site the fix never reached, because the
sentence was written (commit `fa09e98`) against the pre-fix table and never
re-derived afterwards. The canonical table has printed 0.616 since `ba28977`.

**Why only this one.** Of the four percentages in that sentence, gpt-oss Arm B
is the **only** cell with first-pass-wrong attrition (380 judged vs 377
graded). The other three (98.1%, 5.1%, 4.3%) are identical under both
denominators, so they are right by coincidence of zero attrition, not because
they were recomputed.

**One mechanism, many sites — swept.** I re-derived *every* first-pass-wrong-
conditioned quantity the paper quotes under both denominators (recovery,
frozen-answer, never-refuses, cycles, submissions; 9 cells × 5 metrics). 
Denominators disagree in 7 of 9 cells. Of the 20 such values the manuscript
actually quotes, **19 match canonical and exactly one — the 61.8% — matches
the old graded denominator.** The multi-value lists (`0.119/0.092/0.072`,
`0.845/0.208/0.806`, `0.314/0.395/0.139`, `0.222/0.324/0.014`) are all
canonical elementwise, including the Arm C cells where the two denominators
differ most (rec C gemma 0.314 canonical vs 0.412 graded).

**Verdict: the canonical output is right; the paper is wrong.** Fix
`results.tex:249` to `61.6\%`.

### E2 — a `SIG` label in T14 rests on a bootstrap bound sitting at zero

This is **audit #1's D3 defect class, fixed in T2 and still live in T14.**
T2 was converted to seed-free exact McNemar; T14 still reads its label off
`not (lo < 0 < hi)`:

```
[T14]  Llama-3.3-70B-Instruct minus gemma-4-31B-it  +0.0400 [+0.0000,+0.0794]  SIG
```

A `+0.0000` lower bound is the same signature D3 named. Resampling under 60
seeds (4,000 reps, as the script uses):

| contrast | SIG in | 2.5% bound range | bound exactly 0.0 |
|---|---|---|---|
| gpt-oss − gemma-4 | 0/60 | [−0.00687, −0.00437] | 0/60 |
| **Llama-3.3 − gemma-4** | **34/60 (57%)** | **[−0.00188, +0.00188]** | **14/60** |
| Llama-3.3 − gpt-oss | 0/60 | [−0.02000, −0.01564] | 0/60 |

The same comparison in `[T29]` — the Holm section added for exactly this
family — gives `p=0.0553, Holm=0.166, retain H0`. **The canonical output
labels one contrast SIG in T14 and retains its null in T29.**

I swept the other three bootstrap-labelled tables for the same shape and they
are clean: T15 (4 labels) 40/40 or 0/40 across seeds; T17 (4 labels) 40/40 or
0/40; T27's three verdicts 25/25 or 0/25.

**Verdict: T29 and the paper are right; T14's label is wrong.** The paper
says "null in all three pairwise difference-in-differences" and quotes the
interval honestly as `[+0.0000, +0.0794]`, so **no published claim is
affected** — but the canonical output contradicts itself, and a reviewer who
greps `SIG` finds a significant result under a heading that says the primary
test is null.

### E3 — the Arm C first-pass sentence states the opposite of what it does

`results.tex:288–290`, PDF p.7:

> **Conditioning on successful grading instead** would manufacture
> significance out of the same one-sided attrition we reject for accuracy
> below, and also puts Arm C's first-pass column **at 0.779/0.761/0.281**.

The three numbers are correct **but they are the un-conditioned values.**
Measured:

| Arm C first-pass | gemma-4 | gpt-oss | Llama-3.3 |
|---|---|---|---|
| `judged()` — **not** conditioned on grading (canonical T1) | **0.779** | **0.761** | **0.281** |
| `graded()` — conditioning on successful grading | 0.822 | 0.788 | 0.295 |

The sentence promises the reader the *as-graded* column and then prints the
*pre-registered* one. `0.779/0.761/0.281` is what T1 already prints two
paragraphs earlier; conditioning on successful grading gives
`0.822/0.788/0.295`, the pre-fix values audit #1's D1 removed.

Note the direction: as written the sentence tells a reviewer that the
survivorship reading **lowers** Arm C's first pass, when it in fact **raises**
it by +0.043/+0.027/+0.014 — inverting the paper's own argument that
as-graded flatters Arm C. The surrounding paragraph (attrition is one-sided,
as-graded manufactures significance) is correct and is undercut by its own
example.

**Verdict: the numbers are right, the clause introducing them is wrong.**
Either drop "Conditioning on successful grading instead … and also", or keep
the clause and change the values to `0.822/0.788/0.295`. The second is the
repair that matches the sentence's intent.

## 2. Invariants — both hold, both positive-controlled

**Three-way partition**, `n_fpw + n_first-pass-right + n_unjudged == n`:
**11/11 cells exact.**

**`(1 − firstpass) × n_judged == n_fpw`**: **11/11 cells exact** (largest
residual < 1e-6). The five rows audit #1 reported as failing now pass.

*Positive controls.* Re-running both checks with `graded()` substituted for
`judged()` — the exact shape of the defect feared — fires on **8 of 11 cells**
for each check, naming gemma-4 C (262 vs 344) and the partition overshoot
(1682 vs 1600) that the first audit and the T28 comment both describe. A
verifier that could not fail was not accepted.

## 3. PDF-to-canonical trace table

Every result-bearing numeric literal in the manuscript, by source. Sections
`intro`, `related`, `framework`, `measurement`, `method`, `experiments`,
`results`, `discussion`, `limitations`, `conclusion` plus abstract, Tables
1–3 and Figure 1. 271 distinct literals in the section sources; the
non-result ones (years, citation keys, section refs, model names
`gemma-4-31B`/`gpt-oss-120b`/`Llama-3.3-70B`, LaTeX geometry) excluded.

| PDF site | quantity | paper | canonical | verdict |
|---|---|---|---|---|
| abstract, intro, §5.1 | collapse range | 0.000–0.120 → 0.846–0.976 | T1 collapse | OK |
| abstract, §5.3 | gpt-oss first-pass gain | +0.050 / +0.0503 | T3 | OK |
| abstract, intro, §5.4, Fig.1 | gemma recovery | 0.222 → 0.051 | T1 | OK |
| abstract, intro, §5.4 | gpt-oss recovery | 0.324 → 0.247 | T1 | OK |
| abstract, intro, §5.4 | Llama recovery | 0.014 / 0.015 | T1 | OK |
| abstract, intro, §5.6 | Llama Arm C recovery | 0.139 | T1 | OK |
| abstract, intro, §5.5 | cycles / submissions | 5.80 of 5.83 | T5 | OK |
| intro, §5.5 | gemma A submits / revising | 1.54 / 3.98 | T5 | OK |
| abstract, §5.6, Table 3, §7 | Arm C attrition | 8–17%, 8.0/9.9/17.0 | T7 | OK |
| Table 3 footnote, §7 | Arm A / B attrition | 0.0/0.1/0.7, 0.0/0.4/2.5 | T7 | OK |
| §2 | oracle loop value | +0.044 / +0.010 | T13 (+0.0437/+0.0100) | OK |
| §2, §5.3 | gpt-oss fp improvement | +0.0503 | T3 | OK |
| §4, §5.5 | evaluator calls A/B/C | 1.11/1.35/1.03, 1.95/1.85/3.82, 1.20/1.24/1.43 | T0 | OK |
| §4 | actor calls gemma | 6.76 vs 5.87 | T7 | OK |
| §4.2 | scale | 11,600 / 83,320 / 17,486 / 1,600 | T24 (all exact) | OK |
| §4.2 | design arithmetic | 3×(1,600·2+400)+2×400 = 11,600 | verified | OK |
| §4.2, §5.5 | budget, 6 cycles | 3 outer × 2 inner | T24; max(inner_used)=6, 1 distinct budget | OK |
| §5.1 | planner by role | 0.000/0.000/0.183 → 0.979/0.889/0.898 | T8 | OK |
| §5.1 | executor ceiling | 0.907–1.000 | T8 (min .907 max 1.000) | OK |
| §5.1 | reviewer by role | 0.781/0.492/0.823 → 0.998/0.965/0.961 | T8 | OK |
| §5.1, Table 1 | byte duplication | 0.680; ≤0.008; ≤0.003 | T18 (max non-gptB = .008; C/Cp max .003) | OK |
| §3.2, Table 1 | precision / recall | 1.000 / 0.262 | T23 | OK |
| §5.1 | adjudication n | 171 = 42/56/44/29 | T28, KEY.jsonl | OK |
| §5.1, Table 1 | adjudication rates | 1.000 A; 0.857–1.000 B; 0.067–0.286 C/C′ | T23 | OK |
| §5.1, §7 | judge stability | 0.953 | T23 Q5 | OK |
| §5.1 | blinding leak | 42/42 A, 3/56 B, Fisher p=1.5×10⁻²⁴ | recomputed from ITEMS+KEY: **exact** | OK |
| §5.1 | format leak | 39 of 44 Arm C JSON; every Arm B `\boxed` | recomputed: 39/44, 56/56 | OK |
| §5.1 | Arm B planner chars | 1,876 / 1,892 | T9 | OK |
| §5.1 | token-overlap excess | +0.449/+0.432 vs +0.159/+0.145; shift +0.290/+0.287 | T10 | OK |
| §5.1, §5.2, §6, §7 | gpt-oss planner shape | 37 chars, 26.7 s, 2.85 vs 195 ch/s, 2,302 msgs | T9 | OK |
| §5.2 | logging defect | 75.7% / 93.4% / 5.8% / 0.1–0.5% | T26 | OK |
| §5.3 | first-pass B−A + CIs | +0.0000/+0.0077/+0.0503, all 3 CIs | T3 | OK |
| §5.4 | recovery B−A + CIs | −0.1709 / −0.0766, both CIs | T3 | OK |
| §5.4 | paired gemma recovery | 37 vs 3, p=2.0×10⁻⁸ | T4 (1.95e-08) | OK |
| §5.4 | gemma first-pass equality | 0.8025 both arms | recomputed: 1284/1600 both | OK |
| §5.4 | reparameterization | −0.1709×(1−0.8025) = −0.0338 | residual **exactly 0** | OK |
| §5.4 | Llama recovery counts | 4 of 276, 4 of 268 | recomputed | OK |
| §5.4, §5.6, Fig.1 | Llama paired A–C | 0.009 vs 0.096, p=3.8×10⁻⁶ | T4 (3.81e-06) | OK |
| §5.4 | power | ≈80% vs 0.04–0.05 excess; effect 0.171 | `notes/POWER.md` (off-snapshot, caveated) | OK |
| §5.4, §7 | noise floor | 20 of 2,790 = 0.0072 (0.0017–0.0072) | T6, **independently recomputed 20/2790** | OK |
| §5.4 | per-call flip rate | 0.0062 | T6 (84/13,619) | OK |
| §5.4 | noise-propagated CIs | 3 intervals | T27, verdicts stable 25/25 seeds | OK |
| §5.5 | cycles gemma | 5.52 vs 5.83 | T5 | OK |
| §5.5 | never-refuses | 98.1% / 5.1% / **61.8%** / 4.3% | T5 → **E1: 61.6%** | **MISMATCH** |
| §5.5, §8 | frozen answer | 0.845 vs 0.288 | T1 | OK |
| §5.5 | context quartiles | 0.923→0.070; 0.662/0.151; 0.656/0.293; 0.070/0.189; 198 vs 13 | T22 | OK |
| §5.6 | manipulation check | 0.000 Arm C; 0.986/0.916/0.958 Arm B | T11 (1−0.014/0.084/0.042) | OK |
| §5.6 | boundary rejections | 838 / 1,183 / 395 | T11 | OK |
| §5.6 | frozen-answer by arm | 0.119/0.092/0.072; 0.845/0.208/0.806; 0.288/0.750; 0.052 | T1 | OK |
| §5.6 | Arm C recovery | 0.314/0.395/0.139 vs 0.222/0.324/0.014 | T1 | OK |
| §5.6 | judged-then-died count | 150 | recomputed: Arm C exactly 150 | OK |
| §5.6 | gemma/gpt paired A–C p | 0.298 / 0.105 | T4 | OK |
| §5.6 | Arm C first-pass | **0.779/0.761/0.281** | T1 — **E3: clause inverted** | **PROSE WRONG** |
| §5.6 | equation density | 3.11/4.78 vs 2.76/2.12 | T12 | OK |
| §5.6, Table 3 | C−A both scorings + CIs | −0.0225/−0.0050/+0.0175; +0.0190/+0.0361/+0.0453 | T2 | OK |
| §5.7 | P4 DiDs + CIs | +0.0175/+0.0400/+0.0225, 3 CIs | T14 — values OK; **E2: label** | values OK |
| §5.7 | MDE | 0.033 / 0.069 / 0.075 | `notes/POWER.md`, `XDOMAIN-POWER-PREREG.md` | OK (off-snapshot) |
| §5.7 | C′−C | +0.0450/−0.0125 prereg; +0.0196/−0.0089 as-graded | T15 | OK |
| §5, Table 2 | Holm | P3 gemma Holm p=0.0120 | T29 — arithmetic correct (see §4) | OK |
| Table 2 | B−A final + McNemar | −0.0338 p=1.6e−5; +0.0163 p=0.062; +0.0025 p=1.00 | T2; **recomputed b/c: 50/104, 103/77, 27/26** | OK |
| Table 2, §5.8 | single-agent | +0.0131 / +0.0294 / −0.0225 / −0.0563 | T17; coverage 1600/1600 all four | OK |
| §4.2, §5.8, §7 | SA oracle calls | 1.66–1.69 vs 1.11–1.35 | T17 | OK |
| §3.3 | validation | 0.903 κ=0.806 n=72; 0.923 κ=0.843 n=13; 0.967 at n=30 | `notes/VALIDATION-FINAL.md` (off-snapshot, stated) | OK |
| §3.2 | P1a binary rate | 0.722 | T12 gpt-oss B | OK |
| §4.1 | smoke-test confound | 121 trajectories, 74% | `notes/`, pre-campaign, caveated | OK |
| §7 | F18 scoring defect | 17% / 0%; 62; 0 of 10,734 | T19 (**62 = A/B/C total**, verified) | OK |
| §7 | "makes every recovery gap wider" | directional | **tested**: A−B gap widens in all 3 actors | OK |
| §7 | byte-metric firings | gpt-oss 14, gemma-4 3, Llama none | T23 | OK |
| Table 1 | all 18 cells + sensitivity ranges | 0.846–0.999, 0.000–0.892, 9/9 ordering | T1/T18/T20/T23 | OK |
| Figure 1 | n-labels panel A | 1600/1600/1554, 1598/1597/1493, 398/391/349 | FIGDATA `n_judged` — **not** `n_graded` | OK |
| Figure 1 | n-labels panel B | 316/316/344, 463/380/357, 276/268/251 | FIGDATA `n_fpw` | OK |
| Figure 1 | annotation | A 0.014 ≈ B 0.015, C 0.139, p=4e-06 | T1 / T4 | OK |

**Figure 1 is not stale.** Regenerating it from the current `FIGDATA.json`
produces text-identical output to the committed PDF (binary differs only in
embedded timestamps). The only change to `FINAL_TABLES.py` after the figures
were drawn (commit `505c6f9`) was `%.4f` → `%.3g` in three print statements —
no value moved, which is why `FIGDATA.json` is unchanged by a rerun. The
n-labels are the **first-pass denominator `n_judged`**, as required, not
`n_graded`; the two differ in every Arm C cell (1554 vs 1472, 1493 vs 1442,
349 vs 332) and the figure carries the former.

## 4. Holm (T29), checked by hand

Exact bootstrap p-values, script seed: gemma-4 0.004, Llama-3.3 0.3943,
gpt-oss 0.5816.

| i | contrast | p | (m−i)·p | monotone max | printed | verdict |
|---|---|---|---|---|---|---|
| 0 | gemma-4 | 0.004000 | 3×0.004 = 0.012000 | 0.012000 | `0.012` | REJECT |
| 1 | Llama-3.3 | 0.394300 | 2×0.3943 = 0.788600 | 0.788600 | `0.789` | retain |
| 2 | gpt-oss | 0.581600 | 1×0.5816 = 0.581600 | **0.788600** | `0.789` | retain |

The step-down, the monotone running maximum (row 2 correctly inherits row 1's
larger value rather than printing its own 0.582), the `min(1.0, ·)` cap and
the α=0.05 comparisons are all correct. P4 family likewise: 0.0553→0.1659,
0.145→0.290, 0.286→0.290 (inheriting). **Holm is arithmetically correct.**

**Two observations, neither a computational error.**

1. *The Holm input is a bootstrap p, not the exact McNemar the paper
   advertises.* `results.tex:5–8` says "significance is exact McNemar on
   discordant pairs", then quotes the Holm p from `_boot_p()`. Under exact
   McNemar the same family gives Holm 0.0234 / 0.854 / 0.854 — **same three
   verdicts**, so nothing changes substantively, but the paper's quoted
   `0.0120` is not a McNemar-derived number.
2. *`0.0120` is seed-dependent in its digits.* gemma-4's bootstrap p at 20,000
   reps ranges 0.0055–0.0075 over 12 seeds, so Holm ranges 0.0165–0.0225 and
   the paper's exact `0.0120` reproduces in **0 of 12** alternative seeds. The
   **verdict is stable** (REJECT in 12/12 — it is nowhere near 0.05), so this
   is a reproducibility wart on a quoted digit, not a wrong conclusion. Using
   the exact McNemar p the paper already claims to use would remove it.

## 5. No significance label rests on a CI bound at zero — except E2

Swept all four bootstrap-labelled tables:

| table | labels | seed-stable? |
|---|---|---|
| T2 (B−A, C−A, both scorings) | now **exact McNemar**, seed-free | n/a — D3 correctly repaired |
| **T14** | 3 | **1 of 3 unstable (34/60)** → **E2** |
| T15 | 4 | 40/40 or 0/40, all stable |
| T17 | 4 | 40/40 or 0/40, all stable |
| T27 | 3 verdicts | 25/25 or 0/25, all stable |

## 6. What I did that found nothing

So a clean result is not mistaken for a shallow one:

- **Re-derived independently from the frozen JSONL** (not read off the table):
  T1 first-pass/recovery/n_fpw all 11 cells; T5 all five mechanism columns,
  9 cells; T6 noise floor all three estimators (20/2790, 84/13619, 23/13619
  — exact); T19's 62 and its 10,734-row positive control; exact McNemar for
  all six A–B/C–A contrasts (b/c counts 50/104, 103/77, 27/26, 69/105, 87/95,
  32/25); the Fisher blinding leak from `ITEMS_blinded.jsonl`+`KEY.jsonl`;
  T17 single-agent coverage (1,600/1,600 matched, zero unmatched, so no
  problem silently scored 0 for absence).
- **Tested two directional prose claims rather than accepting them**: "recoding
  the 62 makes every recovery gap wider" — true for all three A−B gaps
  (0.171→0.225, 0.077→0.089, −0.000→0.014); "no trajectory was cut short" —
  `max(inner_used)` = 6 = 3×2 from the single distinct budget record.
- **Resolved a 62-vs-67 count discrepancy** rather than reporting it: 67 is
  the all-arm total, 62 is A/B/C, and T19 tabulates only A/B/C. Consistent.
- **Checked the paper is built from the current sources** before trusting any
  PDF literal, and checked Figure 1 against a regeneration rather than
  against its own caption.
- **Positive-controlled every invariant** (§2) and both noise-floor directions
  (planted discordant group → +1 discordant/+1 denominator; planted
  *concordant* repeat → +0 discordant/+1 denominator, i.e. it does not
  over-fire).
- Confirmed the 13 manuscript literals with no exact match in canonical output
  are all legitimate: complements of printed values (0.986/0.916/0.958 =
  1−T11), 2-dp roundings (0.298, 0.105), the four-decimal 0.8025, and
  off-snapshot figures that the paper explicitly sources (validation sheet
  0.903/0.843/0.967, power MDEs 0.033/0.069/0.075).

**Deliberately not proximity-matched.** Every flag above is identified by the
quantity its sentence names and confirmed by reproducing the *wrong*
denominator or the *wrong* seed distribution, not by a value falling within
some tolerance of another value.

## 7. Repairs, in priority order

1. **E1** — `results.tex:249`: `61.8\%` → `61.6\%`. A published number is
   currently the pre-fix survivorship value.
2. **E3** — `results.tex:288–290`: the clause "Conditioning on successful
   grading instead … and also puts Arm C's first-pass column at" introduces
   the un-conditioned values and states the effect's direction backwards.
   Either change the values to `0.822$/$0.788$/$0.295` (matches the sentence's
   intent and the paragraph's argument) or drop the clause.
3. **E2** — `FINAL_TABLES.py` T14: replace the `not (lo<0<hi)` label with the
   seed-free test already used in T2/T29, or delete the label and print the
   T29 p beside it. Canonical output currently says SIG in T14 and retain-H0
   in T29 for the same contrast. Consider auditing for `not (lo<0<hi)` as a
   pattern — T15 and T17 use it too and are stable only by luck of the data.
4. **Minor** — quote the Holm p from the exact McNemar the paper says it uses
   (0.0234), not from `_boot_p()` (0.0120), whose digits do not reproduce
   across seeds. Verdicts are unchanged either way.

---

# DEFECT-CLASS CHECKLIST — what proves each class absent from the submission

**Added 2026-09-30 after three audits each found real defects. The point of
this table is to stop rediscovering a class a fourth time: for every class
this project has actually suffered, it names the ONE check that proves the
class is absent from the artifact, not from the script.**

| # | defect class | how it bit us | the check that proves absence | status |
|---|---|---|---|---|
| 1 | **Stale denominator** — `graded()` where `judged()` is meant | Arm C recovery inflated 0.412 vs 0.314; first-pass 0.822 vs 0.779 | `(1-firstpass) x n_judged == n_fpw` asserted per cell in T1 **and** T28; positive-controlled by substituting `graded()` (fires 8/11) | **PASS 11/11** |
| 2 | **Post-fix sibling** — defect repaired where reported, left running elsewhere | D1 fixed in T1, alive in T28 (figures drew stale values); D3 fixed in T2, alive in T14, T15, T17 | `grep -c "lo<0<hi" FINAL_TABLES.py` == 0; no significance label anywhere derives from a bootstrap CI | **PASS (0 sites)** |
| 3 | **Marginal vs paired population** | T1 0.710/0.762 vs T3 0.713/0.763 — both correct, different questions | audit #2's ~75-row PDF-to-canonical trace names the population for every literal | **PASS** |
| 4 | **As-graded vs prereg population** | C-A flips sign (-0.0225 -> +0.0190) between conventions | both columns printed side by side in the paper with attrition adjacent; T2 prints both scorings | **PASS** |
| 5 | **Wrong test's p-value pasted** | Table 2 carried 2e-8, the recovery test's value, where 1.61e-05 belonged | every p in the paper traced to its T-row; `%.3g` formatting so no p renders as `0.0000` | **PASS** |
| 6 | **Bootstrap nondeterminism** | `set()` iteration under `PYTHONHASHSEED`; one SIG label true in 62% of seeds | 3 runs, seeds 0/1/random, byte-identical output; all significance from exact tests | **PASS** |
| 7 | **Missing gold lookup treated as a negative** | manifest covered n=1600, so 247 of 432 rows silently scored "not under-credited" | T19 asserts complete gold coverage and raises rather than defaulting | **PASS (assert live)** |
| 8 | **Claims file stale behind the paper** | `APPROVED_CLAIMS` still said +0.291/+0.300 and 54 after the fix | chain rule in `SOURCE_OF_TRUTH.md`; claims file re-derived after every `FINAL_TABLES.py` change | **PASS** |
| 9 | **Stale figure data** | FIGDATA's noise floor was fresh while its Arm C first-pass was stale — freshness of one field proves nothing about another | regenerate FIGDATA and all figures in the same run as the tables; audit #2 confirmed text-identical | **PASS** |
| 10 | **Stale Overleaf** | held a stub for two days while GitHub had the real manuscript | file-by-file content hash GitHub `paper/` vs Overleaf tree, then `git ls-remote` after push | **PASS (`cb5e768f`)** |
| 11 | **Page check measuring the wrong subject** | v1 column-blind (missed 539 words); v2 vacuous under `\clearpage` (passed a 10-page paper) | `scripts/pagecheck.py` v3 + positive control: pad the conclusion, confirm EXIT 1, restore, confirm EXIT 0 | **PASS, control run on the fresh clone** |
| 12 | **Interpretation reversed while the numbers are right** | "conditioning on successful grading puts Arm C at 0.779..." — those are the UNconditioned values; the sentence inverted its own paragraph's argument | **no mechanical check exists.** Only a reader who recomputes the direction. This is why the fresh mock review is P0 and cannot be replaced by a script | **MITIGATED, not proven** |

## The one class with no mechanical guard

Class 12 is the reason a human-equivalent read stays in the P0 list. Every
other class above is caught by an assert, a grep, or a positive control that
runs in seconds. A sentence whose numbers are all correct and whose direction
is backwards passes every one of them. Two independent number audits missed
it; the third caught it by asking what the sentence *meant*.

**Any future agent tempted to replace the mock review with more scripts
should read this row first.**
