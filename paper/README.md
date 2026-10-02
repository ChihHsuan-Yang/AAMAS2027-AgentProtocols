# Overleaf handoff — the intended Overleaf project, durably mirrored

## Current title

**From Feedback to Revision: When Multi-Agent Roles Become Load-Bearing**

## Current story

Roles do not primarily improve the first answer. The difference appears
after an external correctness signal arrives: role-structured teams revise,
while role-free teams largely resubmit. This behavioral difference becomes a
recovery difference and replicates for gemma-4 across Omni-MATH and SciBench.

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
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
python3 ../scripts/pagecheck.py main.pdf      # NO PIPE: `| tail` makes $? report tail
```

`latexmk -pdf main.tex` works on a warm tree but fails from a clean one — it
schedules bibtex before any `.aux` exists.

## Gates before any freeze

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
| `refs.bib` | 26 entries, each verified against arXiv or CrossRef | **hand-written** |
| `tables/*.tex` | 6 result tables | **generated** — see `tables/README.md` |
| `figures/*.pdf` | figures LaTeX includes | **generated** — see `figures/README.md` |
| `aamas.cls`, `ACM-Reference-Format.bst` | official IFAAMAS kit | **upstream — never modify** |
| `TERMINOLOGY.md` | internal condition-code map | internal, never compiled |

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
| Cp | context-restored structural enforcement |

The artifact must stay private through review; `scripts/preflight_public.py`
fails by design until institution-naming rows are sanitized after acceptance.

## Main paper vs supplement

Main paper: `main.tex`, the 10 sections, Figures 1–2, and
`tables/main_role_collapse.tex`. The other five generated tables are
supplement-bound — dispositions in `tables/README.md`. **The main paper must
remain readable without the supplement**; it points, never depends.

## Current state

- **8 main-text pages**, references on 9. Every gate above passes.
- **Supplement not yet assembled.** That is the one remaining consumer of the
  five supplement tables.

---

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

## Build

```bash
cd paper
latexmk -pdf -interaction=nonstopmode main.tex
python3 ../scripts/pagecheck.py main.pdf        # NO PIPE: `| tail` makes $? report tail
```

From a clean tree `latexmk` alone can fail (it schedules bibtex before any
`.aux` exists); if so: `pdflatex` → `bibtex main` → `pdflatex` → `pdflatex`.

## Gates that must pass before any freeze

```bash
python3 ../scripts/pagecheck.py main.pdf               # exit 0: main text ends p8
grep -a -c "Undefined citation" main.log               # 0
grep -n "Arm~\?[ABC]" main.tex sections/*.tex          # empty
python3 ../scripts/check_terminology_pdfs.py           # exit 0: no arm codes in figures
shasum -a 256 aamas.cls                                # must equal the official kit copy
```

---

## Layout

| path | what | hand-written or generated? |
|---|---|---|
| `main.tex` | preamble, venue block, abstract | hand-written |
| `sections/*.tex` | 10 sections | hand-written |
| `tables/*.tex` | 6 result tables | **generated** — never edit |
| `tables/README.md` | table index: question, source, denominator, prereg status | — |
| `figures/*.pdf` | figures the paper includes | **generated** — never edit |
| `refs.bib` | 26 entries, every one arXiv/CrossRef-verified | hand-written |
| `aamas.cls`, `ACM-Reference-Format.bst` | official IFAAMAS kit — **do not modify** | upstream |
| `TERMINOLOGY.md` | internal condition-code map | internal, never compiled |

Figures live in **both** `figures/` (project root, where the generators write)
and `paper/figures/` (where LaTeX resolves `\includegraphics`). The copies in
`paper/figures/` are what the PDF uses and what Overleaf will need.

---

## No number in this manuscript is hand-maintained

Every numeric literal traces to:

```
experiments/results/FROZEN/            sha256-manifested, never edited
experiments/results/xdomain/FROZEN_SCIBENCH/
        ↓
analysis/scripts/FINAL_TABLES.py       the ONLY source of a number
        ↓  analysis/out/FINAL_TABLES_OUTPUT.txt
        ↓  analysis/out/FIGDATA.json
analysis/scripts/mk_tables.py      →  paper/tables/*.tex
analysis/scripts/mk_fig*.py        →  figures/*.pdf
```

Regenerate everything:

```bash
python3 analysis/scripts/FINAL_TABLES.py > analysis/out/FINAL_TABLES_OUTPUT.txt
python3 analysis/scripts/mk_tables.py              # --check verifies without writing
python3 analysis/scripts/mk_fig1_story.py
python3 analysis/scripts/mk_fig2_xdomain.py
```

**What may be asserted is governed by `../APPROVED_CLAIMS.md`**, including a
DEAD table of claims that must not reappear. After any change to
`FINAL_TABLES.py`, re-derive that file too — it has gone stale behind the
manuscript twice.

---

## Reader-facing naming

Internal condition codes **never** appear in prose or figures. See
`TERMINOLOGY.md`:

| internal | manuscript |
|---|---|
| A | role-structured |
| B | role-free |
| C | structurally enforced |
| C′ | context-restored enforcement control |

---

## Current state

- **11 pages — intermediate by design.** The expansion pass deliberately
  overshot so the argument could be written properly; compression to 8 is in
  flight. Do not push this believing it is submission-ready.
- **Open:** three inline `table` environments in `sections/results.tex`
  collide with the generated set; `tab:collapse` is defined twice, which
  LaTeX reports only as a warning. Remapping is in `tables/README.md`.
