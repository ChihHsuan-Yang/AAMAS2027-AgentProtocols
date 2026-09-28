"""R13: Three sizing options with wall-clock from REAL observed throughput.

Use MEAN wall time, not median: a batch's completion time is governed by total
work, and PER's distribution is heavily right-skewed (omnimath2/gemma mean 514s
vs median 118s). Using medians would understate by ~4x.
"""
import os
import numpy as np, pandas as pd, pyarrow.parquet as pq

REL = "/Users/bellayang/Documents/note/projects/IEEE-BigData-SciAgentTrace/analysis/hf_cache/release"
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/results"
pd.set_option("display.width", 240)

C = pd.read_parquet(OUT + "/r9_budget.parquet")
t = pq.read_table(REL + "/data/trajectories/part-00000.parquet",
                  columns=["trajectory_uid", "protocol_id", "benchmark_id",
                           "actor_model_id", "wall_time_seconds"]).to_pandas()
per = t[t.protocol_id == "per"].merge(C[["trajectory_uid", "actor_calls", "eval_calls"]],
                                      on="trajectory_uid", how="inner")
per = per[per.wall_time_seconds.notna()]
ACT = ["gpt_oss_120b", "gemma_4_31b"]
TPM = {"omnimath2": 1270, "labbench": 1014, "jeebench": 643}

stats = per.groupby(["benchmark_id", "actor_model_id"]).agg(
    mean_wall=("wall_time_seconds", "mean"),
    mean_calls=("actor_calls", "mean"),
    mean_eval=("eval_calls", "mean")).reset_index()
print("=== per-trajectory means from real logs (used for sizing) ===")
print(stats.round(1).to_string(index=False))

def cost(n, doms, arms=3, actors=ACT):
    calls = tokens = sec = traj = 0
    for d in doms:
        for a in actors:
            row = stats[(stats.benchmark_id == d) & (stats.actor_model_id == a)]
            if row.empty: continue
            mw, mc, me = row.mean_wall.iat[0], row.mean_calls.iat[0], row.mean_eval.iat[0]
            traj += n * arms
            calls += n * arms * (mc + me)
            tokens += n * arms * mc * TPM[d]
            sec += n * arms * mw
    return traj, calls, tokens, sec

print("\n" + "="*94)
print("THREE OPTIONS — 3 arms (A soft / B generic / C hard), 2 actors")
print("="*94)
OPTS = [("1. SMOKE TEST", 25, ["omnimath2"]),
        ("2. MIN DEFENSIBLE", 400, ["omnimath2", "labbench"]),
        ("3. STRONGER", 800, ["omnimath2", "labbench"])]
for name, n, doms in OPTS:
    traj, calls, tok, sec = cost(n, doms)
    print(f"\n{name}: n={n}/cell, domains={doms}")
    print(f"   trajectories {traj:6,}   calls {calls:9,.0f}   tokens {tok/1e6:7.1f}M")
    for conc in [16, 32, 64]:
        print(f"     concurrency {conc:3d} -> {sec/conc/3600:6.1f} h wall-clock")

print("\n" + "="*94)
print("POWER at each size (paired McNemar, from observed discordance)")
print("="*94)
r = np.random.default_rng(0)
def power(n, p_disc, asym, nsim=4000):
    hits = 0
    for _ in range(nsim):
        d = r.binomial(n, p_disc)
        if d == 0: continue
        a = r.binomial(d, 0.5 + asym / 2)
        if abs((a - d / 2) / np.sqrt(d / 4)) > 1.96: hits += 1
    return hits / nsim
for n in [25, 400, 800]:
    print(f"  n={n:4d}  large(.20,.40)={power(n,.20,.40):.2f}  "
          f"moderate(.15,.25)={power(n,.15,.25):.2f}  small(.15,.15)={power(n,.15,.15):.2f}")

print("\n" + "="*94)
print("KEY COMPARISON Bella asked for: n=200 pilot-then-rerun vs n=400-800 once")
print("="*94)
t2, c2, k2, s2 = cost(200, ["omnimath2", "labbench"])
t4, c4, k4, s4 = cost(400, ["omnimath2", "labbench"])
t8, c8, k8, s8 = cost(800, ["omnimath2", "labbench"])
print(f"  n=200 then n=400 rerun: {c2+c4:9,.0f} calls, {(s2+s4)/32/3600:5.1f} h @conc32, power(moderate) {power(400,.15,.25):.2f}")
print(f"  n=400 once            : {c4:9,.0f} calls, {s4/32/3600:5.1f} h @conc32, power(moderate) {power(400,.15,.25):.2f}")
print(f"  n=800 once            : {c8:9,.0f} calls, {s8/32/3600:5.1f} h @conc32, power(moderate) {power(800,.15,.25):.2f}")
print("\n  -> A 200-pilot adds cost and buys no power the 400 run does not already have.")
print("     Go straight to the larger run after a 25-trajectory smoke test.")
