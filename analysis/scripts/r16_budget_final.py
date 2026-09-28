"""R16: FINAL budgets, re-derived at realistic concurrency and per-actor latency.

Corrections forced by the infrastructure audit:
  - conc 32-64 has NO precedent. Tested-clean: 25 workers (OSS/Sophia),
    8-10 (Gemma-4/Crux). Use 10 and 25 as the bracket.
  - Gemma-4-31B is 4-5x slower per call than gpt-oss-120b. Per-actor latency,
    not a pooled average.
  - Wall-clock is driven by the SLOWEST actor arm when arms run concurrently,
    but arms are typically run sequentially per actor -> sum of per-actor times.
"""
import os
import numpy as np, pandas as pd, pyarrow.parquet as pq

REL = "/Users/bellayang/Documents/note/projects/IEEE-BigData-SciAgentTrace/analysis/hf_cache/release"
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/results"
pd.set_option("display.width", 250)

C = pd.read_parquet(OUT + "/r9_budget.parquet")
t = pq.read_table(REL + "/data/trajectories/part-00000.parquet",
                  columns=["trajectory_uid", "protocol_id", "benchmark_id",
                           "actor_model_id", "wall_time_seconds"]).to_pandas()
per = t[t.protocol_id == "per"].merge(C[["trajectory_uid", "actor_calls", "eval_calls"]],
                                      on="trajectory_uid", how="inner")
per = per[per.wall_time_seconds.notna()]
st = per.groupby(["benchmark_id", "actor_model_id"]).agg(
    wall=("wall_time_seconds", "mean"), calls=("actor_calls", "mean"),
    ev=("eval_calls", "mean")).reset_index()
print("=== observed per-trajectory means (real logs) ===")
print(st.round(1).to_string(index=False))

TPM = {"omnimath2": 1270, "labbench": 1014}
ACTORS = ["gpt_oss_120b", "gemma_4_31b", "gemma3_27b"]

def plan(n, doms, actors, arms=3, conc=None):
    """conc: dict actor->concurrency. Returns per-actor and total."""
    rows = []
    for a in actors:
        cw = ct = cc = ce = 0
        for d in doms:
            r = st[(st.benchmark_id == d) & (st.actor_model_id == a)]
            if r.empty:                      # gemma3 has no labbench PER data
                r = st[(st.benchmark_id == d) & (st.actor_model_id == "gemma_4_31b")]
                note = "*"
            else:
                note = ""
            w, c, e = r.wall.iat[0], r.calls.iat[0], r.ev.iat[0]
            cw += n * arms * w; cc += n * arms * c; ce += n * arms * e
            ct += n * arms * c * TPM[d]
        k = conc[a]
        rows.append(dict(actor=a, traj=n*arms*len(doms), actor_calls=cc, eval_calls=ce,
                         tokens_M=ct/1e6, conc=k, hours=cw/k/3600))
    return pd.DataFrame(rows)

CONC = {"gpt_oss_120b": 25, "gemma_4_31b": 10, "gemma3_27b": 10}
print("\n" + "="*100)
print("FINAL BUDGETS — 3 arms (A/B/C), concurrency at validated levels")
print("  gpt_oss 25 workers (tested-clean); gemma family 10 (tested-clean; 25 wedged asyncio)")
print("  '*' = gemma3 labbench latency imputed from gemma_4 (no gemma3 labbench PER data exists)")
print("="*100)
for name, n, doms, actors in [
    ("SMOKE", 25, ["omnimath2"], ACTORS),
    ("MINIMUM DEFENSIBLE", 400, ["omnimath2"], ACTORS),
    ("PREFERRED", 400, ["omnimath2", "labbench"], ACTORS),
    ("STRETCH", 800, ["omnimath2", "labbench"], ACTORS)]:
    D = plan(n, doms, actors, conc=CONC)
    tot = D[["traj", "actor_calls", "eval_calls", "tokens_M", "hours"]].sum()
    print(f"\n{name}: n={n}/cell, domains={doms}, 3 arms x {len(actors)} actors")
    print(D.round(2).to_string(index=False))
    print(f"   TOTAL  traj {tot.traj:,.0f}  actor_calls {tot.actor_calls:,.0f}  "
          f"eval_calls {tot.eval_calls:,.0f}  tokens {tot.tokens_M:,.1f}M")
    print(f"   WALL-CLOCK (actors sequential): {tot.hours:,.1f} h"
          f"   |  (actors in parallel): {D.hours.max():,.1f} h")

print("\n" + "="*100)
print("POWER at each n (paired McNemar, from observed PER-vs-broadcast discordance)")
print("="*100)
r = np.random.default_rng(0)
def power(n, p, a, nsim=4000):
    h = 0
    for _ in range(nsim):
        d = r.binomial(n, p)
        if d == 0: continue
        x = r.binomial(d, 0.5 + a/2)
        if abs((x - d/2)/np.sqrt(d/4)) > 1.96: h += 1
    return h/nsim
for n in [25, 400, 800]:
    print(f"  n={n:4d}  per-cell: large {power(n,.20,.40):.2f}  moderate {power(n,.15,.25):.2f}")
print("\n  Interaction (difference of two paired differences) needs ~2x the n of a")
print("  main effect for equal power -> at n=400 the INTERACTION is powered only")
print("  for large effects. State this as a limit; do not promise moderate ones.")
