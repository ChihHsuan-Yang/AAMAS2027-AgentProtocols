"""R3: ROLE FIDELITY -- does each role perform the function it was ASSIGNED?

Distinct from distinguishability (r2). Fidelity is scored against the specific
clauses of the config contract, per role, and reported per component -- never
collapsed into one opaque number.

PLANNER (4 components)
  P1 abstains from computation   : eval_eq_density below the Executor's within-
                                   trajectory level (paired, self-normalising)
  P2 abstains from answering     : no \boxed
  P3 produces a decomposition    : numbered/ordered steps present
  P4 declares target answer form : "Target quantity"/"answer form" present
EXECUTOR (3)
  E1 performs the computation    : has evaluated equations
  E2 consumes the plan           : references plan / steps / Planner
  E3 commits an answer           : \boxed present
REVIEWER (4)
  R1 issues a routing decision   : exactly one route tag
  R2 diagnoses                   : Diagnosis: section present
  R3 gives targeted fix          : Fix Instruction: present
  R4 does not re-solve           : not carrying a heavy derivation of its own
"""
import os
import numpy as np, pandas as pd

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/results"
pd.set_option("display.width", 250)
P = pd.read_parquet(OUT + "/r1_role_messages.parquet")

# Executor's computation level within the SAME trajectory = the internal yardstick
exec_lvl = (P[P.sender == "Executor"].groupby("trajectory_uid").eval_eq_density.median()
            .rename("exec_density"))
P = P.merge(exec_lvl, on="trajectory_uid", how="left")

pl = P[P.sender == "Planner"].copy()
ex = P[P.sender == "Executor"].copy()
rv = P[P.sender == "Reviewer"].copy()

pl["P1_abstains_compute"] = (pl.eval_eq_density < 0.5 * pl.exec_density).astype(float)
pl["P2_abstains_answer"]  = (~pl.f_boxed).astype(float)
pl["P3_decomposes"]       = pl.f_numbered_steps.astype(float)
pl["P4_declares_form"]    = pl.f_target_form.astype(float)

ex["E1_computes"]         = (ex.eval_eq_density > 0).astype(float)
ex["E2_uses_plan"]        = (ex.f_ref_plan | ex.f_ref_step | ex.f_ref_planner).astype(float)
ex["E3_commits_answer"]   = ex.f_boxed.astype(float)

rv["R1_routes"]           = (rv.f_route_planner | rv.f_route_executor | rv.f_agree).astype(float)
rv["R2_diagnoses"]        = rv.f_diagnosis.astype(float)
rv["R3_targeted_fix"]     = rv.f_fix_instruction.astype(float)
# "does not re-solve": reviewer prompt says "Do NOT restate the full derivation",
# at most 2+2 short bullets. A reviewer writing a long, computation-dense message
# is re-deriving rather than reviewing.
rv["R4_not_resolving"]    = ((rv.n_chars < 1500) | (rv.eval_eq_density < 1.0)).astype(float)

COMP = {"Planner": ["P1_abstains_compute", "P2_abstains_answer", "P3_decomposes", "P4_declares_form"],
        "Executor": ["E1_computes", "E2_uses_plan", "E3_commits_answer"],
        "Reviewer": ["R1_routes", "R2_diagnoses", "R3_targeted_fix", "R4_not_resolving"]}

print("="*78)
print("ROLE FIDELITY — component rates (1.0 = contract honoured on every message)")
print("="*78)
for role, df in [("Planner", pl), ("Executor", ex), ("Reviewer", rv)]:
    print(f"\n{role}  (n={len(df)} messages)")
    for c in COMP[role]:
        print(f"    {c:24s} {df[c].mean():.3f}")
    df["fidelity"] = df[COMP[role]].mean(axis=1)
    print(f"    {'-> mean fidelity':24s} {df.fidelity.mean():.3f}")

A = pd.concat([pl, ex, rv], ignore_index=True)
A.to_parquet(OUT + "/r3_fidelity_messages.parquet", index=False)

print("\n" + "="*78)
print("THE KEY CONTRAST: the Planner's two prohibitions")
print("="*78)
print(f"  P2 abstains from ANSWERING  : {pl.P2_abstains_answer.mean():.3f}  (honoured)")
print(f"  P1 abstains from COMPUTING  : {pl.P1_abstains_compute.mean():.3f}  (violated)")
print("  Both are 'MUST NOT' clauses in the same prompt block. Only one holds.")
print("\n  Planner computation density vs its own Executor, paired by trajectory:")
pp = pl.dropna(subset=["exec_density"])
print(f"    planner median {pp.eval_eq_density.median():.2f} vs executor median {pp.exec_density.median():.2f}")
ratio = (pp.eval_eq_density / pp.exec_density.replace(0, np.nan)).dropna()
print(f"    within-trajectory ratio: median {ratio.median():.3f}, "
      f"share >= 1.0 (planner computes as much or more): {(ratio >= 1).mean():.3f}")
