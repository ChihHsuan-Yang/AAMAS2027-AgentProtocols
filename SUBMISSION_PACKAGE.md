# Submission Package — upload checklist

**Status 2026-10-09, 02:00 CT.** Built from `revision` at 5962081 plus the
storyline rewrite of 2026-10-09 (new title, abstract, Introduction, Results
R1--R4, Discussion and Conclusion, polished by the authors) and the
submission files regenerated on top of it (this file, the two PDFs and the
zip). Upload the
files exactly as committed here rather than rebuilding them: a rebuild on
another TeX installation is a different file.

## Deadline

**Paper: Oct 8, 2026 AoE** (= Fri Oct 9, 06:59 CT), on OpenReview:
`https://openreview.net/group?id=ifaamas.org/AAMAS/2027/Conference`.
OpenReview accepts revisions until the deadline, so submit early.

## What to upload

| item | file | check |
|---|---|---|
| paper PDF | `submission/main.pdf` | 10 pages: main text ends on p. 8 (3.8 lines spare), references on pp. 9–10; sha256 `c72c757040e7f068…` |
| supplementary material | `submission/supplementary_material.zip` | one zip, 843 KB (limit 25 MB), 59 files: `supplement.pdf` (9 pages, 11 tables, 4 figures, AI use statement) + prompts, runner, analysis scripts, table sources, outputs, manifests, README with requirements; anonymity gate passed; sha256 `a508ec18b5e59a67…` |
| abstract (plain text) | `paper/ABSTRACT_SUBMIT.txt` | 246 words (the CFP asks for about 100–300); the same text as the abstract in `main.tex`, paste it, do not retype |

`submission/supplement.pdf` (sha256 `5e9adba8d4ad1f9e…`) is the same file
that is inside the zip, kept beside it for reference. Both PDFs were built
here from the committed sources (TZ=UTC); the Overleaf project still holds
the 2026-10-08 sources and has not been synced to this version. Upload the
files in `submission/`, not Overleaf downloads.

Zip tooling: `scripts/mk_supp_zip.py` sha256 `a28e48b85a1a441e…`,
`analysis/scripts/mk_fig_supp.py` sha256 `d393c0121f37c19a…`. The zip's
redaction rules also rewrite a few development notes in the shipped copies
of `runner.py`, `runner_xdomain.py`, `test_bf_delivery.py`, `bf_numbers.py`
(and its output) and `mk_fig1_bf.py` into neutral descriptions of what each
condition receives; the files in the repository keep their full history.

## Title

**Beyond Division of Labor: How Roles Shape Feedback and Recovery in Multi-Agent Systems**

Chosen by the PI on 2026-10-09 with the storyline rewrite. Registered on
OpenReview (Oct 1): *From Feedback to Revision: When Multi-Agent Roles Become
Load-Bearing*; the authors decided to overwrite the OpenReview title and
abstract fields with the PDF's.

## Decisions to make on OpenReview

1. **Title and abstract versus the registered ones.** The Q&A page (Q11)
   says the title and abstract "should not be changed in any substantive way
   after the abstract deadline"; minor editorial corrections are permitted.
   Registered on OpenReview: *From Feedback to Revision: When Multi-Agent
   Roles Become Load-Bearing*, with an abstract on the same experiments that
   concluded roles help revision. The title change is editorial; the
   abstract's conclusion changed (new results: the feedback-matched control,
   the verdict-matched analysis and the forced-submission run). The
   OpenReview fields must match the PDF. The title has now changed as well;
   the authors decided to overwrite both fields at upload.
2. **Findings.** Earlier mock reviews converged on "Findings or reject";
   do not opt out of Findings unless you have a reason.
3. **Reciprocal reviewer:** at least one designated reciprocal reviewer
   must have accepted the reviewer invitation in OpenReview by Oct 8 AoE.
   **Every author must have an OpenReview account** (one author chip on the
   form showed no linked profile; check it).
4. **"Primary author is a student"** box on OpenReview, if it applies (used
   only for the best-student-paper award).

## What changed on 2026-10-09 (storyline rewrite)

- New title and abstract. The paper now asks what roles change beyond the
  intended division of labor: roles create specialization without a better
  first answer, and the Reviewer's approval decides how often the team
  obtains corrective feedback. The main comparison is role-structured
  against role-free with feedback (exploratory, post-freeze); the
  feedback-withheld condition is a diagnostic.
- Introduction, Results (now R1--R4: specialization; recovery with feedback;
  the Reviewer gate with the forced-submission run and the post hoc
  verdict-matched analysis; generality and enforcement), Discussion and
  Conclusion rewritten, then polished by the authors.
- Figure 2C: "revising" renamed to "no submission / internal", and a bar for
  the forced-submission run added. Figure 1: "internal cycle". Table 2's
  caption reworded.
- Supplement aligned: new title, R5 merged into R4, the pre-registration
  sentence corrected (the pre-registered secondary contrast is RS against
  RF$^{-}$), no "same feedback" or "equal use per verdict" wording, the
  SciBench section described as the feedback-withheld comparison.
- No number changed. An independent read-only check matched the numbers to
  `analysis/out`.

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

The Overleaf project holds the 2026-10-08 sources and was not used for this
version. To sync it later, replace `main.tex`, `supplement.tex`, every file
in `sections/`, `tables/main_results.tex`, `tables/context_quartiles.tex`,
`tables/scibench_replication.tex`, `figures/fig1_v3_story.pdf` and
`figures/fig_pipeline.pdf` with the committed versions, then check that the
main text still ends on page 8.

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
