"""Shared client helpers for ALCF Sophia vLLM throughput measurement.
SECURITY: the bearer token is held in memory only. Never written to disk/logs."""
import sys, os, time, json, threading
sys.path.insert(0, '/Users/bellayang/work/agent-e/mas-eval')
_cwd = os.getcwd()
os.chdir('/Users/bellayang/work/agent-e/mas-eval')
from inference_auth_token import get_access_token
os.chdir(_cwd)
import requests

BASE = "https://inference-api.alcf.anl.gov/resource_server/sophia/vllm/v1"
MODELS = {
    "gpt-oss-120b": "openai/gpt-oss-120b",
    "gemma-4-31B-it": "google/gemma-4-31B-it",
    "Llama-3.3-70B-Instruct": "meta-llama/Llama-3.3-70B-Instruct",
}

_tok_lock = threading.Lock()
_tok = {"v": None}

def token(force=False):
    with _tok_lock:
        if _tok["v"] is None or force:
            _tok["v"] = get_access_token()
        return _tok["v"]

# 30 distinct short olympiad-style problems (distinct text => no vLLM prefix-cache inflation)
PROBLEMS = [
 "Find the remainder when 7^2025 is divided by 13.",
 "How many positive divisors does 2^4 * 3^3 * 5^2 have?",
 "Let x + 1/x = 5. Compute x^3 + 1/x^3.",
 "Find the smallest positive integer n such that n! is divisible by 1000.",
 "In triangle ABC, AB=13, BC=14, CA=15. Find the area.",
 "How many ways can 8 distinct books be split into two nonempty shelves?",
 "Compute the sum of all positive integers less than 100 that are coprime to 30.",
 "Solve for real x: sqrt(x+7) - sqrt(x) = 1.",
 "Find the number of trailing zeros in 100!.",
 "If a, b are roots of x^2 - 6x + 7 = 0, compute a^4 + b^4.",
 "Find the last two digits of 3^400.",
 "A fair coin is flipped 10 times. What is the probability of exactly 6 heads?",
 "Compute the greatest common divisor of 2^30 - 1 and 2^18 - 1.",
 "How many 4-digit numbers have digits summing to 9?",
 "Find all integer solutions to x^2 - y^2 = 91.",
 "Evaluate the sum 1/(1*2) + 1/(2*3) + ... + 1/(99*100).",
 "In how many ways can 5 identical balls go into 3 distinct boxes?",
 "Find the minimum of f(x) = x^2 + 4/x for x > 0.",
 "What is the 100th term of the arithmetic sequence 7, 11, 15, ...?",
 "Compute the number of permutations of AABBCC with no two identical letters adjacent.",
 "Find the area enclosed by |x| + |y| = 6.",
 "If log_2(x) + log_4(x) = 9, find x.",
 "How many subsets of {1,...,10} contain no two consecutive integers?",
 "Find the sum of the roots of x^3 - 7x^2 + 5x - 3 = 0.",
 "A circle of radius 5 has a chord of length 6. Find the distance from center to chord.",
 "Compute 1^2 - 2^2 + 3^2 - 4^2 + ... + 99^2 - 100^2.",
 "Find the number of ordered pairs (a,b) of positive integers with ab = 720.",
 "Determine the units digit of 7^7^7.",
 "Two dice are rolled. What is the probability the sum is a prime number?",
 "Find the largest power of 3 dividing 50!.",
]

def classify(status, exc):
    if exc is not None:
        n = type(exc).__name__
        if "Timeout" in n:
            return "timeout"
        if "Connection" in n:
            return "connection"
        return "other:" + n
    if status == 429:
        return "429"
    if status == 503:
        return "503"
    if status == 401:
        return "401"
    if status and status >= 400:
        return "http_%d" % status
    return None

def one_request(model_id, prompt, max_tokens=512, temperature=0.0,
                timeout=300, max_retries=1, session=None):
    """Returns dict. Retries at most max_retries times on transient errors
    (429/503/timeout/connection). 401 triggers a token refresh and does not
    count as a retry against the transient budget."""
    s = session or requests
    attempts = 0
    retries = 0
    err_events = []
    t0 = time.time()
    last = {}
    while True:
        attempts += 1
        a0 = time.time()
        status = None; exc = None; body = None
        try:
            r = s.post(BASE + "/chat/completions",
                       headers={"Authorization": "Bearer " + token(),
                                "Content-Type": "application/json"},
                       json={"model": model_id,
                             "messages": [{"role": "user", "content": prompt}],
                             "max_tokens": max_tokens, "temperature": temperature},
                       timeout=timeout)
            status = r.status_code
            if status == 200:
                j = r.json()
                last = {"ok": True, "status": 200,
                        "content": j["choices"][0]["message"].get("content") or "",
                        "usage": j.get("usage", {}),
                        "finish": j["choices"][0].get("finish_reason")}
                break
            body = r.text[:300]
        except Exception as e:
            exc = e
        et = classify(status, exc)
        err_events.append({"attempt": attempts, "type": et,
                           "attempt_s": round(time.time() - a0, 3),
                           "body": body})
        if status == 401:
            token(force=True)
            if attempts <= max_retries + 2:
                continue
        if et in ("429", "503", "timeout", "connection") and retries < max_retries:
            retries += 1
            time.sleep(1.0 + 0.5 * retries)
            continue
        last = {"ok": False, "status": status, "error_type": et, "body": body,
                "content": "", "usage": {}, "finish": None}
        break
    last.update({"latency_s": round(time.time() - t0, 3),
                 "attempts": attempts, "retries": retries,
                 "err_events": err_events, "prompt": prompt[:60]})
    return last
