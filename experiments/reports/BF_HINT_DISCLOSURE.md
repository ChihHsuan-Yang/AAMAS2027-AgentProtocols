# Evaluator-hint gold disclosure — both domains

Status: COMPLETE (static, on frozen A/B data). Not a gate; a property of the
shared feedback signal, measured because the delivery gate cannot see it.

## Why this was measured

The Sec.9 delivery gate tests for gold leakage with `gold_answer in prompt`,
guarded by `len(ans) > 1`. Two problems with that instrument on SciBench:

1. **21 of 574 SciBench answers are a single character** (`0`x9, `2`x5, `1`x2,
   `4`x2, `3`, `5`, `9`). 100% of real actor messages contain some digit, so an
   unguarded substring test would fire on every prompt. The guard is correct —
   but it means those 21 problems had **no leak coverage at all**. Omni has the
   same blind spot on 55 of its first-pass-wrong Arm A rows.
2. Inspection of real frozen hints shows that when a hint does give the answer
   away, it is often in **word form** — "which is zero", "should be zero", "the
   correct zero uncertainty". A substring test for `"0"` would never catch that
   at any length.

So the substring test is the wrong instrument for this question, and its
`leak: 0` result does not answer it.

## Instrument

`/tmp/sci_leakscan.py::discloses(ans, hint)` — fires on (i) the word form of a
bare single digit, word-bounded; (ii) numeric equality against any number in the
hint, tolerant to 0.1% so `2.36` matches gold `2.3613`; (iii) verbatim match for
non-numeric symbolic answers.

## Controls

| control | result |
|---|---|
| **Permuted pairing** (each hint judged against a *different* problem's gold, 200 shuffles, self-pairs excluded) | observed **0.0166** vs chance **0.0002** [0.0000, 0.0021], permutation **p = 0.005** |
| **Planted disclosures** (4 cases, word + numeric + rounded) | all 4 fire |
| **Planted non-disclosures** (3 cases naming the right topic without the value) | all 3 silent |

The permutation control is the one that matters: it rules out the reading that
`"2.36"` and `"zero"` simply occur in physics prose. They do, at 0.02%. The
observed rate is ~80x that.

## Result

| domain | arm | first-pass-wrong rows | disclosed | rate (95% CI) |
|---|---|---|---|---|
| SciBench | A | 242 | 5 | 2.07% (0.89–4.74%) |
| Omni-MATH | A | 779 | 18 | 2.31% (1.47–3.62%) |

Denominator note (CORRECTED). An earlier version of this file said frozen
SciBench carries "2 replicates per arm per problem". That is wrong. The two
rows per (arm, uid) are **two different actor models** -- gemma-4-31B-it and
gpt-oss-120b -- not two replicates of one model (574 uids x 2 arms x 2 actors
= 2296 rows). The number 242 is unchanged and still correct: it is Arm A's
first-pass-wrong rows pooled across both actors (154 distinct uids). But the
reason matters, because pooling two *models* is a different and stronger
assumption than pooling two *replicates*, and a reader entitled to check that
assumption cannot do so from a false description. The row count (242) is the
correct unit because
it is the unit the recovery rate itself uses; a uid-keyed count gives 154 and
silently drops one of the two actors.

Pooling the two actors was then **tested rather than assumed**, since the
corrected description makes it a stronger assumption than it looked:

| actor | A first-pass-wrong rows | disclosed | rate |
|---|---|---|---|
| google/gemma-4-31B-it | 118 | 2 | 1.69% |
| openai/gpt-oss-120b   | 124 | 3 | 2.42% |
| **pooled**            | **242** | **5** | **2.07%** |

Fisher exact on actor x disclosure: **p = 1.000**. No detectable difference,
so pooling is supported. The split also reproduces the pooled 5/242 exactly.

Worth noting *why* the rates match: disclosure is a property of the
**problem**, not of the actor. Both actors disclose on the same two items
(`scibench:atkins:e3.13(a)(a)`, gold `0`, via the word "zero"; and
`scibench:diff:page344-14`, gold `2.3613`, via "2.36"), with a third
(`scibench:stat:5.2-13`, gold `0.5117`) reached only by gpt-oss because
gemma-4 did not get that item wrong on the first pass. The evaluator writes
the hint, and the evaluator is the same model in both cells. That is the
mechanism behind p=1.000, and it is also why the disclosure rate should not
be expected to differ between A and Bf either.

Measurement note. My first attempt at this split read gold from the JSONL
rows (`r["reference"]`) and returned **0/242 disclosed, p=1.000** -- a clean
null with a tidy p-value. The field does not exist in these rows; gold lives
in the problems parquet. Every comparison was against the empty string. The
pooling conclusion is unchanged, but it now rests on a measurement that can
see a disclosure: it reproduces the 5/242 the main table reports. A null from
an instrument aimed at an absent field is indistinguishable from a real one
on its face.

## Reading — what this does and does not affect

**Does NOT bias A vs Bf.** Per Sec.4, Bf receives the same `${advice}` string
Arm A receives, byte-for-byte, on the same problems. Whatever a hint gives away,
it gives away to both arms. Disclosure cannot produce an A-minus-Bf difference
in either direction, so the Sec.15 contrast is unaffected.

**Does bound the absolute recovery rate, in both arms equally.** Worst case, if
every disclosed problem recovered *only* because of the disclosure, SciBench
Arm A recovery moves 28.5% -> 26.9%, a shift of **1.7 pp**; the CI on prevalence
caps the shift at **4.7 pp**.

**No claim is made that disclosure drives recovery.** Of the 5 disclosed
SciBench rows, 2 recovered. Under the 27.4% base rate that is p = 0.274 — the
observation is consistent with pure chance. The population is too small to
measure an effect, which is exactly why the conclusion is stated as a *bound on
prevalence* rather than a measured effect size.

**Not a defect in Bf, the runner, or the evaluator.** The evaluator is
oracle-gated by design; it sees the gold answer in order to judge. That it
occasionally mentions the value while explaining the error is a property of the
feedback channel the paper already describes, present identically in the frozen
Arm A data the published numbers come from. Per Sec.21 the evaluator is not to
be altered, and nothing here calls for altering it.

## Relation to Sec.6

This is further reason not to describe A and Bf prompts as "semantically
identical after FAIL". They are not (Sec.6), and ~2% of the time the shared hint
carries the answer itself.
