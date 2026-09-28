#!/usr/bin/env python3
"""Generate throughput_ledger.md strictly from measured JSON artifacts."""
import json, os, glob, datetime
D = os.path.dirname(os.path.abspath(__file__))

def verdict(r):
    if r.get("level_exception"):
        return "FAILED"
    er = r.get("error_rate", 0)
    if er > 0.20:
        return "FAILED"
    if r.get("stop_reason"):
        return "DEGRADED"
    if er > 0.05:
        return "DEGRADED"
    return "STABLE"

def fmt(v, s="%s"):
    return "n/a" if v is None else (s % v)

lines = []
lines.append("# ALCF Sophia vLLM — measured throughput ledger")
lines.append("")
lines.append("Endpoint: `https://inference-api.alcf.anl.gov/resource_server/sophia/vllm/v1`")
lines.append("")
lines.append("Measured %s (local, America/Chicago) by the AAMAS-2027 infrastructure worker."
             % datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
lines.append("Every row below comes from requests actually issued against the live endpoint. "
             "Protocol per row: 30 requests, distinct olympiad-style math prompts, "
             "`max_tokens=512`, `temperature=0`, at most 1 retry per request on a transient error "
             "(429/503/timeout/connection).")
lines.append("")
lines.append("## Ladder results")
lines.append("")
lines.append("| model | concurrency | throughput (req/min) | mean latency (s) | p90 (s) | error rate | retry rate | out tok/s | verdict |")
lines.append("|---|---|---|---|---|---|---|---|---|")

ladders = {}
for p in sorted(glob.glob(os.path.join(D, "ladder_*.json"))):
    key = os.path.basename(p)[len("ladder_"):-len(".json")]
    ladders[key] = json.load(open(p))
    for r in ladders[key]:
        if r.get("level_exception"):
            lines.append("| `%s` | %d | — | — | — | — | — | — | FAILED (%s) |" % (
                key, r["concurrency"], r["level_exception"][:60]))
            continue
        lines.append("| `%s` | %d | %s | %s | %s | %s | %s | %s | %s |" % (
            key, r["concurrency"],
            fmt(r.get("throughput_req_per_min"), "%.2f"),
            fmt(r.get("mean_latency_s"), "%.2f"),
            fmt(r.get("p90_latency_s"), "%.2f"),
            "%.1f%%" % (r.get("error_rate", 0) * 100),
            "%.1f%%" % (r.get("retry_rate", 0) * 100),
            fmt(r.get("out_tok_per_s"), "%.0f"),
            verdict(r)))
lines.append("")

# error breakdown
lines.append("### Error / retry detail")
lines.append("")
lines.append("| model | concurrency | failed reqs | errors by type | transient events (incl. retried-then-succeeded) |")
lines.append("|---|---|---|---|---|")
for key, rows in ladders.items():
    for r in rows:
        if r.get("level_exception"):
            continue
        eb = r.get("errors_by_type") or {}
        tb = r.get("transient_events_by_type") or {}
        lines.append("| `%s` | %d | %d | %s | %s |" % (
            key, r["concurrency"], r.get("failed", 0),
            (", ".join("%s=%d" % kv for kv in sorted(eb.items())) or "none"),
            (", ".join("%s=%d" % kv for kv in sorted(tb.items())) or "none")))
lines.append("")

# unavailable models
lines.append("## Endpoints that could not be measured")
lines.append("")
lines.append("| model | observed | evidence |")
lines.append("|---|---|---|")
for name, f in (("google/gemma-3-27b-it", "gemma3_probe.jsonl"),
                ("meta-llama/Llama-3.3-70B-Instruct", "llama70b_probe.jsonl")):
    p = os.path.join(D, f)
    if not os.path.exists(p):
        continue
    recs = [json.loads(l) for l in open(p) if l.strip()]
    codes = {}
    for r in recs:
        codes[str(r.get("status"))] = codes.get(str(r.get("status")), 0) + 1
    span = ""
    if recs:
        span = "%s → %s UTC" % (recs[0]["utc"][11:19], recs[-1]["utc"][11:19])
    lines.append("| `%s` | %s | %d probes over %s, statuses: %s |" % (
        name,
        "never became ready" if all(r.get("status") != 200 for r in recs) else "became ready",
        len(recs), span,
        ", ".join("%s×%d" % (k, v) for k, v in sorted(codes.items()))))
lines.append("")

# determinism
dp = os.path.join(D, "determinism.json")
if os.path.exists(dp):
    det = json.load(open(dp))
    lines.append("## Resumability / determinism at `temperature=0`")
    lines.append("")
    lines.append("Same request issued 3× per (model, prompt); SHA-256 of the returned message content compared.")
    lines.append("")
    lines.append("| model | prompt | successful reps | distinct outputs | byte-identical? |")
    lines.append("|---|---|---|---|---|")
    for r in det:
        lines.append("| `%s` | %s | %d/3 | %d | %s |" % (
            r["model"], r["prompt"][:46], r["n_ok"], r["distinct_hashes"],
            "YES" if r["identical"] else "**NO**"))
    lines.append("")

open(os.path.join(D, "throughput_ledger.md"), "w").write("\n".join(lines) + "\n")
print("wrote throughput_ledger.md (%d lines)" % len(lines))
