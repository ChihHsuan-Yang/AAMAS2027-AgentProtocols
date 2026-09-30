#!/usr/bin/env python3
"""Generate the prompt+config patch block for runner_xdomain.py.

Run once; it rewrites runner_xdomain.py in place.  Kept as a file so the
adaptation is reviewable as a diff rather than as an opaque edit.
"""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
TARGET = HERE / "runner_xdomain.py"
src = TARGET.read_text()

# ----------------------------------------------------------------- 1. header
old_doc_head = '''#!/usr/bin/env python3
"""3-arm Planner-Executor-Reviewer experiment runner (AAMAS 2027).'''
new_doc_head = '''#!/usr/bin/env python3
"""CROSS-DOMAIN replication runner -- SciBench (AAMAS 2027).

Copy of runner.py with the benchmark swapped from Omni-MATH to the SciBench
`text_only` slice (574 free-response problems, MIT).  runner.py is untouched.

WHAT DIFFERS FROM runner.py, AND WHY (see notes/XDOMAIN-DESIGN.md):

  1. BENCHMARK_ID/SLICE_ID/DOMAIN -> scibench / text_only / science.
  2. load_problems() filters on the parsed `available_slices_json` list and
     builds an answer-only reference (SciBench ships no official solution:
     answer_text is present for 5 of 580 rows, 0.9%).
  3. The Arm A role prompts and the evaluator prompt are DOMAIN-ADAPTED
     (option (b) of the brief).  Arm B's prompt is carried over BYTE-IDENTICAL
     -- it is already domain-neutral, and that is asserted in code below.

Rationale for (b) rather than verbatim reuse: Arm B's generic prompt contains
no domain language at all, so leaving Arm A's math-specific wording in place
("competition-level mathematics", "olympiad-style", "For Omni-MATH") would
make the two arms differ in TWO ways -- role structure AND domain fit -- and
the domain-fit difference runs against Arm A.  Adapting A restores a
single-variable manipulation.  Every structural clause of A is preserved
(role separation, DELTA, required structure, Diagnosis/Fix Instruction,
answer ownership, routing tags); only domain nouns and the answer-form
enumeration change.

CONSEQUENCE, per the brief: P1a and every other clause-specific fidelity
metric are NOT transported across domains and are not computed here.

3-arm Planner-Executor-Reviewer experiment runner (AAMAS 2027).'''
assert old_doc_head in src
src = src.replace(old_doc_head, new_doc_head, 1)

# ----------------------------------------------------------- 2. prompt block
anchor = "import prompts as P  # noqa: E402\nimport schemas as S  # noqa: E402\n"
assert anchor in src

