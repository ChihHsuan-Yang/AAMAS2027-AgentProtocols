#!/usr/bin/env python3
"""bf_requeue -- move infrastructure-failed rows out of a runner output file so
that re-running the IDENTICAL runner command retries them.

Why this is needed: runner.load_done() treats only `model_unavailable` as not
done. A row that ended in `runtime_error` (a call that failed after all
transport retries, an evaluator call that failed, an unexpected exception) is
counted as complete and would never be retried -- and under the pre-registered
scoring it would silently count as an incorrect answer.

Rule (fixed before the Bf launch, see DECISION_LOG.md):
  * `model_unavailable` and `runtime_error` rows are infrastructure failures:
    they are moved to OUT.infra_failed.jsonl and re-run.
  * Every other stopping condition is a protocol outcome and is never touched.
  * `runtime_error` counts as an attempt; after --max-attempts failures of the
    same problem its last row is LEFT in place (counted incorrect, as the
    preregistration prescribes) and reported, so a deterministic failure cannot
    loop forever. `model_unavailable` (an endpoint outage) does not count.

Run it only while no runner is writing to OUT.jsonl. Lines that are kept are
written back byte-for-byte; the rewrite is atomic (temp file + os.replace).

Usage: python3 experiments/bf_requeue.py OUT.jsonl [--max-attempts 3]
"""
import argparse
import collections
import json
import os
import sys

INFRA = ("model_unavailable", "runtime_error")


def key(r):
    return (r.get("problem_uid"), r.get("arm"), r.get("actor_model"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--max-attempts", type=int, default=3)
    a = ap.parse_args()
    if not os.path.exists(a.out):
        print("[bf_requeue] {}: no file yet, nothing to do".format(a.out))
        return 0
    qpath = a.out.replace(".jsonl", "") + ".infra_failed.jsonl"

    prior = collections.Counter()
    if os.path.exists(qpath):
        with open(qpath) as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if r.get("stopping_condition") == "runtime_error":
                    prior[key(r)] += 1

    with open(a.out) as fh:
        lines = fh.readlines()
    keep, move, stuck = [], [], []
    for line in lines:
        if not line.strip():
            continue
        try:
            r = json.loads(line)
        except Exception:
            keep.append(line)  # never drop what we cannot parse
            continue
        sc = r.get("stopping_condition")
        if sc == "model_unavailable":
            move.append(line)
        elif sc == "runtime_error":
            if prior[key(r)] + 1 >= a.max_attempts:
                keep.append(line)
                stuck.append(r)
            else:
                prior[key(r)] += 1
                move.append(line)
        else:
            keep.append(line)

    if move:
        with open(qpath, "a") as q:
            for line in move:
                q.write(line if line.endswith("\n") else line + "\n")
            q.flush()
            os.fsync(q.fileno())
        tmp = a.out + ".tmp"
        with open(tmp, "w") as fh:
            for line in keep:
                fh.write(line if line.endswith("\n") else line + "\n")
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, a.out)
    print("[bf_requeue] {}: kept {}, moved {} to {} for re-run, {} left in place after {} attempts".format(
        os.path.basename(a.out), len(keep), len(move), os.path.basename(qpath), len(stuck), a.max_attempts))
    for r in stuck[:10]:
        print("  STUCK {} {}: {}".format(r.get("problem_uid"), r.get("arm"), (r.get("error") or "")[:120]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
