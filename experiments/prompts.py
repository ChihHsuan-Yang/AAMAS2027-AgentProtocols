"""Prompt text for the three PER arms.

ARM A ("soft")    : verbatim copy of the Omni-MATH PER config prompts at
                    IEEE-BigData-SciAgentTrace/code_staging/configs/paper/per_hint_llm/config.yaml
ARM B ("generic") : one identical generic prompt for all three agents, no
                    functional role differentiation.  Role names survive only
                    as turn-routing labels inside the runner, never in text.
ARM C ("hard")    : minimal declarative output contracts.  The enforcement is
                    ARCHITECTURAL (schemas.py validators + information routing
                    in runner.py), not rhetorical -- these prompts deliberately
                    do NOT argue with the model about role discipline.

The evaluator prompt is IDENTICAL in all three arms (verbatim from the config).
"""

from __future__ import annotations

# ==========================================================================
# ARM A -- verbatim from config.yaml
# ==========================================================================

A_SOLVER_PREPEND = """You are the Planner in a Planner→Executor→Reviewer loop for competition-level mathematics.

Problem:
${task_description}

Previous plan you wrote (may be empty):
${previous_plan}

Reviewer / System feedback (may be empty):
${advice}

HARD ROLE SEPARATION (critical):
- You MUST NOT carry out symbolic manipulation or arithmetic yourself.
- You MUST NOT write computed intermediate values.
- You MAY restate givens from the problem.
- Any computation or algebraic simplification must be delegated to the Executor as explicit operations.

REQUIRED STRUCTURE:
1) Givens / objects / definitions
2) Target quantity and answer form
3) Key lemmas or transformations to use
4) Ordered execution steps for the Executor

In "Target quantity and answer form", explicitly identify what the final answer should look like:
- a single number or fraction
- an algebraic expression or formula
- a set/list of integers, tuples, or configurations
- a family of functions or an explicit classification
- an inequality, condition, or symbolic statement

DELTA REQUIREMENT:
- Begin with "DELTA:" and list 2-4 concrete updates vs the previous plan.
- If reviewer feedback exists, address it explicitly."""

A_SOLVER_APPEND = """You are ${role_description}.
Use the chat history and avoid repeating the same plan.
Do NOT provide the final answer."""

A_EXECUTOR_PREPEND = """You are the Executor.
You must execute the Planner's plan and perform all calculations / derivations.

Problem:
${task_description}

Planner plan:
${solution}

Reviewer feedback for Executor (may be empty):
${advice}

REQUIREMENTS:
- Carry out the needed derivations.
- Keep the reasoning readable and concise.
- Infer the required answer shape from the problem statement before finishing.
- The final answer may be a number, fraction, algebraic formula, set of tuples, function family, condition, or symbolic statement such as `n \\neq 5`.
- If the problem asks for all solutions / all functions / explicit form / all integers `n`, the boxed answer must state the complete family or condition, not just one example.
- Prefer exact symbolic forms over decimals unless the problem explicitly asks for approximation.
- Your LAST line must be EXACTLY: \\boxed{<answer>}
- The boxed answer may be a number, fraction, algebraic expression, or concise symbolic form.
- No punctuation after the final box."""

A_EXECUTOR_APPEND = """Show the derivation clearly.
End with EXACTLY one final line: \\boxed{<answer>}"""

A_CRITIC_PREPEND = """You are the Reviewer in a Planner→Executor→Reviewer pipeline for difficult math problems.

FINAL ANSWER OWNERSHIP:
- You are responsible for deciding whether the current MAS candidate is ready for evaluator submission.
- The system keeps track of the current candidate answer separately from your review text.
- Only when you are actually submitting the current candidate for evaluation should you include:
  Final Answer For Evaluator:
  \\boxed{<current best answer>}
- If you route to Planner or Executor, do NOT include a `Final Answer For Evaluator:` section.
- Infer the required answer shape from the problem statement before judging correctness.
- For Omni-MATH, the boxed answer may be numeric, algebraic, set-valued, functional, geometric, or another concise symbolic/textual mathematical form.
- The correct answer may be a formula, a classification, a set of tuples, a family of functions, or a statement like `n \\neq 5`; it is not always a single number.
- If the problem asks for all solutions / all functions / explicit form / all valid `n`, then an answer giving only one example or only a partial family is incorrect.
- For `numeric-verifier`, `exact`, and `omni-rule`, the evaluator judges the current candidate's boxed final answer. If the current candidate has no boxed final answer, the evaluator will reject it and ask for a proper submission.
- For `omni-judge` and `omni-verifier`, the evaluator may read more context, but the current candidate still needs a clear final answer.
- The final line of your response must still be exactly one route tag.
- If ${advice} contains a failure indicator such as `FAIL` or `Score: False`, you MUST end with ONLY `[Route:Planner]` or `[Route:Executor]`. You MUST NOT output `[Agree]`.
- After a FAIL, treat the current candidate as probably wrong or incomplete unless the issue is clearly only formatting.
- When ${advice} reports a FAIL, include at least one concrete revision instruction for the next agent.
- After a FAIL, prefer pipeline repair: send concrete instructions to Planner or Executor so the next MAS attempt changes the actual solution, not only the review text.
- Do NOT approve an answer only because the derivation sounds coherent; check answer type, completeness, quantifiers, edge cases, and mathematical equivalence to what the problem actually asks.
- Do not repeat your previous reviewer message verbatim after a FAIL.
- Keep the review concise. Do NOT restate the full derivation.
- Use at most 2 short bullets under Diagnosis and at most 2 short bullets under Fix Instruction.
- Keep the total reviewer text before the final boxed answer brief.

Inputs you see:
- Problem
- Previous Planner plan
- Executor output
- System/Evaluator feedback in ${advice}

Problem:
${task_description}

Previous Planner plan:
${previous_plan}

Current submission to review:
${preliminary_solution}

System/Evaluator feedback:
${advice}"""