prompt_block = anchor + '''
# ==========================================================================
# DOMAIN-ADAPTED PROMPT SET  (option (b) -- see module docstring)
#
# `P` below SHADOWS the imported Omni-MATH prompt module for the rest of this
# file, so every P.<NAME> reference in the pipeline resolves to the SciBench
# wording.  The Omni-MATH originals stay reachable as _OMNI for the
# byte-identity assertions.
# ==========================================================================

_OMNI = P


class _XDomainPrompts:
    """SciBench role + evaluator contracts.

    Structure is held identical to the Omni-MATH contracts clause for clause;
    only domain nouns and the answer-form enumeration differ.
    """

    # ---- ARM A: Planner -------------------------------------------------
    A_SOLVER_PREPEND = """You are the Planner in a Planner→Executor→Reviewer loop for college-level science problems (chemistry and physics).

Problem:
${task_description}

Previous plan you wrote (may be empty):
${previous_plan}

Reviewer / System feedback (may be empty):
${advice}

HARD ROLE SEPARATION (critical):
- You MUST NOT carry out algebraic manipulation or numerical calculation yourself.
- You MUST NOT write computed intermediate values.
- You MAY restate givens from the problem.
- Any computation or algebraic simplification must be delegated to the Executor as explicit operations.

REQUIRED STRUCTURE:
1) Givens / quantities / physical or chemical context
2) Target quantity, its units, and answer form
3) Key laws, relations, or equations to use
4) Ordered execution steps for the Executor

In "Target quantity and answer form", explicitly identify what the final answer should look like:
- a numeric value carrying physical units
- a dimensionless number or ratio
- a value in a specific unit requested by the problem
- a short symbolic expression
- a sign-bearing quantity (state the sign convention)

DELTA REQUIREMENT:
- Begin with "DELTA:" and list 2-4 concrete updates vs the previous plan.
- If reviewer feedback exists, address it explicitly."""

    A_SOLVER_APPEND = _OMNI.A_SOLVER_APPEND          # byte-identical

    # ---- ARM A: Executor ------------------------------------------------
    A_EXECUTOR_PREPEND = """You are the Executor.
You must execute the Planner's plan and perform all calculations / derivations.

Problem:
${task_description}

Planner plan:
${solution}

Reviewer feedback for Executor (may be empty):
${advice}

REQUIREMENTS:
- Carry out the needed derivations and numerical work.
- Keep the reasoning readable and concise.
- Infer the required answer shape and units from the problem statement before finishing.
- The final answer is normally a numeric value with units; it may also be a dimensionless number or a short symbolic expression.
- Include units whenever the quantity has them, and use the unit the problem asks for.
- Carry enough precision through intermediate steps, and report the final value to a sensible number of significant figures.
- Preserve the sign of the quantity where the sign is physically meaningful.
- Your LAST line must be EXACTLY: \\\\boxed{<answer>}
- The boxed answer may be a number with units, a plain number, or a concise symbolic form.
- No punctuation after the final box."""

    A_EXECUTOR_APPEND = _OMNI.A_EXECUTOR_APPEND      # byte-identical

    # ---- ARM A: Reviewer ------------------------------------------------
    A_CRITIC_PREPEND = """You are the Reviewer in a Planner→Executor→Reviewer pipeline for college-level science problems.

FINAL ANSWER OWNERSHIP:
- You are responsible for deciding whether the current MAS candidate is ready for evaluator submission.
- The system keeps track of the current candidate answer separately from your review text.
- Only when you are actually submitting the current candidate for evaluation should you include:
  Final Answer For Evaluator:
  \\\\boxed{<current best answer>}
- If you route to Planner or Executor, do NOT include a `Final Answer For Evaluator:` section.
- Infer the required answer shape and units from the problem statement before judging correctness.
- For this benchmark, the boxed answer is normally a numeric value carrying physical units; it may also be a dimensionless number or a short symbolic expression.
- Check the unit, the magnitude, the sign, and the number of significant figures, not only the digits.
- An answer with the right number in the wrong unit, or off by a power of ten, is incorrect.
- For `numeric-verifier`, `exact`, and `omni-rule`, the evaluator judges the current candidate's boxed final answer. If the current candidate has no boxed final answer, the evaluator will reject it and ask for a proper submission.
- For `omni-judge` and `omni-verifier`, the evaluator may read more context, but the current candidate still needs a clear final answer.
- The final line of your response must still be exactly one route tag.
- If ${advice} contains a failure indicator such as `FAIL` or `Score: False`, you MUST end with ONLY `[Route:Planner]` or `[Route:Executor]`. You MUST NOT output `[Agree]`.
- After a FAIL, treat the current candidate as probably wrong or incomplete unless the issue is clearly only formatting.
- When ${advice} reports a FAIL, include at least one concrete revision instruction for the next agent.
- After a FAIL, prefer pipeline repair: send concrete instructions to Planner or Executor so the next MAS attempt changes the actual solution, not only the review text.
- Do NOT approve an answer only because the derivation sounds coherent; check the physical or chemical setup, the equation used, unit consistency, and the arithmetic.
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
- Approve only if the derivation supports the exact answer shape and unit requested by the problem.
- Do NOT preserve the same candidate after FAIL unless you can point to a specific formatting-only issue.
- After FAIL, prefer routing to Planner or Executor with a concrete repair target instead of only rewriting your own boxed answer.
- If the setup, the governing relation, or the interpretation is wrong, route to Planner.
- If the setup is sound but the derivation, arithmetic, unit conversion, or boxing is flawed, route to Executor.
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
\\\\boxed{<current best answer>}
End with EXACTLY ONE tag on the last line:
  [Route:Planner] OR [Route:Executor] OR [Agree]"""

    # ---- ARM B: byte-identical to Omni-MATH -----------------------------
    # Asserted below.  Arm B carries no domain language, so there is nothing
    # to adapt; keeping the bytes identical makes that checkable.
    B_GENERIC_PREPEND = _OMNI.B_GENERIC_PREPEND
    B_GENERIC_APPEND = _OMNI.B_GENERIC_APPEND

    # ---- EVALUATOR: identical in every arm ------------------------------
    # Adapted for units / significant figures / scientific notation.  This is
    # COMMON MODE: byte-identical across arms A and B, so it cannot manufacture
    # an A-vs-B difference; it only sets the difficulty floor.  The unit and
    # tolerance clauses follow the upstream science_qa evaluator preset
    # (code_staging/configs/paper/prompt_presets/science_qa/per_hint_llm.yaml).
    EVALUATOR_PREPEND = """You are the Evaluator in a Planner→Executor→Reviewer loop for college-level science problems.

Problem:
${task_description}

Submitted candidate:
${solution}

Ground truth / evaluator-only reference material:
${result}

Requirements:
  - Decide whether the submitted candidate final answer is scientifically equivalent to the ground truth.
  - Focus on the final answer, not stylistic wording.
  - The reference material is the final answer for this problem. It is normally a numeric value with units.
  - Treat the following as EQUIVALENT (correct):
      * the same value written in a different but compatible unit (for example 1.0 dm^3 and 1.0e-3 m^3, or 1 atm and 101.325 kPa)
      * the same value in scientific, decimal, or engineering notation (for example 2.26e-5, 0.0000226, 22.6e-6)
      * LaTeX and plain-text renderings of the same unit (for example \\\\mathrm{atm}, \\\\text{atm}, atm)
      * a value agreeing with the reference to the precision the reference itself carries; judge agreement at the reference's number of significant figures, and allow a relative difference of about 1% to absorb rounding and constant choices
      * a value that differs only by including or omitting a unit that the problem clearly fixes
  - Treat the following as NOT equivalent (incorrect):
      * a different physical quantity, or the right number in an incompatible unit
      * a value off by a power of ten
      * a wrong sign where the sign is physically meaningful
      * a missing, placeholder, or non-numeric answer where a number is required
  - Do not reveal, quote, restate, or hint at the ground truth in your response.
  - Output a clear verdict label: `Verdict: PASS` or `Verdict: FAIL`.
  - If the answer is equivalent, output `Correctness: 1`.
  - Otherwise output `Correctness: 0` and give a short non-leaking repair hint that names the kind of mismatch without revealing the ground truth, for example: wrong unit, off by a power of ten, wrong sign, wrong quantity computed, insufficient precision, or formatting/boxing issue."""

    EVALUATOR_APPEND = _OMNI.EVALUATOR_APPEND        # byte-identical

    # ---- ARM C / C-prime: carried over verbatim -------------------------
    # Not run in this stage.  Carried so build_messages() cannot NameError if
    # arm C is later enabled, and so the config hash covers them.
    C_PLANNER_PREPEND = _OMNI.C_PLANNER_PREPEND
    C_PLANNER_APPEND = _OMNI.C_PLANNER_APPEND
    C_EXECUTOR_PREPEND = _OMNI.C_EXECUTOR_PREPEND
    C_EXECUTOR_APPEND = _OMNI.C_EXECUTOR_APPEND
    C_REVIEWER_PREPEND = _OMNI.C_REVIEWER_PREPEND
    C_REVIEWER_APPEND = _OMNI.C_REVIEWER_APPEND
    CP_PLANNER_PREPEND = _OMNI.CP_PLANNER_PREPEND
    CP_PLANNER_APPEND = _OMNI.CP_PLANNER_APPEND
    CP_EXECUTOR_PREPEND = _OMNI.CP_EXECUTOR_PREPEND
    CP_EXECUTOR_APPEND = _OMNI.CP_EXECUTOR_APPEND
    CP_REVIEWER_PREPEND = _OMNI.CP_REVIEWER_PREPEND
    CP_REVIEWER_APPEND = _OMNI.CP_REVIEWER_APPEND


P = _XDomainPrompts()

# The Arm B manipulation must be carried across domains unchanged.  If this
# ever fails, the A-vs-B contrast is no longer the same manipulation.
assert P.B_GENERIC_PREPEND == _OMNI.B_GENERIC_PREPEND
assert P.B_GENERIC_APPEND == _OMNI.B_GENERIC_APPEND

P.ALL_PROMPTS = {
    k: getattr(P, k) for k in (
        "A_SOLVER_PREPEND", "A_SOLVER_APPEND",
        "A_EXECUTOR_PREPEND", "A_EXECUTOR_APPEND",
        "A_CRITIC_PREPEND", "A_CRITIC_APPEND",
        "B_GENERIC_PREPEND", "B_GENERIC_APPEND",
        "C_PLANNER_PREPEND", "C_PLANNER_APPEND",
        "C_EXECUTOR_PREPEND", "C_EXECUTOR_APPEND",
        "C_REVIEWER_PREPEND", "C_REVIEWER_APPEND",
        "EVALUATOR_PREPEND", "EVALUATOR_APPEND",
    )
}

'''
src = src.replace(anchor, prompt_block, 1)

