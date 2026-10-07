# Submission checklist — AAMAS 2027

**Stop condition:** the scientific paper and all submission materials are ready
for Bella to submit manually. NOT "the paper has been submitted."

Deadlines: **abstract 2026-10-01 AoE, full paper 2026-10-08 AoE.** 8 pages main
text + unlimited references, double-blind, LaTeX mandatory.

Camera-ready work is out of scope here — see `CAMERA_READY_CHECKLIST.md`.

## Bella — manual submission actions

These require Bella's account and are **not** project blockers. No agent
attempts them and none reports them as blockers.

- [ ] OpenReview profile / account matters for all authors
- [ ] Reciprocal-reviewer action, if AAMAS 2027 requires one
- [ ] Author-list confirmation in the submission system
- [ ] Abstract submission (Oct 1 AoE)
- [ ] Full-paper submission (Oct 8 AoE)
- [ ] Any account-specific administrative step

None of the above could be agent-verified: `api.openreview.net` returned
**HTTP 403 on every call** (a 403 is the API refusing, **not** evidence a
profile is missing or present), and all three candidate AAMAS-2027 CFP
hostnames failed to resolve. Reported as access failures, not as findings.

## Agent deliverables — the package Bella pastes/uploads

| # | item | status |
|---|---|---|
| 1 | Final anonymized AAMAS PDF | **DONE** — official class, **8 main-text pages + references on 9**, every gate passing |
| 2 | Final title | **DONE** — *From Feedback to Revision: When Do Multi-Agent Roles Look Load-Bearing?* |
| 3 | Final abstract | **DONE** — ~294 words, generated to `paper/ABSTRACT_SUBMIT.txt` from `main.tex`; paste the file rather than retyping |
| 4 | Submission metadata to paste | **DONE** — `SUBMISSION_PACKAGE.md` (title, abstract, area, keywords) |
| 5 | Supplementary material | **DONE** — `paper/supplement.pdf`, 11 pp, anonymous, gated. Ships **inside** the submission; the paper contains no pointer to it |
| 6 | Verified bibliography | **DONE** — `refs.bib` holds **27** entries, every one machine-checked against arXiv or CrossRef (`paper_support/BIB-AUDIT-2026-09-29.txt`). **26 render**; `barrak2025traceability` is verified but uncited, so bibtex drops it. Harmless, and left in place rather than cited: adding a citation to a paper at its page limit costs main-text lines for no argumentative gain. |
| 7 | Clean Overleaf | **BLOCKED, not at risk** — git access off (affiliation link pending). `paper/` is the authoritative copy and a fresh clone of this repo rebuilds both PDFs to identical text. Push procedure in `HANDOFF_CURRENT.md` |
| 8 | Clean GitHub / reproducibility artifacts | **DONE** — pushed through `57daaaf2c8cd`, raw JSONL out of git history, secret scan clean |
| 9 | AI-assistance disclosure | **DONE** — `paper/AI_ASSISTANCE_DISCLOSURE.md`, anonymous |
| 10 | This checklist | LIVE |

## Blocking before submission

**None open.** Everything below was blocking and has been verified closed,
each by running the check rather than by recalling that it was fixed.

- [x] **Page budget 9 → 8.** `scripts/pagecheck.py` exit 0; main text ends
      page 8. Met by cutting prose, not by typesetting — AAMAS forbids the
      latter and `microtype` protrusion is explicitly disabled, which makes
      lines looser, not tighter.
- [x] **`STATISTICAL_AUDIT.md` closed out** — 1 FATAL + 5 SERIOUS, all
      resolved and each verified absent from the current prose:
      the "paired-significant in all three" claim is gone (only Llama-3.3
      survived); Holm is actually applied in `FINAL_TABLES.py`; the "floor
      effect" language for Llama-3.3 is gone, falsified by our own enforced
      condition; the n=12 cell is gone; every "effect ÷ noise floor" ratio
      is gone; and the paper now says which P4 contrasts are informative
      nulls and which cannot detect an effect of any plausible size.
