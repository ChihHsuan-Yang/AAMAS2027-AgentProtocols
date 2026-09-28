#!/usr/bin/env python3
"""Task 5: are temperature=0 outputs byte-identical across repeats?
Tests both a fresh-connection repeat and a back-to-back repeat."""
import sys, os, json, hashlib, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import endpoint_lib as E

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "determinism.json")
PROMPTS = [
    "Find the remainder when 7^2025 is divided by 13.",
    "In triangle ABC, AB=13, BC=14, CA=15. Find the area.",
]
REPEATS = 3
rows = []
for pr in PROMPTS:
    for key, mid in E.MODELS.items():
        outs = []
        for i in range(REPEATS):
            r = E.one_request(mid, pr, max_tokens=512, temperature=0.0)
            h = hashlib.sha256((r.get("content") or "").encode()).hexdigest()[:16]
            outs.append({"rep": i, "ok": r.get("ok"), "status": r.get("status"),
                         "error_type": r.get("error_type"),
                         "sha256_16": h, "len": len(r.get("content") or ""),
                         "completion_tokens": r.get("usage", {}).get("completion_tokens"),
                         "latency_s": r["latency_s"],
                         "head": (r.get("content") or "")[:100]})
            time.sleep(1)
        hs = [o["sha256_16"] for o in outs if o["ok"]]
        rows.append({"model": mid, "prompt": pr,
                     "n_ok": len(hs),
                     "identical": (len(set(hs)) == 1 and len(hs) == REPEATS),
                     "distinct_hashes": len(set(hs)),
                     "reps": outs})
        st = rows[-1]
        print("%-36s ok=%d distinct_hashes=%d identical=%s lens=%s" % (
            mid, st["n_ok"], st["distinct_hashes"], st["identical"],
            [o["len"] for o in outs]), flush=True)
with open(OUT, "w") as f:
    json.dump(rows, f, indent=2)
print("DETERMINISM_DONE", flush=True)
