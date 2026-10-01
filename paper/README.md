# AAMAS 2027 manuscript — what is here and how to rebuild it

**From Feedback to Revision: When Multi-Agent Roles Become Load-Bearing**

This directory is the **authoritative manuscript**. The Overleaf project is a
mirror of it, currently un-pushable (see `../HANDOFF_CURRENT.md`). Everything
needed to build the PDF is in this directory and tracked in git.

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
