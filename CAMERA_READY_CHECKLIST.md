# CAMERA_READY_CHECKLIST — what changes after acceptance

**Written 2026-09-30, before submission.** Nothing here is actionable until a
decision arrives. It exists now because the de-anonymization steps are exactly
the ones that get forgotten, and because two of them (the venue metadata and
the HuggingFace release) can go wrong *during review* if someone acts early.

**Read `SUBMISSION_CHECKLIST.md` for the pre-submission gates.** This file is
strictly the delta between the anonymous submission and the camera-ready.

---

## 0. The one rule that binds during review

> **Do not de-anonymize anything, anywhere, until the paper is accepted and
> the camera-ready window opens.**

That includes: pushing a public artifact that matches the paper, renaming a
repo, publishing a HuggingFace dataset whose contents reconstruct the paper's
tables, or adding acknowledgements to the Overleaf project in case they are
needed later. A reviewer who finds the artifact has de-anonymized the
submission, and AAMAS reviewing is double-blind.

---

## 1. De-anonymize the manuscript

| # | change | where | detail |
|---|---|---|---|
| 1.1 | Drop the `anonymous` class option | `paper/main.tex:20` | `\documentclass[sigconf,anonymous]{aamas}` → `\documentclass[sigconf]{aamas}`. Documented in `paper_support/aamas_official/PROVENANCE.md`. |
| 1.2 | Replace the placeholder author block | `paper/main.tex` | Currently `Anonymous Author(s)` / `Anonymous Institution`. The class needs the block present even in anonymous mode, so it is a replacement, not an insertion. |
| 1.3 | Settle the author list | — | **Still unsettled.** `notes/SUBMISSION-ADMIN.md` lists 7 candidates derived from two group arXiv papers, with the companion project recording authors as "interim, final list on hold." This is Bella's call, not an agent's. |
| 1.4 | Add ORCIDs and affiliations | `paper/main.tex` | Per author. |
| 1.5 | Restore acknowledgements | new `\begin{acks}` before `\balance` | **There is no acknowledgements text anywhere in the repo to restore** — it was never written, only suppressed by policy (`main.tex:22`). It must be drafted fresh. Must name the compute facility (ALCF / Sophia inference endpoint) and any grant numbers. |
| 1.6 | Switch prior-group citations from third person to first person — **or don't** | `paper/sections/related.tex` | `2609.27822`, `2608.14927`, `2607.15388` are this group's own work, currently cited in the third person for blinding. Converting them to "our prior work" is optional and stylistic. **If you convert, convert all three**; a mix reads as an oversight. |
| 1.7 | Add the artifact/code URL | intro footnote or a Resources section | Only after §3 below. |

**Verify 1.1–1.2 actually took effect**: rebuild and re-run the anonymity audit
in §5 *inverted* — the author names should now appear on page 1, not just in
the bibliography. A camera-ready that still renders "Anonymous Author(s)" is
the symmetric failure and is just as easy to ship.

---

## 2. Venue metadata — **the block we advanced by hand**

This is the highest-risk item in this file, because the current values are a
plausible-looking guess and nothing will fail loudly if they are wrong.

`paper/main.tex` lines 24–35 carry the IFAAMAS copyright block copied verbatim
from `paper_support/aamas_official/AAMAS_2026_sample.tex` — a block the
official sample marks **"do not change"** — with the year advanced:

```latex
\setcopyright{ifaamas}
\acmConference[AAMAS '27]{Proc.\@ of the 26th International Conference
on Autonomous Agents and Multiagent Systems (AAMAS 2027)}{May 2027}
{Paphos, Cyprus}{Anonymous (eds.)}
\copyrightyear{2027}
\acmYear{2027}
\acmDOI{}  \acmPrice{}  \acmISBN{}
```

**Every field below is unverified for 2027 and must be re-checked against the
AAMAS 2027 author kit when it is published:**

