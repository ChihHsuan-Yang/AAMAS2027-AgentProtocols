#!/usr/bin/env python3
"""Validate the v1.1.0 SciBench tables against the campaign's reported numbers.

Expected values are transcribed from notes/XDOMAIN-RESULTS.md and
notes/XDOMAIN-INTEGRATION-DECISION.md (the Master Agent's own re-derivation
from the frozen file), NOT recomputed here from prose.

Where this validator DISAGREES with a note, the disagreement is the finding and
is listed in the card's defects section rather than silently reconciled.

Exits nonzero on any mismatch.
"""
import os, collections
import pandas as pd
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data", "scibench")

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
    print(f"  {'ok ' if ok else 'FAIL'} {label:<50} got={got!r:<20} want={want!r}")


print("[integrity]")
chk("trajectory rows", len(tr), 2296)
chk("trajectory_key unique", tr.trajectory_key.nunique(), 2296)
chk("distinct problems", tr.problem_uid.nunique(), 574)
chk("calls match submissions", int(tr.submissions.sum()), len(ec))
chk("every call key in traj", int(ec.trajectory_key.isin(set(tr.trajectory_key)).all()), 1)
chk("every msg key in traj", int(rm.trajectory_key.isin(set(tr.trajectory_key)).all()), 1)
chk("one benchmark_id", tr.benchmark_id.nunique(), 1)
chk("benchmark_id value", tr.benchmark_id.iloc[0], "scibench")
chk("one domain", tr.domain.iloc[0], "science")
chk("no Arm C", int(tr.arm.isin(["A", "B"]).all()), 1)
chk("one config_version", tr.config_version.nunique(), 1)
chk("config_version value", tr.config_version.iloc[0], "aed89f28ab338bdb")

print("\n[census] all four cells exactly 574  (XDOMAIN-RESULTS 'Run quality')")
for a in ("gemma-4-31B-it", "gpt-oss-120b"):
    for arm in ("A", "B"):
        chk(f"cell {a}/{arm}", len(tr[(tr.actor_model == a) & (tr.arm == arm)]), 574)
chk("trajectory-level failures", int(tr.hard_failure.notna().sum()), 0)
chk("unjudged (no first verdict)", int((~tr.graded).sum()), 0)

print("\n[Q1] first-pass accuracy  (XDOMAIN-RESULTS Q1)")
Q1 = {("gemma-4-31B-it", "A"): 0.794, ("gemma-4-31B-it", "B"): 0.794,
      ("gpt-oss-120b", "A"): 0.784, ("gpt-oss-120b", "B"): 0.789}
for (a, arm), v in Q1.items():
    s = tr[(tr.actor_model == a) & (tr.arm == arm) & tr.graded]
    chk(f"Q1 {a}/{arm} firstpass", round(float(s.first_pass_correct.mean()), 3), v)

print("\n[Q2] paired recovery on problems first-pass-wrong under BOTH arms")
Q2 = {"gemma-4-31B-it": (99, 0.2121, 0.0202, 21, 2, 6.6e-05),
      "gpt-oss-120b":  (96, 0.2188, 0.1354, 17, 9, 0.169)}
for a, (n_both, recA, recB, aonly, bonly, pexp) in Q2.items():
    s = tr[tr.actor_model == a]
    w = s.pivot_table(index="problem_uid", columns="arm",
                      values=["first_pass_correct", "final_correct_prereg", "graded"],
                      aggfunc="first")
    both = w[(w[("graded", "A")] == 1) & (w[("graded", "B")] == 1)
             & (w[("first_pass_correct", "A")] == 0) & (w[("first_pass_correct", "B")] == 0)]
    fa, fb = both[("final_correct_prereg", "A")], both[("final_correct_prereg", "B")]
    ao = int(((fa == 1) & (fb == 0)).sum()); bo = int(((fb == 1) & (fa == 0)).sum())
    chk(f"Q2 {a} n_both", len(both), n_both)
    chk(f"Q2 {a} recovery A", round(float(fa.mean()), 4), recA)
    chk(f"Q2 {a} recovery B", round(float(fb.mean()), 4), recB)
    chk(f"Q2 {a} A-only", ao, aonly)
    chk(f"Q2 {a} B-only", bo, bonly)
    p = stats.binomtest(bo, ao + bo, 0.5).pvalue
    chk(f"Q2 {a} exact McNemar p", float(f"{p:.3g}"), pexp, tol=max(pexp * 0.02, 1e-7))

