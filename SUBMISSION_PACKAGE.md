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
**Roles Buy Recovery, Not First-Pass Accuracy: When Is Multi-Agent
Organization Load-Bearing?**

Claims a PHASE, not a mechanism, so it survives a reviewer who rejects
answer lock-in as the explanation.

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
