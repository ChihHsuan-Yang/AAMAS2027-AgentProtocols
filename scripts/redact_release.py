#!/usr/bin/env python3
"""Produce the public copies of the trajectory files, with infrastructure error bodies redacted.

A few trajectory rows carry, in their `error` field, the raw response body that
the inference gateway returned on a failed request: an HTML block page or a
server-side traceback. These bodies identify the serving infrastructure and say
nothing about the experiment. This script replaces each such `error` value with
a fixed marker and leaves every other field, and every other row, byte-identical.

The analysis never reads the text of `error` (xdom_analyze.py only counts
whether it is non-empty, and the marker is non-empty), so every number, table
and figure is unchanged. The file hashes do change: this script rewrites the
committed manifests to pin the redacted files and records each original hash
under `redacted_from_sha256`.

Matches outside the `error` field are listed but never modified.

Usage:
    python3 scripts/redact_release.py --source <dir with the original files> --out <new dir>

The source files are never written to. --out receives all pinned files:
    <out>/raw/          frozen campaign (both domains)
    <out>/bf/           post-freeze runs
    <out>/bf/chain2/    second RF run
"""
import argparse, hashlib, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "experiments", "results")

# manifest -> output sub-directory
MANIFESTS = [
    ("FROZEN/MANIFEST.json", "raw"),
    ("xdomain/FROZEN_SCIBENCH/MANIFEST.json", "raw"),
    ("bf/MANIFEST_BF.json", "bf"),
    ("bf/chain2/MANIFEST.json", os.path.join("bf", "chain2")),
]

INFRA = re.compile(r"(?i)\b(argonne|anl\.gov|alcf|anl)\b|cloudflare|/home/[A-Za-z0-9_\-]+"
                   r"|\b(sophia|polaris|aurora)\b")
MARK = "<redacted for public release: response body returned by the inference gateway>"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def locate(source, wanted):
    """sha256 -> path, searching source recursively; size filter first."""
    sizes = {v["bytes"] for v in wanted.values() if v.get("bytes")}
    found = {}
    for dirpath, _, files in os.walk(os.path.abspath(source)):
        for fn in files:
            if not fn.endswith(".jsonl") or fn.endswith(".infra_failed.jsonl"):
                continue
            p = os.path.join(dirpath, fn)
            if sizes and os.path.getsize(p) not in sizes:
                continue
            h = sha256(p)
            if h in wanted and h not in found:
                found[h] = p
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--source", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out_root = os.path.abspath(a.out)
    if os.path.abspath(a.source) == out_root:
        sys.exit("--out must differ from --source; the originals are never overwritten")

    manifests = {}
    style = {}           # manifest -> (indent, trailing newline), preserved on rewrite
    wanted = {}          # sha256 -> manifest entry
    where = {}           # sha256 -> (manifest rel path, file key, out subdir)
    for rel, sub in MANIFESTS:
        text = open(os.path.join(RES, rel)).read()
        m = json.loads(text)
        manifests[rel] = m
        second = text.splitlines()[1] if "\n" in text else ""
        style[rel] = (len(second) - len(second.lstrip(" ")) or 1, text.endswith("\n"))
        for key, v in m["files"].items():
            h = v["sha256"]
            wanted[h] = v
            where[h] = (rel, key, sub)
    if any("redacted_from_sha256" in v for v in wanted.values()):
        sys.exit("manifests already pin redacted files; nothing to do")

    found = locate(a.source, wanted)
    missing = [where[h][1] for h in wanted if h not in found]
    if missing:
        sys.exit("missing source files (by sha256): " + ", ".join(missing))

    # plan everything before writing anything
    plan, untouched_hits = {}, []
    for h, src in found.items():
        rel, key, sub = where[h]
        lines, n = [], 0
        with open(src, encoding="utf-8") as f:
            for i, line in enumerate(f):
                if INFRA.search(line):
                    r = json.loads(line)
                    if isinstance(r.get("error"), str) and INFRA.search(r["error"]):
                        r["error"] = MARK
                        n += 1
                        line = json.dumps(r, ensure_ascii=False) + "\n"
                    if INFRA.search(line):
                        untouched_hits.append("{} line {}".format(key, i + 1))
                lines.append(line)
        plan[h] = (rel, key, sub, lines, n)

    for h, (rel, key, sub, lines, n) in plan.items():
        dst_dir = os.path.join(out_root, sub)
        os.makedirs(dst_dir, exist_ok=True)
        dst = os.path.join(dst_dir, os.path.basename(key))
        if n:
            with open(dst, "w", encoding="utf-8") as f:
                f.writelines(lines)
            entry = manifests[rel]["files"][key]
            entry["redacted_from_sha256"] = entry["sha256"]
            entry["redacted_error_fields"] = n
            entry["sha256"] = sha256(dst)
            entry["bytes"] = os.path.getsize(dst)
        else:
            with open(found[h], "rb") as s, open(dst, "wb") as d:
                d.write(s.read())
            assert sha256(dst) == h
        print("{:<5} {:<45} {} error field(s) redacted".format("EDIT" if n else "COPY", key, n))

    for rel, m in manifests.items():
        if any("redacted_from_sha256" in v for v in m["files"].values()):
            m["redaction"] = ("Public copies: `error` fields holding inference-gateway response "
                              "bodies replaced by a fixed marker (scripts/redact_release.py). "
                              "redacted_from_sha256 pins each original file.")
            indent, newline = style[rel]
            with open(os.path.join(RES, rel), "w") as f:
                f.write(json.dumps(m, indent=indent) + ("\n" if newline else ""))
            print("rewrote", os.path.join("experiments/results", rel))

    if untouched_hits:
        print("\nMatches left in place (outside `error`, e.g. a star named in a physics problem):")
        for u in untouched_hits:
            print("  " + u)
    print("\nPublic copies written to", out_root)


if __name__ == "__main__":
    main()
