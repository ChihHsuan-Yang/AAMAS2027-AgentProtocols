"""R10: Rebuild the validation sample, weighted to the measures that matter.

v1 stratified evenly over role x actor x domain x correctness, which left only
23 P1a-annotatable messages (P1a applies only on omnimath2). P1a is the
load-bearing mediator metric, so it needs the most annotation, not the least.

New allocation (240 total):
  P1a : 120  Planner x omnimath2, balanced across the 3 actors and across the
             automated label (so precision AND recall are estimable)
  E2  :  80  Executor, balanced across actors and automated label
  R4  :  40  Reviewer, balanced across actors and automated label
"""
import os
import numpy as np, pandas as pd, pyarrow.parquet as pq

REL = "/Users/bellayang/Documents/note/projects/IEEE-BigData-SciAgentTrace/analysis/hf_cache/release"
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/results"
NOTES = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + "/notes"

V = pd.read_parquet(OUT + "/r5_fidelity_v2.parquet")
traj = pq.read_table(REL + "/data/trajectories/part-00000.parquet",
                     columns=["trajectory_uid", "benchmark_id", "actor_model_id",
                              "final_correct"]).to_pandas()
V = V.merge(traj, on="trajectory_uid", how="left")
V = V[V.n_chars > 80]

rng = np.random.default_rng(11)
def balanced(df, label_col, per_cell, keys):
    out = []
    for k, g in df.groupby(keys + [label_col]):
        out.append(g.sample(min(len(g), per_cell), random_state=int(rng.integers(1e6))))
    return pd.concat(out) if out else pd.DataFrame()

# P1a: omnimath2 planners, balanced over actor x automated label
p1 = V[(V.sender == "Planner") & (V.benchmark_id == "omnimath2")].copy()
p1["auto"] = p1.P1a_no_computation
s1 = balanced(p1, "auto", 20, ["actor_model_id"]); s1["measure"] = "P1a"

# E2: executors, balanced over actor x automated label (omnimath2 + labbench)
e2 = V[(V.sender == "Executor") & (V.benchmark_id.isin(["omnimath2", "labbench"]))].copy()
e2["auto"] = e2.E2_uses_plan
s2 = balanced(e2, "auto", 10, ["actor_model_id"]); s2["measure"] = "E2"

# R4: reviewers
r4 = V[(V.sender == "Reviewer") & (V.benchmark_id.isin(["omnimath2", "labbench"]))].copy()
r4["auto"] = r4.R4_not_resolving
s3 = balanced(r4, "auto", 5, ["actor_model_id"]); s3["measure"] = "R4"

S = pd.concat([s1, s2, s3], ignore_index=True)
S = S.sample(frac=1, random_state=3).reset_index(drop=True)
S["ann_id"] = range(len(S))
print(f"validation set v2: {len(S)}")
print(S.groupby(["measure", "actor_model_id", "auto"]).size().to_string())

cols = ["ann_id", "measure", "auto", "trajectory_uid", "sequence_index", "sender",
        "stage", "actor_model_id", "benchmark_id", "final_correct", "n_chars",
        "n_eval_eq", "content"]
S[cols].to_parquet(OUT + "/r10_validation_v2.parquet", index=False)
with open(NOTES + "/VALIDATION_SHEET_V2.md", "w") as fh:
    fh.write("# Validation sheet v2 — balanced on the automated label\n\n")
    for _, r in S.iterrows():
        fh.write(f"\n---\n## [{r.ann_id}] {r.measure} | {r.sender} | {r.actor_model_id} "
                 f"| {r.benchmark_id} | auto={r.auto} | n_eq={r.n_eval_eq}\n\n```\n"
                 f"{str(r.content)[:2500]}\n```\n")
print("wrote notes/VALIDATION_SHEET_V2.md")
