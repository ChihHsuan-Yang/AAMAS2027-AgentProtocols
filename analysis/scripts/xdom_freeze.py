#!/usr/bin/env python3
"""Freeze the SciBench cross-domain results into FROZEN_SCIBENCH/ + MANIFEST.

Writes sha256, row counts, per-cell census, config version, and the git
commit, so a later analysis can prove which bytes it read.
"""
from __future__ import annotations
import argparse, collections, hashlib, json, shutil, subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols")
SRC = ROOT / "experiments/results/xdomain"
DST = SRC / "FROZEN_SCIBENCH"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--files", nargs="*", default=["scibench_AB.jsonl"])
    args = ap.parse_args()

    DST.mkdir(parents=True, exist_ok=True)
    try:
        commit = subprocess.check_output(
            ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True).strip()
        dirty = subprocess.check_output(
            ["git", "-C", str(ROOT), "status", "--porcelain"], text=True).strip()
    except Exception as e:
        commit, dirty = "unavailable: {}".format(e), ""

    man = {
        "frozen_at": datetime.now(timezone.utc).isoformat(),
        "benchmark_id": "scibench",
        "slice_id": "text_only",
        "domain": "science",
        "git_commit": commit,
        "git_dirty": bool(dirty),
        "files": {},
        "cells": {},
        "total_rows": 0,
        "config_versions": {},
        "stopping_conditions": {},
        "problem_uids": 0,
    }

    cells = collections.Counter()
    stops = collections.Counter()
    cfgs = collections.Counter()
    uids = set()
    total = 0

    for name in args.files:
        s = SRC / name
        if not s.exists():
            print("MISSING: {}".format(s))
            continue
        d = DST / name
        shutil.copy2(s, d)
        n = 0
        for line in d.open():
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            n += 1
            cells["{}|{}".format(r["actor_model"].split("/")[-1], r["arm"])] += 1
            stops[r.get("stopping_condition", "?")] += 1
            cfgs[r.get("config_version", "?")] += 1
            uids.add(r.get("problem_uid"))
        man["files"][name] = {"rows": n, "sha256": sha256(d),
                              "bytes": d.stat().st_size}
        total += n

    man["cells"] = dict(sorted(cells.items()))
    man["total_rows"] = total
    man["stopping_conditions"] = dict(sorted(stops.items(), key=lambda kv: -kv[1]))
    man["config_versions"] = dict(cfgs)
    man["problem_uids"] = len(uids)

    (DST / "MANIFEST.json").write_text(json.dumps(man, indent=2))

    print("FROZEN -> {}".format(DST))
    print("  total_rows {}   distinct problem_uids {}".format(total, len(uids)))
    print("  config_versions {}".format(dict(cfgs)))
    for k, v in man["files"].items():
        print("  {:<24} {:>6} rows  sha256 {}".format(k, v["rows"], v["sha256"][:16]))
    print("  cells:")
    for k, v in man["cells"].items():
        print("    {:<28} {}".format(k, v))
    print("  stopping conditions:")
    for k, v in man["stopping_conditions"].items():
        print("    {:<44} {}".format(k, v))
    if dirty:
        print("  NOTE: working tree dirty at freeze time")


if __name__ == "__main__":
    raise SystemExit(main())
