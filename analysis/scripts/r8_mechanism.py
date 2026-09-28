"""R8: Does realized role fidelity relate to the organization x actor interaction?

Observational only. Three actors is far too few to regress an interaction on a
model-level covariate, so the honest test is WITHIN actor, across problems:
  does PER's advantage over broadcast track PER's realized fidelity?

Restricted to omnimath2 (the only domain with the full contract) and to
first_pass_correct (oracle-free, per the earlier oracle-budget confound).
"""
import os
import numpy as np, pandas as pd, pyarrow.parquet as pq

REL = "/Users/bellayang/Documents/note/projects/IEEE-BigData-SciAgentTrace/analysis/hf_cache/release"
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/results"
pd.set_option("display.width", 260)

V = pd.read_parquet(OUT + "/r6_fidelity_joined.parquet")
traj = pq.read_table(REL + "/data/trajectories/part-00000.parquet",
                     columns=["trajectory_uid", "problem_uid", "protocol_id",
                              "benchmark_id", "actor_model_id", "first_pass_correct",
                              "final_correct"]).to_pandas()

# ---- 1. reproduce the organization x actor reversal, oracle-free ------------
print("="*92)
print("D. ORGANIZATION x ACTOR — reproduce the reversal (first submission, oracle-free)")
print("="*92)
fp = traj[traj.first_pass_correct.notna()].copy()
fp["first_pass_correct"] = fp.first_pass_correct.astype(int)
w = fp.pivot_table(index=["problem_uid", "benchmark_id", "actor_model_id"],
                   columns="protocol_id", values="first_pass_correct", aggfunc="first").dropna()
w = w.reset_index()
r = np.random.default_rng(0)
for (bm, am), g in w.groupby(["benchmark_id", "actor_model_id"]):
    if len(g) < 100: continue
    d = (g["broadcast"] - g["per"]).values
    bs = [r.choice(d, len(d)).mean() for _ in range(4000)]
    lo, hi = np.percentile(bs, [2.5, 97.5])
    sig = "" if lo < 0 < hi else "  <-- significant"
    print(f"  {bm:10s} {am:13s} n={len(g):5d}  PER={g['per'].mean():.3f} "
          f"BCAST={g['broadcast'].mean():.3f}  bcast-per={d.mean():+.4f} [{lo:+.4f},{hi:+.4f}]{sig}")

print("\n  Is the omnimath2 reversal driven by a few items, or is it broad?")
om = w[(w.benchmark_id == "omnimath2")]
for am, g in om.groupby("actor_model_id"):
    disc = g[g["broadcast"] != g["per"]]
    print(f"    {am:13s} discordant items={len(disc)}/{len(g)}  "
          f"bcast-only-right={int((disc['broadcast']==1).sum())}  "
          f"per-only-right={int((disc['per']==1).sum())}")

# ---- 2. trajectory-level fidelity -> outcome, WITHIN actor ------------------
print("\n" + "="*92)
print("E. MECHANISM (observational): does PER fidelity relate to PER success?")
print("="*92)
tf = (V[V.benchmark_id == "omnimath2"]
      .groupby(["trajectory_uid", "actor_model_id", "sender"]).fidelity_v2.mean()
      .unstack("sender"))
tf.columns = [f"fid_{c}" for c in tf.columns]
tf = tf.reset_index()
per = traj[(traj.protocol_id == "per") & (traj.benchmark_id == "omnimath2")]
tf = tf.merge(per[["trajectory_uid", "problem_uid", "first_pass_correct", "final_correct"]],
              on="trajectory_uid", how="inner")
tf = tf[tf.first_pass_correct.notna()]
tf["first_pass_correct"] = tf.first_pass_correct.astype(int)
print(f"PER omnimath2 trajectories with fidelity + first-pass: {len(tf)}")
for am, g in tf.groupby("actor_model_id"):
    if len(g) < 200: continue
    print(f"\n  {am} (n={len(g)}):")
    for col in ["fid_Planner", "fid_Executor", "fid_Reviewer"]:
        if col not in g or g[col].isna().all(): continue
        hi_ = g[g[col] >= g[col].median()]
        lo_ = g[g[col] < g[col].median()]
        d = hi_.first_pass_correct.mean() - lo_.first_pass_correct.mean()
        bs = [r.choice(hi_.first_pass_correct.values, len(hi_)).mean()
              - r.choice(lo_.first_pass_correct.values, len(lo_)).mean() for _ in range(2000)]
        l, h = np.percentile(bs, [2.5, 97.5])
        flag = "" if l < 0 < h else "  <-- nonzero"
        print(f"    {col:14s} high-vs-low fidelity acc diff = {d:+.4f} [{l:+.4f},{h:+.4f}]{flag}")

# ---- 3. the actual mediation question, stated honestly ----------------------
print("\n" + "="*92)
print("Actor-level: fidelity vs PER advantage (N=3 actors -- NOT a regression)")
print("="*92)
rows = []
for am in tf.actor_model_id.unique():
    g = V[(V.benchmark_id == "omnimath2") & (V.actor_model_id == am)]
    adv = om[om.actor_model_id == am]
    if len(adv) == 0: continue
    rows.append(dict(actor=am,
                     planner_no_compute=g[g.sender == "Planner"].P1a_no_computation.mean(),
                     exec_uses_plan=g[g.sender == "Executor"].E2_uses_plan.mean(),
                     per_first_pass=adv["per"].mean(),
                     bcast_first_pass=adv["broadcast"].mean(),
                     per_advantage=(adv["per"] - adv["broadcast"]).mean()))
D = pd.DataFrame(rows)
print(D.round(4).to_string(index=False))
print("\n  THREE POINTS. Any correlation here is uninterpretable. Reported only to show")
print("  the direction that the controlled experiment would need to test.")
tf.to_parquet(OUT + "/r8_traj_fidelity.parquet", index=False)