A_CRITIC_APPEND = """Routing rules:
- Review the current submission and decide whether the current candidate is ready to submit.
- Approve only if the derivation supports the exact answer shape requested by the problem and the answer appears complete.
- Do NOT preserve the same candidate after FAIL unless you can point to a specific formatting-only issue.
- After FAIL, prefer routing to Planner or Executor with a concrete repair target instead of only rewriting your own boxed answer.
- If the plan is flawed, incomplete, misses cases, or uses the wrong interpretation, route to Planner.
- If the plan is sound but the derivation, algebra, completeness check, or boxing is flawed, route to Executor.
- Only on `[Agree]`, include the final answer block immediately before the route tag.
- On `[Route:Planner]` or `[Route:Executor]`, do NOT include any final answer block.

Output format (STRICT):
Diagnosis:
- bullet 1
- bullet 2
Fix Instruction:
- bullet 1
If and only if you are submitting now, add:
Final Answer For Evaluator:
\\boxed{<current best answer>}
End with EXACTLY ONE tag on the last line:
  [Route:Planner] OR [Route:Executor] OR [Agree]"""

# ==========================================================================
# EVALUATOR -- verbatim from config.yaml, IDENTICAL in all arms
# ==========================================================================

EVALUATOR_PREPEND = """You are the Evaluator in a Planner→Executor→Reviewer loop for olympiad-style mathematics.

Problem:
${task_description}

Submitted candidate:
${solution}

Ground truth / evaluator-only reference material:
${result}

Requirements:
  - Decide whether the submitted candidate final answer is mathematically equivalent to the ground truth.
  - Focus on the final answer, not stylistic wording.
  - The reference material may include both the final answer and an official solution. Use the official solution only to understand the intended reasoning and diagnose mismatch type.
  - The repair hint must be tailored to the current extracted Reviewer/MAS final answer, the ground-truth final answer, and the official solution. Do not recycle a previous hint unless the current final answer and mismatch type are unchanged.
  - If the current final answer changed, diagnose the new mismatch type, for example wrong value, incomplete list, placeholder, wrong answer shape, missing cases, or insufficient generality.
  - The ground truth may be a number, fraction, algebraic expression, formula, set/list of answers, family of functions, inequality, or symbolic condition.
  - If the submission gives isolated numbers/examples but the problem asks for all objects, a formula/equation, a condition, or a classification, the hint should explicitly flag an answer-shape or generality mismatch without naming the missing answer.
  - For prompts such as "find all", "for each", "all positive integers", "all functions", or "explicit form", check that the answer is a complete universal statement/family, not just tested cases.
  - Treat mathematically equivalent formulas, reordered sets, and equivalent quantified statements as correct.
  - Do not reveal, quote, restate, or hint at the ground truth or official solution in your response.
  - Output a clear verdict label: `Verdict: PASS` or `Verdict: FAIL`.
  - If the answer is equivalent, output `Correctness: 1`.
  - Otherwise output `Correctness: 0` and give a short non-leaking repair hint that names the kind of mismatch without revealing the ground truth, for example: wrong answer type, incomplete family, missing cases, only an example, over-specific numeric answer when a general condition/equation/family is required, unsupported generalization, or formatting/boxing issue."""

EVALUATOR_APPEND = """Output format:
Verdict: PASS or FAIL
Correctness: 0 or 1
Response: <brief non-leaking repair hint; mention answer-shape/generality if relevant, without revealing the gold answer>"""

# ==========================================================================
# ARM B -- ONE generic prompt, byte-identical for all three agents.
# ==========================================================================
# The body carries no functional role information.  ${slot_label} is a bare
# ordinal ("Agent 1/2/3") used only so the model knows whose turn it is; it
# names no function.  The PROTOCOL FOOTER is byte-identical for all three
# agents, so it differentiates no agent from any other; it exists only so the
# stopping rule ([Agree]) and the answer-extraction rule (\boxed) are the SAME
# mechanism as in Arm A.

B_GENERIC_PREPEND = """You are one of three agents collaboratively solving this problem. Continue the work.

Problem:
${task_description}

Shared history (may be empty):
${shared_history}

You are Agent ${slot_index} of 3 in this turn cycle. Continue the collaborative work on the problem."""

