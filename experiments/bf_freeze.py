#!/usr/bin/env python3
"""Freeze the Bf control SEPARATELY from the existing frozen campaign.

Writes experiments/results/bf/FROZEN_BF/MANIFEST.json. Never touches
experiments/results/FROZEN/ or experiments/results/xdomain/FROZEN_SCIBENCH/:
Bf must never silently become part of the old frozen data (directive S.12).
"""
import json, hashlib, os, subprocess, sys, collections

USAGE = ("usage: bf_freeze.py [SRC_DIR]            freeze SRC_DIR\n"
         "       bf_freeze.py --verify FROZEN_DIR [SRC_DIR]\n"
         "                                          re-hash sources, compare to manifest")

_args = sys.argv[1:]
_verify = bool(_args) and _args[0] == "--verify"

if not _verify:
    # A flag typo must refuse, not create a directory literally named '--src'.
    if any(a.startswith("-") for a in _args) or len(_args) > 1:
        sys.exit(USAGE)
    SRC = _args[0] if _args else "experiments/results/bf"
    if not os.path.isdir(SRC):
        sys.exit("source dir does not exist: {}".format(SRC))
    OUT = os.path.join(SRC, "FROZEN_BF")

def sh(*a):
    return subprocess.run(a, capture_output=True, text=True).stdout.strip()

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

if _verify:
    if not (2 <= len(_args) <= 3):
        sys.exit(USAGE)
    fdir = _args[1]
    mpath = os.path.join(fdir, "MANIFEST.json")
    if not os.path.exists(mpath):
        sys.exit("no manifest at {}".format(mpath))
    man = json.load(open(mpath))
    src = _args[2] if len(_args) == 3 else os.path.dirname(os.path.abspath(fdir))
    # Two manifest shapes exist in this repo: FROZEN_BF writes {"cells": ...},
    # the pre-existing frozen A/B dirs write {"files": ...}. Accept both, and
    # refuse to "pass" a manifest whose hashed entries we cannot find -- a
    # verifier with nothing to verify must not report success.
    entries = {}
    for key in ("files", "cells"):
        for name, rec in (man.get(key) or {}).items():
            if isinstance(rec, dict) and "sha256" in rec:
                entries[name] = rec
    if not entries:
        sys.exit("manifest at {} has no sha-bearing file entries: "
                 "nothing to verify (refusing to report PASS)".format(mpath))
    bad = 0
    print("verifying {} against sources in {}".format(mpath, src))
    for name, rec in sorted(entries.items()):
        f = os.path.join(src, name)
        if not os.path.exists(f):
            print("  MISSING  {}".format(name)); bad += 1; continue
        h = sha256(f)
        ok = (h == rec["sha256"])
        bad += (not ok)
        print("  {}  {:<40} rows={:<6} {}".format(
            "OK      " if ok else "MISMATCH", name, rec.get("rows", "?"),
            "" if ok else "manifest {}... disk {}...".format(
                rec["sha256"][:16], h[:16])))
    print("\nVERIFY: {}".format("PASS -- manifest describes these bytes"
                                 if bad == 0 else
                                 "FAIL -- {} cell(s) differ from the manifest".format(bad)))
    sys.exit(0 if bad == 0 else 1)


def cell(path):
    rows = [json.loads(l) for l in open(path)]
    uids = [r["problem_uid"] for r in rows]
    dup = [u for u, c in collections.Counter(uids).items() if c > 1]
    budgets = {json.dumps(r.get("budget"), sort_keys=True) for r in rows}
    infra = path + ".infra_failed.jsonl"
    n_infra = sum(1 for _ in open(infra)) if os.path.exists(infra) else 0
    return {
        "file": os.path.basename(path),
        "rows": len(rows),
        "sha256": sha256(path),
        "distinct_problem_uids": len(set(uids)),
        "duplicate_uids": dup,
        "arms": sorted({r["arm"] for r in rows}),
        "config_version": sorted({r.get("config_version") for r in rows}),
        "actor_model": sorted({r.get("actor_model") for r in rows}),
        "evaluator_model": sorted({r.get("evaluator_model") for r in rows}),
        "backend": sorted({str(r.get("backend")) for r in rows}),
        "benchmark_id": sorted({str(r.get("benchmark_id")) for r in rows}),
        "budget_settings": [json.loads(b) for b in budgets],
        "request_timeout_s": sorted({r.get("request_timeout_s") for r in rows}),
        "visibility_policy": rows[0].get("visibility_policy"),
        "started_at_min": min([r["started_at"] for r in rows if r.get("started_at")] or [None]),
        "ended_at_max": max([r["ended_at"] for r in rows if r.get("ended_at")] or [None]),
        "infra_failed_rows_retained": n_infra,
        "infra_failed_file": os.path.basename(infra) if n_infra else None,
        "problem_uid_manifest_sha256": hashlib.sha256(
            "\n".join(sorted(set(uids))).encode()).hexdigest(),
        "problem_uid_manifest": sorted(set(uids)),
    }

cells = {}
for f in sorted(os.listdir(SRC)):
    if f.endswith(".jsonl") and not f.endswith(".infra_failed.jsonl"):
        cells[f] = cell(os.path.join(SRC, f))
if not cells:
    sys.exit("no result cells in {}: refusing to write an empty freeze".format(SRC))
os.makedirs(OUT, exist_ok=True)

man = {
    "freeze_name": "FROZEN_BF",
    "purpose": ("Bf control (role-free organization + evaluator feedback "
                "delivered). SEPARATE from the frozen A/B campaign; never pool."),
    "frozen_at": sh("date", "-u", "+%Y-%m-%dT%H:%M:%SZ"),
    "source_branch": sh("git", "rev-parse", "--abbrev-ref", "HEAD"),
    "source_branch_sha": sh("git", "rev-parse", "HEAD"),
    "runner_sha256": {
        "experiments/runner.py": sha256("experiments/runner.py"),
        "experiments/runner_xdomain.py": sha256("experiments/runner_xdomain.py"),
        "experiments/prompts.py": sha256("experiments/prompts.py"),
    },
    "git_status_dirty": bool(sh("git", "status", "--porcelain")),
    "cells": cells,
}
p = os.path.join(OUT, "MANIFEST.json")
tmp = p + ".tmp"
with open(tmp, "w") as f:
    json.dump(man, f, indent=2, sort_keys=True)
os.replace(tmp, p)          # atomic: never a truncated manifest on disk
print("wrote", p)
for k, v in cells.items():
    print("  %-40s rows=%-6s uids=%-6s dup=%d infra=%d sha=%s"
          % (k, v["rows"], v["distinct_problem_uids"], len(v["duplicate_uids"]),
             v["infra_failed_rows_retained"], v["sha256"][:16]))
