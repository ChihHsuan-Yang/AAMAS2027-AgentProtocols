# Submission Package — Bella's manual actions

**Status 2026-10-07 (evening, CT).** Everything an agent can do is done; the
actions below are yours. Upload the files exactly as committed here rather
than rebuilding them: a rebuild on another TeX installation is a different
file.

## Deadline

**Paper: Oct 8, 2026 AoE** (= Fri Oct 9, 06:59 CT), on OpenReview:
`https://openreview.net/group?id=ifaamas.org/AAMAS/2027/Conference`.
OpenReview accepts revisions until the deadline, so submit early.

## What to upload

| item | file | check |
|---|---|---|
| paper PDF | `submission/main.pdf` | 10 pages: main text ends on p. 8, references on pp. 9–10; sha256 `3b4df70e34ab1a2e…` |
| supplementary material | `submission/supplementary_material.zip` | one zip, 708 KB (limit 25 MB), 43 files: `supplement.pdf` (7 pages) + prompts, runner, analysis scripts, outputs, manifests; anonymity gate passed; sha256 `248920c52a74f570…` |
| abstract (plain text) | `paper/ABSTRACT_SUBMIT.txt` | 299 words (the CFP asks for about 100–300); generated from `main.tex`, paste it, do not retype |

## Title

**From Feedback to Revision: When Do Multi-Agent Roles Look Load-Bearing?**

Changed on 2026-10-07 from *… When Multi-Agent Roles Become Load-Bearing*:
the paper's answer is conditional (roles look load-bearing for repair only
when the role ablation also removes the feedback channel; matched on
verdicts, the gap closes), so the question form fits the claims.

## Decisions only you can make

1. **Title and abstract versus the registered ones.** Both changed after
   abstract registration (new results: the feedback-matched control, the
   verdict-matched analysis and the forced-submission run). The CFP page does
   not say whether changes are allowed; if in doubt, ask the PC chairs, or
   revert the `\title{...}` command in `paper/main.tex` and rebuild.
2. **Findings.** Earlier mock reviews converged on "Findings or reject";
   do not opt out of Findings unless you have a reason.
3. **Reciprocal reviewer** and **OpenReview profiles for every author** —
   check both on the 2027 pages; no agent could reach OpenReview's API.
4. **"Primary author is a student"** box on OpenReview, if it applies (used
   only for the best-student-paper award).

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
python3 ../scripts/final_freeze.py     # every gate must pass
```
