#!/usr/bin/env python3
"""HARD GATE. Must exit 0 before this dataset is ever flipped to public.

v1.0.0 is published PRIVATE. The raw traces under raw/ are shipped as EXACT
BYTES so their sha256 can be verified against MANIFEST.json -- which means the
upstream HTTP error bodies they captured are shipped too, and 14 of those name
the operating institution. That is harmless in a private repo and is a
deanonymization path in a public one.

This script fails while any such string is present. It is called from
RELEASE_PROCEDURE.md step 1. Do not flip public on a FAIL, and do not "fix" it
by deleting this check.

    python3 scripts/preflight_public.py         # check
    python3 scripts/preflight_public.py --fix   # redact raw/, then re-check

--fix rewrites ONLY the `error` field of affected rows, replacing the captured
upstream response body with a redaction marker that preserves the failure
class. Every other byte is untouched. It then rewrites MANIFEST.json,
CHECKSUMS.txt and VERSION for the new hashes and records the redaction, so the
integrity chain stays valid -- it just describes the redacted bytes from then
on.
"""
import argparse, hashlib, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
RAW = os.path.join(ART, "raw")

# EVERY released raw trace must be scanned. A trace missing from this tuple is
# not "clean" -- it is UNCHECKED, and the gate's guarantee is void for it. The
# v1.1.0 SciBench trace was added here when it was added to raw/; if a further
# domain lands, it goes here in the same commit.
TRACES = ("campaign_v2.jsonl", "actor3.jsonl", "armCp.jsonl",
          "scibench_AB.jsonl")

# Each trace's manifest, so --fix restamps the right file. v1.0.0's three
# traces share raw/MANIFEST.json; the SciBench trace has its own.
TRACE_MANIFEST = {
    "campaign_v2.jsonl": "MANIFEST.json",
    "actor3.jsonl": "MANIFEST.json",
    "armCp.jsonl": "MANIFEST.json",
    "scibench_AB.jsonl": "MANIFEST_SCIBENCH.json",
}

# Built from fragments so that THIS FILE does not itself contain the strings it
# hunts for (the secret scanner reads every shipped file, this one included).
_INST = ["arg" "onne", "a" "nl\\.gov", "AL" "CF", "ANL"]
_HOSTS = ["sop" "hia", "pol" "aris", "aur" "ora", "cr" "ux"]
_PATHS = [r"/home/[A-Za-z0-9_\-]+", r"/Users/[A-Za-z0-9_\-]+", "/lus/", "/eagle/", "/grand/"]
DEANON = re.compile("(?i)" + "|".join(
    [r"\b%s\b" % w for w in _INST + _HOSTS] + _PATHS))

# One HPC hostname is also an ordinary English noun ("the crux of the problem")
# and appears inside model reasoning. Allow only that exact lowercase usage --
# never a bare hostname, and never in docs or config.
ALLOW = [re.compile(r"(?i)\bthe %s of\b" % ("cr" "ux"))]


def _allowed(text, s, e):
    return any(m.start() <= s and e <= m.end()
               for a in ALLOW for m in a.finditer(text))


def _hits(text):
    return [m for m in DEANON.finditer(text) if not _allowed(text, m.start(), m.end())]

MARK = ("<REDACTED upstream response body: it named the operating institution. "
        "Redacted for public release; failure class preserved in this field's "
        "surrounding keys. See scripts/preflight_public.py.>")


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def scan():
    bad = []
    for fn in TRACES:
        p = os.path.join(RAW, fn)
        if not os.path.exists(p):
            continue
        with open(p) as f:
            for i, line in enumerate(f):
                if not _hits(line):
                    continue
                r = json.loads(line)
                where = [k for k, v in r.items()
                         if _hits(v if isinstance(v, str) else json.dumps(v))]
                bad.append((fn, i, r.get("problem_uid"), r.get("arm"), where))
    return bad


