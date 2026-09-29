# Finding 21 — The scorer noise floor is 0.0023, not 0.0395, and the
# "self-favouring grader" signal is a resubmission artifact

**2026-09-29. The actor3 worker reported a 3.95% grader noise floor (13/329)
and a directional self-favouring signal (gpt-oss credited 8 of 9, p=0.039),
correctly flagging the latter as unclaimed. Both numbers change when the
control is built on the evaluator's ACTUAL INPUT.**

## 1. The unit was wrong, and it matters in our favour

The worker matched on `final_answer`. But **F18 established that
`final_answer` is not what the evaluator saw** — the evaluator grades
`evaluator_history[i].candidate`, and the two differ in up to 47% of
trajectories in some cells. Matching on `final_answer` therefore pairs
gradings of *different strings* and counts their legitimate disagreement as
scorer noise.

Rebuilt on `(problem_uid, evaluator_history.candidate)` — the actual prompt
payload:

| control | pairs | disagreements | rate |
|---|---|---|---|
| matched on `final_answer` | 15,709 | 224 | 0.0143 |
| **matched on the evaluator's own input** | **33,149** | **75** | **0.0023** |

**The true scorer nondeterminism floor is 0.23%, not 3.95%.**

## 2. Why this control is exactly right

The evaluator prompt is built as
`fill(EVALUATOR_PREPEND, task_description=task, solution=candidate, result=gold)`.
It contains the problem, the candidate answer string, and gold. It does
**not** contain the derivation, the arm, or the actor identity. So for a
fixed `(problem, candidate)` the evaluator prompt is **byte-identical** at
temperature 0. Any verdict disagreement on such a pair is pure sampling
nondeterminism — it *cannot* be arm bias or self-favouring, because neither
variable is visible to the grader.

This makes the control free and airtight, in the same way an empty-coalition
cell is a free noise control.

## 3. The consequence for the headline is the opposite of the worry

The worker's concern was: "every B$-$A contrast is smaller than the noise
floor." At 0.0023 that is no longer true — the largest |B$-$A| is $0.042$,
**18x the floor**. And symmetric scorer noise attenuates an effect toward
zero and inflates its variance, both of which the bootstrap CIs already
carry. It cannot manufacture our effect.

Checking symmetry directly (same actor, different arm, identical prompt):
A-vs-B splits 0 vs 2 (p=0.500), A-vs-C 1 vs 2, B-vs-C 6 vs 1 (p=0.125).
**No differential grading between arms is detectable.**

## 4. The self-favouring signal does not survive

On identical prompts the grader's own model looks *dis*favoured, 16-0
(p<0.001) — the opposite sign to the worker's 8-of-9. A quantity that flips
sign when the matching key is corrected is an artifact of the key, not a
finding.

The mechanism is visible: across the 5 discordant keys involving gpt-oss and
another actor, gpt-oss contributes **4.40 gradings per key (max 9)** against
gemma-4's 2.40 and Llama's 2.00. gpt-oss resubmits the same string far more
often, so it takes more draws from a noisy scorer and is near-certain to lose
at least one. **This is a sampling artifact of resubmission count, and it is
downstream of the very behaviour we study** (Arm B submits on nearly every
cycle), so it is post-treatment and cannot be read as grader bias in either
direction.

## 5. What goes in the paper

- Report the floor as **0.0023 (75/33,149 identical-prompt evaluator calls at
  temperature 0)**, with the construction stated so a reader can check it.
- State that the largest observed |B$-$A| is 18x the floor.
- State that no differential grading across arms is detectable, with the
  sign tests.
- **R-10 (evaluator independence) stays UNTESTED.** This control rules out
  grader bias *on the answer string*, which is all the evaluator sees for
  equivalence judging. It does not test a grader that could see derivations.
  Do not upgrade R-10 on the strength of this.
- Keep the worker's two self-caught errors in the record: the `final_answer`
  key, and a hardcoded verdict string printing "no evidence of self-favoring"
  beside p=0.039.

## 6. Note on my own exposure here

I very nearly reported the worker's 3.95% as the paper's noise floor. It came
with a worked example (`omni2_2877`, three actors submitting "218", one
graded FAIL) that made it feel verified. The example is real; the
*denominator* was built on the wrong key. A correct illustration does not
validate the statistic it illustrates.
