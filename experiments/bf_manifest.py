#!/usr/bin/env python3
"""bf_manifest -- add or refresh entries in experiments/results/bf/MANIFEST_BF.json.

The Bf result files are gitignored. MANIFEST_BF.json is committed, and it pins
each file by sha256 together with its cell counts, so that any later analysis
can prove which bytes it read (analysis/scripts/bf_numbers.py checks it).

Usage (worktree root):
  python3 experiments/bf_manifest.py <results dir> FILE.jsonl [FILE.jsonl ...] \
      [--code-commit "<sha> (<branch>)"] [--note "<text>"]

Only the named files are (re)written. Other entries are kept unchanged. A file
named in "pending" is moved out of it once it has an entry.
"""
import argparse
import collections
import hashlib
import json
import os
import sys


def entry(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    cells, cfg, rid, stop = (collections.Counter() for _ in range(4))
    t0, t1, rows = [], [], 0
    with open(path) as fh:
        for line in fh:
            if not line.strip():
                continue
            r = json.loads(line)
            rows += 1
            cells["{}|{}".format(r["actor_model"].split("/")[-1], r.get("arm"))] += 1
            cfg[r.get("config_version")] += 1
            rid[r.get("run_id")] += 1
            stop[r.get("stopping_condition")] += 1
            if r.get("started_at"): t0.append(r["started_at"])
            if r.get("ended_at"): t1.append(r["ended_at"])
    return dict(sha256=h.hexdigest(), rows=rows, bytes=os.path.getsize(path),
                cells=dict(cells), config_versions=dict(cfg), run_ids=dict(rid),
                stopping_conditions=dict(stop.most_common()),
                first_started=min(t0) if t0 else None, last_ended=max(t1) if t1 else None)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results_dir")
    ap.add_argument("files", nargs="+")
    ap.add_argument("--code-commit")
    ap.add_argument("--note")
    a = ap.parse_args()
    mp = os.path.join(a.results_dir, "MANIFEST_BF.json")
    m = json.load(open(mp)) if os.path.exists(mp) else {"files": {}}
    m.setdefault("files", {})
    for f in a.files:
        name = os.path.basename(f)
        e = entry(os.path.join(a.results_dir, name) if not os.path.exists(f) else f)
        if a.code_commit:
            e["code_commit"] = a.code_commit
        if a.note:
            e["note"] = a.note
        m["files"][name] = e
        (m.get("pending") or {}).pop(name, None)
        print("{}: {} rows, sha256 {}, cells {}".format(name, e["rows"], e["sha256"][:16], e["cells"]))
    if "pending" in m and not m["pending"]:
        del m["pending"]
    tmp = mp + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(m, fh, indent=1)
        fh.write("\n")
    os.replace(tmp, mp)
    print("wrote", mp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
