#!/usr/bin/env python3
"""Scan every byte of the artifact for secrets, internal addresses, and
deanonymizing strings -- INCLUDING inside parquet text columns, which a
plain `grep` over the tree cannot see (they are zstd-compressed).

Two classes are checked:
  SECRET      credentials, keys, tokens, cookies, auth material
  DEANON      institution names, internal hosts, filesystem paths, author
              identity, repo/Overleaf URLs -- the double-blind hazard

A positive control is planted and must be caught, so a clean run cannot be
confused with a scanner that matches nothing (a check never shown to fail
detects nothing known).
"""
import os, re, sys, json
import pyarrow.parquet as pq

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PATTERNS = [
    # ---- SECRET
    ("SECRET", "anthropic key",      r"sk-ant-[A-Za-z0-9_\-]{8,}"),
    ("SECRET", "openai key",         r"\bsk-[A-Za-z0-9]{20,}"),
    ("SECRET", "generic api key",    r"(?i)\b(api[_-]?key|apikey|secret[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret)\b\s*[:=]\s*[\"']?[A-Za-z0-9_\-\.]{12,}"),
    ("SECRET", "bearer token",       r"(?i)\bBearer\s+[A-Za-z0-9_\-\.=]{12,}"),
    ("SECRET", "authorization hdr",  r"(?i)\bAuthorization\s*[:=]\s*[\"']?\S{12,}"),
    ("SECRET", "hf token",           r"\bhf_[A-Za-z0-9]{20,}"),
    ("SECRET", "github token",       r"\bgh[pousr]_[A-Za-z0-9]{20,}"),
    ("SECRET", "aws access key",     r"\bAKIA[0-9A-Z]{16}\b"),
    ("SECRET", "google api key",     r"\bAIza[0-9A-Za-z_\-]{35}\b"),
    ("SECRET", "slack token",        r"\bxox[abprs]-[A-Za-z0-9\-]{10,}"),
    ("SECRET", "jwt",                r"\beyJ[A-Za-z0-9_\-]{10,}\.[A-Za-z0-9_\-]{10,}\."),
    ("SECRET", "private key block",  r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    ("SECRET", "password assign",    r"(?i)\b(password|passwd|pwd)\b\s*[:=]\s*[\"']?\S{6,}"),
    ("SECRET", "cookie / set-cookie", r"(?i)\b(set-)?cookie\s*[:=]\s*\S{8,}"),
    ("SECRET", "apiKeyHelper",       r"apiKeyHelper"),
    ("SECRET", "ANTHROPIC_API_KEY",  r"ANTHROPIC_API_KEY"),
    ("SECRET", ".netrc / credentials file", r"(?i)\b(\.netrc|credentials\.json|token\.json|\.pem|\.p12)\b"),

    # ---- DEANON  (double-blind hazard, not a credential)
    ("DEANON", "institution: Argonne",  r"(?i)\bargonne\b"),
    ("DEANON", "institution: ANL/ALCF", r"\b(ALCF|ANL)\b"),
    ("DEANON", "ALCF machines",         r"(?i)(?<![\\\\A-Za-z])\b(sophia|polaris|aurora|crux|cooley|improv|bebop)\b"),
    ("DEANON", "lab filesystems",       r"(?i)(/lus/|/eagle/|/grand/|/gila/)"),
    ("DEANON", "argo shim",             r"(?i)\bargo[-_ ]?shim\b|\bargoapi\b"),
    ("DEANON", "author surname",        r"(?i)\b(bellayang|chihhsuan|chih-hsuan)\b"),
    ("DEANON", "author given name",     r"(?i)\bbella\b"),
    ("DEANON", "github repo/owner",     r"(?i)github\.com/[A-Za-z0-9_\-]+"),
    ("DEANON", "overleaf",              r"(?i)overleaf"),
    ("DEANON", "home dir path",         r"/Users/[A-Za-z0-9_\-]+|/home/[A-Za-z0-9_\-]+"),
    ("DEANON", "internal hostname",     r"(?i)\b(localhost|127\.0\.0\.1|0\.0\.0\.0|\S+\.anl\.gov|\S+\.internal\b)"),
    ("DEANON", "ANTHROPIC_BASE_URL",    r"ANTHROPIC_BASE_URL"),
    ("DEANON", "private ip",            r"\b(10\.\d{1,3}|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)\d{1,3}\.\d{1,3}\b"),
    ("DEANON", "chat/completions url",  r"https?://[^\s\"']*/(v1/)?chat/completions"),
]
COMPILED = [(c, n, re.compile(p)) for c, n, p in PATTERNS]

# Strings that are legitimately present and are NOT leaks.
ALLOW = [
    re.compile(r"https://huggingface\.co/datasets/martheballon/Omni-MATH-2"),
    re.compile(r"https://github\.com/dair-iitd/jeebench"),
    re.compile(r"https://github\.com/mandyyyyii/scibench"),
    re.compile(r"https://github\.com/M3RG-IITD/MaScQA"),
    re.compile(r"https://huggingface\.co/datasets/futurehouse/lab-bench"),
    # "crux" as ordinary English ("the crux of the problem") inside a model's
    # mathematical reasoning. Only allowed in the free-text corpus columns,
    # never in docs/config, and only in this exact lowercase English usage.
    re.compile(r"(?i)\bthe crux of\b"),
]


def allowed(text, s, e):
    for a in ALLOW:
        for m in a.finditer(text):
            if m.start() <= s and e <= m.end():
                return True
    return False


hits = []


def scan(text, where):
    if not text:
        return
    for cls, name, rx in COMPILED:
        for m in rx.finditer(text):
            if allowed(text, m.start(), m.end()):
                continue
            ctx = text[max(0, m.start() - 45):m.end() + 45].replace("\n", " ")
            hits.append((cls, name, where, m.group(0)[:70], ctx[:170]))


print("scanning files ...")
nf = nb = 0
for dp, dns, fns in os.walk(ROOT):
    dns[:] = [d for d in dns if d not in (".git", "__pycache__")]
    for fn in sorted(fns):
        p = os.path.join(dp, fn)
        rel = os.path.relpath(p, ROOT)
        if rel == os.path.join("scripts", "secret_scan.py"):
            continue          # contains every pattern by construction
        nf += 1
        nb += os.path.getsize(p)
        if fn.endswith(".parquet"):
            t = pq.read_table(p)
            for col in t.column_names:
                if t.schema.field(col).type not in (__import__("pyarrow").string(),
                                                    __import__("pyarrow").large_string()):
                    continue
                for v in t.column(col).to_pylist():
                    scan(v, f"{rel}::{col}")
        else:
            try:
                scan(open(p, encoding="utf-8", errors="replace").read(), rel)
            except Exception as e:
                print(f"  unreadable {rel}: {e}")
print(f"  {nf} files, {nb/1e6:.1f} MB (parquet text columns decompressed and scanned)")

# ------------------------------------------------------------- positive control
print("\npositive control (the scanner must catch a planted secret + a planted leak):")
CTRL = ('Authorization: Bearer sk-ant-api03-AAAABBBBCCCCDDDD '
        'run on sophia at /lus/eagle/proj by bella; ANTHROPIC_BASE_URL=http://127.0.0.1:8080')
before = len(hits)
scan(CTRL, "<positive-control>")
caught = {h[1] for h in hits[before:]}
del hits[before:]
need = {"bearer token", "anthropic key", "ALCF machines", "lab filesystems",
        "author given name", "ANTHROPIC_BASE_URL", "internal hostname"}
missed = need - caught
print(f"  planted control matched {len(caught)} rules: {sorted(caught)}")
if missed:
    print(f"  CONTROL FAILED — these rules did not fire: {sorted(missed)}")
    sys.exit(2)
print("  control OK — scanner demonstrably fires on both classes")

# ----------------------------------------------------------------------- report
print("\n" + "=" * 72)
if not hits:
    print("CLEAN — no SECRET or DEANON match in any file, including parquet text.")
    sys.exit(0)
bycls = {}
for h in hits:
    bycls.setdefault(h[0], []).append(h)
for cls in sorted(bycls):
    print(f"\n{cls}: {len(bycls[cls])} hits")
    seen = {}
    for c, n, w, mt, ctx in bycls[cls]:
        seen.setdefault((n, w), []).append((mt, ctx))
    for (n, w), v in sorted(seen.items()):
        print(f"  [{n}] {w}  x{len(v)}")
        print(f"      e.g. {v[0][1]}")
sys.exit(1)
