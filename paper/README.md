# Overleaf handoff — the intended Overleaf project, durably mirrored

## Current title

**From Feedback to Revision: When Do Multi-Agent Roles Look Load-Bearing?**

## Current story

Roles do not primarily improve the first answer. The difference appears
after an external correctness signal arrives: role-structured teams revise,
while role-free teams largely resubmit. This behavioral difference becomes a
recovery difference and replicates for gemma-4 across Omni-MATH and SciBench.

## The paper in one paragraph

Multi-agent LLM systems are specified as role diagrams, and the diagram is
read as a mechanism. We ask which **phase** of the work that organization
actually carries. Deleting every role instruction — topology, model,
information, retry budget and evaluator held fixed — destroys the intended
division of labor but leaves first-pass solving intact. The difference
appears only after a team is told its answer is wrong: both teams hold the
same six deliberation cycles and the role-free team draws *more* oracle
verdicts, so it is neither stopped early nor given less information. What
differs is use — told they are wrong, one team revises and the other
resubmits. That behavioral split becomes a recovery split, and the same
dissociation reappears in a second free-response domain.
---

## PRIVATE HANDOFF LINKS — DO NOT COMPILE OR COPY INTO THE DOUBLE-BLIND PAPER

| | |
|---|---|
| Private GitHub | `https://github.com/ChihHsuan-Yang/AAMAS2027-AgentProtocols` |
| Overleaf browser project | `https://www.overleaf.com/project/6abae70ebd16e2dc9cdecee6` |
| Overleaf git remote | `https://git@git.overleaf.com/6abae70ebd16e2dc9cdecee6` |
| Private HF data artifact | `https://huggingface.co/datasets/AgentsSci/AAMAS2027-Roles` |

These appear **only** in this file, which is never compiled. An anonymity
audit runs on the rendered PDF, not the source, so a link here cannot leak —
but do not paste one into a `.tex` file.

---

## This directory IS the Overleaf project

Overleaf git access is currently blocked (affiliation link pending; see
`../HANDOFF_CURRENT.md`). **That is not a blocker and nothing is at risk:**
`paper/` is a complete, verified mirror.

**Verified 2026-10-02:** a fresh `git clone` of this repository, building
`paper/` and nothing else, produces a PDF whose extracted text is
byte-identical to the working copy — exit 0, 9 pages, 0 undefined citations,
pagecheck pass. If the Overleaf project vanished today it could be rebuilt
from this directory alone. `/tmp/aamas_ol` is convenience only.

## Build

```bash
cd paper
for d in main supplement; do
  pdflatex -interaction=nonstopmode $d.tex
  bibtex $d
  pdflatex -interaction=nonstopmode $d.tex
  pdflatex -interaction=nonstopmode $d.tex
done
python3 ../scripts/pagecheck.py main.pdf      # NO PIPE: `| tail` makes $? report tail
```

The page check applies to `main.pdf` only; the supplement has no limit.

`latexmk -pdf main.tex` works on a warm tree but fails from a clean one — it
schedules bibtex before any `.aux` exists.

## Gates before any freeze

**Run `python3 scripts/final_freeze.py` from the project root** — it runs
all of the below over *both* documents and writes `FINAL_FREEZE.json`.
Individually:

```bash
python3 ../scripts/pagecheck.py main.pdf              # exit 0: main text ends p8
grep -a -c "Undefined citation" main.log              # 0
grep -a -c "multiply defined" main.log                # 0
grep -n "Arm~\?[ABC]" main.tex sections/*.tex         # empty
python3 ../scripts/check_terminology_pdfs.py          # exit 0
shasum -a 256 aamas.cls                               # == ../paper_support/aamas_official/aamas.cls
pdftotext main.pdf - | grep -icE "argonne|github|huggingface|overleaf"   # 0
```

## Hand-written vs generated

