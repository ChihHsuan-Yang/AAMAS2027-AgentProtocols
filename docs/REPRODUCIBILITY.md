# Reproducibility

Back to [the project README](../README.md) ·
[artifact map](PAPER_ARTIFACT_MAP.md) ·
[data provenance](DATA_PROVENANCE.md) ·
[trace availability](TRACE_AVAILABILITY.md) ·
[invalid and superseded](INVALID_AND_SUPERSEDED.md)

Three levels, in increasing cost. **Most work needs only level A.**
Do not re-run inference to reproduce a figure whose rows already exist.

| level | what it does | cost | needs a live endpoint? |
|---|---|---|---|
| **A** | regenerate every figure and table from the frozen rows | ~1 min | no |
| **B** | re-derive every number, and check the paper against them | ~2 min | no |
| **C** | re-run the campaign from scratch | ~8 h | **yes**, and it will **not** reproduce the frozen numbers |

Working directory for everything below is the repository root unless a block
says otherwise.

---

## Environment

What the frozen results were produced under. There is **no lockfile**; this
is a record, not a pin.

| | |
|---|---|
| Python | 3.9.6 (macOS system `python3`, Darwin arm64) |
| packages | numpy 2.0.2 · pandas 2.3.3 · pyarrow 21.0.0 · matplotlib 3.9.4 · requests 2.32.5 |
| LaTeX | TeX Live 2026 (TinyTeX), `pdflatex` + `bibtex`; `pdftotext`/`pdfinfo` from poppler |

Levels A and B need numpy, plus pandas/pyarrow for the single-agent table
and matplotlib for figures. Level C adds `requests`.

**No HPC, no scheduler, no cluster filesystem.** Every trajectory was
produced by an HTTP client running on one laptop against a remote inference
gateway. Any document implying a job queue or a cluster results directory
for this project is wrong.

---

## A. Regenerate figures and tables from canonical data

```bash
python3 analysis/scripts/FINAL_TABLES.py > analysis/out/FINAL_TABLES_OUTPUT.txt
python3 analysis/scripts/mk_tables.py              # -> paper/tables/*.tex
python3 analysis/scripts/mk_fig1_bf.py             # -> figures/ AND paper/figures/
python3 scripts/mk_artifact_map.py                 # -> docs/PAPER_ARTIFACT_MAP.md
python3 scripts/mk_trace_availability.py           # -> docs/TRACE_AVAILABILITY.md
```

| item | command | input | expected output | verify |
|---|---|---|---|---|
| all numbers | `python3 analysis/scripts/FINAL_TABLES.py` | `experiments/results/FROZEN/` | `analysis/out/FINAL_TABLES_OUTPUT.txt` (~22 s) | re-running is **byte-identical** — RNG seeded `20261008` |
| all 7 tables | `python3 analysis/scripts/mk_tables.py` | the canonical output above | `paper/tables/*.tex` | `mk_tables.py --check` → exit 0 |
| Figure 1 | `python3 analysis/scripts/mk_fig1_bf.py` | `analysis/out/FIGDATA.json`, `FIGDATA_BF.json`, `FIGDATA_GATE.json` | `paper/figures/fig1_v3_story.pdf` | hash stable across runs |
| both PDFs | `cd paper && for d in main supplement; do pdflatex -interaction=nonstopmode $d; bibtex $d; pdflatex -interaction=nonstopmode $d; pdflatex -interaction=nonstopmode $d; done` | `paper/` | `main.pdf` (9 pp), `supplement.pdf` (11 pp) | see the one-command gate below |

The figure generators copy into `paper/figures/` themselves — LaTeX resolves
`\includegraphics` there, not against `figures/`, and the manual copy step
used to be skippable. Figure PDFs are **byte-reproducible**: the wall-clock
`CreationDate` is stripped, so a changed hash means changed *data*.

`latexmk -pdf main.tex` works on a warm tree but **fails from a clean one** —
it schedules bibtex before any `.aux` exists. Use the explicit sequence.

### The one command that answers "is this releasable?"

```bash
python3 scripts/final_freeze.py       # exit 0 = every gate passes
```

