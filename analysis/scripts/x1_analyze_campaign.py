"""X1: Campaign analysis — runs the pre-registered tests on runner JSONL output.

Built BEFORE the data exists, deliberately: the tests are fixed in
notes/PREREGISTRATION.md and must not be chosen after seeing results.

Input : one or more JSONL files, one completed trajectory per line.
Output: analysis/results/x1_*.csv + a printed report.
"""
import argparse, glob, json, os, sys
import numpy as np, pandas as pd

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/results"
os.makedirs(OUT, exist_ok=True)
pd.set_option("display.width", 250)
RNG = np.random.default_rng(20261008)

def load(paths):
    rows = []
    for p in paths:
        for pat in ([p] if os.path.isfile(p) else glob.glob(p + "/**/*.jsonl", recursive=True)):
            with open(pat) as f:
                for ln in f:
                    ln = ln.strip()
                    if not ln: continue
                    try: rows.append(json.loads(ln))
                    except json.JSONDecodeError: pass
    return pd.DataFrame(rows)

def boot_paired(d, n=5000):
    d = np.asarray(d, float); d = d[~np.isnan(d)]
    if len(d) < 2: return (np.nan, np.nan, np.nan)
    b = RNG.choice(d, (n, len(d))).mean(1)
    return d.mean(), *np.percentile(b, [2.5, 97.5])

def holm(pvals, labels):
    order = np.argsort(pvals); m = len(pvals); out = {}
    prev = 0
    for rank, i in enumerate(order):
        adj = min(1.0, max(prev, (m - rank) * pvals[i])); prev = adj
        out[labels[i]] = adj
    return out

def perm_p(d, n=10000):
    """Two-sided permutation p for a paired mean difference (sign-flip)."""
    d = np.asarray(d, float); d = d[~np.isnan(d)]
    if len(d) < 2: return np.nan
    obs = abs(d.mean())
    signs = RNG.choice([-1, 1], (n, len(d)))
    return float(((np.abs((signs * d).mean(1)) >= obs).sum() + 1) / (n + 1))

def main(paths):
    df = load(paths)
    if df.empty:
        print("no trajectories found"); return
    print(f"trajectories: {len(df)}  arms: {sorted(df.arm.unique())}  "
          f"actors: {sorted(df.actor_model.unique())}")
    print("\n=== completeness (arm x actor) ===")
    print(pd.crosstab(df.arm, df.actor_model).to_string())

    # ---- fairness audit: no arm may get extra calls ------------------------
    print("\n=== FAIRNESS AUDIT (must be comparable across arms) ===")
    fa = df.groupby(["actor_model", "arm"]).agg(
        n=("problem_uid", "size"),
        actor_calls=("actor_calls", "mean"),
        eval_calls=("evaluator_calls", "mean"),
        retries=("retries", "mean")).round(2)
    print(fa.to_string())
    if df.evaluator_calls.isna().all():
        print("  !! evaluator_calls entirely null — oracle-exposure control UNVERIFIABLE")

    # ---- Arm C manipulation check -----------------------------------------
    print("\n=== ARM C MANIPULATION CHECK ===")
    c = df[df.arm == "C"]
    if len(c):
        regen = c.get("n_regenerations", pd.Series(dtype=float))
        print(f"  trajectories: {len(c)}   mean regenerations: {regen.mean():.3f}"
              f"   with >=1 rejection: {(regen > 0).mean():.3%}")
        if (regen.fillna(0) == 0).all():
            print("  !! ZERO rejections everywhere — constraint may never have bound.")
            print("     Do NOT interpret Arm C results until this is explained.")
    else:
        print("  no Arm C rows yet")

    # ---- paired wide table -------------------------------------------------
    w = df.pivot_table(index=["problem_uid", "actor_model"], columns="arm",
                       values=["correct", "p1a", "e2v2"], aggfunc="first")
    w.columns = [f"{a}__{b}" for a, b in w.columns]
    w = w.reset_index()

    res, pv, lab = [], [], []
    for actor, g in w.groupby("actor_model"):
        for metric, pretty in [("p1a", "P1 fidelity(Planner)"),
                               ("e2v2", "P2 fidelity(Executor)"),
                               ("correct", "P3 outcome")]:
            ca, cc = f"{metric}__A", f"{metric}__C"
            if ca not in w or cc not in w: continue
            d = (g[cc] - g[ca]).dropna()
            if len(d) < 2: continue
            m, lo, hi = boot_paired(d)
            p = perm_p(d)
            res.append(dict(actor=actor, test=pretty, contrast="C-A", n=len(d),
                            mean=m, lo=lo, hi=hi, p=p))
            pv.append(p); lab.append(f"{actor}|{pretty}")
    R = pd.DataFrame(res)
    if len(R):
        adj = holm(pv, lab)
        R["p_holm"] = [adj[f"{a}|{t}"] for a, t in zip(R.actor, R.test)]
        print("\n=== PRIMARY: intervention effects (C - A), per actor ===")
        print(R.round(4).to_string(index=False))
        R.to_csv(OUT + "/x1_primary.csv", index=False)

    # ---- P4: actor x intervention interaction (THE central test) ----------
    print("\n=== P4 (CENTRAL): actor x intervention interaction ===")
    inter = []
    actors = sorted(w.actor_model.unique())
    for metric, pretty in [("correct", "outcome"), ("p1a", "fidelity_planner")]:
        ca, cc = f"{metric}__A", f"{metric}__C"
        if ca not in w: continue
        eff = {a: (g[cc] - g[ca]) for a, g in w.groupby("actor_model")}
        for i in range(len(actors)):
            for j in range(i+1, len(actors)):
                ai, aj = actors[i], actors[j]
                # unpaired difference of paired differences
                di, dj = eff[ai].dropna().values, eff[aj].dropna().values
                if len(di) < 2 or len(dj) < 2: continue
                obs = di.mean() - dj.mean()
                b = [RNG.choice(di, len(di)).mean() - RNG.choice(dj, len(dj)).mean()
                     for _ in range(4000)]
                lo, hi = np.percentile(b, [2.5, 97.5])
                inter.append(dict(metric=pretty, pair=f"{ai} - {aj}",
                                  interaction=obs, lo=lo, hi=hi,
                                  crosses_zero=bool(lo < 0 < hi)))
    I = pd.DataFrame(inter)
    if len(I):
        print(I.round(4).to_string(index=False))
        I.to_csv(OUT + "/x1_interaction.csv", index=False)

    # ---- P5: does fidelity change track outcome change? -------------------
    print("\n=== P5: Delta-fidelity vs Delta-outcome (association only) ===")
    for actor, g in w.groupby("actor_model"):
        if "p1a__C" not in g or "correct__C" not in g: continue
        df_ = (g["p1a__C"] - g["p1a__A"]); do_ = (g["correct__C"] - g["correct__A"])
        ok = df_.notna() & do_.notna()
        if ok.sum() < 10: continue
        print(f"  {actor:34s} n={ok.sum():4d}  corr={np.corrcoef(df_[ok], do_[ok])[0,1]:+.3f}")
    w.to_csv(OUT + "/x1_paired_wide.csv", index=False)
    print(f"\nwrote x1_* to {OUT}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    main(ap.parse_args().paths)
