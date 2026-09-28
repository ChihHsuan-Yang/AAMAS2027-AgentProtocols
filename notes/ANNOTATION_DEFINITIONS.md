# Annotation definitions — frozen before annotating (2026-09-28)

Written BEFORE looking at the 240-message sheet, so the definitions cannot be
tuned to make the automated measures look good.

## Scope

Only clauses that the message's OWN domain contract imposes are annotated.
Per `DEFECT-prompt-varies-by-domain.md`, the full contract exists only in
omni_math; lab_bench_mc and science_qa presets impose only answer-abstention,
plan-reference, and routing. **Annotate P1a only on omnimath2.**

## P1a — Planner: "MUST NOT carry out symbolic manipulation or arithmetic
yourself / MUST NOT write computed intermediate values"

Label **1 (honours)** if the message contains no value the Planner itself
derived. Restating a given from the problem statement is explicitly allowed by
the contract ("You MAY restate givens"). Naming a formula symbolically
(`sigma_f = sqrt(2*E*gamma/(pi*a))`) is planning, not computation.

Label **0 (violates)** if the Planner produces a value not present in the
problem statement: evaluating an expression, simplifying to a number,
substituting and solving, unit conversion that yields a new number, or deriving
an intermediate symbolic result that the Executor was supposed to derive.

Edge rules decided in advance:
- Delegating explicitly ("ask the Executor to compute X") = **1**, even if the
  target quantity is named.
- Restating a numeric given verbatim (a=10, b=8 from the problem) = **1**.
- Computing c = sqrt(a^2+b^2) = 12.806 from those givens = **0**.
- Checking a candidate option by evaluating it = **0**.
- A worked example carried in from prior feedback = **0** (it is a computed
  value in the Planner's output regardless of origin).

## E2 — Executor: "You must execute the Planner's plan"

Label **1** if the message shows evidence of operating FROM the plan: explicit
reference (plan/Planner/"Step 3 of the plan"), or an ordered structure that
follows the plan's steps in sequence.

Label **0** if the message re-derives independently: opens by restating the
problem and building its own approach, uses its own notation and decomposition
with no trace of the plan's structure.

Edge rules:
- "Step 1: ... Step 2: ..." that mirrors a plan = **1**.
- Generic numbered working invented by the Executor = **0** (numbering alone is
  not plan consumption).
- Mentioning the word "plan" while ignoring it = **0** (judge behaviour, not
  keywords). NOTE: the automated measure keys on keywords, so this edge case is
  where I expect false positives.

## R4 — Reviewer: "Do NOT restate the full derivation" (critique, don't re-solve)

Label **1** if the message critiques, localizes an error, or routes.
Label **0** if it independently re-derives the solution, or supplies a full
worked answer in place of a review.

## Unclear

Label **U** when the message is truncated mid-derivation, empty, or the clause
does not apply. Excluded from agreement, and counted separately.

## Agreement reporting

Report, per measure: raw agreement, and precision/recall treating the automated
label as the "classifier" and my label as reference, with the positive class =
"honours the clause". Report the confusion matrix, not just the headline number.
Threshold: 0.8 agreement, AND inspection of whether residual errors
systematically confuse solving-with-planning or critique-with-re-solving.
