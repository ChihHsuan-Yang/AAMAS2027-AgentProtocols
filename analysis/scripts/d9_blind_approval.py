"""D9: Broadcast already contains a BLIND verifier -- the peer approval vote.

approval_* events are peer reviews of the current candidate, explicitly stamped
"Source Type: peer review/suggestion (not evaluator feedback; not system proof)".
They carry a Review Position (approve / revise / reject) and the candidate under
review. No ground truth is involved.

So: is the group's own blind approval signal informative about correctness --
i.e. is there an ORACLE-FREE verification signal already in the traces?
"""
import os, re, glob
import numpy as np, pandas as pd, pyarrow.parquet as pq

REL = "/Users/bellayang/Documents/note/projects/IEEE-BigData-SciAgentTrace/analysis/hf_cache/release"
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/results"
pd.set_option("display.width", 250)

def mcq_set(s):
    if not isinstance(s, str): return None
    x = s
    for _ in range(4):
        m = re.search(r"\\boxed\{(.*)\}", x, re.S)
        if not m: break
        x = m.group(1).strip()
    x = re.sub(r"[\\${}\s\(\)\[\].,;:]", "", x).upper()
    return "".join(sorted(set(x))) if x and re.fullmatch(r"[A-E]+", x) else None

rows = []
for f in sorted(glob.glob(REL + "/data/messages/part-*.parquet")):
    d = pq.read_table(f, columns=["trajectory_uid", "problem_uid", "round_index",
                                  "stage", "sender", "content"]).to_pandas()
    d = d[d.stage.str.match(r"^approval_\d+$", na=False)]
    if not len(d): continue
    for r in d.itertuples(index=False):
        c = r.content or ""
        pos = re.search(r"Review Position:\s*(\w+)", c)
        cand = re.search(r"Candidate under review:\s*(.+)", c)
        rows.append(dict(trajectory_uid=r.trajectory_uid, problem_uid=r.problem_uid,
                         round_index=r.round_index, stage=r.stage, sender=r.sender,
                         position=(pos.group(1).lower() if pos else None),
                         cand_set=mcq_set(cand.group(1)) if cand else None))
A = pd.DataFrame(rows)
print("approval events:", len(A), "| trajectories:", A.trajectory_uid.nunique())
print("\nreview positions:"); print(A.position.value_counts(dropna=False).to_string())

prob = pq.read_table(REL + "/data/problems/part-00000.parquet",
                     columns=["problem_uid", "benchmark_id", "answer", "answer_text"]).to_pandas()
A = A.merge(prob, on="problem_uid", how="left")
A["gold_set"] = [mcq_set(a if isinstance(a, str) and a.strip() else b)
                 for a, b in zip(A.answer, A.answer_text)]
A = A[A.benchmark_id.isin(["labbench", "jeebench", "mascqa"])]
A["correct"] = [None if (a is None or b is None) else int(a == b)
                for a, b in zip(A.cand_set, A.gold_set)]
A = A.dropna(subset=["correct", "position"]).copy()
A["correct"] = A.correct.astype(int)
print(f"\ngradable approval reviews: {len(A)}  trajectories: {A.trajectory_uid.nunique()}")

print("\n=== [1] individual blind peer review vs candidate correctness ===")
print(A.groupby("position").correct.agg(["mean", "size"]).round(4).to_string())

print("\n=== [2] aggregate over the reviewing panel per (traj, round, stage) ===")
g = A.groupby(["trajectory_uid", "round_index", "stage"]).agg(
    n_rev=("position", "size"),
    n_approve=("position", lambda s: (s == "approve").sum()),
    correct=("correct", "first"),
    benchmark_id=("benchmark_id", "first"))
g = g[g.n_rev >= 2].reset_index()
g["frac_approve"] = g.n_approve / g.n_rev
g["unanimous"] = (g.n_approve == g.n_rev).astype(int)
print(f"panels: {len(g)}")
print(g.groupby("frac_approve").correct.agg(["mean", "size"]).round(4).to_string())

print("\n=== [3] is UNANIMOUS blind approval informative? ===")
print(g.groupby("unanimous").correct.agg(["mean", "size"]).round(4).to_string())
r = np.random.default_rng(0)
u = g[g.unanimous == 1].correct.values; nu = g[g.unanimous == 0].correct.values
bs = [r.choice(u, len(u)).mean() - r.choice(nu, len(nu)).mean() for _ in range(4000)]
print(f"unanimous - split = {u.mean()-nu.mean():+.4f} "
      f"[{np.percentile(bs,2.5):+.4f}, {np.percentile(bs,97.5):+.4f}]")

print("\n=== [4] by benchmark ===")
print(g.groupby(["benchmark_id", "unanimous"]).correct.agg(["mean", "size"]).round(4).to_string())

# AUC of frac_approve
from scipy.stats import rankdata
def auc(y, x):
    pos, neg = np.asarray(x)[np.asarray(y) == 1], np.asarray(x)[np.asarray(y) == 0]
    if not len(pos) or not len(neg): return np.nan
    rr = rankdata(np.concatenate([pos, neg]))
    return (rr[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))
print(f"\nAUC(frac_approve -> correct) = {auc(g.correct, g.frac_approve):.4f}")
print("compare: within-turn confidence AUC = 0.4975 (d6)")
g.to_parquet(OUT + "/d9_approval_panels.parquet", index=False)
A.to_parquet(OUT + "/d9_approval_reviews.parquet", index=False)
