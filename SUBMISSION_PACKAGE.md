# Submission Package — upload checklist

**Status 2026-10-08, 23:30 CT.** Built from `revision` at 3dc579b plus the
rewritten Results section, the polished supplement and the submission files
regenerated on top of it (this file, the two PDFs and the zip). Upload the
files exactly as committed here rather than rebuilding them: a rebuild on
another TeX installation is a different file.

## Deadline

**Paper: Oct 8, 2026 AoE** (= Fri Oct 9, 06:59 CT), on OpenReview:
`https://openreview.net/group?id=ifaamas.org/AAMAS/2027/Conference`.
OpenReview accepts revisions until the deadline, so submit early.

## What to upload

| item | file | check |
|---|---|---|
| paper PDF | `submission/main.pdf` | 10 pages: main text ends on p. 8 (3.9 lines spare), references on pp. 9–10; sha256 `ee32030009f54046…` |
| supplementary material | `submission/supplementary_material.zip` | one zip, 838 KB (limit 25 MB), 59 files: `supplement.pdf` (9 pages, 11 tables, 4 figures, AI use statement) + prompts, runner, analysis scripts (including `mk_fig_pipeline.py` and `mk_fig_supp.py`), table sources, outputs, manifests, README with requirements; anonymity gate passed; sha256 `9963ad52d03fbd55…` |
| abstract (plain text) | `paper/ABSTRACT_SUBMIT.txt` | 263 words (the CFP asks for about 100–300); generated from the abstract in `main.tex`, paste it, do not retype |

`submission/supplement.pdf` (sha256 `7f2ec4343769e8ae…`) is the same file
that is inside the zip, kept beside it for reference. It is the Overleaf
build; `paper/supplement.tex` reproduces its text exactly (only one
line-end hyphen differs on this TeX installation). The Overleaf build of the
main paper (sha256 `495d166b238ae283…`) has the same text as
`submission/main.pdf`; either may be uploaded. Overleaf names its downloads
after the project, so rename a downloaded PDF (for example to `main.pdf`)
before uploading it.

Zip tooling: `scripts/mk_supp_zip.py` sha256 `c6fbd33a5b7174cd…`,
`analysis/scripts/mk_fig_supp.py` sha256 `d393c0121f37c19a…`.

## Title

**From Feedback to Revision: When Do Multi-Agent Roles Look Load-Bearing?**

Changed on 2026-10-07 from *… When Multi-Agent Roles Become Load-Bearing*:
the paper's answer is conditional (roles look load-bearing for repair only
when the role ablation also removes the feedback channel; matched on
verdicts, the gap closes), so the question form fits the claims.

## Decisions to make on OpenReview

1. **Title and abstract versus the registered ones.** The Q&A page (Q11)
   says the title and abstract "should not be changed in any substantive way
   after the abstract deadline"; minor editorial corrections are permitted.
   Registered on OpenReview: *From Feedback to Revision: When Multi-Agent
   Roles Become Load-Bearing*, with an abstract on the same experiments that
   concluded roles help revision. The title change is editorial; the
   abstract's conclusion changed (new results: the feedback-matched control,
   the verdict-matched analysis and the forced-submission run). The
   OpenReview fields must match the PDF; decide whether to also send the PC
   chairs a short note.
2. **Findings.** Earlier mock reviews converged on "Findings or reject";
   do not opt out of Findings unless you have a reason.
3. **Reciprocal reviewer:** at least one designated reciprocal reviewer
   must have accepted the reviewer invitation in OpenReview by Oct 8 AoE.
   **Every author must have an OpenReview account** (one author chip on the
   form showed no linked profile; check it).
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
- Results (Section 5) rewritten to explain each finding rather than list
  numbers: every paragraph now states the result, the reason (marked as
  untested where it is a candidate explanation) and what it implies. About
  half of the numbers in the section moved to the tables or to the
  supplement, which gained short paragraphs with the per-role answer rates,
  the numeric overlap, the judge's stability, the logging-defect detail,
  the revision and leakage checks, the freeze-crossing verdict-matched check,
  the enforced submission and rejection counts, and the SciBench answer-lock
  rates. The main text now ends 3.9 lines short of the end of page 8.
- The main text no longer mentions sha256 or hashing (three sentences in
  Sections 3 and 4 reworded; the manifests are still in the zip).
- Supplement rewritten and reordered to follow the main paper's R1--R5, with a
  glossary up front, short captions with the column definitions in a note
  under each table, one table style, full model ids, and four new figures
  (`analysis/scripts/mk_fig_supp.py`; byte-reproducible).
- Supplementary zip rebuilt with the table sources and `mk_fig_supp.py`, a
  requirements paragraph in its README, and stricter redaction and gate rules
  (internal paths, gateway names, commit and branch ids, US time-zone offsets
  in timestamps). An independent scan of the unpacked zip found nothing
  identifying; `mk_fig_supp.py` reproduces the four figures byte for byte
  from the unpacked zip.
- No number changed. The abstract is a new one-paragraph version (263 words).

## Overleaf

The Overleaf project was created from a sources-only zip (`main.tex`,
`supplement.tex`, class, bst, bib, `by.pdf`, `sections/`, `tables/`,
`figures/`), which is not committed. The authors then wrote the AI use
statement there; `paper/supplement.tex` carries the same text. Overleaf's
TeX Live breaks one line of the main text differently from the build here;
the page layout and the 3.9 lines of slack on page 8 are unchanged.

## Anonymity

Checked on the final files: no author, institution, repository, dataset or
endpoint name in `main.pdf`, `supplement.pdf` or any file of the zip; PDF
metadata carries only the title and the LaTeX producer string. **Do not make
the HuggingFace dataset public before the decision** — a public dataset that
matches the paper's numbers would de-anonymize it.

## AI use

The AAMAS 2027 submission instructions require detailed disclosure "in the
paper or in the supplementary material" when AI-assisted technologies
contribute to hypotheses or methodology, including the tool and version; the
Q&A page asks authors to state plainly what was not retained. The
supplement's Section 8, "AI use statement", was written by the authors. The
main text carries no pointer to it.

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
cd .. && python3 scripts/mk_supp_zip.py --pdf submission/supplement.pdf   # anonymity gate must pass
```

`scripts/final_freeze.py` additionally needs the raw trajectory files
(`experiments/results/hf_frozen/raw/*.jsonl` plus `armCp.jsonl`) and the
`AAMAS_FROZEN_DIR` / `AAMAS_XDOM_SRC` environment variables; it was not
rerun for this package.
