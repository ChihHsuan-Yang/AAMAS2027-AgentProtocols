"""D1: Decompose protocol gain into (a) oracle-free deliberation and (b) oracle-gated retry.

All four protocols run inside the SAME outer loop: an Evaluator that sees ground
truth and returns PASS/FAIL + a repair hint. `first_pass_correct` is the verdict
on the FIRST submission, i.e. before any oracle bit has been returned to agents.
`final_correct` is after the retry loop. The difference is oracle-driven.
"""
import os, numpy as np, pandas as pd, pyarrow.parquet as pq

REL = "/Users/bellayang/Documents/note/projects/IEEE-BigData-SciAgentTrace/analysis/hf_cache/release"
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/results"
os.makedirs(OUT, exist_ok=True)
pd.set_option("display.width", 250)

t = pq.read_table(REL + "/data/trajectories/part-00000.parquet").to_pandas()
fp = t[t.first_pass_correct.notna()].copy()
fp["first_pass_correct"] = fp.first_pass_correct.astype(int)
fp["final_correct"] = fp.final_correct.astype(int)

# ---- paired wide table on (problem, actor, evaluator, benchmark) -------------
key = ["problem_uid", "benchmark_id", "actor_model_id", "evaluator_model_id"]
w = fp.pivot_table(index=key, columns="protocol_id",
                   values=["first_pass_correct", "final_correct"], aggfunc="first")
w.columns = [f"{a}__{b}" for a, b in w.columns]
w = w.dropna()
print(f"complete paired cells (all 4 protocols, first_pass present): {len(w)}")

protos = ["baseline_llm", "single_agent", "per", "broadcast"]

def boot_ci(x, n=4000, seed=0):
    r = np.random.default_rng(seed); x = np.asarray(x, float)
    b = r.choice(x, (n, len(x)), replace=True).mean(1)
    return np.percentile(b, [2.5, 97.5])

rows = []
base_fp = w["first_pass_correct__baseline_llm"].values
for p in protos:
    a = w[f"first_pass_correct__{p}"].values
    z = w[f"final_correct__{p}"].values
    d_delib = a - base_fp          # oracle-free gain vs one-shot baseline
    d_oracle = z - a               # gain from the oracle retry loop
    rows.append(dict(
        protocol=p, n=len(w),
        first_pass=a.mean(), final=z.mean(),
        delib_gain=d_delib.mean(), delib_lo=boot_ci(d_delib)[0], delib_hi=boot_ci(d_delib)[1],
        oracle_gain=d_oracle.mean(), oracle_lo=boot_ci(d_oracle)[0], oracle_hi=boot_ci(d_oracle)[1],
        total_gain=(z - base_fp).mean(),
        frac_from_oracle=d_oracle.mean() / max((z - base_fp).mean(), 1e-9),
    ))
tot = pd.DataFrame(rows)
print("\n=== POOLED DECOMPOSITION ===")
print(tot.round(4).to_string(index=False))

# ---- per benchmark x actor --------------------------------------------------
cells = []
wr = w.reset_index()
for (bm, am), g in wr.groupby(["benchmark_id", "actor_model_id"]):
    if len(g) < 100: continue
    b0 = g["first_pass_correct__baseline_llm"].values
    for p in protos:
        a = g[f"first_pass_correct__{p}"].values
        z = g[f"final_correct__{p}"].values
        cells.append(dict(benchmark=bm, actor=am, protocol=p, n=len(g),
                          base_fp=b0.mean(), first_pass=a.mean(), final=z.mean(),
                          delib_gain=(a - b0).mean(), oracle_gain=(z - a).mean(),
                          total_gain=(z - b0).mean()))
cdf = pd.DataFrame(cells)
print("\n=== PER BENCHMARK x ACTOR ===")
print(cdf.round(4).to_string(index=False))

# ---- transition matrix: first-pass -> final --------------------------------
print("\n=== OUTCOME TRANSITIONS (first submission -> final), within protocol ===")
tr = []
for p in protos:
    a = w[f"first_pass_correct__{p}"].values.astype(int)
    z = w[f"final_correct__{p}"].values.astype(int)
    tr.append(dict(protocol=p,
                   wrong_to_right=((a == 0) & (z == 1)).mean(),
                   right_to_wrong=((a == 1) & (z == 0)).mean(),
                   right_to_right=((a == 1) & (z == 1)).mean(),
                   wrong_to_wrong=((a == 0) & (z == 0)).mean(),
                   n_wrong_start=(a == 0).sum(),
                   rescue_rate_given_wrong=(((a == 0) & (z == 1)).sum() / max((a == 0).sum(), 1))))
trdf = pd.DataFrame(tr)
print(trdf.round(4).to_string(index=False))

tot.to_csv(OUT + "/d1_pooled_decomposition.csv", index=False)
cdf.to_csv(OUT + "/d1_cell_decomposition.csv", index=False)
trdf.to_csv(OUT + "/d1_transitions.csv", index=False)
w.reset_index().to_parquet(OUT + "/d1_paired_wide.parquet")
print("\nwrote d1_* to", OUT)
