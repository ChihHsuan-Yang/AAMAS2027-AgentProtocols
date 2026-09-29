# Submission checklist — AAMAS 2027

**Stop condition:** the scientific paper and all submission materials are ready
for Bella to submit manually. NOT "the paper has been submitted."

## Bella — manual submission actions

These require Bella's account and are **not** project blockers. The Master Agent
does not attempt them and does not report them as blockers.

- [ ] OpenReview profile / account matters for all authors
- [ ] Reciprocal-reviewer action, if AAMAS 2027 requires one
- [ ] Author-list confirmation in the submission system
- [ ] Abstract submission (Oct 1 AoE)
- [ ] Full-paper submission (Oct 8 AoE)
- [ ] Any account-specific administrative step

## Master Agent deliverables — the package Bella pastes/uploads

| # | item | status |
|---|---|---|
| 1 | Final anonymized AAMAS PDF | IN PROGRESS — compiles, 9 pp, Results being rewritten |
| 2 | Final title | IN PROGRESS — candidates under evaluation against final results |
| 3 | Final abstract | DRAFTED (result-agnostic); rewrite pending final numbers |
| 4 | Author-independent submission metadata/text to paste | TODO |
| 5 | Supplementary material (if used) | TODO — decide after page budget |
| 6 | Verified bibliography | DONE — 10 entries, each fetched from arxiv.org/abs and title-matched |
| 7 | Clean Overleaf | DONE — pushed commit 128771e (main.tex + refs.bib + 9 sections) |
| 8 | Clean GitHub / reproducibility artifacts | DONE — 2.7 MiB, raw JSONL stripped from history, secret scan clean |
| 9 | This checklist | LIVE |

## Anonymity gates (Master Agent owns these)
- [x] **no repo URL, HF org (`AgentsSci`), or author account in the rendered PDF** — audited 2026-09-29 against the PDF text, not just the source: zero hits for AgentsSci / ChihHsuan / github.com / huggingface / Argonne / ALCF / Sophia / bellayang
- [x] **PDF metadata clean** — no Author field; Creator/Producer are toolchain strings only; no local paths
- [x] **author block renders "Anonymous Author(s)"**
- [x] **.bib warning comments do not render** — verified they are stripped by bibtex
- [x] prior group work (2609.27822, 2608.14927, **2607.15388**) cited in **third person**
- [ ] AAMAS document class in place of the current acmart substitution — **the official .cls could not be fetched**; acmart `[sigconf,anonymous,review]` is the documented substitution, one-line swap noted in main.tex
- [ ] re-run this audit after the final trim + number refresh (anonymity is not a one-time check)
