"""D5: Is argmax-confidence better than picking a random agent?

Baselines at each turn (over the gradable candidates present):
  random     = mean correctness across agents == E[accuracy of uniform pick]
  argmax     = correctness of the highest-confidence agent (what the system does)
  majority   = plurality answer (ties -> none)
  oracle     = max correctness (upper bound; mechanically inflated, reported as ceiling)
Paired bootstrap over turns, clustered by trajectory.
"""
import os
import numpy as np, pandas as pd

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/results"
pd.set_option("display.width", 250)

q = pd.read_parquet(OUT + "/d4_graded_polls.parquet")
rows = []
for (tid, rnd, turn), g in q.groupby(["trajectory_uid", "round_index", "turn"]):
    if len(g) < 2: continue
    gold = g.gold_set.iloc[0]
    vc = g.cand_set.value_counts()
    maj = vc.index[0] if len(vc) and vc.iloc[0] > 1 else None
    mx = g.score.max()
    tied = g[g.score == mx]
    rows.append(dict(
        trajectory_uid=tid, benchmark_id=g.benchmark_id.iloc[0], actor=g.actor_model_id.iloc[0],
        n_agents=len(g), n_distinct=g.cand_set.nunique(),
        random=g.correct.mean(),                      # expected accuracy of a uniform pick
        argmax=tied.correct.mean(),                   # expected accuracy under tie-break-at-random
        majority=(int(maj == gold) if maj is not None else np.nan),
        oracle=g.correct.max(),
        conf_spread=g.score.max() - g.score.min(),
        max_conf=mx,
        n_tied_at_max=len(tied),
        any_parse_fail=int((g.parse_succeeded != True).any()),
    ))
s = pd.DataFrame(rows)
print("turns:", len(s), "| trajectories:", s.trajectory_uid.nunique())

def clustered_boot(df, cols, n=4000, seed=0):
    r = np.random.default_rng(seed)
    cl = df.trajectory_uid.values
    uniq = pd.unique(cl)
    idx = {u: np.where(cl == u)[0] for u in uniq}
    out = {c: [] for c in cols}
    for _ in range(n):
        pick = r.choice(uniq, len(uniq), replace=True)
        sel = np.concatenate([idx[u] for u in pick])
        d = df.iloc[sel]
        for c in cols:
            out[c].append(d[c].mean())
    return {c: (np.mean(out[c]), *np.percentile(out[c], [2.5, 97.5])) for c in cols}

def report(df, label):
    cols = ["random", "argmax", "majority", "oracle"]
    d = df.copy()
    ci = clustered_boot(d.assign(majority=d.majority.fillna(d.random)), cols)
    print(f"\n--- {label} (n_turns={len(d)}, n_traj={d.trajectory_uid.nunique()}) ---")
    for c in cols:
        m, lo, hi = ci[c]
        print(f"  {c:9s} {m:.4f}  [{lo:.4f}, {hi:.4f}]")
    # paired delta argmax - random
    dd = (d.argmax - d.random)
    dci = clustered_boot(d.assign(delta=dd), ["delta"])["delta"]
    print(f"  argmax - random  = {dci[0]:+.4f}  [{dci[1]:+.4f}, {dci[2]:+.4f}]")
    dm = (d.majority.fillna(d.random) - d.argmax)
    mci = clustered_boot(d.assign(dm=dm), ["dm"])["dm"]
    print(f"  majority - argmax = {mci[0]:+.4f}  [{mci[1]:+.4f}, {mci[2]:+.4f}]")

report(s, "ALL turns")
report(s[s.n_distinct > 1], "DISAGREEMENT turns (n_distinct>1)")
report(s[s.n_distinct == 1], "CONSENSUS turns (n_distinct==1)")

print("\n=== by benchmark, disagreement turns only ===")
for bm, g in s[s.n_distinct > 1].groupby("benchmark_id"):
    if len(g) < 150: continue
    report(g, f"disagreement / {bm}")

print("\n=== confidence spread: does a bigger gap mean a better pick? ===")
d = s[s.n_distinct > 1].copy()
d["spread_b"] = pd.cut(d.conf_spread, [-1, 0, 5, 10, 20, 100])
print(d.groupby("spread_b", observed=True)[["argmax", "random", "oracle"]].agg(["mean"]).round(4).to_string())
print(d.groupby("spread_b", observed=True).size().to_string())

s.to_parquet(OUT + "/d5_selection.parquet", index=False)
