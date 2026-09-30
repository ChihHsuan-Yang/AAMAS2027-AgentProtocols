#!/usr/bin/env python3
"""Validate the artifact reproduces FINAL_TABLES.py's published numbers.

This is the test that matters for a consumer: if the derived tables cannot
regenerate the paper's tables, the artifact is decoration. Every expected value
below is transcribed from analysis/out/FINAL_TABLES_OUTPUT.txt (the canonical
output, per SOURCE_OF_TRUTH.md) -- NOT recomputed here and NOT taken from prose.

Exits nonzero on any mismatch.
"""
import os, json, collections
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data")

tr = pd.read_parquet(os.path.join(D, "trajectories.parquet"))
ec = pd.read_parquet(os.path.join(D, "evaluator_calls.parquet"))
rm = pd.read_parquet(os.path.join(D, "role_messages.parquet"))

fails, checks = [], 0


def chk(label, got, want, tol=5e-4):
    global checks
    checks += 1
    ok = (abs(got - want) <= tol) if isinstance(want, float) else (got == want)
    if not ok:
        fails.append(f"{label}: got {got!r}, expected {want!r}")
    print(f"  {'ok ' if ok else 'FAIL'} {label:<52} got={got!r:<22} want={want!r}")


print("[integrity]")
chk("trajectory rows", len(tr), 11600)
chk("trajectory_key unique", tr.trajectory_key.nunique(), 11600)
chk("evaluator_calls rows", len(ec), 17486)
chk("calls match submissions", int(tr.submissions.sum()), len(ec))
chk("every call key in traj", int(ec.trajectory_key.isin(set(tr.trajectory_key)).all()), 1)
chk("every msg key in traj", int(rm.trajectory_key.isin(set(tr.trajectory_key)).all()), 1)
chk("distinct problems", tr.problem_uid.nunique(), 1600)

# ---------------------------------------------------------------- T0 census
print("\n[T0] cell census  (FINAL_TABLES_OUTPUT.txt lines 10-20)")
T0 = {  # actor, arm -> (n, graded, ungraded, hardfail)
    ("gemma-4-31B-it", "A"): (1600, 1600, 0, 0),
    ("gemma-4-31B-it", "B"): (1600, 1600, 0, 0),
    ("gemma-4-31B-it", "C"): (1600, 1472, 128, 128),
    ("gemma-4-31B-it", "Cp"): (400, 382, 18, 17),
    ("gpt-oss-120b", "A"): (1600, 1598, 2, 0),
    ("gpt-oss-120b", "B"): (1600, 1594, 6, 0),
    ("gpt-oss-120b", "C"): (1600, 1442, 158, 95),
    ("gpt-oss-120b", "Cp"): (400, 361, 39, 16),
    ("Llama-3.3-70B-Instruct", "A"): (400, 397, 3, 0),
    ("Llama-3.3-70B-Instruct", "B"): (400, 390, 10, 0),
    ("Llama-3.3-70B-Instruct", "C"): (400, 332, 68, 64),
}
for (a, arm), (n, g, u, hf) in T0.items():
    s = tr[(tr.actor_model == a) & (tr.arm == arm)]
    chk(f"T0 {a}/{arm} n", len(s), n)
    chk(f"T0 {a}/{arm} graded", int(s.graded.sum()), g)
    chk(f"T0 {a}/{arm} ungraded", int((~s.graded).sum()), u)
    chk(f"T0 {a}/{arm} hardfail", int(s.hard_failure.notna().sum()), hf)

