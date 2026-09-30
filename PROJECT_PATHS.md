# PROJECT_PATHS — canonical location map

**Verified 2026-09-30.** Every path below was checked to exist at the time of
writing. "Authoritative" means a number or artifact may be sourced from here.
"Derived" means it was produced from an authoritative source and may be
regenerated or deleted without loss.

Check a path before trusting it: paths in this project have moved before.

---

## LOCAL_PROJECT_ROOT — authoritative for code and workflow

```
/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols
```

The git working tree. Remote:
`https://github.com/ChihHsuan-Yang/AAMAS2027-AgentProtocols` (`origin/main`).
Packed size 2.70 MiB — raw trajectory JSONL is deliberately excluded (see
FROZEN_RESULTS below).

**As of 2026-09-30 the local branch is ahead of `origin/main` by 16 commits.**
A clone of the GitHub remote alone does NOT have the current state. Push
before treating GitHub as the handoff surface.

---

## OVERLEAF_CLONE — authoritative for the manuscript *as submitted*

```
/tmp/aamas_ol            (git clone of git.overleaf.com/6abae70ebd16e2dc9cdecee6)
```

Contains `main.tex`, `refs.bib`, `sections/*.tex` — 12 tracked files, HEAD
`128771e`. **This is a `/tmp` path and will not survive a reboot.** Re-clone
from Overleaf if it is gone; the project id is above, the credential is in the
clone's `origin` URL and in Bella's Overleaf account, nowhere in this repo.

**The Overleaf clone is STALE relative to `paper/` in the repo** — it has the
9 sections from commit `128771e` but not the class file, the `.bbl`, or the
subsequent section rewrites. The repo's `paper/` is the working copy; Overleaf
is where it must be synced before Bella submits.

---

## HPC_CODE_ROOT and HPC_RESULTS_ROOT — there are none

**This project has no HPC code root and no HPC results root.** Nothing was ever
staged onto a cluster filesystem, and no scheduler was used. All computation
ran from LOCAL_PROJECT_ROOT on Bella's laptop as an HTTP client against a
remote inference endpoint:

```
https://inference-api.alcf.anl.gov/resource_server/sophia/vllm/v1
```

That is ALCF's Sophia vLLM inference gateway, reached over HTTPS. There is no
`qsub`, no PBS job, no `/lus/eagle` path, and no code or results on a login
node. Any handoff document claiming an HPC results directory for this project
is wrong.

Auth helper (path only, never contents):
`/Users/bellayang/work/agent-e/mas-eval/inference_auth_token.py`, which reads a
Globus token cache under `~/.globus/app/.../tokens.json`. See README
§"Endpoint and authentication".

---

## FROZEN_RESULTS — **authoritative. The final numeric truth.**

```
/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols/experiments/results/FROZEN/
  MANIFEST.json        922 B     sha256 + rows + bytes for each file   [IN GIT]
  campaign_v2.jsonl    227.5 MB  9,600 rows  sha256 e4e53cb117d91129…  [NOT IN GIT]
  actor3.jsonl          46.0 MB  1,200 rows  sha256 fa22a446d5314bb6…  [NOT IN GIT]
  armCp.jsonl           23.6 MB    800 rows  sha256 038e08aec4d4aee1…  [NOT IN GIT]
```

Frozen at `2026-09-30T10:09:30`. 11,600 rows total, 11 cells.
All three hashes **verified 2026-09-30** against `MANIFEST.json`.

**READ THIS.** The three `.jsonl` files are excluded by `.gitignore` line 14
(`experiments/results/**/*.jsonl`). Only `MANIFEST.json` is committed. A fresh
`git clone` therefore CANNOT reproduce a single headline number. The frozen
data exists in exactly one place: this local directory. It is not backed up,
not on HuggingFace, and not recoverable from the runner — re-running would
produce different trajectories, because temperature 0 is not deterministic on
this endpoint. **Copy these three files off this machine before anything else.**

---

## RAW_LOGS — derived (audit trail), also not in git