- [x] **Abstract re-checked** — the dead claims ("restores both
      organization and recovery", Llama as "a floor effect") are absent.
- [x] **All commits pushed** — `origin/main..HEAD` is empty.
- [x] **Anonymity re-audited after the final trim** — 0 hits in the
      rendered text of **both** PDFs. Re-run by `scripts/final_freeze.py`,
      so it is no longer a one-time manual check.
- [x] **`experiments/results/FROZEN/` is no longer single-copy.** The old
      entry here said "297 MB, one laptop, losing it ends the project."
      That is now false and the correction matters: all three Omni-MATH
      traces plus the SciBench trace are in the **private** HF repo, and I
      verified the bytes rather than the filenames — `campaign_v2`
      `e4e53cb117d91129`, `actor3` `fa22a446d5314bb6`, `armCp`
      `038e08aec4d4aee1`, identical local and remote. The laptop copy is
      still the working copy and a second local backup is still worth
      having, but losing it no longer ends the project.

## Anonymity gates

- [x] **No repo URL, HF org (`AgentsSci`), or author account in the rendered PDF.** Re-audited **2026-09-30** against the PDF text via `pdftotext`, not the source: **0 hits** for AgentsSci / ChihHsuan / github.com / huggingface / Argonne / ALCF / Sophia / bellayang.
- [x] **PDF metadata clean** — verified 2026-09-30 with `pdfinfo`: no Author field; Creator/Producer are toolchain strings (`LaTeX with aamas … hyperref`, `pdfTeX … TeX Live 2026`); no local paths.
- [x] **Author block renders "Anonymous Author(s)."**
- [x] **`.bib` warning comments do not render** — stripped by bibtex.
- [x] **Prior group work (2609.27822, 2608.14927, 2607.15388) cited in third person.** Author surnames therefore appear in the bibliography — Yang ×7, Jiang ×4, Zheng ×5, Thakur ×3, Vishwanath ×2, Chih-Hsuan ×3, all confined to entries [10], [19], [20]. **That is the required blinding form, not a leak.**
- [x] **Official AAMAS document class in place.** The earlier "the .cls could not be fetched" finding was **wrong** — the 404 was a hotlink guard returning 401 KB of HTML. Retrieved 2026-09-30; see `paper_support/aamas_official/PROVENANCE.md`.
- [x] **Re-run after the final trim** — automated. `scripts/final_freeze.py`
  runs the anonymity scan over the rendered text of **both** PDFs on every
  invocation, so it cannot be forgotten, and it fails the freeze on a
  single hit. Positive-controlled: planting an HF URL in `supplement.tex`
  made it report 2 hits and fail.

Reproduce the audit:

```bash
python3 scripts/final_freeze.py          # runs it over both PDFs, among all gates

# or by hand, on the RENDERED text -- never on the source, which legitimately
# contains these strings in comments and in paper/README.md:
for d in main supplement; do
  pdftotext paper/$d.pdf /tmp/anon.txt
  for t in AgentsSci ChihHsuan github.com huggingface overleaf Argonne ALCF Sophia bellayang; do
    printf '%s %s: %s\n' "$d" "$t" "$(grep -ci "$t" /tmp/anon.txt)"; done
done
pdfinfo paper/main.pdf | grep -Ei 'Author|Creator|Producer|Pages'
```

## Pre-declared NOT-SUBMIT condition — evaluated, NOT triggered

`PREREGISTRATION.md` committed, before results:

> **What would make us NOT submit** — "The interaction (P4) is null AND the
> main effect matches 2608.21747's published direction — that is their result
> in a new setting, not ours."

**Evaluated against the final frozen data** (`notes/FINDING-24-P4-NOTSUBMIT-CHECK.md`):

- **First conjunct holds.** P4 is null; all three pairwise DiDs contain zero (T14).
- **Second conjunct fails, and it is close.** Under *as-graded* scoring all three C−A effects are positive, significant, and monotonically decreasing in actor strength — Canedo's direction exactly, and the condition would be met on its face. But that scoring violates the preregistration's own exclusion rule (*"trajectories failing to parse are counted as incorrect, not dropped"*), and Arm C's unjudged rows are `hard_failure: regeneration_exhausted`, i.e. parse failures, at 8–17% against 0.0–0.7% in Arm A. Under the preregistered rule the main effect **reverses sign for gemma-4 (−0.0203, SIG negative) and vanishes for gpt-oss**. It matches no monotone direction.

The condition requires **both** conjuncts. **It is not met, and the paper may
be submitted.** The gap between the two readings is entirely Arm C's
attrition, which is why both scorings ship with the attrition rates beside
them.

## Standing rules

1. Calibrate any measure against a validated reference before using it.
2. Stratify before pooling — two Simpson's reversals were found in this project.
3. Never quote a number from a data cut other than the reported n.
4. A retracted number stays visible and marked, never deleted.
5. No campaign, and no claim, without the artifact that supports it.
6. Final numeric truth = `experiments/results/FROZEN/` + `analysis/scripts/FINAL_TABLES.py`. No manually maintained duplicate numbers.
