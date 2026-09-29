# Finding 23 — The grader noise floor, settled across every reasonable
# estimator, and a wrong summary line I caught in my own output

**2026-09-29. Two different floors were circulating after the F21 correction:
mine (0.0023) and the worker's (0.0015). Both used the correct key. The
discrepancy is the DENOMINATOR, and resolving it changes the conclusion.**

## 1. My denominator was inflated by clustering

Both of us counted *pairs* of gradings that share `(problem_uid, graded
candidate)`. But a single trajectory that resubmits one string is graded
repeatedly, and every such repeat enters as a pair:

| pairing rule | disagree / pairs | rate |
|---|---|---|
| all pairs (**mine**) | 90 / 36,933 | 0.0024 |
| different trajectories | 60 / 26,641 | 0.0023 |
| different actors | 39 / 14,880 | 0.0026 |
| different arms | 41 / 21,965 | 0.0019 |

**10,292 of my 36,933 pairs had the same trajectory on both sides.** Those are
still identical prompts at temperature 0, so they are legitimate
nondeterminism draws — but they are *clustered*, not independent, and they
concentrate in the arm that resubmits most. That clustering is precisely what
manufactured the bogus "gpt-oss self-favouring" signal, so it should not be
in the denominator of a floor either.

## 2. The clustering-free estimators

Treating each `(problem, candidate)` **group** as the unit removes the pair
count entirely:

| estimator | value |
|---|---|
| group-level: groups containing both verdicts | **24 / 2,596 = 0.0092** |
| per-call: gradings sitting in a non-unanimous group | 100 / 12,695 = 0.0079 |
| minority-verdict: gradings dissenting from their own group majority | 27 / 12,695 = 0.0021 |
| pairwise, independent trajectories | 60 / 26,641 = 0.0023 |

They span 0.0021–0.0092, a factor of ~4.4. **The group-level rate 0.0092 is
the most conservative and is the one the paper should quote**, with the others
as a stated range. It is the right headline choice because it asks the
question a skeptic asks: *for what fraction of distinct graded strings does
the grader contradict itself at all?*

## 3. Correcting a wrong sentence in my own output

My script printed *"All four framings agree to within a factor of ~3 and all
are $\leq 0.006$"* immediately above a table whose largest entry is 0.0092.
Both clauses are false — the spread is 4.4x and the maximum is 0.0092. The
sentence was hardcoded text, not derived from the values it described; the
numbers were right and only the prose was wrong. **This is the same defect
class the worker caught in its own script an hour ago** (a hardcoded
"no evidence of self-favoring" printed beside p=0.039), and I reproduced it
while writing up that very correction.

## 4. The headline comparison, on the conservative floor

| actor | B$-$A | 95% CI | n |
|---|---|---|---|
| gemma-4 | $-0.0312$ | $[-0.0461,-0.0156]$ | 1,475 |
| gpt-oss | $+0.0103$ | $[-0.0068,+0.0273]$ | 1,463 |
| Llama-3.3 | $+0.0115$ | $[-0.0258,+0.0516]$ | 349 |

Largest $|$B$-$A$|$ = $0.0312$ against a floor of $0.0092$ — **3.4x**, not the
18x I reported in F21 (which used my inflated denominator) and not "inside the
noise" as originally claimed.

**3.4x is a real but modest margin, and it applies to only ONE of three
actors.** gpt-oss and Llama-3.3 have intervals spanning zero and effect sizes
at or near the floor: for those two actors the honest statement is that the
accuracy contrast is **not resolvable above grader noise**. The worker's
instinct was directionally right for two of three cells even though its
statistic was wrong.

## 5. What the paper must say

- Quote the floor as **0.0092 (24 of 2,596 distinct graded strings receive
  contradictory verdicts across repeated identical prompts at temperature 0)**,
  with the 0.0021–0.0092 range across estimators disclosed.
- gemma-4's B$-$A clears it by 3.4x. **Say plainly that gpt-oss's and
  Llama-3.3's do not.** The preregistered null for those cells is therefore
  reported as a null that the instrument could not have resolved either way —
  which is a weaker and more honest statement than "no effect."
- This does not touch the recovery or lock-in results: those contrasts are
  0.203 vs 0.048 and 0.866 vs 0.353, one to two orders of magnitude above any
  version of the floor.