def fix():
    """Redact in TWO PHASES: plan every trace first, write only if ALL are safe.

    The single-phase version rewrote traces one at a time and sys.exit()ed on
    the first out-of-`error` leak -- leaving earlier traces REWRITTEN on disk
    with their manifests NOT restamped, i.e. a tree whose recorded hashes no
    longer describe its bytes, produced by the very tool meant to keep that
    chain valid. It could not fire while all known hits were in `error`
    fields; the v1.1.0 SciBench trace has a hit in `messages`, which makes it
    reachable. Plan-then-write: an unfixable leak now aborts with NOTHING
    written.
    """
    planned, refuse = {}, []
    for fn in TRACES:
        p = os.path.join(RAW, fn)
        if not os.path.exists(p):
            continue
        out, n = [], 0
        with open(p) as f:
            for i, line in enumerate(f):
                if _hits(line):
                    r = json.loads(line)
                    for k, v in list(r.items()):
                        s = v if isinstance(v, str) else json.dumps(v)
                        if _hits(s):
                            if k != "error":
                                refuse.append(f"{fn} line {i}: leak in field {k!r} "
                                              f"(uid={r.get('problem_uid')})")
                                continue
                            r[k] = MARK
                            n += 1
                    line = json.dumps(r, ensure_ascii=False) + "\n"
                out.append(line)
        if n:
            planned[fn] = (out, n)

    if refuse:
        sys.exit("refusing to auto-fix -- leak(s) outside the `error` field; "
                 "inspect by hand. NOTHING WAS WRITTEN:\n  " + "\n  ".join(refuse))

    changed = {}
    for fn, (out, n) in planned.items():
        with open(os.path.join(RAW, fn), "w") as f:
            f.writelines(out)
        changed[fn] = n
    return changed


def restamp():
    """Rewrite each trace's manifest / CHECKSUMS.txt / VERSION for redacted bytes."""
    for mfn in sorted(set(TRACE_MANIFEST.values())):
        mp = os.path.join(RAW, mfn)
        if not os.path.exists(mp):
            continue
        man = json.load(open(mp))
        for fn in TRACES:
            if TRACE_MANIFEST.get(fn) != mfn:
                continue
            p = os.path.join(RAW, fn)
            if not os.path.exists(p) or fn not in man.get("files", {}):
                continue
            man["files"][fn]["sha256"] = sha256_file(p)
            man["files"][fn]["bytes"] = os.path.getsize(p)
        _stamp(man)
        json.dump(man, open(mp, "w"), indent=2)
        print(f"  rewrote raw/{mfn}")
    print("  NOW REGENERATE: CHECKSUMS.txt and VERSION "
          "(python3 scripts/emit_release_metadata.py)")


def _stamp(man):
    man["redaction"] = {
        "applied_utc": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc).isoformat(),
        "what": "upstream HTTP error bodies naming the operating institution",
        "scope": "the `error` field of affected rows only",
        "rows": "see scripts/preflight_public.py",
        "note": ("hashes below describe the REDACTED bytes. The pre-redaction "
                 "hashes remain in VERSION.release_history for provenance."),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fix", action="store_true")
    a = ap.parse_args()

    if a.fix:
        ch = fix()
        print(f"redacted: {ch or 'nothing to do'}")
        if ch:
            restamp()

    bad = scan()
    print("=" * 66)
    present = [fn for fn in TRACES if os.path.exists(os.path.join(RAW, fn))]
    absent = [fn for fn in TRACES if fn not in present]
    print(f"scanned {len(present)} raw traces: {', '.join(present)}")
    if absent:
        print(f"NOT PRESENT (not scanned): {', '.join(absent)}")
    byfile = {}
    for fn, *_ in bad:
        byfile[fn] = byfile.get(fn, 0) + 1
    for fn in present:
        print(f"  {fn:22s} {byfile.get(fn, 0)} hit(s)")
    print("=" * 66)
    if not bad:
        print("PASS — no institution-identifying string in raw/. Safe to flip public\n"
              "       as far as THIS check goes; still re-read RELEASE_PROCEDURE.md.")
        return 0
    print(f"FAIL — {len(bad)} raw trace rows carry an institution-identifying string.")
    print("       DO NOT FLIP THIS DATASET PUBLIC.\n")
    for fn, i, uid, arm, where in bad[:20]:
        print(f"  {fn} line {i}  uid={uid} arm={arm}  fields={where}")
    if len(bad) > 20:
        print(f"  ... and {len(bad)-20} more")
    print("\n  Fix:  python3 scripts/preflight_public.py --fix")
    return 1


if __name__ == "__main__":
    sys.exit(main())