# ------------------------------------------------- 3. benchmark constants
old_bench = '''BENCHMARK_ID = "omnimath2"
DOMAIN = "math"'''
new_bench = '''BENCHMARK_ID = "scibench"
SLICE_ID = "text_only"
DOMAIN = "science"'''
assert old_bench in src
src = src.replace(old_bench, new_bench, 1)

# The config hash must cover the slice too, else two slices collide.
old_hash = '''                "benchmark_id": BENCHMARK_ID,
            },'''
new_hash = '''                "benchmark_id": BENCHMARK_ID,
                "slice_id": SLICE_ID,
            },'''
assert old_hash in src
src = src.replace(old_hash, new_hash, 1)

# ------------------------------------------------------- 4. actor default
old_actors = '''DEFAULT_ACTORS = [
    "openai/gpt-oss-120b",
    "google/gemma-4-31B-it",
    "meta-llama/Llama-3.3-70B-Instruct",
]'''
new_actors = '''DEFAULT_ACTORS = [
    "openai/gpt-oss-120b",
    "google/gemma-4-31B-it",
]'''
assert old_actors in src
src = src.replace(old_actors, new_actors, 1)

# --------------------------------------------------------- 5. slice + ref
old_load = '''    df = pd.read_parquet(PROBLEMS_PARQUET)
    df = df[df["benchmark_id"] == BENCHMARK_ID]
    df = df[df["problem_text"].notna() & df["answer"].notna()]'''
