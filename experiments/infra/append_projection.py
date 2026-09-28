#!/usr/bin/env python3
"""Append the campaign projection (task 4) to throughput_ledger.md from projection.json."""
import json, os
D = os.path.dirname(os.path.abspath(__file__))
pj = json.load(open(os.path.join(D, "projection.json")))
L = []
L.append("## Campaign projection (task 4)")
L.append("")
a = pj["assumptions"]
L.append("Campaign shape: **%d arms x %d actors x N problems**, %.1f actor calls + %.1f evaluator "
         "calls per trajectory (historical PER logs). Arms run sequentially per actor; different "
         "actors run in parallel on separate model endpoints."
         % (a["arms"], a["actors_required_by_design"], a["actor_calls_per_traj"], a["eval_calls_per_traj"]))
L.append("")
L.append("Rates used are the measured best-stable points above. Evaluator placed on `%s`."
         % pj["evaluator_endpoint"])
L.append("")
L.append("> **Only %d of the %d actor endpoints the design calls for are live.** Scenario A is fully "
         "measured. Scenario B fills the third actor with the slowest measured rate — that row is an "
         "ASSUMPTION, not a measurement."
         % (a["measured_actor_count"], a["actors_required_by_design"]))
L.append("")
for sc in pj["scenarios"]:
    L.append("### %s" % sc["title"])
    L.append("")
    L.append("Actor rates: " + ", ".join("`%s` %.2f req/min (%s)" % (x["name"], x["tp_req_min"], x["basis"])
                                         for x in sc["actors"]))
    L.append("")
    L.append("| N | trajectories | actor calls | evaluator calls | SEQUENTIAL total (h) | PARALLEL, evaluator overlapped (h) | PARALLEL, evaluator after (h) |")
    L.append("|---|---|---|---|---|---|---|")
    for r in sc["rows"]:
        L.append("| %d | %d | %d | %d | **%.2f** | **%.2f** | %.2f |" % (
            r["N"], r["trajectories_total"], r["total_actor_calls"], r["total_eval_calls"],
            r["seq_total_hours"], r["par_overlapped_total_hours"], r["par_then_eval_hours"]))
    L.append("")
    L.append("Per-actor generation hours (the parallel makespan is the largest of these):")
    L.append("")
    for r in sc["rows"]:
        L.append("- N=%d: %s; evaluator %.2f h" % (
            r["N"], ", ".join("`%s` %.2f h" % kv for kv in r["per_actor_hours"].items()), r["eval_hours"]))
    L.append("")
L.append("**Read-out.** Even at N=400 the campaign is a matter of hours, not days: "
         "%.2f h sequential / %.2f h parallel in the fully-measured 2-actor scenario, and "
         "%.2f h / %.2f h in the 3-actor scenario. Throughput is not the binding constraint — "
         "**endpoint availability is.** Two of the four candidate models were dead for the "
         "entire measurement window."
         % (pj["scenarios"][0]["rows"][-1]["seq_total_hours"],
            pj["scenarios"][0]["rows"][-1]["par_overlapped_total_hours"],
            pj["scenarios"][1]["rows"][-1]["seq_total_hours"],
            pj["scenarios"][1]["rows"][-1]["par_overlapped_total_hours"]))
L.append("")
L.append("These projections assume the measured rate is sustained for the whole campaign and "
         "exclude client-side overhead, prompt-construction time, and any 503 outage. The 429s "
         "seen at concurrency 25 mean a real campaign should budget retry headroom.")
L.append("")
p = os.path.join(D, "throughput_ledger.md")
open(p, "a").write("\n" + "\n".join(L))
print("appended projection section")
