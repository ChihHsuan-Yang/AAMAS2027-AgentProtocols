# Finding 24 — I checked the pre-declared NOT-SUBMIT condition. It is not
# triggered, but only because the preregistration's own scoring rule says so.

**2026-09-29. This was a near-miss in both directions and must be recorded
before any of it reaches the manuscript.**

## 1. The condition

`PREREGISTRATION.md`, written before results:

> **What would make us NOT submit** — "The interaction (P4) is null AND the
> main effect matches 2608.21747's published direction — that is their result
> in a new setting, not ours."

2608.21747 (Canedo) reports structure helping *weak* models and barely helping
strong ones: value inversely proportional to model strength.

## 2. Why I raised the alarm

Scoring Arm C **as graded** (dropping unjudged trajectories):

| actor | base acc(A) | C$-$A | 95% CI |
|---|---|---|---|
| Llama-3.3 | 0.356 | $+0.0453$ | $[+0.0060,+0.0876]$ SIG |
| gpt-oss | 0.850 | $+0.0379$ | $[+0.0233,+0.0525]$ SIG |
| gemma-4 | 0.874 | $+0.0221$ | $[+0.0079,+0.0364]$ SIG |

All three positive and significant, **monotonically decreasing in actor
strength** — Canedo's direction exactly. And P4 is null in all three pairwise
diff-in-differences (CIs $[-0.037,+0.005]$, $[-0.067,+0.022]$,
$[-0.053,+0.037]$).

Null interaction + Canedo's main effect = **the pre-declared not-submit
condition, met on its face.**

## 3. Why it is not actually triggered

That scoring **violates the preregistration's own exclusion rule**:

> "Trajectories failing to parse are counted as incorrect (not dropped),
> matching the existing corpus convention."

Arm C's unjudged trajectories are `hard_failure: regeneration_exhausted` —
the schema validator rejected the output until the regeneration budget ran
out. That is a parse failure, and the prereg says score it 0. Attrition is
**8.2% / 9.7% / 17.0%** in Arm C against **0.0% / 0.1% / 0.7%** in Arm A, so
dropping it is a large, one-sided survivorship selection.

Applying the preregistered rule:

| actor | C$-$A (prereg scoring) | 95% CI |
|---|---|---|
| gemma-4 | $\mathbf{-0.0203}$ | $[-0.0360,-0.0033]$ **SIG, negative** |
| gpt-oss | $-0.0040$ | $[-0.0204,+0.0132]$ null |
| Llama-3.3 | $+0.0176$ | $[-0.0202,+0.0554]$ null |

**The main effect reverses sign for gemma-4 and vanishes for gpt-oss.** It no
longer matches Canedo's direction — it does not match any monotone direction.
The not-submit condition requires *both* conjuncts; the second fails.

This is the P4 null the manuscript already reports, and it stays null. What
changes is that I can now state the not-submit test was actually run.

## 4. The honest reading, which is uncomfortable both ways

- **As-graded scoring** would have let us claim "architectural enforcement
  improves accuracy in all three actors" — a positive, clean, publishable
  result. It is survivorship.
- **Preregistered scoring** gives a null with one significant *negative*.
- The gap between them is entirely Arm C's 8–17% attrition.

I must not present the as-graded numbers as the headline. They belong in the
paper as the sensitivity analysis, with the attrition rates beside them, and
the preregistered scoring as primary. The manuscript's existing "P4 null"
framing is correct and survives; it is the C$-$A *main effect* that needed
this check.

## 5. Near-miss, recorded

Had I run only the as-graded numbers I would have reported a positive
enforcement effect ordered by capability — which is both (a) survivorship and
(b) the exact pattern the preregistration told us not to submit on. Had I run
only the prereg-scored numbers I would never have known how close the two
readings are, or that the difference is one exclusion rule.

**Both scorings must appear in the paper**, with attrition disclosed, because
a reader who re-derives either one needs to find the other.

## 6. Action
- `results.tex` §\ref{subsec:p4null}: confirm it uses prereg scoring. Add the
  as-graded row as a disclosed sensitivity with attrition.
- `SUBMISSION_CHECKLIST.md`: record that the not-submit condition was
  evaluated against final data and not met, with the derivation.
- Report Arm C attrition per cell in the results table, not only in
  limitations.