- [ ] **Ordinal** — "26th". AAMAS 2026 is the 25th; 2027 being the 26th is arithmetic, not a citation. Confirm.
- [ ] **Month** — "May 2027". Copied from the 2026 pattern.
- [ ] **Location** — **"Paphos, Cyprus" is the AAMAS *2026* venue.** AAMAS 2027's location is almost certainly different. This is the single most likely field to ship wrong.
- [ ] **Editors** — currently the literal string `Anonymous (eds.)`. The real editor names go here.
- [ ] `\acmDOI`, `\acmISBN` — supplied by the publisher with the camera-ready instructions.
- [ ] `\copyrightyear` / `\acmYear`.
- [ ] **The class file itself.** `paper/aamas.cls` is the **AAMAS-2026** class. If 2027 ships a new one, replace it — and note it must not be modified (an explicit AAMAS rule), so a 2027 class is a swap, never an edit.

Provenance, including the exact fetch command (the server 404s without a
browser User-Agent and a same-site Referer):
`paper_support/aamas_official/PROVENANCE.md`.

**Also re-verify the submission rules themselves.** The ones this project
worked to — 8 pages main text plus unlimited references, LaTeX mandatory, no
style-file modification, no typesetting tricks, double-blind, supplementary as
a single ≤25 MB zip — are the **2026** rules. The abstract/paper deadlines Bella
gave (Oct 1 / Oct 8 AoE) match the 2026 pattern exactly, which is suggestive,
not confirming.

---

## 3. Public artifact release

### 3.1 Timing — the deanonymization hazard

| phase | what may be public |
|---|---|
| now → notification | **nothing new.** The GitHub repo must stay private, or at minimum must not be discoverable from the paper. No HF dataset. No public link in the PDF. |
| after acceptance, before camera-ready | make the repo public, publish the HF dataset, get the DOI |
| camera-ready | add the URL/DOI to the paper |

The temptation is to publish early "so the link is ready." Don't. A public
repo named `AAMAS2027-AgentProtocols` under an identifiable account, with an
abstract matching the submission, de-anonymizes the paper to any reviewer who
searches one distinctive phrase.

**AAMAS rule, verified:** *"Papers must not include pointers to any
supplementary material that is not provided as part of the submission."* If
supplementary material is wanted at review time, it goes in the single ≤25 MB
zip under the same anonymity policy — not behind a link.

### 3.2 What to release, and the size problem

| artifact | size | currently |
|---|---|---|
| code (runner, schemas, prompts, analysis, adjudication) | 2.7 MiB packed | in git |
| `experiments/results/FROZEN/*.jsonl` | **297 MB, 11,600 trajectories** | **NOT in git** (`.gitignore:14`) |
| `adjudication/` verdicts, key, rubric, items | ~1.1 MB | in git |
| `analysis/out/FINAL_TABLES_OUTPUT.txt` | 25 KB | in git |
| `figures/` | 100 KB | in git |

The frozen JSONL is the release's whole value and is too large for git. It
needs HuggingFace (or Zenodo for a DOI). See `PROJECT_PATHS.md` — **it
currently exists in exactly one place on one laptop, with no backup.** Copy it
somewhere safe today; that is not a camera-ready task.

### 3.3 Release checklist

- [ ] Frozen JSONL copied off the laptop (**do this now, not at camera-ready**)
- [ ] Re-verify all three sha256 against `MANIFEST.json` immediately before upload, and publish the manifest alongside the data
- [ ] Secret scan the JSONL itself, not just the code — smoke gate 12 checks trajectory rows for bearer/JWT material; re-run it against the frozen files
- [ ] Decide the HF org. **The paper must not name `AgentsSci` before acceptance**; check `OVERLAP_AUDIT.md` §Residual risk
- [ ] HF dataset card: state that trajectories carry both `final_answer` and the graded answer so a reader can re-derive either scoring (**F18**), and that temperature 0 is not deterministic on this endpoint
- [ ] Ship `MANIFEST.json`, `PREREGISTRATION.md`, `APPROVED_CLAIMS.md` and the `notes/FINDING-*.md` series with the data — the self-corrections are part of the record
- [ ] Zenodo DOI if a permanent citable identifier is wanted
- [ ] Make the GitHub repo public; confirm no secret in history (`git log -p | grep`-style scan, not just a scan of HEAD)
- [ ] Add the URL/DOI to the paper, and only then

