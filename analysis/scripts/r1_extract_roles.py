"""R1: Extract the PER role-message corpus with behavioural features.

Design rule: features are derived from the ROLE CONTRACT in the config, not from
convenient regexes. Each maps to a clause the prompt actually imposes.

PLANNER contract (config, verbatim):
  "You MUST NOT carry out symbolic manipulation or arithmetic yourself."
  "You MUST NOT write computed intermediate values."
  "Do NOT provide the final answer."
  REQUIRED STRUCTURE: 1) Givens 2) Target quantity and answer form
                      3) Key lemmas 4) Ordered execution steps
  "Begin with 'DELTA:' and list 2-4 concrete updates vs the previous plan."
EXECUTOR contract:
  "You must execute the Planner's plan and perform all calculations."
  "Your LAST line must be EXACTLY: \\boxed{<answer>}"
REVIEWER contract:
  "Do NOT restate the full derivation." / at most 2 bullets Diagnosis + 2 Fix
  "End with EXACTLY ONE tag: [Route:Planner] | [Route:Executor] | [Agree]"
  "Only on [Agree], include the final answer block"
"""
import os, re, glob
import pandas as pd, pyarrow.parquet as pq

REL = "/Users/bellayang/Documents/note/projects/IEEE-BigData-SciAgentTrace/analysis/hf_cache/release"
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/results"

parts = []
for f in sorted(glob.glob(REL + "/data/messages/part-*.parquet")):
    d = pq.read_table(f, columns=["trajectory_uid", "problem_uid", "sequence_index",
                                  "stage", "sender", "content"]).to_pandas()
    d = d[d.sender.isin(["Planner", "Executor", "Reviewer"])]
    if len(d): parts.append(d)
P = pd.concat(parts, ignore_index=True)
P["content"] = P.content.fillna("").astype(str)
P["n_chars"] = P.content.str.len()
P["round"] = P.stage.str.extract(r"_(\d+)$")[0].astype("Float64")
P["is_post_eval"] = P.stage.str.contains("post_eval")

C = P.content

# ---- COMPUTATION markers (the Planner is forbidden all of these) -----------
P["f_eval_equation"]  = C.str.contains(r"=\s*[-+]?\d+(?:\.\d+)?", regex=True)   # "= 12.806"
P["f_arith_op"]       = C.str.contains(r"\d+\s*[*×/÷]\s*\d+", regex=True)
P["f_sqrt_num"]       = C.str.contains(r"sqrt\s*\(?\s*\d", regex=True, case=False)
P["f_approx"]         = C.str.contains(r"\\approx|≈", regex=True)
P["f_boxed"]          = C.str.contains(r"\\boxed", regex=True)
# density, not just presence: how much computation per 1k chars
P["n_eval_eq"] = C.str.count(r"=\s*[-+]?\d+(?:\.\d+)?")
P["eval_eq_density"] = 1000 * P.n_eval_eq / P.n_chars.clip(lower=1)

# ---- PLAN-STRUCTURE markers (the Planner is required to produce these) -----
P["f_delta"]          = C.str.contains(r"\bDELTA\s*:", regex=True)
P["f_givens"]         = C.str.contains(r"\bGivens\b", regex=True, case=False)
P["f_target_form"]    = C.str.contains(r"Target quantity|answer form", regex=True, case=False)
P["f_numbered_steps"] = C.str.contains(r"(?m)^\s*\d[\.\)]\s", regex=True)
P["f_imperative_step"]= C.str.contains(r"(?m)^\s*(?:Step\s*\d|\d[\.\)])\s*[A-Z]", regex=True)

# ---- PLAN-CONSUMPTION markers (Executor is required to use the plan) -------
P["f_ref_plan"]       = C.str.contains(r"\bplan\b", regex=True, case=False)
P["f_ref_planner"]    = C.str.contains(r"\bPlanner\b", regex=True)
P["f_ref_step"]       = C.str.contains(r"\bstep\s*\d|\bper the plan|\bas planned", regex=True, case=False)

# ---- REVIEW markers (Reviewer is required to critique + route) -------------
P["f_route_planner"]  = C.str.contains(r"\[Route:Planner\]", regex=True)
P["f_route_executor"] = C.str.contains(r"\[Route:Executor\]", regex=True)
P["f_agree"]          = C.str.contains(r"\[Agree\]", regex=True)
P["f_diagnosis"]      = C.str.contains(r"Diagnosis\s*:", regex=True, case=False)
P["f_fix_instruction"]= C.str.contains(r"Fix Instruction\s*:", regex=True, case=False)
P["f_final_for_eval"] = C.str.contains(r"Final Answer For Evaluator", regex=True, case=False)
P["f_bare_route"]     = C.str.strip().str.fullmatch(r"\[(?:Agree|Route:Planner|Route:Executor)\]").fillna(False)
P["f_error_word"]     = C.str.contains(r"\b(?:incorrect|wrong|error|mistake|flaw|invalid|missing)\b",
                                       regex=True, case=False)

P.to_parquet(OUT + "/r1_role_messages.parquet", index=False)
print(f"rows={len(P)}  trajectories={P.trajectory_uid.nunique()}  problems={P.problem_uid.nunique()}")
feat = [c for c in P.columns if c.startswith("f_")]
print("\n=== marker prevalence by role ===")
print(P.groupby("sender")[feat].mean().round(3).T.to_string())
print("\n=== computation density (evaluated equations per 1k chars) ===")
print(P.groupby("sender").eval_eq_density.describe(percentiles=[.25,.5,.75]).round(2).to_string())
