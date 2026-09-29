# Finding 17 — The mechanism, with two of my own F16 numbers CORRECTED

**2026-09-29. Supersedes the quantitative claims of F16. The qualitative
conclusion of F16 survives; two of the numbers I used to reach it did not.**

## 0. What I got wrong in F16

### E1 — "Arm B gets 2.5x MORE repair opportunity"
**Wrong unit.** I counted `evaluator_calls` and called it opportunity. But the
runner gives every arm the SAME budget:

```
MAX_OUTER_ROUNDS = 3   x   INNER_ROUNDS = 2   =  6 deliberation cycles
```

and the evaluator fires **only when the Reviewer approves**. So
`evaluator_calls` counts **submissions**, not chances. It is a *behaviour*, not
a budget. Measured properly, the cycle spend is nearly identical:

| actor / arm | cycles used | submissions | cycles spent revising | recovery |
|---|---|---|---|---|
| gemma-4 / A | 5.53 | 1.53 | **4.01** | 0.207 |
| gemma-4 / B | 5.84 | 5.82 | **0.03** | 0.049 |
| gpt-oss / A | 5.26 | 2.22 | **3.04** | 0.340 |
| gpt-oss / B | 5.35 | 4.62 | **0.73** | 0.245 |
| Llama-3.3 / A | 5.92 | 1.06 | **4.87** | 0.016 |
| Llama-3.3 / B | 5.97 | 5.44 | **0.53** | 0.017 |

The arms use the same number of cycles. Arm B converts essentially *every*
cycle into a submission; Arm A spends 3-5 of its 6 cycles on internal revision
before submitting anything. **Same budget, opposite spending.**

This is a better result than the one I reported, and the corrected framing is
also the one that refutes premature stopping more cleanly: the role-free team
is not cut short. It has the same six cycles. It just never uses one to think
again.

### E2 — the matched-opportunity table matched on the wrong variable
F16 matched Arm A against Arm B *at equal evaluator-call counts* and concluded
"per opportunity, B recovers BETTER." But evaluator calls are submissions, and
submissions differ by arm by construction — conditioning on them is
conditioning on the treatment's own effect. Matched on **cycles**, the sign
reverses to the expected direction and the magnitude collapses:

| actor | cycles | Arm A | Arm B | delta |
|---|---|---|---|---|
| gemma-4 | 6 | 0.032 (n=218) | 0.004 (n=254) | **-0.028** |
| gpt-oss | 6 | 0.070 (n=271) | 0.033 (n=243) | **-0.037** |
| Llama-3.3 | 6 | 0.000 (n=124) | 0.000 (n=116) | 0.000 |

**The F16 claim "per-opportunity B recovers better" is RETRACTED.** It was an
artifact of matching on a post-treatment variable.

### E3 — a third error, caught in the same pass
My first lock-in script extracted answers with a `\boxed{}` regex only. Arms
C/C' never emit `\boxed` — they author the answer in a JSON `answer` field. The
script therefore read Arm C as **"1.000 never changes its answer"**, i.e. the
most frozen arm in the study, when arm-aware extraction shows it is the
**least** frozen (0.113-0.165). A `\boxed`-only extractor does not measure "no
answer change"; it measures "no `\boxed`". Fixed; both numbers below come from
the arm-aware extractor.

## 1. The mechanism, restated on correct units

**Premature stopping: still REFUTED, and now for a stronger reason.** It is not
that Arm B gets more chances — it gets the *same* chances. The Reviewer never
terminates the trajectory early; the budget is fixed at 6 cycles regardless.
What changes is that Arm B's Reviewer stops refusing:

| actor / arm | P(agree on turn 1) | **P(never refuses at all)** | refusals/traj |
|---|---|---|---|
| gemma-4 / A | 0.451 | **0.053** | 4.28 |
| gemma-4 / B | 0.985 | **0.985** | 0.03 |
| gpt-oss / A | 0.479 | 0.050 | 3.15 |
| gpt-oss / B | 0.860 | 0.615 | 0.73 |
| Llama-3.3 / A | 0.260 | 0.008 | 5.58 |
| Llama-3.3 / B | 0.831 | 0.797 | 0.56 |

**98.5% of gemma-4's role-free trajectories contain not one refusal** across
all six cycles. The role-labelled Reviewer refuses 4.28 times per trajectory.

**And the refusal is what moves the answer.** Pooling arms within actor (so the
arm label is not doing the work):