### 3.4 What must NOT be released

- Anything under `~/.globus/` or any token cache. The runner holds the bearer token in memory only and scrubs error strings; keep it that way.
- The Overleaf clone's `origin` URL — it embeds a credential.
- Raw evaluator prompts containing gold answers, if the benchmark's license restricts redistribution of answers. **Check the Omni-MATH / source-corpus license before publishing gold-bearing rows.**

---

## 4. Page budget

`paper/main.pdf` is **9 pages** as of 2026-09-30, against an 8-page main-text
limit (references unlimited). This is a *submission* problem, not a
camera-ready one — but note that camera-ready adds the author block,
acknowledgements, and possibly ORCIDs, so **the page budget gets tighter after
acceptance, not looser.** Do not trim to exactly 8.0 pages at submission and
assume it holds.

AAMAS: *"Excessive use of typesetting tricks to make everything fit into 8
pages is not admissible."* Cut content, not leading.

---

## 5. Re-run the audits — anonymity is not a one-time check

Both directions, on the **rendered PDF**, never on the source:

```bash
cd /Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols/paper
pdflatex -interaction=nonstopmode main.tex && bibtex main && \
  pdflatex -interaction=nonstopmode main.tex && pdflatex -interaction=nonstopmode main.tex
pdftotext main.pdf /tmp/cr.txt
for t in AgentsSci ChihHsuan github.com huggingface Argonne ALCF Sophia bellayang; do
  printf '%s: %s\n' "$t" "$(grep -ci "$t" /tmp/cr.txt)"
done
pdfinfo main.pdf | grep -Ei 'Author|Creator|Producer|Title|Pages'
```

- [ ] **Before submission**: every count must be 0. *Known and acceptable:* author surnames (Yang, Jiang, Zheng, Thakur, Vishwanath) appear in the **bibliography** from the three third-person self-citations — that is the required blinding form, not a leak. Verified 2026-09-30: `Chih-Hsuan` appears 3×, all in reference entries [10], [19], [20].
- [ ] **Before submission**: PDF metadata carries no Author field and no local paths.
- [ ] **At camera-ready**: the inverse — author names now render on page 1.
- [ ] **At camera-ready**: re-run after the *final* trim. A number refresh or a page cut can reintroduce a leak.

---

## 6. Order of operations

1. Acceptance notification arrives.
2. Fetch the AAMAS 2027 author kit. Redo §2 against it — class file, copyright block, page rules.
3. Settle the author list (§1.3). Everything else in §1 depends on it.
4. De-anonymize (§1). Rebuild. Re-run §5 inverted.
5. Draft acknowledgements (§1.5) — new text, name the compute facility.
6. Re-check the page budget (§4) *after* 4 and 5 have added their lines.
7. Release the artifact (§3). Verify hashes at upload time.
8. Add the URL/DOI. Rebuild. Final §5 pass.
9. Submit the camera-ready.

---

## 7. Carried over from `SUBMISSION_CHECKLIST.md`

Open at submission time and therefore still open at camera-ready unless closed
in between:

- [ ] OpenReview profiles for every author — could not be verified by any agent (**HTTP 403 on every API call**; a 403 is the API refusing, not evidence a profile is missing). Bella must check in a browser.
- [ ] Reciprocal-reviewer requirement — unverified; the 2027 CFP site did not resolve.
- [ ] Whether the submission system locks the author list at the abstract deadline — unverified, explicitly not inferred.
