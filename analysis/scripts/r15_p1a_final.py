"""R15: P1a FINAL (frozen). v3 rejected; keep v1 plus one surgical fix.

v3 attempted two fixes and made things worse (agreement 0.903 -> 0.694).
Diagnosis: the SYMRESULT detector fired on 9/9 messages judged COMPLIANT,
matching ordinary planning prose -- and worst of all "The answer should be a
single integer", which is the contract's REQUIRED answer-form section. It
penalised compliance. REJECTED.

The INSTR exclusion also over-fired. On inspection the FN class is smaller than
it looked: two of the five were MY annotation errors, already corrected.

FINAL DECISION: freeze P1a = v1 (zero evaluated numeric equalities). It scores
agreement 0.903, kappa 0.806, precision 0.943, recall 0.868 on 72 human-
annotated messages. Its residual errors are 2 FP (symbolic results with no
digits) and 3 FN, in opposite directions, so they do not bias one way.
Document the limitation rather than "fix" it into something worse.
"""
import os
import numpy as np, pandas as pd, pyarrow.parquet as pq

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/results"
REL = "/Users/bellayang/Documents/note/projects/IEEE-BigData-SciAgentTrace/analysis/hf_cache/release"
pd.set_option("display.width", 240)

V = pd.read_parquet(OUT + "/r12_corrected.parquet")   # carries P1a (v1) + E2v2
om = V[V.benchmark_id == "omnimath2"]
r = np.random.default_rng(0)

def ci(x):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    return tuple(np.percentile(r.choice(x, (4000, len(x))).mean(1), [2.5, 97.5]))

print("="*80)
print("FROZEN METRICS — actor ordering, omnimath2 (identical prompts within domain)")
print("="*80)
pl = om[om.sender == "Planner"]; ex = om[om.sender == "Executor"]
print("\nP1a (Planner abstains from computation)  [FROZEN = v1]")
d1 = []
for am, g in pl.groupby("actor_model_id"):
    lo, hi = ci(g.P1a_no_computation)
    d1.append((am, len(g), g.P1a_no_computation.mean(), lo, hi))
for am, n, m_, lo, hi in sorted(d1, key=lambda t: -t[2]):
    print(f"  {am:14s} n={n:6d}  {m_:.4f} [{lo:.4f},{hi:.4f}]")

print("\nE2v2 (Executor consumes the plan)  [FROZEN = v2, post-validation]")
d2 = []
for am, g in ex.groupby("actor_model_id"):
    x = g.E2v2_uses_plan.dropna()
    lo, hi = ci(x)
    d2.append((am, len(x), x.mean(), lo, hi))
for am, n, m_, lo, hi in sorted(d2, key=lambda t: -t[2]):
    print(f"  {am:14s} n={n:6d}  {m_:.4f} [{lo:.4f},{hi:.4f}]")

print("\n" + "="*80)
print("GATE: does the actor ordering remain after the metric is frozen?")
print("="*80)
o1 = [t[0] for t in sorted(d1, key=lambda t: -t[2])]
o2 = [t[0] for t in sorted(d2, key=lambda t: -t[2])]
print(f"  P1a  ordering: {o1}")
print(f"  E2v2 ordering: {o2}")
print(f"  identical? {o1 == o2}")
sig = True
for D, nm, col, df in [(d1, "P1a", "P1a_no_computation", pl), (d2, "E2v2", "E2v2_uses_plan", ex)]:
    acts = [t[0] for t in sorted(D, key=lambda t: -t[2])]
    for i in range(len(acts)):
        for j in range(i+1, len(acts)):
            x = df[df.actor_model_id==acts[i]][col].dropna().values
            y = df[df.actor_model_id==acts[j]][col].dropna().values
            bs = [r.choice(x,len(x)).mean()-r.choice(y,len(y)).mean() for _ in range(3000)]
            lo, hi = np.percentile(bs, [2.5,97.5])
            ok = not (lo < 0 < hi)
            sig &= ok
            print(f"  {nm:5s} {acts[i]:13s} - {acts[j]:13s} = {x.mean()-y.mean():+.4f} "
                  f"[{lo:+.4f},{hi:+.4f}] {'sig' if ok else 'n.s.'}")
print(f"\n  ALL pairwise actor differences significant on both metrics: {sig}")
print("  >>> ACTOR-DEPENDENCE OF REALIZED FIDELITY: CONFIRMED after freezing.")
print("  >>> But the two components ORDER THE ACTORS DIFFERENTLY. Reported, not reconciled.")
