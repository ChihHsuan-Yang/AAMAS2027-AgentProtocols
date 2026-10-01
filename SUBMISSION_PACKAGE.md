# Submission Package — Bella's manual actions

**Status 2026-09-30. Everything below is ready; the actions are Bella's.**

## Deadlines
- **Abstract: Oct 1, 2026 AoE** (tomorrow)
- **Paper: Oct 8, 2026 AoE**

## The PDF
Build from Overleaf (current, commit `797b781`) or locally:
```
cd paper && latexmk -pdf main.tex
```
Verified: 8 main-text pages + references on 9-10; official `aamas.cls`;
`latexmk` exit 0; 0 undefined citations; no TODO markers; anonymous;
self-citations third person. A fresh clone of the Overleaf tree builds
standalone (verified, not assumed).

## Title
**When Is Multi-Agent Organization Load-Bearing?**

Decided 2026-09-30. The subtitled form "Roles Buy Recovery, Not First-Pass
Accuracy: ..." was set and then reverted: the extra title line pushed main
text onto page 9. The page budget has a one-sentence margin and a subtitle is
not worth a limit violation.

The short form is also the safer claim. "Roles buy recovery" as a title
asserts universally what holds cleanly for gemma-4, weakly for gpt-oss, and
not at all for Llama-3.3. The question form claims a PHASE, not a mechanism
and not a universal effect, so it survives a reviewer who rejects answer
lock-in as the explanation or who reads the actor scope closely.

## Abstract (paste as plain text, ~250 words)
See `paper/main.tex`. AAMAS wants 100-300 words plain text, due one week
before the paper.

## Area
Generative AI and Agents (GAAI). Secondary fit: COINE (organizations).

## Keywords
multi-agent systems; large language models; role specialization;
error recovery; ablation study; agent organization

## BELLA — MANUAL ACTIONS (I cannot do these)

1. **OpenReview profiles.** All authors need one, and the author list must
   be complete at abstract submission.
2. **Submit the abstract by Oct 1 AoE.** Plain text, 100-300 words.
3. **Submit the PDF by Oct 8 AoE** at
   `https://openreview.net/group?id=ifaamas.org/AAMAS/2027/Conference`
   (2026's URL pattern; verify the 2027 one).
4. **Paper tracking number.** AAMAS asks that the first page carry the
   tracking number in place of authors. It is assigned at submission, so
   it cannot be added beforehand — add it after you get it, if required.
5. **Reciprocal reviewing.** AAMAS has required this in past years. Check
   whether 2027 does.
6. **Supplementary (optional).** A <=25MB anonymous zip is prepared in
   `hf_artifact/` — see `RELEASE_PROCEDURE.md` section 5. Only include it
   if you want reviewers to have the data; it must stay anonymous.
7. **Do NOT publish the HuggingFace artifact before acceptance.** A public
   dataset matching the paper's numbers is a deanonymization path. Release
   procedure is documented for after.

## Verify before submitting
- AAMAS 2027 may publish its own author kit; ours is the 2026 kit with the
  year advanced. Re-check page limit, anonymity rules, and the copyright
  block against the 2027 instructions if they exist.

---

# FINAL SUBMISSION FREEZE — 2026-09-30 19:50

Machine-readable record: `FINAL_FREEZE.json`, regenerable by
`python3 scripts/final_freeze.py` (exits non-zero if any gate fails).

| | |
|---|---|
| title | When Is Multi-Agent Organization Load-Bearing? |
| GitHub HEAD | `72eef9fe4384` |
| Overleaf HEAD | `c31475b34973` |
| **PDF sha256** | `4e9ca7f22697530b...ea17c189` (665,627 bytes) |
| Figure 1 sha256 | `695e7d973145c079...90efeaf8` |
| abstract sha256 | `5170459c62d548d3...a7c54452` |
| Omni-MATH data | 11,600 rows, 3 files, sha256 in `FROZEN/MANIFEST.json` |
| SciBench data | 2,296 rows, `10068f72cfd936d3...` |
| HF artifact | `AgentsSci/AAMAS2027-Roles` v1.1.0, **PRIVATE** |

**Gates, all passing:** latexmk 0 · pagecheck 0 (main text ends p8) ·
undefined citations 0 · anonymity hits 0 · `aamas.cls` byte-identical to the
official kit. The single `TODO{` hit is a comment in `main.tex` telling a
future editor how to grep for TODOs, not a placeholder.

**Overleaf equivalence verified, not assumed.** A fresh clone of the Overleaf
remote builds to **text-identical output** (`pdftotext | shasum` matches the
frozen PDF exactly). PDF bytes differ only by build timestamp.

## After this freeze
No scientific content changes without re-running the canonical chain in
`SOURCE_OF_TRUTH.md` and regenerating this freeze. If you edit the paper,
`python3 scripts/final_freeze.py` must pass again before submitting.