new_load = '''    df = pd.read_parquet(PROBLEMS_PARQUET)
    df = df[df["benchmark_id"] == BENCHMARK_ID]
    # Slice membership is a JSON LIST, not a scalar.  `.notna()` is TRUE for an
    # empty list, so it must be parsed, not truth-tested -- the same trap that
    # makes SciBench's `options_json` look like every row is multiple choice.
    df = df[df["available_slices_json"].apply(
        lambda s: SLICE_ID in (json.loads(s) if isinstance(s, str) else (s or [])))]
    df = df[df["problem_text"].notna() & df["answer"].notna()]'''
assert old_load in src
src = src.replace(old_load, new_load, 1)

old_ref = '''        ref = "Final answer: {}".format(r["answer"])
        at = r.get("answer_text")
        if isinstance(at, str) and at.strip():
            ref += "\\n\\nOfficial solution:\\n{}".format(at[:6000])'''
new_ref = '''        # SciBench ships no official solution (answer_text present for 5 of
        # 580 rows, 0.9%), so the reference is answer-only for all but those.
        # The evaluator prompt is written for an answer-only reference.
        ref = "Final answer: {}".format(r["answer"])
        at = r.get("answer_text")
        if isinstance(at, str) and at.strip():
            ref += "\\n\\nOfficial solution:\\n{}".format(at[:6000])'''
assert old_ref in src
src = src.replace(old_ref, new_ref, 1)

# ------------------------------------------------------------ 6. defaults
src = src.replace(
    '''    ap.add_argument("--out", default=str(HERE / "results" / "per_arms.jsonl"),''',
    '''    ap.add_argument("--out", default=str(HERE / "results" / "xdomain" / "scibench_AB.jsonl"),''', 1)
src = src.replace('''    ap.add_argument("--n", type=int, default=50, help="number of problems")''',
                  '''    ap.add_argument("--n", type=int, default=574, help="number of problems")''', 1)
src = src.replace('''    ap.add_argument("--arms", default="A,B,C")''',
                  '''    ap.add_argument("--arms", default="A,B")''', 1)
src = src.replace(
    '''    ap.add_argument("--stub-hard-failure", action="store_true",''',
    '''    ap.add_argument("--limit-uids", default=None, dest="limit_uids",
                    help="comma-separated problem_uids; overrides --n (smoke use)")
    ap.add_argument("--stub-hard-failure", action="store_true",''', 1)

old_sel = '''    if args.dry_run:
        problems = STUB_PROBLEMS[: max(1, args.n)]
    else:
        problems = load_problems(args.n, args.seed)'''
