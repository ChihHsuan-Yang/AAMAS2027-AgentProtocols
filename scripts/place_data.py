#!/usr/bin/env python3
"""Find the released trajectory files by sha256 and link them where the analysis expects them.

Every trajectory file the paper reads is pinned by a committed manifest:

  experiments/results/FROZEN/MANIFEST.json                    Omni-MATH frozen campaign (3 files)
  experiments/results/xdomain/FROZEN_SCIBENCH/MANIFEST.json   SciBench frozen campaign  (1 file)
  experiments/results/bf/MANIFEST_BF.json                     post-freeze runs          (7 files)
  experiments/results/bf/chain2/MANIFEST.json                 second RF run             (3 files)

This script walks a download directory, hashes every .jsonl whose size could
match, and symlinks each match into place. It never trusts a file name: the two
RF runs share file names and differ only by content. It exits 1 if any pinned
file is missing, so it doubles as the data check.

Usage:  python3 scripts/place_data.py --source data/
"""
import argparse, hashlib, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "experiments", "results")

# manifest -> directories its files are linked into
TARGETS = [
    ("FROZEN/MANIFEST.json",                  ["FROZEN", "hf_frozen/raw"]),
    ("xdomain/FROZEN_SCIBENCH/MANIFEST.json", ["xdomain/FROZEN_SCIBENCH", "hf_frozen/raw"]),
    ("bf/MANIFEST_BF.json",                   ["bf"]),
    ("bf/chain2/MANIFEST.json",               ["bf/chain2"]),
]
# FINAL_TABLES.py reads FROZEN/*.jsonl (Omni-MATH only) and xdomain/FROZEN_SCIBENCH/;
# bf_numbers.py and bf_gate.py read hf_frozen/raw/ (both domains).

PARQUETS = [
    "analysis/hf_cache/release/data/problems/part-00000.parquet",
    "analysis/hf_cache/release/data/trajectories/part-00000.parquet",
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--source", required=True, help="directory holding the downloaded .jsonl files (searched recursively)")
    ap.add_argument("--copy", action="store_true", help="copy instead of symlinking")
    a = ap.parse_args()

    wanted = {}  # sha256 -> (basename, bytes, [target dirs])
    for manifest, dirs in TARGETS:
        m = json.load(open(os.path.join(RES, manifest)))
        for name, v in m["files"].items():
            entry = wanted.setdefault(v["sha256"], [os.path.basename(name), v.get("bytes"), []])
            entry[2] += dirs

    sizes = {v[1] for v in wanted.values()}
    by_size = None not in sizes   # every manifest entry records bytes: skip hashing other files
    found = {}
    for dirpath, _, files in os.walk(os.path.abspath(a.source)):
        for fn in files:
            if not fn.endswith(".jsonl") or fn.endswith(".infra_failed.jsonl"):
                continue
            p = os.path.join(dirpath, fn)
            if os.path.islink(p) and os.path.realpath(p).startswith(RES):
                continue
            if by_size and os.path.getsize(p) not in sizes:
                continue
            h = sha256(p)
            if h in wanted and h not in found:
                found[h] = p

    missing = 0
    for h, (name, nbytes, dirs) in sorted(wanted.items(), key=lambda kv: kv[1][2][0] + kv[1][0]):
        if h not in found:
            print("MISSING  {:<40} sha256 {}".format(name, h[:12]))
            missing += 1
            continue
        for d in dirs:
            dst_dir = os.path.join(RES, d)
            os.makedirs(dst_dir, exist_ok=True)
            dst = os.path.join(dst_dir, name)
            if os.path.lexists(dst):
                os.remove(dst)
            if a.copy:
                import shutil
                shutil.copyfile(found[h], dst)
            else:
                os.symlink(found[h], dst)
        print("OK       {:<40} sha256 {}  -> {}".format(name, h[:12], ", ".join(dirs)))

    for rel in PARQUETS:
        ok = os.path.exists(os.path.join(ROOT, rel))
        print("{}  {}".format("OK      " if ok else "MISSING ", rel))
        missing += 0 if ok else 1

    print("\n{} of {} trajectory files found; {}".format(
        len(found), len(wanted), "all data in place" if not missing else "{} item(s) missing".format(missing)))
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
