"""R7: Corrected analysis -- score each domain against ITS OWN contract.

Per DEFECT-prompt-varies-by-domain.md, only clauses a domain's prompt actually
imposes may be scored there, and only WITHIN-domain cross-actor comparisons are
valid (both actors get an identical prompt inside a domain).

Headline contrast = omnimath2, the only domain whose Planner prompt carries the
"MUST NOT carry out ... arithmetic yourself" clause.
"""
import os
import numpy as np, pandas as pd

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/results"
pd.set_option("display.width", 260)
V = pd.read_parquet(OUT + "/r6_fidelity_joined.parquet")

# clauses actually present in each domain's PER preset
CONTRACT = {
    "omnimath2": dict(Planner=["P1a_no_computation", "P2_abstains_answer",
                               "P3_decomposes", "P4_declares_form"],
                      Executor=["E1_computes", "E2_uses_plan", "E3_commits_answer"],
                      Reviewer=["R1_routes", "R2_diagnoses", "R3_targeted_fix",
                                "R4_not_resolving"]),
    # non-math presets: no computation prohibition, no DELTA/Diagnosis/Target-form
    "_other":   dict(Planner=["P2_abstains_answer", "P3_decomposes"],
                     Executor=["E2_uses_plan", "E3_commits_answer"],
                     Reviewer=["R1_routes", "R4_not_resolving"]),
}

def comps(domain, role):
    return CONTRACT.get(domain, CONTRACT["_other"])[role]

print("="*92)
print("HEADLINE: omnimath2 only -- the one domain that imposes 'MUST NOT compute'")
print("Both actors receive a byte-identical Planner prompt here.")
print("="*92)
om = V[V.benchmark_id == "omnimath2"]
r = np.random.default_rng(0)
def ci(x):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    if len(x) < 2: return (np.nan, np.nan)
    return tuple(np.percentile(r.choice(x, (3000, len(x))).mean(1), [2.5, 97.5]))

for role in ["Planner", "Executor", "Reviewer"]:
    print(f"\n--- {role} (omnimath2) ---")
    g0 = om[om.sender == role]
    for am, g in g0.groupby("actor_model_id"):
        parts = " ".join(f"{c.split('_')[0]}={g[c].mean():.3f}" for c in comps("omnimath2", role))
        f = g[comps("omnimath2", role)].mean(axis=1)
        lo, hi = ci(f)
        print(f"  {am:14s} n={len(g):6d}  fidelity={f.mean():.3f} [{lo:.3f},{hi:.3f}]   {parts}")

print("\n" + "="*92)
print("The Planner computation clause, omnimath2, by actor")
print("="*92)
pl = om[om.sender == "Planner"]
for am, g in pl.groupby("actor_model_id"):
    lo, hi = ci(g.P1a_no_computation)
    print(f"  {am:14s} n={len(g):6d}  no-computation={g.P1a_no_computation.mean():.3f} [{lo:.3f},{hi:.3f}]"
          f"  median_eqs={g.n_eval_eq.median():.0f}  dol_ratio_med={g.dol_ratio.median():.3f}")

print("\n  pairwise differences (bootstrap):")
acts = sorted(pl.actor_model_id.unique())
for i in range(len(acts)):
    for j in range(i+1, len(acts)):
        a = pl[pl.actor_model_id == acts[i]].P1a_no_computation.values
        b = pl[pl.actor_model_id == acts[j]].P1a_no_computation.values
        bs = [r.choice(a, len(a)).mean() - r.choice(b, len(b)).mean() for _ in range(3000)]
        print(f"    {acts[i]:13s} - {acts[j]:13s} = {a.mean()-b.mean():+.3f} "
              f"[{np.percentile(bs,2.5):+.3f},{np.percentile(bs,97.5):+.3f}]")

print("\n" + "="*92)
print("EXECUTOR plan-consumption, omnimath2, by actor (prompt identical within domain)")
print("="*92)
ex = om[om.sender == "Executor"]
for am, g in ex.groupby("actor_model_id"):
    lo, hi = ci(g.E2_uses_plan)
    print(f"  {am:14s} n={len(g):6d}  uses_plan={g.E2_uses_plan.mean():.3f} [{lo:.3f},{hi:.3f}]")
a = ex[ex.actor_model_id == "gemma_4_31b"].E2_uses_plan.values
b = ex[ex.actor_model_id == "gpt_oss_120b"].E2_uses_plan.values
bs = [r.choice(a, len(a)).mean() - r.choice(b, len(b)).mean() for _ in range(3000)]
print(f"    gemma_4_31b - gpt_oss_120b = {a.mean()-b.mean():+.3f} "
      f"[{np.percentile(bs,2.5):+.3f},{np.percentile(bs,97.5):+.3f}]")

print("\n" + "="*92)
print("LABBENCH (contract = answer-abstention + routing only)")
print("="*92)
lb = V[V.benchmark_id == "labbench"]
for role in ["Planner", "Executor", "Reviewer"]:
    g0 = lb[lb.sender == role]
    for am, g in g0.groupby("actor_model_id"):
        cs = comps("labbench", role)
        print(f"  {role:9s} {am:14s} n={len(g):6d}  " +
              " ".join(f"{c}={g[c].mean():.3f}" for c in cs))
