#!/usr/bin/env python3
"""Task 4: campaign wall-clock projection from MEASURED best-stable throughput.

Campaign shape: 3 arms x 3 actors x N problems.
Per trajectory: ~8.4 actor calls + ~1.2 evaluator calls (historical PER logs).
Arms run sequentially per actor; different actors run in parallel (separate endpoints).

IMPORTANT: only the models with a measured ladder contribute measured rates.
Any actor without a live endpoint is reported separately as an ASSUMPTION, never
as a measurement.
"""
import json, os
D = os.path.dirname(os.path.abspath(__file__))

ACTOR_CALLS = 8.4
EVAL_CALLS = 1.2
ARMS = 3
ACTORS_REQUIRED = 3

def load_best():
    best = {}
    for key in ("gpt-oss-120b", "gemma-4-31B-it", "Llama-3.3-70B-Instruct"):
        p = os.path.join(D, "ladder_%s.json" % key)
        if not os.path.exists(p):
            continue
        rows = [r for r in json.load(open(p)) if r.get("throughput_req_per_min")]
        stable = [r for r in rows if r.get("error_rate", 1) <= 0.20]
        if not stable:
            continue
        b = max(stable, key=lambda r: r["throughput_req_per_min"])
        best[key] = {"concurrency": b["concurrency"],
                     "tp_req_min": b["throughput_req_per_min"],
                     "mean_latency_s": b.get("mean_latency_s"),
                     "p90_latency_s": b.get("p90_latency_s"),
                     "error_rate": b.get("error_rate")}
    return best

def hours(calls, tp):
    return calls / tp / 60.0

def main():
    best = load_best()
    print("=" * 78)
    print("MEASURED best-stable operating points (from the ladders in this directory)")
    print("=" * 78)
    for k, v in best.items():
        print("  %-24s conc=%-3d %8.2f req/min   mean=%.2fs p90=%.2fs err=%.1f%%" % (
            k, v["concurrency"], v["tp_req_min"], v["mean_latency_s"],
            v["p90_latency_s"], v["error_rate"] * 100))
    n_meas = len(best)
    print("\n  Measured live actor endpoints: %d of the %d the campaign calls for."
          % (n_meas, ACTORS_REQUIRED))
    if n_meas < ACTORS_REQUIRED:
        print("  -> The 3rd actor has NO live endpoint and therefore NO measured rate.")
        print("     Scenario rows below mark it ASSUMED (slowest measured rate), not measured.")
    print()

    slowest = min(best.values(), key=lambda v: v["tp_req_min"])["tp_req_min"]
    fastest_key = max(best, key=lambda k: best[k]["tp_req_min"])
    ev_tp = best[fastest_key]["tp_req_min"]
    print("Evaluator placed on fastest measured endpoint: %s (%.2f req/min)" % (fastest_key, ev_tp))
    print("Per trajectory: %.1f actor calls + %.1f evaluator calls; %d arms." % (ACTOR_CALLS, EVAL_CALLS, ARMS))
    print()

    scenarios = [
        ("A. 2 measured actors only (what the endpoint supports RIGHT NOW)",
         [(k, best[k]["tp_req_min"], "measured") for k in best]),
        ("B. 3 actors, 3rd ASSUMED at slowest measured rate (%.2f req/min)" % slowest,
         [(k, best[k]["tp_req_min"], "measured") for k in best] + [("actor3_ASSUMED", slowest, "ASSUMED")]),
    ]

    out = {"best_stable_measured": best, "evaluator_endpoint": fastest_key,
           "assumptions": {"arms": ARMS, "actor_calls_per_traj": ACTOR_CALLS,
                           "eval_calls_per_traj": EVAL_CALLS,
                           "measured_actor_count": n_meas,
                           "actors_required_by_design": ACTORS_REQUIRED},
           "scenarios": []}

    for title, actors in scenarios:
        print("-" * 78)
        print(title)
        print("-" * 78)
        hdr = "%-5s | %-11s | %-10s | %-11s | %-11s | %-11s" % (
            "N", "actor calls", "eval calls", "SEQ total h", "PAR total h", "PAR(+eval) h")
        print(hdr); print("-" * len(hdr))
        srows = []
        for N in (100, 200, 400):
            traj_per_actor = ARMS * N
            acalls_per_actor = traj_per_actor * ACTOR_CALLS
            total_actor_calls = acalls_per_actor * len(actors)
            total_eval_calls = traj_per_actor * len(actors) * EVAL_CALLS

            per_actor_h = {k: hours(acalls_per_actor, tp) for k, tp, _ in actors}
            seq_actor_h = sum(per_actor_h.values())
            eval_h = hours(total_eval_calls, ev_tp)

            seq_total = seq_actor_h + eval_h          # everything one after another
            par_makespan = max(per_actor_h.values())  # actors in parallel
            par_overlapped = max(par_makespan, eval_h)  # evaluator overlaps generation
            par_then_eval = par_makespan + eval_h     # conservative: evaluator after

            print("%-5d | %-11.0f | %-10.0f | %-11.2f | %-11.2f | %-11.2f" % (
                N, total_actor_calls, total_eval_calls, seq_total, par_overlapped, par_then_eval))
            srows.append({"N": N,
                          "trajectories_total": traj_per_actor * len(actors),
                          "total_actor_calls": round(total_actor_calls),
                          "total_eval_calls": round(total_eval_calls),
                          "per_actor_hours": {k: round(v, 2) for k, v in per_actor_h.items()},
                          "seq_actor_hours": round(seq_actor_h, 2),
                          "eval_hours": round(eval_h, 2),
                          "seq_total_hours": round(seq_total, 2),
                          "par_makespan_actor_hours": round(par_makespan, 2),
                          "par_overlapped_total_hours": round(par_overlapped, 2),
                          "par_then_eval_hours": round(par_then_eval, 2)})
        print()
        for r in srows:
            print("   N=%-4d per-actor hours: %s" % (r["N"], r["per_actor_hours"]))
        print()
        out["scenarios"].append({"title": title,
                                 "actors": [{"name": k, "tp_req_min": tp, "basis": b} for k, tp, b in actors],
                                 "rows": srows})

    json.dump(out, open(os.path.join(D, "projection.json"), "w"), indent=2)
    print("wrote projection.json")

if __name__ == "__main__":
    main()
