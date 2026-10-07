#!/usr/bin/env python3
"""Build the anonymous supplementary-material ZIP.

    python3 scripts/mk_supp_zip.py --pdf PATH/TO/supplement.pdf
        -> submission/supplementary_material.zip

Contents: supplement.pdf (built elsewhere with a full TeX installation and
passed in), the prompts,
runner and analysis scripts, the canonical analysis outputs and the sha256
manifests. Every text file is copied through REDACT (endpoint URL, auth
helper, local paths, organisation and dataset names), and the staged tree is
then searched for every identifying token; any hit aborts the build. Raw
trajectories are not included (about 300 MB; released on acceptance).
"""
import hashlib
import os
import re
import shutil
import subprocess
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "submission")
# a fresh staging directory per build: nothing is ever deleted (the build
# machine may forbid deletion); stale stages are ignored by git
STAGE = os.path.join(OUT_DIR, "stage_" + __import__("time").strftime("%Y%m%dT%H%M%S"),
                     "supplementary_material")
ZIP = os.path.join(OUT_DIR, "supplementary_material.zip")

FILES = [
    "experiments/runner.py", "experiments/runner_xdomain.py", "experiments/prompts.py",
    "experiments/schemas.py", "experiments/_xdom_prompt_patch.py", "experiments/run_bf.sh",
    "experiments/bf_requeue.py", "experiments/bf_status.py", "experiments/bf_warm.py",
    "experiments/bf_preflight.py", "experiments/bf_manifest.py", "experiments/make_manifest.py",
    "experiments/test_bf_delivery.py", "experiments/test_afs.py",
    "analysis/scripts/FINAL_TABLES.py", "analysis/scripts/INDEPENDENT_AUDIT.py",
    "analysis/scripts/bf_numbers.py", "analysis/scripts/bf_gate.py",
    "analysis/scripts/mk_tables.py", "analysis/scripts/mk_table_main.py",
    "analysis/scripts/mk_gate_table.py", "analysis/scripts/mk_afs_table.py",
    "analysis/scripts/mk_bf_replication.py",
    "analysis/scripts/mk_fig1_bf.py", "analysis/scripts/mk_figstyle.py",
    "analysis/scripts/stat_audit_a7_power.py", "analysis/scripts/xdom_analyze.py",
    "analysis/scripts/r15_p1a_final.py",
    "analysis/out/FINAL_TABLES_OUTPUT.txt", "analysis/out/INDEPENDENT_AUDIT_OUTPUT.txt",
    "analysis/out/BF_TABLES_OUTPUT.txt", "analysis/out/BF_TABLES_OUTPUT_chain2.txt",
    "analysis/out/BF_GATE_OUTPUT.txt", "analysis/out/FIGDATA.json",
    "analysis/out/FIGDATA_BF.json", "analysis/out/FIGDATA_BF_chain2.json",
    "analysis/out/FIGDATA_GATE.json",
    "experiments/results/FROZEN/MANIFEST.json",
    "experiments/results/xdomain/FROZEN_SCIBENCH/MANIFEST.json",
    "experiments/results/bf/MANIFEST_BF.json",
    "experiments/results/bf/chain2/MANIFEST.json",
]

# (pattern, replacement), applied in order to every staged text file.
REDACT = [
    (r"https?://[^\s\"'<>]*alcf[^\s\"'<>]*", "https://INFERENCE-ENDPOINT/v1"),
    (r"/Users/[^\s\"'<>)\]]+", "LOCAL-PATH"),
    (r"/home/[A-Za-z0-9_.-]+/[^\s\"'<>)\]]*", "LOCAL-PATH"),
    (r"/sessions/[^\s\"'<>)\]]+", "LOCAL-PATH"),
    (r"sophia_vllm", "hosted_vllm"),
    (r"(?i)\balcf\b", "ANON-HPC"),
    (r"(?i)\bsophia\b", "CLUSTER"),
    (r"IEEE2026_BigData_MAS-4-Science-Matching", "PRIOR-CORPUS"),
    (r"IEEE-BigData-SciAgentTrace", "PRIOR-CORPUS-REPO"),
    (r"IEEE-BigData corpus", "previously released corpus"),
    (r"IEEE-BigData", "PRIOR-CORPUS"),
    (r"(?i)AgentsSci", "ANON-ORG"),
    (r"AAMAS2027-Roles", "ANON-DATASET"),
    (r"inference_auth_token", "auth_token_helper"),
    (r"(?i)globus-sdk", "auth-sdk"),
    (r"(?i)globus", "auth"),
    (r"(?i)argonne", "ANON-LAB"),
    (r"(?i)github\.com/[^\s\"'<>)]*", "REPO-URL"),
    (r"(?i)huggingface\.co/[^\s\"'<>)]*", "DATA-URL"),
    (r"(?i)\bhf\.co/[^\s\"'<>)]*", "DATA-URL"),
    (r"(?i)bellayang|chihhsuan|uhxinyang|xinyang", "ANON"),
    (r"\blxy\b", "ANON"),
    (r"(?i)mac-?mini[^\s\"'<>]*", "ANON-HOST"),
]
FORBIDDEN = ["argonne", "alcf", "anl.gov", "bellayang", "chihhsuan", "xinyang", "agentssci",
             "huggingface", "github.com", "sophia", "sciagenttrace", "bigdata", "/users/",
             "globus", "overleaf", "aamas2027-roles", "inference_auth", "macmini"]