| actor | refusals | n | P(answer moves) | recovery |
|---|---|---|---|---|
| gemma-4 | 0 | 276 | 0.196 | 0.098 |
| gemma-4 | 1 | 17 | 0.941 | 0.765 |
| gemma-4 | 2+ | 239 | 0.674 | 0.117 |
| gpt-oss | 0 | 212 | 0.722 | 0.354 |
| gpt-oss | 1 | 114 | 0.939 | 0.518 |
| gpt-oss | 2+ | 370 | 0.938 | 0.197 |

Note the **non-monotonicity**: recovery peaks at *one* refusal and falls again
at 2+. Trajectories needing repeated refusal are the hard ones. So "more
refusal is better" is NOT the finding; the finding is that zero refusal is a
distinct failure mode.

## 2. The lock-in numbers, corrected

At the full 6-cycle spend — identical budget, identical realized spend, both
first-pass wrong:

| actor / arm | n | **P(answer never changes)** | 95% CI | recovery |
|---|---|---|---|---|
| gemma-4 / A | 218 | 0.353 | [0.294,0.417] | 0.032 |
| **gemma-4 / B** | 254 | **0.866** | [0.823,0.906] | 0.004 |
| gemma-4 / C | 139 | **0.165** | [0.108,0.230] | 0.036 |
| gpt-oss / A | 271 | 0.074 | [0.044,0.107] | 0.070 |
| **gpt-oss / B** | 243 | **0.276** | [0.222,0.333] | 0.033 |
| gpt-oss / C | 150 | 0.113 | [0.067,0.167] | 0.067 |
| Llama-3.3 / A | 124 | 0.774 | [0.702,0.847] | 0.000 |
| Llama-3.3 / B | 116 | 0.862 | [0.793,0.922] | 0.000 |
| Llama-3.3 / C | 93 | **0.108** | [0.043,0.172] | 0.022 |

The 0.866 for gemma-4 Arm B is close to the 0.866 F16 reported, but it is now
computed on the right denominator (full-spend trajectories, message stream)
rather than on budget-exhausted trajectories via submissions. **The Arm A
figure changes materially: 0.353, not 0.037.** The A-B gap is real and large
but roughly half the size F16 implied.

**Llama-3.3 does NOT show the lock-in contrast** (0.774 vs 0.862, overlapping
CIs). Its Arm A is nearly as frozen as its Arm B, and neither recovers at all
(0.000/0.000). The third actor replicates the *first-pass* result and the
*organization* result but **does not replicate the lock-in mechanism** — it is
too weak a solver for the recovery channel to exist at all. This must be
stated, not smoothed over.

## 3. What survives, and what the paper may claim

**SURVIVES:**
- Roles do not buy first-pass accuracy (preregistered null, three actors).
- Removing roles collapses the Reviewer's refusal behaviour to near zero
  (0.985 never-refuse in gemma-4).
- Conditional on a first-pass error, role-free teams freeze their answer far
  more often, and frozen trajectories essentially never recover.
- Arm C, which restores organization structurally, also restores **un-freezing**
  (0.108-0.165 frozen, the lowest of any arm) and restores recovery
  (0.305/0.388/0.101 vs Arm B 0.049/0.246/0.017).

**RETRACTED from F16:**
- "Arm B gets 2.5x more repair opportunity" — wrong unit.
- "Per-opportunity, Arm B recovers better" — post-treatment conditioning.
- "Arm A never changes its answer 3.7% of the time" — 35.3% on the corrected
  measure.

**STILL TRUE:** the §9 fixed-opportunity control remains unnecessary, but for
the corrected reason: **the opportunity is already fixed and equal at 6 cycles
in both arms.** There is nothing to equalize. The experiment would re-run the
existing design.

## 4. Caveats that must travel with these numbers
- Recovery is oracle-gated: the evaluator sees gold. "Recovery" means recovery
  *given* a ground-truth-informed failure signal. **100% of recoveries in every
  cell are oracle-assisted** (x4 S6: pre-oracle recovery is 0 everywhere) —
  none of this is unaided multi-agent self-correction.
- Conditioning on first-pass-wrong, on cycles, and on answer movement are all
  post-treatment. Every number here is descriptive/associational.
- Arm C carries a differential attrition problem (27-79 unjudged trajectories
  per cell vs 0-3 in A/B) that must be reported alongside its recovery figures.
