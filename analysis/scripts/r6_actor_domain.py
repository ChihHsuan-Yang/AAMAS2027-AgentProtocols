"""R6: Does realized role fidelity vary by ACTOR MODEL and DOMAIN?

Standing rule from the prior session: stratify before pooling. Two Simpson's
reversals have already been found in this project, so every cell is reported.
"""
import os
import numpy as np, pandas as pd, pyarrow.parquet as pq

REL = "/Users/bellayang/Documents/note/projects/IEEE-BigData-SciAgentTrace/analysis/hf_cache/release"
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/results"
pd.set_option("display.width", 260)

V = pd.read_parquet(OUT + "/r5_fidelity_v2.parquet")
traj = pq.read_table(REL + "/data/trajectories/part-00000.parquet",
                     columns=["trajectory_uid", "benchmark_id", "actor_model_id",
                              "final_correct", "first_pass_correct"]).to_pandas()
V = V.merge(traj, on="trajectory_uid", how="left")

def boot(x, n=3000, seed=0):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    if len(x) < 2: return (np.nan, np.nan)
    r = np.random.default_rng(seed)
    b = r.choice(x, (n, len(x))).mean(1)
    return tuple(np.percentile(b, [2.5, 97.5]))

print("="*90)
print("A. PLANNER 'no computation' compliance by ACTOR MODEL (pooled over domains)")
print("="*90)
pl = V[V.sender == "Planner"]
for am, g in pl.groupby("actor_model_id"):
    lo, hi = boot(g.P1a_no_computation)
    print(f"  {am:14s} n={len(g):6d}  P1a={g.P1a_no_computation.mean():.3f} [{lo:.3f},{hi:.3f}]"
          f"   fidelity={g.fidelity_v2.mean():.3f}   dol_ratio_med={g.dol_ratio.median():.3f}")

print("\n" + "="*90)
print("B. STRATIFIED: actor x domain (pooling hides interactions -- standing rule)")
print("="*90)
rows = []
for (am, bm), g in pl.groupby(["actor_model_id", "benchmark_id"]):
    if len(g) < 100: continue
    lo, hi = boot(g.P1a_no_computation)
    rows.append(dict(actor=am, domain=bm, n=len(g),
                     P1a=g.P1a_no_computation.mean(), lo=lo, hi=hi,
                     P3=g.P3_decomposes.mean(), P4=g.P4_declares_form.mean(),
                     fidelity=g.fidelity_v2.mean()))
print(pd.DataFrame(rows).round(3).to_string(index=False))

print("\n" + "="*90)
print("C. EXECUTOR plan-consumption by actor x domain  (E2_uses_plan)")
print("="*90)
ex = V[V.sender == "Executor"]
rows = []
for (am, bm), g in ex.groupby(["actor_model_id", "benchmark_id"]):
    if len(g) < 100: continue
    lo, hi = boot(g.E2_uses_plan)
    rows.append(dict(actor=am, domain=bm, n=len(g), E1=g.E1_computes.mean(),
                     E2_uses_plan=g.E2_uses_plan.mean(), lo=lo, hi=hi,
                     E3=g.E3_commits_answer.mean(), fidelity=g.fidelity_v2.mean()))
print(pd.DataFrame(rows).round(3).to_string(index=False))

print("\n" + "="*90)
print("D. REVIEWER behaviour by actor x domain")
print("="*90)
rv = V[V.sender == "Reviewer"]
rows = []
for (am, bm), g in rv.groupby(["actor_model_id", "benchmark_id"]):
    if len(g) < 100: continue
    rows.append(dict(actor=am, domain=bm, n=len(g), R1_routes=g.R1_routes.mean(),
                     R2_diag=g.R2_diagnoses.mean(), R3_fix=g.R3_targeted_fix.mean(),
                     R4_not_resolve=g.R4_not_resolving.mean(),
                     agree_rate=g.f_agree.mean(), fidelity=g.fidelity_v2.mean()))
print(pd.DataFrame(rows).round(3).to_string(index=False))

print("\n" + "="*90)
print("E. Does fidelity change across ROUNDS / after an evaluator FAIL?")
print("="*90)
for role, g0 in V.groupby("sender"):
    a = g0[~g0.is_post_eval].fidelity_v2.mean()
    b = g0[g0.is_post_eval].fidelity_v2.mean()
    d = b - a
    x = g0[g0.is_post_eval].fidelity_v2.dropna().values
    y = g0[~g0.is_post_eval].fidelity_v2.dropna().values
    r = np.random.default_rng(0)
    bs = [r.choice(x, len(x)).mean() - r.choice(y, len(y)).mean() for _ in range(2000)]
    print(f"  {role:9s} initial={a:.3f}  post-eval-fail={b:.3f}  "
          f"delta={d:+.3f} [{np.percentile(bs,2.5):+.3f},{np.percentile(bs,97.5):+.3f}]")

V.to_parquet(OUT + "/r6_fidelity_joined.parquet", index=False)
