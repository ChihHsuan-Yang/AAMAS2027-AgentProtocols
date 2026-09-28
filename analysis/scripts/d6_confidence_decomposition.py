"""D6: Where does confidence carry information -- between problems, or between agents?

Broadcast selects the speaker by argmax(confidence) WITHIN a turn. All agents in
a turn face the same problem with the same context. So the only variance that
selection can exploit is the WITHIN-turn component.

Decompose:
  conf_ij = mu + a_i (turn/problem effect) + e_ij (agent deviation)
and measure the predictive value of each component separately.
"""
import os
import numpy as np, pandas as pd
from scipy.stats import rankdata

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/results"
pd.set_option("display.width", 250)

def auc(y, x):
    y, x = np.asarray(y, float), np.asarray(x, float)
    ok = ~np.isnan(x); y, x = y[ok], x[ok]
    pos, neg = x[y == 1], x[y == 0]
    if len(pos) == 0 or len(neg) == 0: return np.nan
    r = rankdata(np.concatenate([pos, neg]))
    return (r[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))

def boot_auc(y, x, cl, n=2000, seed=0):
    r = np.random.default_rng(seed)
    df = pd.DataFrame(dict(y=y, x=x, cl=cl)).dropna()
    uniq = pd.unique(df.cl); idx = {u: np.where(df.cl.values == u)[0] for u in uniq}
    out = []
    for _ in range(n):
        pick = r.choice(uniq, len(uniq), replace=True)
        d = df.iloc[np.concatenate([idx[u] for u in pick])]
        out.append(auc(d.y, d.x))
    out = np.array(out); out = out[~np.isnan(out)]
    return np.percentile(out, [2.5, 97.5])

q = pd.read_parquet(OUT + "/d4_graded_polls.parquet")
q = q[q.parse_succeeded == True].copy()
q["turn_key"] = q.trajectory_uid + "|" + q.round_index.astype(str) + "|" + q.turn.astype(str)

# keep turns with >= 2 agents so a within-component exists
sz = q.groupby("turn_key").size()
q = q[q.turn_key.isin(sz[sz >= 2].index)].copy()

g = q.groupby("turn_key")
q["conf_between"] = g.score.transform("mean")     # turn-level (problem) component
q["conf_within"] = q.score - q.conf_between       # agent deviation within the turn
q["acc_between"] = g.correct.transform("mean")

print(f"rows={len(q)}  turns={q.turn_key.nunique()}  trajectories={q.trajectory_uid.nunique()}")
print("\nvariance of confidence:")
vb, vw = q.conf_between.var(), q.conf_within.var()
print(f"  between-turn (problem): {vb:8.2f}   ({vb/(vb+vw):.1%})")
print(f"  within-turn  (agent)  : {vw:8.2f}   ({vw/(vb+vw):.1%})")

print("\n=== AUC of each component for predicting candidate correctness ===")
for name, x in [("raw confidence", q.score),
                ("BETWEEN component (turn mean conf)", q.conf_between),
                ("WITHIN component (agent dev. from turn mean)", q.conf_within)]:
    a = auc(q.correct, x); lo, hi = boot_auc(q.correct.values, x.values, q.trajectory_uid.values)
    print(f"  {name:46s} AUC={a:.4f}  [{lo:.4f}, {hi:.4f}]")

print("\n=== the within-turn component, per benchmark ===")
for bm, gg in q.groupby("benchmark_id"):
    if len(gg) < 500: continue
    a = auc(gg.correct, gg.conf_within)
    lo, hi = boot_auc(gg.correct.values, gg.conf_within.values, gg.trajectory_uid.values)
    print(f"  {bm:10s} n={len(gg):6d}  AUC_within={a:.4f} [{lo:.4f}, {hi:.4f}]")

print("\n=== within-turn confidence rank vs accuracy (ties -> average rank) ===")
q["wrank"] = q.groupby("turn_key").score.rank(ascending=False, method="min")
print(q.groupby("wrank").correct.agg(["mean", "size"]).round(4).to_string())

print("\n=== restricted to turns with a UNIQUE argmax and real spread (>=5 pts) ===")
u = q[q.groupby("turn_key").score.transform(lambda s: (s == s.max()).sum()) == 1].copy()
u = u[u.groupby("turn_key").score.transform(lambda s: s.max() - s.min()) >= 5]
u["is_top"] = (u.groupby("turn_key").score.transform("max") == u.score).astype(int)
print(f"turns={u.turn_key.nunique()}")
print(u.groupby("is_top").correct.agg(["mean", "size"]).round(4).to_string())
d = u.groupby("turn_key").apply(
    lambda g: g.loc[g.is_top == 1, "correct"].mean() - g.loc[g.is_top == 0, "correct"].mean(),
    include_groups=False)
r = np.random.default_rng(0); bs = [r.choice(d.values, len(d)).mean() for _ in range(4000)]
print(f"top-minus-rest accuracy = {d.mean():+.4f}  [{np.percentile(bs,2.5):+.4f}, {np.percentile(bs,97.5):+.4f}]")

q.to_parquet(OUT + "/d6_decomposed_polls.parquet", index=False)
