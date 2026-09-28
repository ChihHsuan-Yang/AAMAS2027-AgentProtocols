"""D7: Can ANY within-turn observable pick the right agent?

d6 showed self-reported confidence carries no within-turn signal. Test the
other features a selection rule could actually use at decision time.
Vectorised paired-within-turn AUC (concordance over right/wrong pairs inside
the same turn), clustered bootstrap by trajectory.
"""
import os
import numpy as np, pandas as pd

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/results"
pd.set_option("display.width", 250)

q = pd.read_parquet(OUT + "/d4_graded_polls.parquet")
tx = pd.read_parquet(OUT + "/d2_poll_text.parquet")
q = q.merge(tx, on=["trajectory_uid", "round_index", "turn", "sender"], how="left")
q["turn_key"] = q.trajectory_uid + "|" + q.round_index.astype(str) + "|" + q.turn.astype(str)
sz = q.groupby("turn_key").size()
q = q[q.turn_key.isin(sz[sz >= 2].index)].copy()
q["reason_len"] = q.reason.fillna("").str.len()
q["intent_len"] = q.intent.fillna("").str.len()
q["has_candidate"] = q.cand_set.notna().astype(int)
q["agreement"] = q.groupby(["turn_key", "cand_set"]).cand_set.transform("size") - 1

FEATS = ["score", "agreement", "reason_len", "intent_len", "has_candidate"]

def pair_stats(df, col):
    """Per-turn (wins+0.5*ties, total) over right x wrong pairs. Vectorised."""
    out = []
    for tk, g in df.groupby("turn_key", sort=False):
        pos = g.loc[g.correct == 1, col].values
        neg = g.loc[g.correct == 0, col].values
        if not len(pos) or not len(neg):
            continue
        d = pos[:, None] - neg[None, :]
        out.append((g.trajectory_uid.iat[0], (d > 0).sum() + 0.5 * (d == 0).sum(), d.size))
    return pd.DataFrame(out, columns=["traj", "w", "n"])

def auc_ci(df, col, nboot=2000, seed=0):
    ps = pair_stats(df, col)
    if ps.empty: return np.nan, np.nan, np.nan, 0
    auc = ps.w.sum() / ps.n.sum()
    agg = ps.groupby("traj")[["w", "n"]].sum()
    W, N = agg.w.values, agg.n.values
    r = np.random.default_rng(seed)
    idx = r.integers(0, len(W), (nboot, len(W)))
    bs = W[idx].sum(1) / N[idx].sum(1)
    lo, hi = np.percentile(bs, [2.5, 97.5])
    return auc, lo, hi, int(ps.n.sum())

mixed = q.groupby("turn_key").correct.transform("nunique") == 2
qm = q[mixed]

def block(df, label):
    print(f"\n--- {label}: turns={df.turn_key.nunique()} traj={df.trajectory_uid.nunique()} ---")
    for f in FEATS:
        a, lo, hi, n = auc_ci(df, f)
        flag = "" if (lo < 0.5 < hi) else "   <-- SIGNAL"
        print(f"  {f:14s} AUC={a:.4f}  [{lo:.4f}, {hi:.4f}]  pairs={n}{flag}")

print("=== WITHIN-TURN discrimination: can the feature tell the right agent")
print("    from the wrong one, among agents facing the SAME problem? ===")
print("    AUC 0.5 = no. Only mixed-outcome turns contribute.")
block(qm, "ALL MCQ benchmarks")
block(qm[qm.benchmark_id == "labbench"], "labbench (largest, exact grader)")
block(qm[qm.benchmark_id == "jeebench"], "jeebench")
block(qm[qm.benchmark_id == "mascqa"], "mascqa")

rows = []
for bm in ["__all__", "labbench", "jeebench", "mascqa"]:
    d = qm if bm == "__all__" else qm[qm.benchmark_id == bm]
    for f in FEATS:
        a, lo, hi, n = auc_ci(d, f)
        rows.append(dict(scope=bm, feature=f, auc=a, lo=lo, hi=hi, pairs=n))
pd.DataFrame(rows).to_csv(OUT + "/d7_within_turn_auc.csv", index=False)
q.to_parquet(OUT + "/d7_polls_featured.parquet", index=False)
print("\nwrote d7_within_turn_auc.csv")
