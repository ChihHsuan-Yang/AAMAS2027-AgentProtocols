"""D11: CONFIRMATION on the held-out actor model.

Everything in d1-d10 was discovered on the pooled data, dominated by
gpt_oss_120b. gemma_4_31b is a separate actor model run on separate hardware.
Treat it as the confirmation set: re-run the two load-bearing tests WITHOUT
refitting anything.

Pre-registered predictions (stated before looking):
  P1. within-turn AUC of self-confidence is indistinguishable from 0.5
  P2. within-turn AUC of peer agreement is > 0.5
  P3. argmax-confidence minus random is indistinguishable from 0
"""
import os
import numpy as np, pandas as pd

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/results"
pd.set_option("display.width", 250)

q = pd.read_parquet(OUT + "/d7_polls_featured.parquet")

def pair_auc(df, col, seed=0, nboot=4000):
    out = []
    for tk, g in df.groupby("turn_key", sort=False):
        pos = g.loc[g.correct == 1, col].values
        neg = g.loc[g.correct == 0, col].values
        if not len(pos) or not len(neg): continue
        d = pos[:, None] - neg[None, :]
        out.append((g.trajectory_uid.iat[0], (d > 0).sum() + 0.5 * (d == 0).sum(), d.size))
    if not out: return np.nan, np.nan, np.nan, 0
    P = pd.DataFrame(out, columns=["traj", "w", "n"])
    agg = P.groupby("traj")[["w", "n"]].sum()
    W, N = agg.w.values, agg.n.values
    r = np.random.default_rng(seed)
    idx = r.integers(0, len(W), (nboot, len(W)))
    bs = W[idx].sum(1) / N[idx].sum(1)
    return P.w.sum() / P.n.sum(), *np.percentile(bs, [2.5, 97.5]), int(P.n.sum())

def sel_test(df, seed=0, nboot=4000):
    rows = []
    for tk, g in df.groupby("turn_key", sort=False):
        if g.cand_set.nunique() <= 1: continue
        rows.append(dict(traj=g.trajectory_uid.iat[0],
                         rand=g.correct.mean(),
                         conf=g.loc[g.score == g.score.max(), "correct"].mean(),
                         agree=g.loc[g.agreement == g.agreement.max(), "correct"].mean(),
                         oracle=g.correct.max()))
    T = pd.DataFrame(rows)
    if T.empty: return T, {}
    u = pd.unique(T.traj); idx = {x: np.where(T.traj.values == x)[0] for x in u}
    r = np.random.default_rng(seed)
    picks = [np.concatenate([idx[x] for x in r.choice(u, len(u))]) for _ in range(nboot)]
    ci = {}
    for c in ["rand", "conf", "agree", "oracle"]:
        b = [T.iloc[p][c].mean() for p in picks]
        ci[c] = (T[c].mean(), *np.percentile(b, [2.5, 97.5]))
    d = T.conf - T.rand
    b = [(T.iloc[p].conf - T.iloc[p].rand).mean() for p in picks]
    ci["conf_minus_rand"] = (d.mean(), *np.percentile(b, [2.5, 97.5]))
    d2 = T.agree - T.conf
    b2 = [(T.iloc[p].agree - T.iloc[p].conf).mean() for p in picks]
    ci["agree_minus_conf"] = (d2.mean(), *np.percentile(b2, [2.5, 97.5]))
    return T, ci

for actor in ["gpt_oss_120b", "gemma_4_31b"]:
    d = q[(q.actor_model_id == actor) & (q.benchmark_id == "labbench")]
    mixed = d.groupby("turn_key").correct.transform("nunique") == 2
    tag = "DISCOVERY" if actor == "gpt_oss_120b" else "HELD-OUT CONFIRMATION"
    print(f"\n{'='*78}\n{actor}  [{tag}]   polls={len(d)}  traj={d.trajectory_uid.nunique()}")
    for f in ["score", "agreement"]:
        a, lo, hi, n = pair_auc(d[mixed], f)
        verdict = "no signal" if (lo < 0.5 < hi) else "SIGNAL"
        print(f"  within-turn AUC {f:10s} = {a:.4f} [{lo:.4f}, {hi:.4f}]  pairs={n}  -> {verdict}")
    T, ci = sel_test(d)
    if ci:
        print(f"  disagreement turns: {len(T)}")
        for k in ["rand", "conf", "agree", "oracle"]:
            m, lo, hi = ci[k]; print(f"    {k:7s} {m:.4f} [{lo:.4f}, {hi:.4f}]")
        for k in ["conf_minus_rand", "agree_minus_conf"]:
            m, lo, hi = ci[k]
            v = "consistent with 0" if lo < 0 < hi else "NONZERO"
            print(f"    {k:18s} {m:+.4f} [{lo:+.4f}, {hi:+.4f}]  -> {v}")

print("\n" + "="*78)
print("PRE-REGISTERED PREDICTIONS:")
print("  P1 confidence within-turn AUC ~ 0.5 ............ check gemma row above")
print("  P2 agreement within-turn AUC  > 0.5 ............ check gemma row above")
print("  P3 argmax-conf - random ~ 0 .................... check conf_minus_rand")