```
experiments/results/main/
  campaign_v2.jsonl  + .log      byte-identical to FROZEN/campaign_v2.jsonl (verified)
  actor3.jsonl       + .log      byte-identical to FROZEN/actor3.jsonl (verified)
  armCp.jsonl        + .log      byte-identical to FROZEN/armCp.jsonl (verified)
  campaign_v1_TRUNCATION_BUG.jsonl + .log   QUARANTINED — never pool
experiments/results/smoke/
  smoke_v3.jsonl + .log          the 78-trajectory gate run (current)
  smoke_v1_prefix_PREFIX_BUG.jsonl  QUARANTINED — pre-fix validators
experiments/results/{dryrun,realtest,dr_hf,unavail}.jsonl   scratch
```

`main/` and `FROZEN/` hold the same bytes today. Use `FROZEN/`: it is the one
with a manifest, and `main/` is a live output directory that a re-run would
append to.

---

## ANALYSIS_SCRIPTS — authoritative for code, derived for output

```
analysis/scripts/FINAL_TABLES.py        THE canonical table generator (712 lines)
analysis/scripts/mk_fig1_dissociation.py  Figure 1 (3 variants)
analysis/scripts/mk_figstyle.py           shared style + figdata() accessor
analysis/scripts/{d,r,x}*.py            ~40 exploratory scripts, historical
scripts/verify_paper_numbers.py         live cross-check of headline figures
scripts/smoke_gates.py                  the 15 launch gates
adjudication/{build_sample,adjudicate,analyze}.py   blinded adjudication pipeline
experiments/{runner,schemas,prompts,make_manifest}.py   the campaign itself
experiments/infra/*.py                  endpoint probes, concurrency ladder
```

**Only `FINAL_TABLES.py` may source a manuscript number.** It reads
`FROZEN/` exclusively (plus two clearly-marked external sources, T17 and T23).
Every other script under `analysis/scripts/` reads `experiments/results/main/`
or older cuts and exists for the audit record; its printed numbers may predate
a correction. Treat them as history, not as current results.

```
analysis/out/FINAL_TABLES_OUTPUT.txt    committed output of FINAL_TABLES.py
analysis/out/FIGDATA.json               figure input, written by T28 from FROZEN/
analysis/results/*.{csv,parquet}        derived outputs of the d/r/x scripts
                                        (.parquet is gitignored)
analysis/audit/                         untracked scratch from the stats audit
```

---

## FIGURES — derived, but **owned by another worker**

```
figures/fig1_v1_grouped.{pdf,png}     current — grouped columns, 1 column wide
figures/fig1_v2_slopes.{pdf,png}      current — small-multiple slopes, 1 column
figures/fig1_v3_dumbbell.{pdf,png}    current — dumbbell rows, 2 columns
figures/fig1_dissociation.{pdf,png}   SUPERSEDED — do not revive
```

Regenerate (two steps — the figure script needs `FIGDATA.json` first):

```bash
python3 analysis/scripts/FINAL_TABLES.py          # T28 writes analysis/out/FIGDATA.json
python3 analysis/scripts/mk_fig1_dissociation.py  # writes all three variants
```

The current generation reads `analysis/out/FIGDATA.json`, which T28 of
`FINAL_TABLES.py` derives from `FROZEN/`, and prints a provenance line (frozen
timestamp, n, the three sha prefixes) on every run. Verified exit 0
2026-09-30.

`fig1_dissociation.*` is the **previous** generation. It plotted byte-identity
collapse — a **LOWER BOUND ONLY** metric (recall 0.262) whose scope reading is
dead claim **F22** — and read `experiments/results/main/` rather than
`FROZEN/`. Kept for the record; must not be captioned as "organizational
collapse" and must not be revived.

**`figures/` and the figure scripts are owned by the figures/paper worker.**
Coordinate before touching either. No figure is `\includegraphics`-ed into
`paper/main.tex` yet.

## TABLES

```
tables/        EMPTY. No table artifacts are stored as files.
```

Tables live in two places instead: `analysis/out/FINAL_TABLES_OUTPUT.txt`
(the frozen numbers, T0–T27) and hand-written LaTeX `table` environments in
`paper/sections/results.tex` (3 of them). There is no table-generation step
that writes into `tables/`.

---

## ADJUDICATION — authoritative for the blinded-judge result