FORBIDDEN_RE = [re.compile(r"\blxy\b", re.I)]

README = """# Supplementary material (anonymous)

* `supplement.pdf` -- the supplementary document referenced by the paper.
* `code/experiments/` -- the prompts (`prompts.py`; the SciBench variants are
  produced by `_xdom_prompt_patch.py`), the JSON schemas of the enforced condition
  (`schemas.py`), the runners (`runner.py` for Omni-MATH, `runner_xdomain.py` for
  SciBench), the batch driver (`run_bf.sh`) and its helpers, and the offline tests
  (`test_bf_delivery.py`, `test_afs.py`; zero API calls).
* `code/analysis/scripts/` -- every script that produces a number, table or figure:
  `FINAL_TABLES.py` (frozen snapshot), `INDEPENDENT_AUDIT.py` (an independent
  re-implementation), `bf_numbers.py` (the feedback-matched condition),
  `bf_gate.py` (submission gate, verdict-matched recovery, the forced-submission
  run), `mk_*.py` (tables and Figure 1).
* `code/analysis/out/` -- the canonical outputs those scripts write; every number
  in the paper and in `supplement.pdf` can be found in them.
* `code/experiments/results/**/MANIFEST*.json` -- sha256 manifests of the frozen
  snapshot and of the feedback-matched runs.

For anonymity, the inference endpoint URL, the name of the authentication helper,
local file paths and organisation/dataset names have been replaced by placeholders
(`INFERENCE-ENDPOINT`, `auth_token_helper`, `LOCAL-PATH`, `ANON-*`, `PRIOR-CORPUS*`).
The raw trajectories (about 300 MB of JSONL) are not included; they will be
released with the camera-ready version. The scripts read them from the paths
recorded in the manifests.
"""


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def build_supplement():
    paper = os.path.join(ROOT, "paper")
    for _ in range(1):
        subprocess.run("pdflatex -interaction=nonstopmode supplement.tex", shell=True,
                       cwd=paper, capture_output=True)
        subprocess.run("bibtex supplement", shell=True, cwd=paper, capture_output=True)
        for _ in range(2):
            r = subprocess.run("pdflatex -interaction=nonstopmode supplement.tex", shell=True,
                               cwd=paper, capture_output=True)
    pdf = os.path.join(paper, "supplement.pdf")
    assert os.path.exists(pdf), "supplement.pdf was not built"
    return pdf


def main():
    os.makedirs(os.path.join(STAGE, "code"))
    missing = [f for f in FILES if not os.path.exists(os.path.join(ROOT, f))]
    assert not missing, ("missing inputs", missing)
    for f in FILES:
        src = os.path.join(ROOT, f)
        dst = os.path.join(STAGE, "code", f)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        text = open(src, encoding="utf-8", errors="strict").read()
        for pat, rep in REDACT:
            text = re.sub(pat, rep, text)
        open(dst, "w", encoding="utf-8").write(text)
    open(os.path.join(STAGE, "README.md"), "w").write(README)
    pdf = sys.argv[sys.argv.index("--pdf") + 1] if "--pdf" in sys.argv else None
    assert pdf and os.path.exists(pdf), "pass --pdf PATH to a built supplement.pdf"
    if pdf:
        shutil.copy(pdf, os.path.join(STAGE, "supplement.pdf"))
        txt = subprocess.run(["pdftotext", pdf, "-"], capture_output=True, text=True).stdout
        open(os.path.join(os.path.dirname(STAGE), "supplement.txt"), "w").write(txt)
    # anonymity gate over every staged text file and the PDF's text
    hits = []
    for dirpath, _, names in os.walk(STAGE):
        for n in names:
            p = os.path.join(dirpath, n)
            if n.endswith(".pdf"):
                s = open(os.path.join(os.path.dirname(STAGE), "supplement.txt")).read().lower()
            else:
                s = open(p, encoding="utf-8").read().lower()
            for k in FORBIDDEN:
                if k in s:
                    hits.append((os.path.relpath(p, STAGE), k))
            for rx in FORBIDDEN_RE:
                if rx.search(s):
                    hits.append((os.path.relpath(p, STAGE), rx.pattern))
    if hits:
        for h in hits:
            print("IDENTIFYING:", h)
        sys.exit("anonymity gate FAILED; no zip written")
    base = os.path.dirname(STAGE)
    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:   # "w" truncates
        for dirpath, _, names in os.walk(STAGE):
            for n in sorted(names):
                p = os.path.join(dirpath, n)
                z.write(p, os.path.relpath(p, base))
    n = sum(len(f) for _, _, f in os.walk(STAGE))
    print("anonymity gate PASSED over {} files".format(n))
    print("wrote {}  {:.1f} KB  sha256 {}".format(
        os.path.relpath(ZIP, ROOT), os.path.getsize(ZIP) / 1024, sha256(ZIP)[:16]))


if __name__ == "__main__":
    main()