# ---------------------------------------------------------------- T1 master
print("\n[T1] master results  (lines 23-33)")
T1 = {  # (firstpass, final_prereg, recovery, n_fpw, frozen_ans)
    ("gemma-4-31B-it", "A"): (0.802, 0.846, 0.222, 316, 0.288),
    ("gemma-4-31B-it", "B"): (0.802, 0.812, 0.051, 316, 0.845),
    ("gemma-4-31B-it", "C"): (0.822, 0.824, 0.412, 262, 0.122),
    ("gemma-4-31B-it", "Cp"): (0.825, 0.858, 0.418, 67, 0.179),
    ("gpt-oss-120b", "A"): (0.710, 0.803, 0.324, 463, 0.052),
    ("gpt-oss-120b", "B"): (0.763, 0.819, 0.249, 377, 0.202),
    ("gpt-oss-120b", "C"): (0.788, 0.798, 0.461, 306, 0.069),
    ("gpt-oss-120b", "Cp"): (0.773, 0.775, 0.378, 82, 0.073),
    ("Llama-3.3-70B-Instruct", "A"): (0.307, 0.315, 0.015, 275, 0.749),
    ("Llama-3.3-70B-Instruct", "B"): (0.315, 0.318, 0.015, 267, 0.805),
    ("Llama-3.3-70B-Instruct", "C"): (0.295, 0.333, 0.150, 234, 0.064),
}
for (a, arm), (f1, fin, rec, nfpw, fz) in T1.items():
    s = tr[(tr.actor_model == a) & (tr.arm == arm)]
    g = s[s.graded]
    w = g[g.first_pass_correct == 0]
    chk(f"T1 {a}/{arm} firstpass", float(f"{g.first_pass_correct.mean():.3f}"), f1)
    chk(f"T1 {a}/{arm} final", float(f"{s.final_correct_prereg.mean():.3f}"), fin)
    chk(f"T1 {a}/{arm} recovery", float(f"{w.final_correct_prereg.mean():.3f}"), rec)
    chk(f"T1 {a}/{arm} n_fpw", len(w), nfpw)
    chk(f"T1 {a}/{arm} frozen_ans", float(f"{w.frozen_answer.mean():.3f}"), fz)

# functional collapse, A/B only (T1 'collapse' column)
print("\n[T1] functional collapse (A/B only)")
for (a, arm), v in {("gemma-4-31B-it", "A"): 0.000, ("gemma-4-31B-it", "B"): 0.976,
                    ("gpt-oss-120b", "A"): 0.120, ("gpt-oss-120b", "B"): 0.846,
                    ("Llama-3.3-70B-Instruct", "A"): 0.000,
                    ("Llama-3.3-70B-Instruct", "B"): 0.872}.items():
    s = tr[(tr.actor_model == a) & (tr.arm == arm)]
    chk(f"T1 collapse {a}/{arm}", round(s.functional_collapse.dropna().mean(), 3), v)

# ---------------------------------------------------------------- T5 mechanism
print("\n[T5] mechanism: cycles / submissions / never-refuses  (lines 76-83)")
T5 = {  # cycles, submits, neverrefuse
    ("gemma-4-31B-it", "A"): (5.52, 1.54, 0.051),
    ("gemma-4-31B-it", "B"): (5.83, 5.80, 0.981),
}
for (a, arm), (cy, su, nv) in T5.items():
    w = tr[(tr.actor_model == a) & (tr.arm == arm) & tr.graded & (tr.first_pass_correct == 0)]
    chk(f"T5 {a}/{arm} cycles", round(w.cycles.mean(), 2), cy, tol=6e-3)
    chk(f"T5 {a}/{arm} submissions", round(w.submissions.mean(), 2), su, tol=6e-3)
    chk(f"T5 {a}/{arm} neverrefuse", round(w.reviewer_never_declines.dropna().mean(), 3), nv)

# ---------------------------------------------------------------- T6 noise floor
print("\n[T6] grader noise floor  (line 86: 24/2791 = 0.0086)")
sub = ec[ec.candidate_normalized.notna() & ec.verdict.notna()]
grp = sub.groupby(["problem_uid", "candidate_normalized"]).verdict.agg(["nunique", "size"])
multi = grp[grp["size"] >= 2]
disc = multi[multi["nunique"] > 1]
chk("T6 discordant groups", len(disc), 24)
chk("T6 multi-graded groups", len(multi), 2791)
chk("T6 noise floor", round(len(disc) / len(multi), 4), 0.0086)

# ---------------------------------------------------------------- T19 F18
print("\n[T19] F18 scoring defect  (lines 242-252)")
T19 = {("gemma-4-31B-it", "A"): (0.171, 17), ("gemma-4-31B-it", "B"): (0.000, 0),
       ("gemma-4-31B-it", "C"): (0.244, 12), ("gpt-oss-120b", "A"): (0.164, 8),
       ("gpt-oss-120b", "B"): (0.066, 2), ("gpt-oss-120b", "C"): (0.216, 5),
       ("Llama-3.3-70B-Instruct", "A"): (0.058, 4),
       ("Llama-3.3-70B-Instruct", "B"): (0.004, 0),
       ("Llama-3.3-70B-Instruct", "C"): (0.457, 6)}