print("\n[Q3] mechanism on first-pass-wrong  (XDOMAIN-RESULTS Q3)")
Q3 = {("gemma-4-31B-it", "A"): (118, 5.36, 1.97, 0.042, 0.076),
      ("gemma-4-31B-it", "B"): (118, 5.84, 5.84, 1.000, 0.932),
      ("gpt-oss-120b", "A"):   (124, 5.22, 2.69, 0.024, 0.008),
      ("gpt-oss-120b", "B"):   (121, 5.33, 5.20, 0.909, 0.355)}
for (a, arm), (n, cyc, sub, nref, frz) in Q3.items():
    w = tr[(tr.actor_model == a) & (tr.arm == arm) & tr.graded & (tr.first_pass_correct == 0)]
    chk(f"Q3 {a}/{arm} n_fpw", len(w), n)
    chk(f"Q3 {a}/{arm} cycles", round(float(w.cycles.mean()), 2), cyc, tol=6e-3)
    chk(f"Q3 {a}/{arm} submissions", round(float(w.submissions.mean()), 2), sub, tol=6e-3)
    chk(f"Q3 {a}/{arm} never_refuse",
        round(float(w.reviewer_never_declines.dropna().mean()), 3), nref)
    chk(f"Q3 {a}/{arm} frozen", round(float(w.frozen_answer.mean()), 3), frz)

print("\n[Q4] functional collapse  (XDOMAIN-RESULTS Q4)")
Q4 = {("gemma-4-31B-it", "A"): 0.000, ("gemma-4-31B-it", "B"): 0.998,
      ("gpt-oss-120b", "A"): 0.347, ("gpt-oss-120b", "B"): 0.990}
for (a, arm), v in Q4.items():
    s = tr[(tr.actor_model == a) & (tr.arm == arm)]
    chk(f"Q4 collapse {a}/{arm}", round(float(s.functional_collapse.dropna().mean()), 3), v)

print("\n[noise floor] grader disagreement on byte-identical candidates")
sub = ec[ec.candidate_raw.notna() & ec.verdict.notna()]
g = sub.groupby(["problem_uid", "candidate_raw"]).verdict.agg(["nunique", "size"])
multi = g[g["size"] >= 2]; disc = multi[multi["nunique"] > 1]
chk("noise: discordant groups", len(disc), 19)
chk("noise: multi-graded groups", len(multi), 678)
chk("noise floor (exact bytes)", round(len(disc) / len(multi), 4), 0.0280)

print("\n[F18] scoring defect, SciBench  (re-derived; see card)")
F18 = {("gemma-4-31B-it", "A"): (0.288, 2), ("gemma-4-31B-it", "B"): (0.000, 0),
       ("gpt-oss-120b", "A"): (0.105, 0), ("gpt-oss-120b", "B"): (0.017, 0)}
for (a, arm), (mr, uc) in F18.items():
    w = tr[(tr.actor_model == a) & (tr.arm == arm) & tr.graded & (tr.first_pass_correct == 0)]
    chk(f"F18 {a}/{arm} mismatch", round(float(w.f18_mismatch.mean()), 3), mr)
    chk(f"F18 {a}/{arm} undercredit", int(w.f18_under_credited.sum()), uc)
wfp = tr[tr.graded & (tr.first_pass_correct == 0)]
chk("F18 total mismatched (fpw)", int(wfp.f18_mismatch.sum()), 49)
chk("F18 total under-credited", int(wfp.f18_under_credited.sum()), 2)

print("\n" + "=" * 70)
if fails:
    print(f"FAILED {len(fails)}/{checks}")
    for f in fails:
        print("  " + f)
    raise SystemExit(1)
print(f"ALL {checks} CHECKS PASSED — SciBench tables reproduce the campaign")
