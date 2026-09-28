"""D8: Match protocols on ORACLE-FEEDBACK budget, not on name.

Every protocol sits inside the same outer loop: an Evaluator that SEES GROUND
TRUTH, returns PASS/FAIL, and on FAIL emits a repair hint back to the agents.
The arms differ in how many of those oracle bits they consume:
  baseline_llm : 1 submission, 0 feedback rounds
  single_agent : up to 3 submissions
  per          : up to 3 outer x 2 inner
  broadcast    : up to 3 outer x (4 discussion + 2 approval)

So "Broadcast > Baseline" confounds (more agents) x (more attempts) x (more
oracle feedback). This script asks: at a MATCHED number of oracle submissions,
does the multi-agent structure still buy anything?
"""
import os
import numpy as np, pandas as pd, pyarrow.parquet as pq

REL = "/Users/bellayang/Documents/note/projects/IEEE-BigData-SciAgentTrace/analysis/hf_cache/release"
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/results"
pd.set_option("display.width", 250)

t = pq.read_table(REL + "/data/trajectories/part-00000.parquet").to_pandas()

print("=== oracle submissions (evaluator_calls) actually consumed ===")
print(t.groupby("protocol_id").evaluator_calls.agg(["count", "mean", "median", "max"]).round(3).to_string())
print("\n(PER logs no evaluator_calls counter -> excluded from budget matching)")

fp = t[t.first_pass_correct.notna()].copy()
for c in ["first_pass_correct", "final_correct"]:
    fp[c] = fp[c].astype(int)

# --- 1. ZERO-FEEDBACK comparison: everyone's FIRST submission ---------------
print("\n=== [A] ZERO oracle feedback: accuracy of the FIRST submission ===")
print("    (this is the only arm-comparison with equal oracle exposure)")
key = ["problem_uid", "benchmark_id", "actor_model_id"]
w = fp.pivot_table(index=key, columns="protocol_id",
                   values="first_pass_correct", aggfunc="first").dropna()
print(f"paired problems: {len(w)}")
base = w["baseline_llm"].values
r = np.random.default_rng(0)
for p in ["baseline_llm", "single_agent", "per", "broadcast"]:
    d = w[p].values - base
    bs = [r.choice(d, len(d)).mean() for _ in range(4000)]
    print(f"  {p:13s} acc={w[p].mean():.4f}   vs baseline {d.mean():+.4f} "
          f"[{np.percentile(bs,2.5):+.4f}, {np.percentile(bs,97.5):+.4f}]")

# --- 2. Accuracy vs oracle budget, per protocol ------------------------------
print("\n=== [B] final accuracy by number of oracle submissions consumed ===")
e = fp[fp.evaluator_calls.notna() & (fp.evaluator_calls > 0)].copy()
e["ec"] = e.evaluator_calls.clip(upper=4)
print(pd.crosstab(e.protocol_id, e.ec, values=e.final_correct, aggfunc="mean").round(4).to_string())
print(pd.crosstab(e.protocol_id, e.ec).to_string())
print("\nNOTE: this conditions on a post-treatment variable (runs stop on PASS),")
print("      so it is descriptive only -- it cannot identify a causal effect.")

# --- 3. The honest headline: how much of each arm's gain is oracle-driven ----
print("\n=== [C] gain decomposition on the paired set ===")
wf = fp.pivot_table(index=key, columns="protocol_id",
                    values=["first_pass_correct", "final_correct"], aggfunc="first")
wf.columns = [f"{a}__{b}" for a, b in wf.columns]
wf = wf.dropna()
b0 = wf["first_pass_correct__baseline_llm"].values
rows = []
for p in ["single_agent", "per", "broadcast"]:
    a = wf[f"first_pass_correct__{p}"].values
    z = wf[f"final_correct__{p}"].values
    tot = (z - b0).mean()
    rows.append(dict(protocol=p, total_gain=tot,
                     structure_gain=(a - b0).mean(), oracle_gain=(z - a).mean(),
                     pct_from_oracle=100 * (z - a).mean() / tot))
print(pd.DataFrame(rows).round(4).to_string(index=False))
pd.DataFrame(rows).to_csv(OUT + "/d8_gain_decomposition.csv", index=False)
