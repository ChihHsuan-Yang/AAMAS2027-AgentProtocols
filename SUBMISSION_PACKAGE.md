# Submission Package — upload checklist

**Status 2026-10-08, 20:00 CT.** Built from `revision` at 4db8242 plus the
reference audit and the submission files regenerated on top of it (this
file, the abstract text, the two PDFs and the zip). Upload the files exactly as committed here rather
than rebuilding them: a rebuild on another TeX installation is a different
file.

## Deadline

**Paper: Oct 8, 2026 AoE** (= Fri Oct 9, 06:59 CT), on OpenReview:
`https://openreview.net/group?id=ifaamas.org/AAMAS/2027/Conference`.
OpenReview accepts revisions until the deadline, so submit early.

## What to upload

| item | file | check |
|---|---|---|
| paper PDF | `submission/main.pdf` | 10 pages: main text ends on p. 8, references on pp. 9–10; sha256 `518a6ada9047008e…` |
| supplementary material | `submission/supplementary_material.zip` | one zip, 804 KB (limit 25 MB), 45 files: `supplement.pdf` (9 pages, 11 tables) + prompts, runner, analysis scripts (now including `mk_fig_pipeline.py`), outputs, manifests; anonymity gate passed; sha256 `9be41667dd0caf7d…` |
| abstract (plain text) | `paper/ABSTRACT_SUBMIT.txt` | 263 words (the CFP asks for about 100–300); generated from the abstract in `main.tex`, paste it, do not retype |

`submission/supplement.pdf` (sha256 `461a181f8558b669…`) is the same file
that is inside the zip, kept beside it for reference.

## Title

**From Feedback to Revision: When Do Multi-Agent Roles Look Load-Bearing?**

Changed on 2026-10-07 from *… When Multi-Agent Roles Become Load-Bearing*:
the paper's answer is conditional (roles look load-bearing for repair only
when the role ablation also removes the feedback channel; matched on
verdicts, the gap closes), so the question form fits the claims.

## Decisions to make on OpenReview

1. **Title and abstract versus the registered ones.** Both changed after
   abstract registration (new results: the feedback-matched control, the
   verdict-matched analysis and the forced-submission run). The CFP page does
   not say whether changes are allowed; if in doubt, ask the PC chairs, or
   revert the `\title{...}` command in `paper/main.tex` and rebuild.
2. **Findings.** Earlier mock reviews converged on "Findings or reject";
   do not opt out of Findings unless you have a reason.
3. **Reciprocal reviewer** and **OpenReview profiles for every author** —
   check both on the 2027 pages.
4. **"Primary author is a student"** box on OpenReview, if it applies (used
   only for the best-student-paper award).

## What changed since the 2026-10-07 package

- Main text polished section by section; every model and benchmark is
  named at its first mention in each section; uncommon terms are glossed at
  first use, with four added statistical references (McNemar, Holm, Efron,
  Montgomery et al.).
- Figure 1 (pipeline schematic) redrawn; Figure 2 panel spacing fixed.
- Every figure and table caption rewritten to be self-contained. Table 1 is
  now a compact three-row table; the full collapse table with the
  byte-duplication lower bound and the answer-marker sensitivity note is
  Table 2 of the supplement.
- Reference audit: all 47 cited works were checked against their arXiv,
  DOI or venue pages. Fixed one author name (MetaGPT), one name order
  (El Kandoussi), one venue track (NeurIPS Datasets and Benchmarks), added
  one DOI (Kamoi et al., TACL), removed an unverifiable "to appear" note
  (Orogat et al.), title-cased four titles, and aligned five citing
  sentences with what the cited papers say. The single-agent corpus is now
  described neutrally as "an earlier, separately collected corpus" in the
  paper, the supplement, the table caption and the zip.
- No number changed. The abstract is a new one-paragraph version (263 words).

## Anonymity

Checked on the final files: no author, institution, repository, dataset or
endpoint name in `main.pdf`, `supplement.pdf` or any file of the zip; PDF
metadata carries only the title and the LaTeX producer string. **Do not make
the HuggingFace dataset public before the decision** — a public dataset that
matches the paper's numbers would de-anonymize it.

## AI use

The supplement's "AI assistance" section discloses the tools used for
experimental design, analysis and writing, as the CFP requires when AI
contributed to methodology.

## Not done

A Llama-3.3 forced-submission run (suggested by mock reviewers) could not be
run: on 2026-10-07 the inference service listed no running or queued
Llama-3.3-70B job. The paper reports the forced-submission test for gemma-4
only and says so in Limitations.

## Rebuild (only if you must)

```bash
cd paper
for d in main supplement; do
  TZ=UTC pdflatex -interaction=nonstopmode $d.tex; bibtex $d
  TZ=UTC pdflatex -interaction=nonstopmode $d.tex; TZ=UTC pdflatex -interaction=nonstopmode $d.tex
done
python3 ../scripts/pagecheck.py main.pdf          # must exit 0
python3 ../scripts/check_terminology_pdfs.py      # must pass
cd .. && python3 scripts/mk_supp_zip.py --pdf paper/supplement.pdf   # anonymity gate must pass
```

`scripts/final_freeze.py` additionally needs the raw trajectory files
(`experiments/results/hf_frozen/raw/*.jsonl` plus `armCp.jsonl`) and the
`AAMAS_FROZEN_DIR` / `AAMAS_XDOM_SRC` environment variables; it was not
rerun for this package.
