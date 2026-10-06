#!/usr/bin/env python3
"""bf_preflight -- gate before the Bf launch. Zero API calls.

Checks, per domain:
  1. the downloaded frozen JSONL matches the sha256 in the MANIFEST committed
     to git (experiments/results/FROZEN/MANIFEST.json,
     experiments/results/xdomain/FROZEN_SCIBENCH/MANIFEST.json);
  2. the problems parquet named by AAMAS_PROBLEMS_PARQUET makes the runner
     select EXACTLY the frozen problem set (gemma-4 Arm A and Arm B uids);
  3. the auth helper named by AAMAS_AUTH_SCRIPT_DIR imports and returns a
     token (the token itself is never printed).

Any failure exits non-zero: do not launch.

Usage (from the worktree root, env vars exported):
  python3 experiments/bf_preflight.py --frozen-dir <dir with the raw/ files> \
      --manifest-root /Users/lxy/AAMAS/AAMAS2027-AgentProtocols
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEED = 20270101
DOMAINS = {
    "omni": dict(runner="runner", n=1600, frozen="campaign_v2.jsonl",
                 manifest="experiments/results/FROZEN/MANIFEST.json"),
    "scibench": dict(runner="runner_xdomain", n=574, frozen="scibench_AB.jsonl",
                     manifest="experiments/results/xdomain/FROZEN_SCIBENCH/MANIFEST.json"),
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def frozen_uids(path, arm):
    s = set()
    with open(path) as fh:
        for line in fh:
            r = json.loads(line)
            if r.get("arm") == arm and r["actor_model"].endswith("gemma-4-31B-it"):
                s.add(r["problem_uid"])
    return s


def selected_uids(runner, n):
    # Each runner is imported in its own interpreter: the two modules patch the
    # shared prompts module differently.
    code = ("import sys, json; sys.path.insert(0, {!r}); import {} as R; "
            "print(json.dumps([p['problem_uid'] for p in R.load_problems({}, {})]))").format(
                HERE, runner, n, SEED)
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    if out.returncode != 0:
        raise RuntimeError(out.stderr[-800:])
    return set(json.loads(out.stdout.strip().splitlines()[-1]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frozen-dir", required=True)
    ap.add_argument("--manifest-root", required=True)
    ap.add_argument("--domains", default="omni,scibench")
    a = ap.parse_args()
    failures = []

    pq = os.environ.get("AAMAS_PROBLEMS_PARQUET", "")
    print("parquet: {}  exists={}".format(pq, os.path.exists(pq)))
    if os.path.exists(pq):
        print("parquet sha256: {}".format(sha256(pq)))
    else:
        failures.append("AAMAS_PROBLEMS_PARQUET missing")

    for d in a.domains.split(","):
        c = DOMAINS[d]
        print("\n== {} ==".format(d))
        fpath = os.path.join(a.frozen_dir, c["frozen"])
        man = json.load(open(os.path.join(a.manifest_root, c["manifest"])))
        want = man["files"][c["frozen"]]["sha256"]
        if not os.path.exists(fpath):
            failures.append("{}: {} not found".format(d, fpath))
            continue
        got = sha256(fpath)
        print("frozen {} sha256 {}  manifest {}  {}".format(
            c["frozen"], got[:16], want[:16], "OK" if got == want else "MISMATCH"))
        if got != want:
            failures.append("{}: frozen file sha256 mismatch".format(d))
        fa, fb = frozen_uids(fpath, "A"), frozen_uids(fpath, "B")
        print("frozen gemma-4 uids: A={} B={} identical={}".format(len(fa), len(fb), fa == fb))
        try:
            sel = selected_uids(c["runner"], c["n"])
        except Exception as exc:  # noqa: BLE001
            failures.append("{}: load_problems failed: {}".format(d, exc))
            continue
        same = sel == fa
        print("runner.load_problems(n={}, seed={}) -> {} uids; equal to frozen A: {}".format(
            c["n"], SEED, len(sel), same))
        if not same:
            print("  only selected: {}  only frozen: {}".format(
                sorted(sel - fa)[:5], sorted(fa - sel)[:5]))
            failures.append("{}: problem selection differs from frozen".format(d))

    print("\n== auth ==")
    sys.path.insert(0, os.environ.get("AAMAS_AUTH_SCRIPT_DIR", ""))
    try:
        import inference_auth_token  # noqa: PLC0415
        tok = inference_auth_token.get_access_token()
        print("token obtained: {} characters (not printed)".format(len(tok or "")))
        if not tok:
            failures.append("auth: empty token")
    except Exception as exc:  # noqa: BLE001
        failures.append("auth: {}: {}".format(type(exc).__name__, str(exc)[:200]))

    print("\nPREFLIGHT {}".format("PASS" if not failures else "FAIL"))
    for f in failures:
        print("  - " + f)
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
