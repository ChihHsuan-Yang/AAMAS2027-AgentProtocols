#!/usr/bin/env python3
"""Concurrency ladder against one model. Emits JSON results + human log.
Guard rails: stop climbing if error rate > 20% or throughput drops vs prev level."""
import sys, os, json, time, statistics, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from concurrent.futures import ThreadPoolExecutor
import requests
import endpoint_lib as E

OUTDIR = os.path.dirname(os.path.abspath(__file__))
N_REQ = 30
LEVELS = [1, 4, 8, 16, 25]
PAUSE = 20  # seconds between levels, be polite to shared endpoint


def run_level(model_id, conc, n=N_REQ):
    sess = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=conc + 2, pool_maxsize=conc + 2)
    sess.mount("https://", adapter)
    prompts = [E.PROBLEMS[i % len(E.PROBLEMS)] for i in range(n)]
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=conc) as ex:
        results = list(ex.map(lambda p: E.one_request(model_id, p, session=sess), prompts))
    wall = time.time() - t0
    sess.close()

    ok = [r for r in results if r.get("ok")]
    bad = [r for r in results if not r.get("ok")]
    lats = sorted(r["latency_s"] for r in ok)
    def p(q):
        if not lats: return None
        k = min(len(lats) - 1, int(round(q * (len(lats) - 1))))
        return lats[k]
    errtypes = {}
    for r in bad:
        errtypes[r.get("error_type") or "unknown"] = errtypes.get(r.get("error_type") or "unknown", 0) + 1
    # retry accounting over ALL requests (including ones that eventually succeeded)
    retried = sum(1 for r in results if r.get("retries", 0) > 0)
    transient = {}
    for r in results:
        for ev in r.get("err_events", []):
            transient[ev["type"]] = transient.get(ev["type"], 0) + 1
    ctoks = [r["usage"].get("completion_tokens") for r in ok if r.get("usage", {}).get("completion_tokens")]

    return {
        "model": model_id, "concurrency": conc, "n_requests": n,
        "wall_s": round(wall, 2),
        "completed": len(ok), "failed": len(bad),
        "throughput_req_per_min": round(len(ok) / wall * 60, 2) if wall > 0 else None,
        "mean_latency_s": round(statistics.mean(lats), 3) if lats else None,
        "median_latency_s": round(statistics.median(lats), 3) if lats else None,
        "p90_latency_s": round(p(0.90), 3) if lats else None,
        "max_latency_s": lats[-1] if lats else None,
        "error_rate": round(len(bad) / n, 4),
        "errors_by_type": errtypes,
        "transient_events_by_type": transient,
        "retried_requests": retried,
        "retry_rate": round(retried / n, 4),
        "mean_completion_tokens": round(statistics.mean(ctoks), 1) if ctoks else None,
        "total_completion_tokens": sum(ctoks) if ctoks else 0,
        "out_tok_per_s": round(sum(ctoks) / wall, 1) if ctoks and wall > 0 else None,
        "finish_reasons": {fr: sum(1 for r in ok if r.get("finish") == fr) for fr in set(r.get("finish") for r in ok)},
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }


def main():
    key = sys.argv[1]
    model_id = E.MODELS[key]
    outp = os.path.join(OUTDIR, "ladder_%s.json" % key)
    rows = []
    prev_tp = None
    for lvl in LEVELS:
        print("=== %s conc=%d starting %s" % (key, lvl, datetime.datetime.now().strftime("%H:%M:%S")), flush=True)
        try:
            row = run_level(model_id, lvl)
        except Exception as e:
            print("LEVEL_EXC conc=%d %s: %s" % (lvl, type(e).__name__, e), flush=True)
            rows.append({"model": model_id, "concurrency": lvl, "level_exception": "%s: %s" % (type(e).__name__, e)})
            break
        rows.append(row)
        with open(outp, "w") as f:
            json.dump(rows, f, indent=2)
        print(json.dumps({k: row[k] for k in ("concurrency","wall_s","completed","failed",
              "throughput_req_per_min","mean_latency_s","p90_latency_s","error_rate",
              "retry_rate","errors_by_type","mean_completion_tokens","out_tok_per_s")}), flush=True)

        stop = None
        if row["error_rate"] > 0.20:
            stop = "error_rate %.1f%% > 20%%" % (row["error_rate"] * 100)
        elif prev_tp is not None and row["throughput_req_per_min"] is not None and row["throughput_req_per_min"] < prev_tp:
            stop = "throughput decreased %.2f -> %.2f req/min" % (prev_tp, row["throughput_req_per_min"])
        if stop:
            print("STOP_LADDER conc=%d reason: %s" % (lvl, stop), flush=True)
            rows[-1]["stop_reason"] = stop
            with open(outp, "w") as f:
                json.dump(rows, f, indent=2)
            break
        prev_tp = row["throughput_req_per_min"]
        if lvl != LEVELS[-1]:
            time.sleep(PAUSE)
    print("LADDER_DONE %s" % key, flush=True)


if __name__ == "__main__":
    main()
