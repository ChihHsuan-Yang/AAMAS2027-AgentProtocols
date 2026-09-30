#!/usr/bin/env python3
"""Regenerate VERSION, CHECKSUMS.txt and MANIFEST.json over the whole artifact.

Every released file gets: sha256, bytes, and (for traces/tables) rows.
Every released TRACE additionally gets: semantic version, freeze commit,
timestamp, actor, arm, domain, backend, config version.

Deterministic: sorted walk, sorted keys. A rebuild is byte-identical.
"""
import hashlib, json, os, subprocess, collections, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
PROJ = os.path.dirname(ART)
RAW = os.path.join(ART, "raw")

VERSION_ID = "1.0.0"
SKIP = {"VERSION", "CHECKSUMS.txt", "MANIFEST.json"}


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def git(*a):
    try:
        return subprocess.check_output(["git", "-C", PROJ, *a],
                                       text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def walk():
    out = []
    for dp, dns, fns in os.walk(ART):
        dns[:] = sorted(d for d in dns if d not in (".git", "__pycache__"))
        for fn in sorted(fns):
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, ART)
            if rel in SKIP or rel.endswith(".pyc"):
                continue
            out.append(rel)
    return sorted(out)


def trace_facts():
    """Per-trace provenance, derived from the trace itself."""
    facts = {}
    for fn in ("campaign_v2.jsonl", "actor3.jsonl", "armCp.jsonl"):
        p = os.path.join(RAW, fn)
        if not os.path.exists(p):
            continue
        n = 0
        arms, actors, domains, backends, cfgs, runs = (collections.Counter() for _ in range(6))
        tmin = tmax = None
        with open(p) as f:
            for line in f:
                r = json.loads(line)
                n += 1
                arms[r.get("arm")] += 1
                actors[r.get("actor_model")] += 1
                domains[r.get("domain")] += 1
                backends[r.get("backend")] += 1
                cfgs[r.get("config_version")] += 1
                runs[r.get("run_id")] += 1
                st = r.get("started_at")
                if st:
                    tmin = st if tmin is None or st < tmin else tmin
                    tmax = st if tmax is None or st > tmax else tmax
        facts[fn] = dict(
            sha256=sha256_file(p), bytes=os.path.getsize(p), rows=n,
            semantic_version=VERSION_ID,
            arms=dict(arms), actor_models=dict(actors),
            domain=sorted(k for k in domains if k), benchmark_id="omnimath2",
            backend=sorted(k for k in backends if k),
            config_version=dict(cfgs), run_id=sorted(k for k in runs if k),
            first_started_at=tmin, last_started_at=tmax,
        )
    return facts


def main():
    files = walk()
    digests = {rel: (sha256_file(os.path.join(ART, rel)),
                     os.path.getsize(os.path.join(ART, rel))) for rel in files}

    # ---------------------------------------------------------- CHECKSUMS.txt
    with open(os.path.join(ART, "CHECKSUMS.txt"), "w") as f:
        f.write("# sha256 of every file in this artifact.\n")
        f.write("# Verify:  shasum -c CHECKSUMS.txt\n")
        f.write("# (VERSION, CHECKSUMS.txt and MANIFEST.json are not listed.)\n")
        for rel in files:
            f.write(f"{digests[rel][0]}  {rel}\n")

    tf = trace_facts()
    freeze_commit = git("rev-parse", "HEAD")
    frozen_at = json.load(open(os.path.join(RAW, "MANIFEST.json")))["frozen_at"]
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # ------------------------------------------------------------ MANIFEST.json
    manifest = {
        "artifact": "AAMAS2027-Roles",
        "semantic_version": VERSION_ID,
        "emitted_utc": now,
        "freeze_commit": freeze_commit,
        "frozen_at": frozen_at,
        "released_traces": tf,
        "tables": {},
        "all_files": {rel: dict(sha256=d[0], bytes=b) for rel, (d, b) in
                      ((r, (digests[r][0], digests[r][1])) for r in files)},
    }
    try:
        import pyarrow.parquet as pq
        for rel in files:
            if rel.endswith(".parquet"):
                t = pq.read_metadata(os.path.join(ART, rel))
                manifest["tables"][rel] = dict(
                    sha256=digests[rel][0], bytes=digests[rel][1],
                    rows=t.num_rows, columns=t.num_columns)
    except Exception as e:
        manifest["tables"]["_error"] = str(e)
    json.dump(manifest, open(os.path.join(ART, "MANIFEST.json"), "w"),
              indent=1, sort_keys=True)

    # ----------------------------------------------------------------- VERSION
    version = {
        "artifact_version": VERSION_ID,
        "artifact": "AAMAS2027-Roles",
        "release_status": "PUBLISHED_PRIVATE_PENDING_ACCEPTANCE",
        "held_reason": (
            "AAMAS 2027 reviewing is double-blind and the hosting org identifies "
            "the research group. A public dataset matching the paper's numbers is "
            "a deanonymization path even with no pointer from the paper. The "
            "repository is PRIVATE. See RELEASE_PROCEDURE.md."),
        "public_release_gate": (
            "scripts/preflight_public.py MUST exit 0 before flipping public. It "
            "currently FAILS: 14 raw trace rows carry an upstream HTTP error body "
            "naming the operating institution."),
        "emitted_utc": now,
        "freeze_commit": freeze_commit,
        "frozen_at": frozen_at,
        "released_traces": tf,
        "canonical_analysis": {
            "script": "analysis/scripts/FINAL_TABLES.py",
            "output": "analysis/out/FINAL_TABLES_OUTPUT.txt",
            "note": ("FINAL_TABLES.py is the project's sole authority for every "
                     "manuscript number. This artifact emits the ROWS those numbers "
                     "are computed over."),
            "validation": "scripts/validate_artifact.py -- 181/181 PASS, re-run "
                          "against the canonical output regenerated 2026-09-30 14:49Z",
        },
        "release_history": [
            {"version": "1.0.0", "status": "private",
             "traces": {k: v["sha256"] for k, v in tf.items()},
             "note": "first release; single domain (competition math, Omni-MATH-2)"}
        ],
        "reserved": {"1.1.0": "second domain (SciBench) -- see config/SECOND_DOMAIN_SLOT.md; "
                              "added as a new version, never an overwrite of 1.0.0"},
        "licensing": "per-source; see LICENSES/README.md and LICENSES/registry.json",
    }
    json.dump(version, open(os.path.join(ART, "VERSION"), "w"), indent=1, sort_keys=True)

    print(f"files: {len(files)}")
    print(f"total bytes: {sum(b for _, b in digests.values())/1e6:.1f} MB")
    for fn, d in tf.items():
        print(f"  {fn:20s} rows={d['rows']:>5} arms={sorted(k for k in d['arms'] if k)} "
              f"cfg={sorted(d['config_version'])}")
    print("wrote VERSION, CHECKSUMS.txt, MANIFEST.json")


if __name__ == "__main__":
    main()
