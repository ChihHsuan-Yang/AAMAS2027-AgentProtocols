"""D12: Are PER's roles functionally distinct, or cosmetic?

The PER config imposes HARD ROLE SEPARATION on the Planner, in capitals:
  "You MUST NOT carry out symbolic manipulation or arithmetic yourself."
  "You MUST NOT write computed intermediate values."
  "Do NOT provide the final answer."

If the Planner computes anyway, then 'role specialization' in this protocol is a
prompt-level label rather than a behavioural division of labour -- which bears
directly on whether PER's measured gain comes from specialization at all.
"""
import os, re, glob
import numpy as np, pandas as pd, pyarrow.parquet as pq

REL = "/Users/bellayang/Documents/note/projects/IEEE-BigData-SciAgentTrace/analysis/hf_cache/release"
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/results"
pd.set_option("display.width", 250)

parts = []
for f in sorted(glob.glob(REL + "/data/messages/part-*.parquet")):
    d = pq.read_table(f, columns=["trajectory_uid", "stage", "sender", "content"]).to_pandas()
    d = d[d.sender.isin(["Planner", "Executor", "Reviewer"])]
    if len(d): parts.append(d)
P = pd.concat(parts, ignore_index=True)
P["content"] = P.content.fillna("").astype(str)
print(f"PER role messages: {len(P)}  trajectories: {P.trajectory_uid.nunique()}")
print(P.sender.value_counts().to_string())

# --- behavioural markers of "doing the computation" -------------------------
PATS = {
    "numeric_equation": r"=\s*[-+]?\d+\.?\d*",       # an evaluated equality
    "boxed_answer":     r"\\boxed",                   # committing an answer
    "arith_op":         r"\d+\s*[\*\×/÷]\s*\d+",      # explicit arithmetic
    "approx_result":    r"\\approx|≈",                # numeric approximation
}
for k, p in PATS.items():
    P[k] = P.content.str.contains(p, regex=True)
P["chars"] = P.content.str.len()

print("\n=== behavioural markers by role (share of messages) ===")
tab = P.groupby("sender")[list(PATS) + ["chars"]].mean().round(3)
tab["n"] = P.groupby("sender").size()
print(tab.to_string())

print("\n=== the contract the Planner was given, vs what it did ===")
pl = P[P.sender == "Planner"]; ex = P[P.sender == "Executor"]
r = np.random.default_rng(0)
for k in ["numeric_equation", "boxed_answer", "arith_op"]:
    a, b = pl[k].values, ex[k].values
    d = a.mean() - b.mean()
    bs = [r.choice(a, len(a)).mean() - r.choice(b, len(b)).mean() for _ in range(2000)]
    lo, hi = np.percentile(bs, [2.5, 97.5])
    print(f"  {k:18s} planner={a.mean():.3f}  executor={b.mean():.3f}  "
          f"diff={d:+.3f} [{lo:+.3f}, {hi:+.3f}]")
print("\n  The config FORBIDS all three to the Planner. A compliant planner would")
print("  score ~0. Interpretation: role separation is instructed, not enforced,")
print("  and largely not obeyed for arithmetic.")

# --- does compliance matter for the outcome? --------------------------------
traj = pq.read_table(REL + "/data/trajectories/part-00000.parquet",
                     columns=["trajectory_uid", "final_correct", "first_pass_correct",
                              "benchmark_id", "actor_model_id"]).to_pandas()
comp = (P[P.sender == "Planner"].groupby("trajectory_uid")
        .agg(planner_computes=("numeric_equation", "max"),
             planner_boxes=("boxed_answer", "max")).reset_index())
m = comp.merge(traj, on="trajectory_uid", how="inner")
m = m[m.first_pass_correct.notna()]
print(f"\n=== outcome by planner compliance (first-pass, oracle-free) n={len(m)} ===")
print(m.groupby("planner_computes").first_pass_correct.agg(["mean", "size"]).round(4).to_string())
print("\n  by benchmark x actor:")
print(m.groupby(["benchmark_id", "actor_model_id", "planner_computes"])
       .first_pass_correct.agg(["mean", "size"]).round(4).to_string())
print("\n  NOTE: observational and confounded by problem difficulty -- a planner")
print("  computes when the problem invites it. Not a causal claim.")

print("\n=== Reviewer routing ===")
rv = P[P.sender == "Reviewer"].content
for tag in ["[Agree]", "[Route:Planner]", "[Route:Executor]"]:
    s = rv.str.contains(re.escape(tag))
    print(f"  {tag:18s} {s.mean():.3f}  ({s.sum()})")
P.groupby("sender")[list(PATS)].mean().to_csv(OUT + "/d12_role_markers.csv")