| path | | |
|---|---|---|
| `main.tex` | preamble, venue block, abstract | **hand-written** |
| `sections/*.tex` | 10 sections | **hand-written** |
| `refs.bib` | 27 entries, each machine-verified against arXiv or CrossRef; 26 are cited and render | **hand-written** |
| `tables/*.tex` | 6 result tables | **generated** — see `tables/README.md` |
| `figures/*.pdf` | figures LaTeX includes | **generated** — see `figures/README.md` |
| `aamas.cls`, `ACM-Reference-Format.bst` | official IFAAMAS kit | **upstream — never modify** |
| `TERMINOLOGY.md` | internal condition-code map | internal, never compiled |

Figures exist in **two** places: `figures/` at the project root, where the
generators write, and `paper/figures/`, where LaTeX resolves
`\includegraphics`. The copies under `paper/` are what the PDF uses and what
Overleaf needs; regenerating a figure is not finished until it is copied over.

## Canonical numeric source

No number in this manuscript is hand-maintained.

```
experiments/results/FROZEN/                  Omni-MATH, 11,600 rows, sha256-manifested
experiments/results/xdomain/FROZEN_SCIBENCH/ SciBench, 2,296 rows, sha256 10068f72cfd936d3…
        |
        v
analysis/scripts/FINAL_TABLES.py             the ONLY source of a number
        |--> analysis/out/FINAL_TABLES_OUTPUT.txt
        `--> analysis/out/FIGDATA.json
        |
        +--> analysis/scripts/mk_tables.py   -> paper/tables/*.tex
        `--> analysis/scripts/mk_fig*.py     -> figures/*.pdf -> paper/figures/
```

```bash
python3 analysis/scripts/FINAL_TABLES.py > analysis/out/FINAL_TABLES_OUTPUT.txt
python3 analysis/scripts/mk_tables.py          # --check verifies without writing
python3 analysis/scripts/mk_fig1_story.py
python3 analysis/scripts/mk_fig2_xdomain.py
cp figures/fig1_v1_story.pdf figures/fig2_v2_xdomain.pdf paper/figures/
```

What may be asserted is governed by `../APPROVED_CLAIMS.md`; its DEAD table
is binding. **After any change to `FINAL_TABLES.py`, re-derive that file
too** — it has gone stale behind the manuscript twice, and workers are told
to follow it over their own derivations.

## Where the data live — HF `AgentsSci/AAMAS2027-Roles` **v1.1.0, PRIVATE**

**Omni-MATH** — raw frozen trajectories (`campaign_v2`, `actor3`, `armCp`);
normalized trajectory table; role messages; evaluator calls; enforcement
events; prompts and configs; manifests.

**SciBench** — raw frozen trajectories (2,296, over the complete 574-problem
matched slice); normalized trajectory table; role messages; evaluator calls;
SciBench-specific prompts and config; SciBench manifest.

**Condition codes.** Raw columns keep `A`/`B`/`C`/`Cp` because renaming would
break provenance against every manifest and analysis script. The manuscript
uses semantic names:

| raw | manuscript |
|---|---|
| A | role-structured |
| B | role-free |
| C | structurally enforced |
| Cp (written C′ in `TERMINOLOGY.md`) | context-restored structural enforcement |

The artifact must stay private through review; `hf_artifact/scripts/preflight_public.py`
fails by design until institution-naming rows are sanitized after acceptance.

## Main paper vs supplement

Two documents, one project. `main.tex` is the 8-page submission: the 10
sections, Figures 1–2, and `tables/main_role_collapse.tex`.
`supplement.tex` is a second document in **this same directory**, sharing
`aamas.cls`, `refs.bib` and `tables/`, so a regenerated table lands in both
at once and the two can never disagree. It carries the other six generated
tables and has no page limit.

**The main paper must remain readable without the supplement.** It points;
it never depends. If you find yourself moving an argument step into the
supplement, move it back.

Build the supplement the same way (`pdflatex supplement` → `bibtex
supplement` → `pdflatex` ×2) and gate it the same way — it has no page
limit, but it must stay anonymous and free of internal condition codes.
`scripts/final_freeze.py` does both documents.

## Current state

- **8 main-text pages**, references on 9. Supplement 11 pages.
- `python3 scripts/final_freeze.py` → **ALL_GATES_PASS true**, FAILED_GATES
  empty. That is the single command that answers "is this releasable?".
