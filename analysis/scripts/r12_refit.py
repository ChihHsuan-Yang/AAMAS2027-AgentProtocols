"""R12: Fix E2 per the validation error analysis, then re-run the actor ordering.

Validation found one systematic E2 false positive: `f_ref_step` matches
"Step 0", "Inductive step" etc. in the Executor's OWN construction, which is not
plan consumption. Drop the bare step-number pattern and require an explicit
reference to the plan or planner.

Then: does the actor ordering survive the corrected metric? (Bella's P0 gate.)
"""
import os, re, glob
import numpy as np, pandas as pd, pyarrow.parquet as pq

REL = "/Users/bellayang/Documents/note/projects/IEEE-BigData-SciAgentTrace/analysis/hf_cache/release"
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/results"
pd.set_option("display.width", 240)

V = pd.read_parquet(OUT + "/r6_fidelity_joined.parquet")

# need the raw text to recompute; reload contents for executors only
parts = []
for f in sorted(glob.glob(REL + "/data/messages/part-*.parquet")):
    d = pq.read_table(f, columns=["trajectory_uid", "sequence_index", "sender", "content"]).to_pandas()
    d = d[d.sender == "Executor"]
    if len(d): parts.append(d)
X = pd.concat(parts, ignore_index=True)
X["content"] = X.content.fillna("").astype(str)

# v2: explicit plan reference only. "the plan", "Planner", "per the plan",
# "as planned", "following the plan", "planned steps" -- NOT bare "Step N".
PAT = r"\b(?:the\s+plan|Planner|per\s+the\s+plan|as\s+planned|following\s+the\s+plan|planned\s+steps?|structured\s+plan|plan'?s)\b"
X["E2v2_uses_plan"] = X.content.str.contains(PAT, regex=True, case=False).astype(float)

V = V.merge(X[["trajectory_uid", "sequence_index", "E2v2_uses_plan"]],
            on=["trajectory_uid", "sequence_index"], how="left")

ex = V[(V.sender == "Executor") & (V.benchmark_id == "omnimath2")]
print("="*84)
print("E2 CORRECTED — Executor plan consumption, omnimath2, by actor")
print("="*84)
r = np.random.default_rng(0)
def ci(x):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    return tuple(np.percentile(r.choice(x, (3000, len(x))).mean(1), [2.5, 97.5]))
rows = []
for am, g in ex.groupby("actor_model_id"):
    lo1, hi1 = ci(g.E2_uses_plan); lo2, hi2 = ci(g.E2v2_uses_plan)
    rows.append(dict(actor=am, n=len(g),
                     E2_v1=g.E2_uses_plan.mean(), v1_lo=lo1, v1_hi=hi1,
                     E2_v2=g.E2v2_uses_plan.mean(), v2_lo=lo2, v2_hi=hi2))
D = pd.DataFrame(rows).sort_values("E2_v2", ascending=False)
print(D.round(4).to_string(index=False))

print("\npairwise differences under the CORRECTED metric:")
acts = list(D.actor)
for i in range(len(acts)):
    for j in range(i+1, len(acts)):
        a = ex[ex.actor_model_id == acts[i]].E2v2_uses_plan.dropna().values
        b = ex[ex.actor_model_id == acts[j]].E2v2_uses_plan.dropna().values
        bs = [r.choice(a, len(a)).mean() - r.choice(b, len(b)).mean() for _ in range(3000)]
        lo, hi = np.percentile(bs, [2.5, 97.5])
        sig = "" if lo < 0 < hi else "  significant"
        print(f"  {acts[i]:13s} - {acts[j]:13s} = {a.mean()-b.mean():+.4f} [{lo:+.4f},{hi:+.4f}]{sig}")

print("\n" + "="*84)
print("P1a unchanged (validation found only a conservative FN, no metric change needed)")
print("="*84)
pl = V[(V.sender == "Planner") & (V.benchmark_id == "omnimath2")]
for am, g in pl.groupby("actor_model_id"):
    lo, hi = ci(g.P1a_no_computation)
    print(f"  {am:14s} n={len(g):6d}  no-computation={g.P1a_no_computation.mean():.3f} [{lo:.3f},{hi:.3f}]")

print("\n>>> GATE: does the actor ordering survive the corrected metric?")
print(f"    E2 v1 ordering: {list(D.sort_values('E2_v1',ascending=False).actor)}")
print(f"    E2 v2 ordering: {list(D.sort_values('E2_v2',ascending=False).actor)}")
print(f"    P1a  ordering: {list(pl.groupby('actor_model_id').P1a_no_computation.mean().sort_values(ascending=False).index)}")
V.to_parquet(OUT + "/r12_corrected.parquet", index=False)
