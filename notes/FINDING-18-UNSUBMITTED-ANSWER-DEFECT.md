# Finding 18 — A scoring defect that penalises exactly the arm the paper credits

**2026-09-29. Found while verifying the manuscript's own mechanism caveat.
Direction matters: the defect works AGAINST our headline, so correcting it
STRENGTHENS the result. It must still be disclosed and reported both ways.**

## 1. The defect

`runner.py` records two things that can disagree:

```python
traj.final_answer = current_answer   # the last answer the team HELD
traj.correct      = last_correct     # the grade of the last answer it SUBMITTED
```

A trajectory that revises its answer after its final submission — and then
runs out of cycles — is graded on a string it no longer holds. The recorded
`final_answer` was never graded at all.

## 2. How often, and in which arm

Among first-pass-wrong trajectories, `final_answer != last submitted`:

| actor / arm | rate | of those, never resubmitted at all |
|---|---|---|
| gemma-4 / A | **0.182** | 0.837 |
| gemma-4 / B | **0.000** | — |
| gemma-4 / C | 0.380 | 0.589 |
| gpt-oss / A | 0.150 | 0.483 |
| gpt-oss / B | 0.082 | 0.115 |
| Llama-3.3 / C | 0.472 | 0.424 |

**The defect is concentrated in the arms that revise.** Arm B/gemma-4 has a
mismatch rate of exactly 0.000 — it never revises after submitting, so it can
never be mis-scored this way. Arm A is mis-scored 18% of the time. This is not
random noise: it is a measurement error whose magnitude is proportional to the
very behaviour the paper's headline is about.

## 3. Exposure, bounded by a positive-controlled conservative check

Exact string match against the gold answer is a strictly conservative proxy
for the LLM grader. **Positive control on 9,020 non-mismatched rows: P(exact
match AND graded wrong) = 0.0000.** Exact match never disagrees with the
grader in the "we under-credited" direction, so any row it flags is a real
mis-score, and the count it produces is a floor, not an estimate.

- 426 mismatched rows total.
- **59 rows are recorded WRONG while the answer the team actually held exactly
  matches gold.** 24 of those 59 are Arm A (17 gemma-4, 5 gpt-oss, 4 Llama).
- The true count is higher, because the grader accepts equivalent forms that
  exact match rejects (it credits 0.843 where exact match credits 0.500).

## 4. Sensitivity: nothing flips, one thing gets bigger

Recoding the 59 exact-match rows as correct (a valid upper bound on the
direction, a lower bound on the size):

| quantity | as recorded | recoded | flips? |
|---|---|---|---|
| gemma-4 B$-$A | $-0.0300$ [$-0.0461$,$-0.0139$] | $-0.0424$ [$-0.0585$,$-0.0270$] | no, **larger** |
| gpt-oss B$-$A | $+0.0088$ [$-0.0088$,$+0.0271$] | $+0.0066$ [$-0.0095$,$+0.0242$] | no, still null |
| Llama B$-$A | $+0.0335$ [$-0.0144$,$+0.0861$] | $+0.0144$ [$-0.0335$,$+0.0622$] | no, still null |
| gemma-4 recovery A | 0.203 | **0.266** | no, **larger** |
| gemma-4 recovery B | 0.048 | 0.048 | unchanged |
| gpt-oss recovery A | 0.339 | 0.351 | no |
| gpt-oss recovery B | 0.245 | 0.251 | no |
| Llama recovery A | 0.014 | 0.042 | no |

**Every recovery gap the paper claims gets WIDER, and no interval crosses
zero that did not already.** The gemma-4 A recovery advantage goes from
0.203 vs 0.048 to 0.266 vs 0.048.

## 5. Decision

- **Primary analysis stays AS RECORDED.** It is the pre-registered outcome
  variable and it is the conservative direction for our claim. Changing the
  primary outcome after seeing which way it moves would be exactly the thing
  the preregistration exists to prevent.
- **Report the recoded row as a disclosed sensitivity analysis**, with the
  positive control, in the same table as the transport-null sensitivity the
  actor3 worker found (D15).
- **Do NOT fix the runner mid-campaign.** A grading change partway through
  would split the corpus under two outcome definitions — the verifier-version
  drift failure. Fix it in the released code with a comment, and note that
  released trajectories carry both fields so any reader can re-derive either.
- The limitation section must say plainly: *the recorded grade is the grade of
  the last submitted answer, and revising arms are therefore under-credited at
  a rate proportional to how much they revise.*

## 6. The manuscript sentence this came from is also wrong

`results.tex` currently says $59\%$ (gemma-4) and $22\%$ (gpt-oss) of failed
first submissions "were never retried before the round budget ran out." Those
numbers are right (0.593 / 0.228) but the words are wrong in the same way F16
was: **0.000 of trajectories in every cell fail to get another cycle.** They
were never *re-submitted*; they were all retried. The sentence describes a
budget exhaustion that does not occur and understates our own result — the
correct statement is that Arm A spends those cycles revising instead of
resubmitting. Must be rewritten.