for (a, arm), (mr, uc) in T19.items():
    w = tr[(tr.actor_model == a) & (tr.arm == arm) & tr.graded & (tr.first_pass_correct == 0)]
    chk(f"T19 {a}/{arm} mismatch", round(w.f18_mismatch.mean(), 3), mr)
    chk(f"T19 {a}/{arm} undercredit", int(w.f18_under_credited.sum()), uc)
wfp = tr[tr.graded & (tr.first_pass_correct == 0) & tr.arm.isin(["A", "B", "C"])]
chk("T19 total mismatched (fpw)", int(wfp.f18_mismatch.sum()), 409)
chk("T19 total under-credited", int(wfp.f18_under_credited.sum()), 54)

# ---------------------------------------------------------------- T24 scale
print("\n[T24] scale  (lines ~300)")
chk("T24 evaluator gradings", len(ec), 17486)
chk("T24 trajectories", len(tr), 11600)

# ---------------------------------------------------------------- T9 / F13
print("\n[T9] Arm B planner shape / F13 signature  (lines 121-128)")
# NOTE: FINDING-22's table quotes 4,072 chars / 178.1 ch/s for gpt-oss Arm A and
# 3.28 for Arm B. Those predate the freeze. The canonical FINAL_TABLES_OUTPUT.txt
# values below are the ones this artifact must match (SOURCE_OF_TRUTH.md).
T9 = {("gemma-4-31B-it", "A"): (3608, 2490, 188.61, 0.001),
      ("gemma-4-31B-it", "B"): (3132, 1876, 149.89, 0.011),
      ("gpt-oss-120b", "A"): (4022, 4824, 195.16, 0.002),
      ("gpt-oss-120b", "B"): (3330, 37, 2.85, 0.804),
      ("Llama-3.3-70B-Instruct", "A"): (1981, 2149, 97.78, 0.000),
      ("Llama-3.3-70B-Instruct", "B"): (1774, 1892, 93.15, 0.034)}
for (a, arm), (n, ch, cs, f5) in T9.items():
    p = rm[(rm.actor_model == a) & (rm.arm == arm) & (rm.role == "planner")]
    ok = p[p.latency_s > 0]
    chk(f"T9 {a}/{arm} n", len(p), n)
    chk(f"T9 {a}/{arm} med chars", int(p.n_chars.median()), ch)
    chk(f"T9 {a}/{arm} med ch/s", round(float(ok.chars_per_sec.median()), 2), cs, tol=6e-3)
    chk(f"T9 {a}/{arm} frac<500ch", float(f"{(p.n_chars < 500).mean():.3f}"), f5)
sub100 = rm[(rm.actor_model == "gpt-oss-120b") & (rm.arm == "B")
            & (rm.role == "planner") & (rm.n_chars < 100)]
chk("T9 gpt-oss/B planner <100 chars", len(sub100), 2302)
chk("T9 ... of which fallback-flagged", int(sub100.used_reasoning_fallback.sum()), 0)

print("\n[T26] F13 low-ch/s rate over all role messages  (lines 352-357)")
T26 = {("gemma-4-31B-it", "A"): (10824, 0.004), ("gemma-4-31B-it", "B"): (9396, 0.001),
       ("gpt-oss-120b", "A"): (12064, 0.077), ("gpt-oss-120b", "B"): (9986, 0.757),
       ("Llama-3.3-70B-Instruct", "A"): (5940, 0.003),
       ("Llama-3.3-70B-Instruct", "B"): (5314, 0.005)}
for (a, arm), (nmsg, low) in T26.items():
    m = rm[(rm.actor_model == a) & (rm.arm == arm) & (rm.latency_s > 0)]
    chk(f"T26 {a}/{arm} msgs", len(m), nmsg)
    chk(f"T26 {a}/{arm} low ch/s", float(f"{(m.chars_per_sec < 10).mean():.3f}"), low)

print("\n" + "=" * 70)
if fails:
    print(f"FAILED {len(fails)}/{checks}")
    for f in fails:
        print("  " + f)
    raise SystemExit(1)
print(f"ALL {checks} CHECKS PASSED — artifact reproduces FINAL_TABLES.py")
