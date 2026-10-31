#!/usr/bin/env python3
"""bf_status -- progress, health and completion of one run cell (Arm Bf, or the
Arm A bridge), read straight from the runner's JSONL output.

Usage
-----
  python3 experiments/bf_status.py OUT.jsonl --n 1600 [--arm Bf]
          [--actor gemma-4-31B-it] [--quiet]

Exit status 0 iff the cell is COMPLETE: n distinct problem_uids, each with a
row whose stopping_condition is not an infrastructure failure
(model_unavailable / runtime_error). Anything else exits 1, so a shell loop
can use it as the completion test.

Read-only. Never modifies OUT.jsonl.
"""
import argparse
import collections
import json
import re
import sys
from datetime import datetime

INFRA = {"model_unavailable", "runtime_error"}
# Bearer tokens and JWT-shaped strings must never reach a row.
SECRET = re.compile(r"(?i)bearer\s+[A-Za-z0-9._\-]{12,}|eyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}")


def ts(s):
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--n", type=int, required=True)
    ap.add_argument("--arm", default="Bf")
    ap.add_argument("--actor", default="gemma-4-31B-it")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--max-attempts", type=int, default=3,
                    help="must match bf_requeue.py: a problem whose runtime_error has "
                         "recurred this often is final (counted incorrect), not pending")
    a = ap.parse_args()

    # runtime_error attempts already moved aside by bf_requeue.py
    prior = collections.Counter()
    qpath = a.out.replace(".jsonl", "") + ".infra_failed.jsonl"
    try:
        with open(qpath) as q:
            for line in q:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if (r.get("arm") == a.arm and str(r.get("actor_model", "")).endswith(a.actor)
                        and r.get("stopping_condition") == "runtime_error"):
                    prior[r["problem_uid"]] += 1
    except FileNotFoundError:
        pass

    rows, secrets, bad = [], 0, 0
    try:
        fh = open(a.out)
    except FileNotFoundError:
        print("[bf_status] {}: no file yet".format(a.out))
        return 1
    with fh:
        for line in fh:
            if not line.strip():
                continue
            if SECRET.search(line):
                secrets += 1
            try:
                r = json.loads(line)
            except Exception:
                bad += 1
                continue
            if r.get("arm") == a.arm and str(r.get("actor_model", "")).endswith(a.actor):
                rows.append(r)

    last = {}
    for r in rows:  # a later good row supersedes an earlier infra row
        u = r["problem_uid"]
        if u not in last or last[u].get("stopping_condition") in INFRA:
            last[u] = r
    ok = {u for u, r in last.items() if r.get("stopping_condition") not in INFRA}
    stuck = {u for u, r in last.items() if r.get("stopping_condition") == "runtime_error"
             and prior[u] + 1 >= a.max_attempts}
    infra = {u for u, r in last.items() if r.get("stopping_condition") in INFRA} - stuck
    complete = len(ok) + len(stuck) >= a.n and not infra and secrets == 0

    if a.quiet:
        print("[bf_status] {} {}: {}/{} complete, {} infra-failed pending, {} final failures{}".format(
            a.arm, a.out.split("/")[-1], len(ok), a.n, len(infra), len(stuck),
            "  ** SECRET-LIKE STRING IN ROWS **" if secrets else ""))
        return 0 if complete else 1

    good = [last[u] for u in ok]
    stops = collections.Counter(r.get("stopping_condition") for r in last.values())
    ev = [r.get("evaluator_history") or [] for r in good]
    judged = [e for e in ev if e]
    fp_ok = sum(1 for e in judged if int(e[0].get("correctness") or 0) == 1)
    fpw = [r for r in good if (r.get("evaluator_history") or [])
           and int(r["evaluator_history"][0].get("correctness") or 0) == 0]
    rec = sum(1 for r in fpw if r.get("correct") == 1)
    final = sum(1 for r in good if r.get("correct") == 1)
    cfg = collections.Counter(r.get("config_version") for r in good)

    print("=" * 72)
    print("{}  arm={}  actor={}".format(a.out, a.arm, a.actor))
    print("=" * 72)
    print("rows for this cell: {}   distinct problems: {}   unparseable lines: {}".format(
        len(rows), len(last), bad))
    print("COMPLETE problems: {}/{}   infra-failed pending requeue: {}   "
          "final failures after {} attempts (count incorrect): {}".format(
              len(ok), a.n, len(infra), a.max_attempts, len(stuck)))
    print("stopping conditions: {}".format(dict(stops.most_common())))
    print("config_version: {}".format(dict(cfg)))
    if good:
        print("first-pass correct: {}/{} = {:.3f}   (frozen gemma-4 Omni-MATH: 0.802)".format(
            fp_ok, len(judged), fp_ok / max(len(judged), 1)))
        print("final correct:      {}/{} = {:.3f}".format(final, len(good), final / len(good)))
        print("recovery:           {}/{} = {:.3f}   (frozen A 0.222, B 0.051)".format(
            rec, len(fpw), rec / max(len(fpw), 1)))
    if a.arm == "Bf" and fpw:
        # Delivery: a first-pass-wrong trajectory that ran at least one more
        # cycle must show the feedback flag on some actor message.
        flagged = [r for r in fpw if any(m.get("evaluator_feedback_in_prompt") for m in r.get("messages") or [])]
        msgs = [m for r in good for m in (r.get("messages") or [])]
        print("feedback delivered: {}/{} first-pass-wrong trajectories carry a flagged message;"
              " {} flagged actor messages in total".format(
                  len(flagged), len(fpw), sum(1 for m in msgs if m.get("evaluator_feedback_in_prompt"))))
        print("  (a first-pass-wrong trajectory without a flag is only acceptable if its FAIL"
              " came in the last cycle)")
    t0 = [ts(r.get("started_at") or "") for r in rows]
    t1 = [ts(r.get("ended_at") or "") for r in rows]
    t0 = [t for t in t0 if t]
    t1 = [t for t in t1 if t]
    if t0 and t1 and len(ok) > 1:
        span = (max(t1) - min(t0)).total_seconds()
        rate = len(rows) / max(span, 1) * 3600
        left = a.n - len(ok)
        print("throughput: {:.0f} rows/h over {:.1f} h; ETA for the remaining {}: {:.1f} h".format(
            rate, span / 3600, left, left / max(rate, 1e-9)))
    if infra:
        print("infra-failed examples:")
        for u in sorted(infra)[:5]:
            print("  {}  {}  {}".format(u, last[u].get("stopping_condition"),
                                        (last[u].get("error") or "")[:120]))
    if secrets:
        print("** {} line(s) contain a bearer/JWT-like string. STOP and inspect. **".format(secrets))
    print("RESULT: {}".format("COMPLETE" if complete else "NOT complete"))
    return 0 if complete else 1


if __name__ == "__main__":
    sys.exit(main())
