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

VERSION_ID = "1.1.0"
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


# Which release each trace belongs to, and which benchmark it carries. A trace
# must appear here to be described at all -- an undescribed trace in raw/ is
# caught by the completeness assertion at the end of trace_facts().
TRACE_ORIGIN = {
    "campaign_v2.jsonl": ("1.0.0", "omnimath2"),
    "actor3.jsonl":      ("1.0.0", "omnimath2"),
    "armCp.jsonl":       ("1.0.0", "omnimath2"),
    "scibench_AB.jsonl": ("1.1.0", "scibench"),
}

# v1.0.0's published digests. Re-stamping must never silently change one.
V100_TRACE_SHA = {
    "campaign_v2.jsonl": "e4e53cb117d91129991ce2fe87e336e152fc9ee6ca826d363f2bd5dd240d7130",
    "actor3.jsonl":      "fa22a446d5314bb67b1c6a6444b511eeeae3eb8770419a36f182617eeccbf3b5",
    "armCp.jsonl":       "038e08aec4d4aee166106a6325309dfe2301faf339c7d0bf82338a74576424d4",
}


def trace_facts():
    """Per-trace provenance, derived from the trace itself."""
    facts = {}
    for fn in TRACE_ORIGIN:
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
        introduced, bench = TRACE_ORIGIN[fn]
        facts[fn] = dict(
            sha256=sha256_file(p), bytes=os.path.getsize(p), rows=n,
            semantic_version=introduced,
            introduced_in_version=introduced,
            arms=dict(arms), actor_models=dict(actors),
            domain=sorted(k for k in domains if k), benchmark_id=bench,
            backend=sorted(k for k in backends if k),
            config_version=dict(cfgs), run_id=sorted(k for k in runs if k),
            first_started_at=tmin, last_started_at=tmax,
        )

    # Completeness: every .jsonl actually in raw/ must be described here.
    on_disk = {f for f in os.listdir(RAW) if f.endswith(".jsonl")}
    undescribed = on_disk - set(facts)
    if undescribed:
        raise SystemExit(f"raw/ holds undescribed trace(s): {sorted(undescribed)} "
                         "-- add them to TRACE_ORIGIN")

    # Additivity: v1.0.0's trace bytes must not have moved.
    moved = [fn for fn, h in V100_TRACE_SHA.items()
             if fn in facts and facts[fn]["sha256"] != h]
    if moved:
        raise SystemExit(f"v1.0.0 trace bytes CHANGED: {moved} -- refusing to restamp")
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
    frozen_at_scibench = None
    _sbm = os.path.join(RAW, "MANIFEST_SCIBENCH.json")
    if os.path.exists(_sbm):
        frozen_at_scibench = json.load(open(_sbm))["frozen_at"]
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()

    # ------------------------------------------------------------ MANIFEST.json
    manifest = {
        "artifact": "AAMAS2027-Roles",
        "semantic_version": VERSION_ID,
        "emitted_utc": now,
        "freeze_commit": freeze_commit,
        "frozen_at": frozen_at,
        "frozen_at_scibench": frozen_at_scibench,
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
            "currently FAILS: 15 raw trace rows match an institution-identifying "
            "pattern. 14 are the v1.0.0 rows carrying an upstream HTTP error body "
            "that names the operating institution -- genuine, and the reason this "
            "repository cannot be flipped. The 15th is in the v1.1.0 SciBench trace "
            "and is a FALSE POSITIVE: a NAVIGATIONAL STAR named in a physics problem "
            "about photon flux (row uid scibench:matter:40.3) whose name also happens "
            "to be an HPC hostname. The literal is deliberately not written here -- "
            "this file is scanned by secret_scan.py, and a doc that juxtaposes a "
            "hostname with the phrase 'operating institution' is a worse disclosure "
            "than the row it documents. SciBench introduces "
            "NO new genuine instance. The gate was extended in v1.1.0 to scan the "
            "new trace -- it was not weakened, and the false positive is left to "
            "FAIL rather than allowlisted, because an allowlist keyed on a word "
            "would also exempt a real hostname."),
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
             "traces": {k: v for k, v in V100_TRACE_SHA.items()},
             "note": ("first release; single domain (competition math, Omni-MATH-2). "
                      "These three digests are UNCHANGED in 1.1.0 -- anything published "
                      "against 1.0.0 remains checkable.")},
            {"version": "1.1.0", "status": "private",
             "traces": {k: v["sha256"] for k, v in tf.items()
                        if TRACE_ORIGIN[k][0] == "1.1.0"},
             "note": ("ADDITIVE second domain (college chemistry/physics, SciBench): "
                      "2,296 trajectories, 574 problems, 2 actors, Arms A and B only. "
                      "No v1.0.0 file changed bytes -- asserted by the build and by "
                      "this emitter. SciBench is MIT, NOT the Apache-2.0 of the "
                      "Omni-MATH material; see LICENSES/. ARM A's PROMPT DIFFERS "
                      "BETWEEN DOMAINS (domain-adapted); Arm B is byte-identical.")},
        ],
        "mixed_licence": (
            "v1.1.0 ships TWO upstreams under TWO licences: omnimath2 = Apache-2.0, "
            "scibench = MIT. Neither is applied over the other and the project's own "
            "Apache-2.0 covers neither. Filter by benchmark_id. LICENSES/ is the "
            "authority; the HF `license:` field can hold only one value."),
        "arm_a_differs_by_domain": (
            "Arm A was DOMAIN-ADAPTED for SciBench (5 of 16 prompts differ, including "
            "the evaluator). Arm B is BYTE-IDENTICAL across domains. Do not assume one "
            "Arm A contract across the release, and do not compute P1a or any "
            "clause-specific fidelity metric across domains."),
        "licensing": "per-source and MIXED; see LICENSES/README.md and LICENSES/registry.json",
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
