"""D10: Does peer assessment have a WITHIN-ITEM component that self-report lacks?

This is the seam in the story. d6 killed confidence because its usable variance
(within-turn, between-agent, same problem) was AUC 0.4975. d9 showed approval is
informative -- but approval panels all review ONE candidate, so correctness is
constant within a panel and d9's AUC is a BETWEEN-item quantity. Not comparable.

Test: find items where the SAME candidate answer is reviewed by peers, and vary
only which candidate. Specifically, within one trajectory+round, the approval
phase can run over successive candidate revisions. If peer approval tracks
correctness ACROSS candidates for the SAME problem, that is a within-problem
(between-candidate) signal -- the kind a selector could actually use.
"""
import os
import numpy as np, pandas as pd

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/results"
pd.set_option("display.width", 250)

A = pd.read_parquet(OUT + "/d9_approval_reviews.parquet")
A["app"] = (A.position == "approve").astype(int)

# panel = one candidate under review
pan = A.groupby(["trajectory_uid", "problem_uid", "round_index", "stage"]).agg(
    frac_approve=("app", "mean"), n_rev=("app", "size"),
    cand=("cand_set", "first"), correct=("correct", "first"),
    benchmark_id=("benchmark_id", "first")).reset_index()
pan = pan[pan.n_rev >= 2]
print(f"panels: {len(pan)}  trajectories: {pan.trajectory_uid.nunique()}")

# WITHIN-PROBLEM contrast: same problem, >=2 DISTINCT candidates reviewed,
# with differing correctness -> can peer approval rank them?
print("\n=== WITHIN-PROBLEM, BETWEEN-CANDIDATE discrimination ===")
print("(same problem_uid; >=2 distinct candidates reviewed; mixed correctness)")
rows = []
for pid, g in pan.groupby("problem_uid"):
    g = g.drop_duplicates(subset=["cand"])
    if g.cand.nunique() < 2 or g.correct.nunique() < 2:
        continue
    pos = g.loc[g.correct == 1, "frac_approve"].values
    neg = g.loc[g.correct == 0, "frac_approve"].values
    d = pos[:, None] - neg[None, :]
    rows.append(dict(problem_uid=pid, benchmark_id=g.benchmark_id.iat[0],
                     w=(d > 0).sum() + 0.5 * (d == 0).sum(), n=d.size))
R = pd.DataFrame(rows)
if len(R):
    auc = R.w.sum() / R.n.sum()
    r = np.random.default_rng(0)
    idx = r.integers(0, len(R), (4000, len(R)))
    bs = R.w.values[idx].sum(1) / R.n.values[idx].sum(1)
    lo, hi = np.percentile(bs, [2.5, 97.5])
    print(f"  problems contributing: {len(R)}   pairs: {int(R.n.sum())}")
    print(f"  AUC(peer approval -> correct, WITHIN problem) = {auc:.4f} [{lo:.4f}, {hi:.4f}]")
    print(f"  compare: self-confidence WITHIN turn = 0.4975 [.4921, .5027]")
    for bm, g in R.groupby("benchmark_id"):
        if g.n.sum() < 100: continue
        print(f"    {bm:10s} AUC={g.w.sum()/g.n.sum():.4f}  pairs={int(g.n.sum())}")
else:
    print("  no qualifying contrasts")

# Also: does approval vary at all across candidates within a problem?
print("\n=== is approval responsive to WHICH candidate, or just to the problem? ===")
multi = pan.groupby("problem_uid").filter(lambda g: g.cand.nunique() >= 2)
if len(multi):
    b = multi.groupby("problem_uid").frac_approve.mean()
    within = multi.frac_approve - multi.problem_uid.map(b)
    print(f"  problems with >=2 distinct candidates: {multi.problem_uid.nunique()}")
    print(f"  between-problem var: {b.var():.4f}   within-problem var: {within.var():.4f}")
    print(f"  within share: {within.var()/(b.var()+within.var()):.1%}")
    print("  (confidence, for comparison: within share 31.2% but AUC 0.4975 -- "
          "variance alone is not signal)")
pan.to_parquet(OUT + "/d10_panels.parquet", index=False)