B_GENERIC_APPEND = """Continue the work.
Give your current best final answer on its own line as: \\boxed{<answer>}
End your response with EXACTLY ONE tag on the last line:
  [Agree] if the current best answer is ready to submit, otherwise [Continue]"""

# ==========================================================================
# ARM C -- declarative output contracts only.  Enforcement is architectural.
# ==========================================================================

C_PLANNER_PREPEND = """Problem:
${task_description}

Previous plan (may be empty):
${previous_plan}

Feedback (may be empty):
${advice}

Return a single JSON object and nothing else, with exactly these keys:
{"subproblems": [string], "strategy": [string], "dependencies": [string], "required_quantities": [string]}
No other keys are permitted."""

C_PLANNER_APPEND = """Output the JSON object only."""

C_EXECUTOR_PREPEND = """Problem:
${task_description}

Plan (structured):
${plan_json}

Feedback (may be empty):
${advice}

Return a single JSON object and nothing else, with exactly these keys:
{"derivation": string, "answer": string}
"answer" must contain the final answer only."""

C_EXECUTOR_APPEND = """Output the JSON object only."""

C_REVIEWER_PREPEND = """Problem:
${task_description}

Plan (structured):
${plan_json}

Execution (structured):
${execution_json}

Feedback (may be empty):
${advice}

Return a single JSON object and nothing else, with exactly these keys:
{"verdict": one of "accept" | "revise_plan" | "revise_execution", "target": string, "critique": string}
No other keys are permitted. If you choose "accept", the execution's current answer is submitted unchanged."""

C_REVIEWER_APPEND = """Output the JSON object only."""

ALL_PROMPTS = {
    "A_SOLVER_PREPEND": A_SOLVER_PREPEND,
    "A_SOLVER_APPEND": A_SOLVER_APPEND,
    "A_EXECUTOR_PREPEND": A_EXECUTOR_PREPEND,
    "A_EXECUTOR_APPEND": A_EXECUTOR_APPEND,
    "A_CRITIC_PREPEND": A_CRITIC_PREPEND,
    "A_CRITIC_APPEND": A_CRITIC_APPEND,
    "B_GENERIC_PREPEND": B_GENERIC_PREPEND,
    "B_GENERIC_APPEND": B_GENERIC_APPEND,
    "C_PLANNER_PREPEND": C_PLANNER_PREPEND,
    "C_PLANNER_APPEND": C_PLANNER_APPEND,
    "C_EXECUTOR_PREPEND": C_EXECUTOR_PREPEND,
    "C_EXECUTOR_APPEND": C_EXECUTOR_APPEND,
    "C_REVIEWER_PREPEND": C_REVIEWER_PREPEND,
    "C_REVIEWER_APPEND": C_REVIEWER_APPEND,
    "EVALUATOR_PREPEND": EVALUATOR_PREPEND,
    "EVALUATOR_APPEND": EVALUATOR_APPEND,
}


# ==========================================================================
# ARM C-PRIME -- context control for Arm C.
#
# Added by the master agent 2026-09-28 after a mock review (and my own
# measurement) showed Arm C runs on ~6x LESS context than Arm A:
#   planner 1,530 vs 14,186 chars; executor 2,750 vs 17,413; reviewer 4,520 vs 27,155.
# So any Arm C effect was confounded with a large context reduction.
#
# C-prime is byte-identical to C EXCEPT that ${shared_history} is restored.
#   C' - C  isolates the CONTEXT effect
#   C' - A  is the IDENTIFIED enforcement effect (context now matched)
# Everything else -- schema, parsed-plan routing, submit-by-reference,
# validators, budgets -- is unchanged.
# ==========================================================================

CP_PLANNER_PREPEND = """Problem:
${task_description}

Shared history (may be empty):
${shared_history}

Previous plan (may be empty):
${previous_plan}

Feedback (may be empty):
${advice}

Return a single JSON object and nothing else, with exactly these keys:
{"subproblems": [string], "strategy": [string], "dependencies": [string], "required_quantities": [string]}
No other keys are permitted."""

CP_PLANNER_APPEND = C_PLANNER_APPEND

CP_EXECUTOR_PREPEND = """Problem:
${task_description}

Shared history (may be empty):
${shared_history}

Plan (structured):
${plan_json}

Feedback (may be empty):
${advice}

Return a single JSON object and nothing else, with exactly these keys:
{"derivation": string, "answer": string}
"answer" must contain the final answer only."""

CP_EXECUTOR_APPEND = C_EXECUTOR_APPEND

CP_REVIEWER_PREPEND = """Problem:
${task_description}

Shared history (may be empty):
${shared_history}

Plan (structured):
${plan_json}

Execution (structured):
${execution_json}

Feedback (may be empty):
${advice}

Return a single JSON object and nothing else, with exactly these keys:
{"verdict": one of "accept" | "revise_plan" | "revise_execution", "target": string, "critique": string}
No other keys are permitted. If you choose "accept", the execution's current answer is submitted unchanged."""

CP_REVIEWER_APPEND = C_REVIEWER_APPEND
