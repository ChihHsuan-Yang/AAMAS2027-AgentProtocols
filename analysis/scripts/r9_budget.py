"""R9: Endpoint budget from REAL logs.

PER logs no model_calls counter (coverage 0.000), so reconstruct actor calls
from the trace layer: every Planner/Executor/Reviewer message = one actor call.
Evaluator calls come from the evaluator events. Tokens are unavailable for PER,
so scale them from the token-bearing protocols on the same problems.
"""
import os, glob
import numpy as np, pandas as pd, pyarrow.parquet as pq

REL = "/Users/bellayang/Documents/note/projects/IEEE-BigData-SciAgentTrace/analysis/hf_cache/release"
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/results"
pd.set_option("display.width", 250)

P = pd.read_parquet(OUT + "/r1_role_messages.parquet")
traj = pq.read_table(REL + "/data/trajectories/part-00000.parquet",
                     columns=["trajectory_uid", "benchmark_id", "actor_model_id",
                              "wall_time_seconds", "event_count"]).to_pandas()
calls = P.groupby("trajectory_uid").size().rename("actor_calls").reset_index()
C = calls.merge(traj, on="trajectory_uid", how="left")

print("="*86)
print("ACTOR CALLS PER PER TRAJECTORY (reconstructed from role messages)")
print("="*86)
s = C.groupby(["benchmark_id", "actor_model_id"]).actor_calls.agg(
    n="size", mean="mean", median="median",
    p90=lambda x: np.percentile(x, 90), p99=lambda x: np.percentile(x, 99), max="max")
print(s.round(2).to_string())
print("\npooled:", C.actor_calls.agg(["mean", "median"]).round(2).to_dict(),
      "p90:", round(np.percentile(C.actor_calls, 90), 1))

# evaluator calls: PER's counter is absent; count evaluator events from messages
ev = []
for f in sorted(glob.glob(REL + "/data/messages/part-*.parquet")):
    d = pq.read_table(f, columns=["trajectory_uid", "sender", "stage"]).to_pandas()
    d = d[(d.sender == "Evaluator") & (d.stage == "evaluation")]
    if len(d): ev.append(d.groupby("trajectory_uid").size().rename("eval_calls"))
E = pd.concat(ev).groupby(level=0).sum().reset_index()
E.columns = ["trajectory_uid", "eval_calls"]
C = C.merge(E, on="trajectory_uid", how="left")
C["eval_calls"] = C.eval_calls.fillna(0)
print("\nEVALUATOR calls per PER trajectory:")
print(C.groupby("benchmark_id").eval_calls.agg(["mean", "median",
      lambda x: np.percentile(x, 90)]).rename(columns={"<lambda_0>": "p90"}).round(2).to_string())

# token scaling: PER has no tokens; use broadcast/single on the same benchmark
tk = pq.read_table(REL + "/data/trajectories/part-00000.parquet",
                   columns=["benchmark_id", "protocol_id", "actor_model_id",
                            "total_tokens", "message_count"]).to_pandas()
tk = tk[tk.total_tokens.notna() & (tk.message_count > 0)]
tk["tok_per_msg"] = tk.total_tokens / tk.message_count
print("\nTOKENS PER MESSAGE (from token-bearing protocols, same benchmarks):")
print(tk.groupby("benchmark_id").tok_per_msg.median().round(0).to_string())

tpm = tk.groupby("benchmark_id").tok_per_msg.median()
print("\n" + "="*86)
print("BUDGET: cost of ONE arm x ONE actor x N problems")
print("="*86)
for bm in ["omnimath2", "labbench", "jeebench"]:
    g = C[C.benchmark_id == bm]
    if len(g) == 0: continue
    mc, p90 = g.actor_calls.mean(), np.percentile(g.actor_calls, 90)
    ec = g.eval_calls.mean()
    t = tpm.get(bm, np.nan)
    print(f"\n  {bm}: mean {mc:.1f} actor calls (p90 {p90:.0f}) + {ec:.1f} evaluator calls")
    for n in [200, 400]:
        tot = n * (mc + ec)
        print(f"    n={n:4d} -> {tot:8,.0f} calls, ~{n*mc*t/1e6:6.1f}M actor tokens")
C.to_parquet(OUT + "/r9_budget.parquet", index=False)
