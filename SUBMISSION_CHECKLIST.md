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
| 1 | Final anonymized AAMAS PDF | **IN PROGRESS** — compiles clean on the official class, **9 pp against an 8 pp limit** |
| 2 | Final title | "When Is Multi-Agent Organization Load-Bearing?" — in `main.tex` and the PDF |
| 3 | Final abstract | **DRAFTED** against the frozen 11,600-trajectory snapshot, in `main.tex`. **Needs a pass against `STATISTICAL_AUDIT.md`** — see below. |
| 4 | Author-independent submission metadata to paste | TODO |
| 5 | Supplementary material | TODO — decide after the page budget. **Must ship inside the submission, never behind a link** (AAMAS: "Papers must not include pointers to any supplementary material that is not provided as part of the submission"). Single zip, ≤ 25 MB, same anonymity policy. |
| 6 | Verified bibliography | **DONE** — 24 entries; audit in `paper_support/BIB-AUDIT-2026-09-29.txt` |
| 7 | Clean Overleaf | **STALE** — clone is at `128771e` (12 files), missing the class file and the later section rewrites. `paper/` is the working copy and must be synced to Overleaf before submission. The clone lives at `/tmp/aamas_ol` and will not survive a reboot. |
| 8 | Clean GitHub / reproducibility artifacts | **PARTIAL** — 2.70 MiB packed, raw JSONL stripped from history, secret scan clean. **`origin/main` is 16 commits behind local** — push. |
| 9 | This checklist | LIVE |

## Blocking before submission

- [ ] **Page budget 9 → 8.** AAMAS: *"Excessive use of typesetting tricks to make everything fit into 8 pages is not admissible."* Cut content.
- [ ] **Close out `STATISTICAL_AUDIT.md`** — 1 FATAL + 5 SERIOUS. The FATAL and two of the SERIOUS are claims a reviewer can check against the artifact:
  - **FATAL-1** — Arm C's recovery denominator dropped 173 rows. **The tables are fixed** (commit `ba28977`; T1 now 0.314/0.395/0.139). Still open in prose: `results.tex` §R5's "paired-significant in all three (p=1.6e-3, 1.6e-3, 3.8e-6)" must go — only Llama-3.3 survives.
  - **SERIOUS-1** — `method.tex:63` and `results.tex:6` assert a Holm correction that `FINAL_TABLES.py` never applies. **A reviewer verifies this with one grep.** Running it changes no verdict, so run it.
  - **SERIOUS-2** — the "floor effect" language for Llama-3.3 is falsified by our own Arm C. `results.tex` §R3 and `limitations.tex` both need it removed; limitations has it exactly backwards.
  - **SERIOUS-3** — `results.tex` §R4 quotes an n=12 cell and pooled quartiles that are arm indicators.
  - **SERIOUS-4** — drop every "effect ÷ noise floor" ratio.
  - **SERIOUS-5** — say which P4 DiDs are informative nulls (only gpt-oss−gemma, MDE 0.033) and which are not.
- [ ] **Abstract re-check.** It currently says enforcement "restores both organization and recovery" and calls Llama's result "a floor effect that does not replicate." Both are now dead claims (FATAL-1, SERIOUS-2).
- [ ] **Push the 16 local commits.**
- [ ] **Sync `paper/` → Overleaf.**
- [ ] **Back up `experiments/results/FROZEN/`.** 297 MB, one laptop, not in git, not regenerable (temperature 0 is not deterministic on this endpoint). Losing it ends the project.
- [ ] **Re-run the anonymity audit after the final trim** — it is not a one-time check.

## Anonymity gates

- [x] **No repo URL, HF org (`AgentsSci`), or author account in the rendered PDF.** Re-audited **2026-09-30** against the PDF text via `pdftotext`, not the source: **0 hits** for AgentsSci / ChihHsuan / github.com / huggingface / Argonne / ALCF / Sophia / bellayang.
- [x] **PDF metadata clean** — verified 2026-09-30 with `pdfinfo`: no Author field; Creator/Producer are toolchain strings (`LaTeX with aamas … hyperref`, `pdfTeX … TeX Live 2026`); no local paths.
- [x] **Author block renders "Anonymous Author(s)."**
- [x] **`.bib` warning comments do not render** — stripped by bibtex.
- [x] **Prior group work (2609.27822, 2608.14927, 2607.15388) cited in third person.** Author surnames therefore appear in the bibliography — Yang ×7, Jiang ×4, Zheng ×5, Thakur ×3, Vishwanath ×2, Chih-Hsuan ×3, all confined to entries [10], [19], [20]. **That is the required blinding form, not a leak.**
- [x] **Official AAMAS document class in place.** The earlier "the .cls could not be fetched" finding was **wrong** — the 404 was a hotlink guard returning 401 KB of HTML. Retrieved 2026-09-30; see `paper_support/aamas_official/PROVENANCE.md`.
- [ ] **Re-run this audit after the final trim and number refresh.**

Reproduce the audit:

```bash
pdftotext paper/main.pdf /tmp/anon.txt
for t in AgentsSci ChihHsuan github.com huggingface Argonne ALCF Sophia bellayang; do
  printf '%s: %s\n' "$t" "$(grep -ci "$t" /tmp/anon.txt)"; done
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