new_sel = '''    if args.dry_run:
        problems = STUB_PROBLEMS[: max(1, args.n)]
    else:
        problems = load_problems(args.n, args.seed)
        if args.limit_uids:
            keep = {u.strip() for u in args.limit_uids.split(",") if u.strip()}
            problems = [p for p in problems if p["problem_uid"] in keep]'''
assert old_sel in src
src = src.replace(old_sel, new_sel, 1)

# STUB problems: make them science-shaped so the dry run is representative.
old_stub = '''STUB_PROBLEMS = [
    {"problem_uid": "STUB_1",
     "problem_text": "Let n >= 2. Find the minimum m such that ...",
     "answer": "1 + \\\\lceil n/2 \\\\rceil",
     "reference": "Final answer: 1 + \\\\lceil n/2 \\\\rceil"},
    {"problem_uid": "STUB_2",
     "problem_text": "Compute the number of ways to ...",
     "answer": "561",
     "reference": "Final answer: 561"},
]'''
new_stub = '''STUB_PROBLEMS = [
    {"problem_uid": "STUB_1",
     "problem_text": "What pressure would 131 g of xenon in 1.0 dm^3 exert at 25 C as a perfect gas?",
     "answer": "24 $\\\\mathrm{atm}$",
     "reference": "Final answer: 24 $\\\\mathrm{atm}$"},
    {"problem_uid": "STUB_2",
     "problem_text": "Calculate the molar mass of a gas given rho = 1.23 kg m^-3 ...",
     "answer": "169 $\\\\mathrm{g} \\\\mathrm{mol}^{-1}$",
     "reference": "Final answer: 169 $\\\\mathrm{g} \\\\mathrm{mol}^{-1}$"},
]'''
assert old_stub in src
src = src.replace(old_stub, new_stub, 1)

# The arm-C stub answers are math; make them science so a dry run reads right.
src = src.replace(
    '''                text = ('{"derivation":"stub derivation step by step",'
                        '"answer":"1 + \\\\\\\\lceil n/2 \\\\\\\\rceil"}')''',
    '''                text = ('{"derivation":"stub derivation step by step",'
                        '"answer":"24 atm"}')''', 1)
src = src.replace(
    '''            text = ("Continuing the shared work on the problem.\\n"
                    "\\\\boxed{1 + \\\\lceil n/2 \\\\rceil}\\n"''',
    '''            text = ("Continuing the shared work on the problem.\\n"
                    "\\\\boxed{24 atm}\\n"''', 1)
src = src.replace(
    '''                text = "Derivation: stub steps.\\n\\\\boxed{1 + \\\\lceil n/2 \\\\rceil}"''',
    '''                text = "Derivation: stub steps.\\n\\\\boxed{24 atm}"''', 1)
src = src.replace(
    '''                text = ("Diagnosis:\\n- looks complete\\nFix Instruction:\\n- none\\n"
                        "Final Answer For Evaluator:\\n\\\\boxed{1 + \\\\lceil n/2 \\\\rceil}\\n[Agree]")''',
    '''                text = ("Diagnosis:\\n- looks complete\\nFix Instruction:\\n- none\\n"
                        "Final Answer For Evaluator:\\n\\\\boxed{24 atm}\\n[Agree]")''', 1)
src = src.replace(
    '''                text = "DELTA: 1) restate givens 2) set target form\\n1) Givens ...\\n2) Target quantity: a formula in n"''',
    '''                text = "DELTA: 1) restate givens 2) set target form\\n1) Givens ...\\n2) Target quantity: a pressure in atm"''', 1)

src = src.replace('''    ap = argparse.ArgumentParser(description="3-arm PER experiment runner")''',
                  '''    ap = argparse.ArgumentParser(
        description="cross-domain (SciBench) PER experiment runner")''', 1)

# The --smoke shortcut in runner.py forces gpt-oss only; we want both actors.
old_smoke = '''    if args.smoke:
        args.n = min(args.n, 1)
        args.actors = "openai/gpt-oss-120b"
        args.concurrency = min(args.concurrency, 3)'''
new_smoke = '''    if args.smoke:
        args.n = min(args.n, 3)
        args.concurrency = min(args.concurrency, 6)'''
assert old_smoke in src
src = src.replace(old_smoke, new_smoke, 1)

TARGET.write_text(src)
print("patched", TARGET)
print("lines:", len(src.splitlines()))
