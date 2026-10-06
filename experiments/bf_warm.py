#!/usr/bin/env python3
"""bf_warm -- wait until a model on the inference endpoint answers, before a run.

Cold models (Llama-3.3-70B-Instruct on this endpoint) return
"503 ... online but not ready" for 15-30 minutes after the first request. The
runner records that as model_unavailable and skips the rest of the pass, and
run_bf.sh retries only 4 times over about 20 minutes. Warming the model first
keeps a slow start from ending the run.

One tiny request (max_tokens 8) every --every seconds until a 200 or until
--minutes have passed. The bearer token is never printed or written.
Exit 0 when the model answered, 1 otherwise. Zero rows are written anywhere.

Usage: python3 experiments/bf_warm.py meta-llama/Llama-3.3-70B-Instruct [--minutes 90]
"""
import argparse
import os
import sys
import time
from datetime import datetime

import httpx

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from runner import BASE_URL  # noqa: E402  same endpoint the run uses


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("--minutes", type=float, default=90)
    ap.add_argument("--every", type=float, default=60)
    a = ap.parse_args()
    sys.path.insert(0, os.environ.get("AAMAS_AUTH_SCRIPT_DIR", ""))
    import inference_auth_token  # noqa: PLC0415
    deadline = time.time() + a.minutes * 60
    i = 0
    while True:
        i += 1
        tok = inference_auth_token.get_access_token()
        t0 = time.time()
        try:
            r = httpx.post(BASE_URL + "/chat/completions",
                           headers={"Authorization": "Bearer " + tok},
                           json={"model": a.model, "max_tokens": 8, "temperature": 0,
                                 "messages": [{"role": "user", "content": "What is 2+2? Answer with the number."}]},
                           timeout=120)
            status = r.status_code
            note = "" if status == 200 else r.text[:160].replace(tok, "<token>")
        except Exception as exc:  # noqa: BLE001
            status, note = "EXC", type(exc).__name__
        print("[bf_warm] {} probe {} {} {:.1f}s {}".format(
            datetime.now().strftime("%F %T"), i, status, time.time() - t0, note), flush=True)
        if status == 200:
            print("[bf_warm] {} is ready".format(a.model), flush=True)
            return 0
        if time.time() > deadline:
            print("[bf_warm] {} NOT ready after {:.0f} min".format(a.model, a.minutes), flush=True)
            return 1
        time.sleep(a.every)


if __name__ == "__main__":
    sys.exit(main())
