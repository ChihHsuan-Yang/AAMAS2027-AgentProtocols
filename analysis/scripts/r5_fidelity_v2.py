"""R5: Fidelity v2 — P1 rebuilt after hand-validation exposed a defect.

DEFECT FOUND (r4 hand-read, 83 Planner messages):
  v1 P1 = (planner_density < 0.5 * executor_density) degenerates when the
  executor's density is 0 or NaN: a Planner writing NO computation at all then
  scores as a VIOLATOR. 22 of 49 v1 "violations" were zero-computation planners
  -- the cleanest possible compliance. The relative yardstick was backwards in
  exactly the cases that matter most.

FIX: score the contract clause on its own terms. The clause is absolute
("MUST NOT write computed intermediate values"), so measure absolutely, and keep
the relative measure separately as a division-of-labour statistic, not as fidelity.
"""
import os
import numpy as np, pandas as pd

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/results"
pd.set_option("display.width", 250)
A = pd.read_parquet(OUT + "/r3_fidelity_messages.parquet")

pl = A[A.sender == "Planner"].copy()
# absolute: does the message contain evaluated numeric results at all?
pl["P1a_no_computation"] = (pl.n_eval_eq == 0).astype(float)
# graded: light (<=2 evaluated equations) vs heavy
pl["P1b_light_computation"] = (pl.n_eval_eq <= 2).astype(float)
# relative division of labour, reported separately (NOT as fidelity)
pl["dol_ratio"] = pl.eval_eq_density / pl.exec_density.replace(0, np.nan)

print("="*78)
print("PLANNER 'MUST NOT compute' — three measures of the same clause")
print("="*78)
print(f"  P1a strict  (zero evaluated equations)      : {pl.P1a_no_computation.mean():.3f}")
print(f"  P1b lenient (<=2 evaluated equations)       : {pl.P1b_light_computation.mean():.3f}")
print(f"  v1 relative (superseded, defective)         : {pl.P1_abstains_compute.mean():.3f}")
print(f"\n  division-of-labour ratio (planner/executor density), median: "
      f"{pl.dol_ratio.median():.3f}")
print(f"  share of planners computing >= their executor: {(pl.dol_ratio >= 1).mean():.3f}")

print("\n  distribution of evaluated equations per Planner message:")
print(pl.n_eval_eq.describe(percentiles=[.25, .5, .75, .9]).round(2).to_string())
print(f"\n  >>> {(pl.n_eval_eq == 0).mean():.1%} of Planner messages contain NO computed value.")
print(f"  >>> {(pl.n_eval_eq > 5).mean():.1%} contain more than five.")

COMP = ["P1a_no_computation", "P2_abstains_answer", "P3_decomposes", "P4_declares_form"]
pl["fidelity_v2"] = pl[COMP].mean(axis=1)
print("\n=== Planner fidelity v2, components ===")
for c in COMP:
    print(f"    {c:24s} {pl[c].mean():.3f}")
print(f"    {'-> mean':24s} {pl.fidelity_v2.mean():.3f}")

ex = A[A.sender == "Executor"].copy()
rv = A[A.sender == "Reviewer"].copy()
ex["fidelity_v2"] = ex[["E1_computes", "E2_uses_plan", "E3_commits_answer"]].mean(axis=1)
rv["fidelity_v2"] = rv[["R1_routes", "R2_diagnoses", "R3_targeted_fix", "R4_not_resolving"]].mean(axis=1)
V = pd.concat([pl, ex, rv], ignore_index=True)
V.to_parquet(OUT + "/r5_fidelity_v2.parquet", index=False)
print("\n=== all roles, fidelity v2 ===")
print(V.groupby("sender").fidelity_v2.agg(["mean", "size"]).round(3).to_string())