```
adjudication/
  RUBRIC_v1.md          sha256 4f624de5b1073940…   frozen before first judgement
  ITEMS_blinded.jsonl   sha256 997d0185133a1205…   171 items, role tokens neutralized
  KEY.jsonl             sha256 94fa8ee76b532948…   171 unblinding keys (withheld from judge)
  VERDICTS.jsonl        sha256 a6d18adabbd3f547…   513 calls = 171 items x 3 reps
  SAMPLING_MANIFEST.json                           strata, seed 20260929
  PROTOCOL.md                                      the protocol, incl. 3 defects found mid-run
  build_sample.py / adjudicate.py / analyze.py
  adjudicate.log (0 B) / adjudicate2.log (556 B)
```

All four hashes **verified 2026-09-30**; all are committed to git. This is the
only headline evidence in the project that is fully reproducible from a clone.

**Not in the frozen snapshot** — T23 of `FINAL_TABLES_OUTPUT.txt` reads these
files directly and says so. Judge is Opus 5 via a local proxy; re-running
`adjudicate.py` needs that proxy and would produce new verdicts. Use the
committed `VERDICTS.jsonl` and re-run only `analyze.py`.

---

## PAPER_SUPPORT — authoritative for the venue template

```
paper_support/aamas_official/
  aamas.cls                  the OFFICIAL IFAAMAS class
  AAMAS_2026_sample.tex      official sample, incl. the copyright block
  ACM-Reference-Format.bst
  sample.bib
  PROVENANCE.md              source URL, the User-Agent/Referer needed to fetch it,
                             and the verified 2026 submission rules
paper_support/BIB-AUDIT-2026-09-29.txt   per-entry bibliography verification
```

`aamas.cls` and `ACM-Reference-Format.bst` are copied into `paper/`; the class
must not be modified (an explicit AAMAS rule). **PROVENANCE.md records that
these are the AAMAS-2026 instructions** — 2027 had not published its own kit.

---

## PAPER — manuscript working copy

```
paper/main.tex            preamble, abstract, CCS, copyright block
paper/sections/*.tex      10 sections
paper/refs.bib            24 entries
paper/aamas.cls           the official class (copy)
paper/main.pdf            9 pages — over the 8-page main-text limit
paper/main.{aux,log,bbl,blg,out,fls,fdb_latexmk}   build artifacts (gitignored)
```

**Owned by the paper worker. Do not edit.**

---

## External sources reached by name from inside this repo

Two headline tables read files that live OUTSIDE this project. Both are
labelled in the output as not-in-the-frozen-snapshot. Both verified present
2026-09-30:

| used by | path | what for |
|---|---|---|
| `FINAL_TABLES.py` T17 | `…/IEEE-BigData-SciAgentTrace/analysis/hf_cache/release/data/trajectories/part-00000.parquet` (3.7 MB) | budget-matched single-agent control (A9) |
| `make_manifest.py` | `…/IEEE-BigData-SciAgentTrace/analysis/hf_cache/release/data/problems/part-00000.parquet` (2.7 MB) | the Omni-MATH problem set the manifests sample from |

Full prefix for both:
`/Users/bellayang/Documents/note/projects/IEEE-BigData-SciAgentTrace/analysis/hf_cache/release/`

If that sibling project moves, T17 prints `UNAVAILABLE: …` and the manifests
cannot be rebuilt. `FINAL_TABLES.py` degrades gracefully; `make_manifest.py`
does not.

---

## Authority summary

| location | authoritative for | regenerable? |
|---|---|---|
| `experiments/results/FROZEN/` | **every final number** | **NO — irreplaceable** |
| `adjudication/` (verdicts, key, rubric) | the blinded organization result | no (new judge calls ≠ old) |
| `experiments/manifest_omnimath2_n*.json` | which problems were run | yes, from the sibling parquet |
| GitHub `origin/main` | code and workflow | — |
| Overleaf project | the submitted manuscript | — |
| `analysis/out/FINAL_TABLES_OUTPUT.txt` | derived — a cached print of FROZEN | yes, exactly |
| `analysis/results/*` | derived — historical, may be stale | yes, but may not match FROZEN |
| `figures/` | derived — current variants read `FROZEN/` via `FIGDATA.json` | yes (but see FIGURES above) |
| `paper/main.pdf` | derived | yes, from `paper/` |