Runs both documents through: build, page limit (main text must end p8),
undefined citations and references, multiply-defined labels, anonymity over
the **rendered text** of both PDFs, internal condition codes in either PDF
or any shipped figure, unrun placeholders, class-file integrity, table
freshness, and bibliography counts. Writes `FINAL_FREEZE.json`, which
records the text hashes — not byte hashes: pdflatex embeds a wall-clock
timestamp, so a PDF's byte hash identifies a *build*, while
`pdftotext x.pdf - | shasum -a 256` identifies the *paper*.

---

## B. Reproduce the analysis from existing data

```bash
# integrity first -- the numbers mean nothing if the rows moved
cd experiments/results/FROZEN && python3 -c "
import json,hashlib
m=json.load(open('MANIFEST.json'))
for f,v in m['files'].items():
    h=hashlib.sha256(open(f,'rb').read()).hexdigest()
    print(f, 'OK' if h==v['sha256'] else 'MISMATCH')"
cd -

python3 analysis/scripts/FINAL_TABLES.py > /tmp/ft.txt && diff /tmp/ft.txt analysis/out/FINAL_TABLES_OUTPUT.txt
python3 adjudication/analyze.py                 # the collapse second opinion, ~1 s
python3 scripts/verify_paper_numbers.py         # cross-check against the live tree, ~25 s
python3 scripts/smoke_gates.py experiments/results/smoke/smoke_v3.jsonl   # 15/15
```

**Do not re-run `adjudication/adjudicate.py`.** It issues new judge calls and
would produce a different verdict file; the committed `VERDICTS.jsonl` is the
one every reported adjudication number comes from.

Two tables read sources **outside** the frozen snapshot and say so in their
own output: the single-agent comparator (external corpus — if that sibling
project moves, the section prints `UNAVAILABLE:` rather than silently
dropping) and the adjudication (`adjudication/`, in git).

Two scoring conventions are reported throughout, per `PREREGISTRATION.md`:
**PREREG** (ungraded counted incorrect; *primary*) and **AS-GRADED**
(ungraded dropped; *sensitivity only*). They disagree in sign for the
enforced condition, because it carries 8–17% one-sided attrition. Never
quote as-graded as a headline.

---

## C. Re-run the campaign

**This will not reproduce the frozen numbers.** Temperature 0 is not
bit-deterministic on this endpoint, so a re-run produces different
trajectories and different values. That is why the snapshot is
irreplaceable rather than regenerable, and why its sha256 manifest is what
makes a reported number checkable.

| | |
|---|---|
| endpoint | ALCF Sophia vLLM gateway (HTTPS; the URL is in `PROJECT_PATHS.md`) |
| auth | a Globus bearer token from a helper script outside this repo. **No credential is in this repository**; the runner holds the token in memory and scrubs it from every error string, and a smoke gate checks trajectory rows for bearer/JWT material. Re-auth is interactive — it needs a browser and a human |
| cost | ~8 h at concurrency 24 for the 9,600-row campaign |
| calls | 30 actor + 6 evaluator per trajectory, capped and recorded on every row |

```bash
python3 experiments/runner.py --dry-run --n 2 --arms A,B,C     # zero API calls
python3 experiments/make_manifest.py 1600                      # needs the sibling parquet
python3 experiments/runner.py --n 1600 --arms A,B,C \
    --actors "openai/gpt-oss-120b,google/gemma-4-31B-it" \
    --out experiments/results/main/campaign_v2.jsonl \
    --run-id main-n1600-v2 --concurrency 24
```

Manifests are deterministic and hash-verified (n=1600 `39cdeeecffc383a7`,
n=400 `94955e7f65332258`, n=25 `04009d74a21bc13a`). `make_manifest.py`
reads a parquet in a sibling project and **fails without it**;
`FINAL_TABLES.py` degrades gracefully in the same situation, `make_manifest`
does not.

**Resume is automatic and is the completion criterion.** Writes are one
fsync'd JSONL line per completed trajectory; on restart the runner reads the
output file and skips every completed `(problem_uid, arm, actor_model)`. Re-run
the identical command. Rows recorded `model_unavailable` are **not** treated
as complete and are retried. The run is done when every cell in the manifest
census is full — not when the process exits, which it can do with rows
missing.

### Seeds

There is **no seed in the generation path** and no replicate dimension:
decoding is temperature 0, each cell ran once, and the endpoint is not
bit-deterministic. The only seed in the project is in the analysis —
`np.random.default_rng(20261008)` for the bootstrap — which is why level A
is byte-reproducible and level C is not.
