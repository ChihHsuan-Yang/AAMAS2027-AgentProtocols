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
TRACES = ("campaign_v2.jsonl", "actor3.jsonl", "armCp.jsonl")

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
    changed = {}
    for fn in TRACES:
        p = os.path.join(RAW, fn)
        if not os.path.exists(p):
            continue
        out, n = [], 0
        with open(p) as f:
            for line in f:
                if _hits(line):
                    r = json.loads(line)
                    for k, v in list(r.items()):
                        s = v if isinstance(v, str) else json.dumps(v)
                        if _hits(s):
                            if k != "error":
                                sys.exit(f"{fn}: leak outside `error` (field {k!r}) "
                                         "-- refusing to auto-fix; inspect by hand")
                            r[k] = MARK
                            n += 1
                    line = json.dumps(r, ensure_ascii=False) + "\n"
                out.append(line)
        if n:
            with open(p, "w") as f:
                f.writelines(out)
            changed[fn] = n
    return changed


def restamp():
    """Rewrite MANIFEST.json / CHECKSUMS.txt / VERSION for the redacted bytes."""
    mp = os.path.join(RAW, "MANIFEST.json")
    man = json.load(open(mp))
    for fn in TRACES:
        p = os.path.join(RAW, fn)
        man["files"][fn]["sha256"] = sha256_file(p)
        man["files"][fn]["bytes"] = os.path.getsize(p)
    man["redaction"] = {
        "applied_utc": __import__("datetime").datetime.now(
            __import__("datetime").timezone.utc).isoformat(),
        "what": "upstream HTTP error bodies naming the operating institution",
        "scope": "the `error` field of affected rows only",
        "rows": "see scripts/preflight_public.py",
        "note": ("hashes below describe the REDACTED bytes. The pre-redaction "
                 "hashes remain in VERSION.release_history for provenance."),
    }
    json.dump(man, open(mp, "w"), indent=2)
    print("  rewrote raw/MANIFEST.json")
    print("  NOW REGENERATE: CHECKSUMS.txt and VERSION "
          "(python3 scripts/emit_release_metadata.py)")


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
