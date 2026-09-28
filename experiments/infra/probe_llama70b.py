#!/usr/bin/env python3
"""Probe meta-llama/Llama-3.3-70B-Instruct every 3 min for up to 15 min with one tiny request.
Never writes the bearer token anywhere. Emits JSONL to llama70b_probe.jsonl."""
import sys, os, json, time, datetime
sys.path.insert(0, '/Users/bellayang/work/agent-e/mas-eval')
os.chdir('/Users/bellayang/work/agent-e/mas-eval')
from inference_auth_token import get_access_token
import requests

BASE = "https://inference-api.alcf.anl.gov/resource_server/sophia/vllm/v1"
MODEL = "meta-llama/Llama-3.3-70B-Instruct"
OUT = "/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols/experiments/infra/llama70b_probe.jsonl"

tok = get_access_token()
N = 6           # t=0,3,6,9,12,15 min
INTERVAL = 180

for i in range(N):
    ts = datetime.datetime.now(datetime.timezone.utc).isoformat()
    rec = {"probe": i, "utc": ts, "model": MODEL}
    t0 = time.time()
    try:
        r = requests.post(
            BASE + "/chat/completions",
            headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"},
            json={"model": MODEL,
                  "messages": [{"role": "user", "content": "What is 2+2? Answer with just the number."}],
                  "max_tokens": 8, "temperature": 0},
            timeout=120,
        )
        rec["elapsed_s"] = round(time.time() - t0, 3)
        rec["status"] = r.status_code
        body = r.text[:400]
        rec["body_head"] = body
        if r.status_code == 401:
            tok = get_access_token()
            rec["note"] = "refetched token"
    except Exception as e:
        rec["elapsed_s"] = round(time.time() - t0, 3)
        rec["status"] = "EXC"
        rec["body_head"] = "%s: %s" % (type(e).__name__, str(e)[:300])
    with open(OUT, "a") as f:
        f.write(json.dumps(rec) + "\n")
    print("PROBE %d t=%s status=%s elapsed=%.2fs :: %s" % (i, ts, rec["status"], rec["elapsed_s"], str(rec["body_head"])[:200]), flush=True)
    if i < N - 1:
        time.sleep(INTERVAL)
print("PROBE_DONE", flush=True)
