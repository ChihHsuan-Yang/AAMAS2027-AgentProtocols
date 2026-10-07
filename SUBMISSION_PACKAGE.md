# Submission Package — Bella's manual actions

**Status 2026-10-02.** Everything in the agent column is done; the actions
below are yours. Machine-readable record: `FINAL_FREEZE.json`, regenerable
by `python3 scripts/final_freeze.py`, which exits non-zero if any gate
fails.

## Deadlines
- **Abstract: Oct 1, 2026 AoE** — *this date has passed.* If the abstract
  was not registered, check whether AAMAS still accepts the paper; nothing
  in the project can answer that.
- **Paper: Oct 8, 2026 AoE**

## Title

**From Feedback to Revision: When Do Multi-Agent Roles Look Load-Bearing?**

Set 2026-10-01 with the narrative rewrite, replacing *When Is Multi-Agent
Organization Load-Bearing?*. The earlier short form named the question;
this one names the answer, which is what the Results now march toward. The
second line costs vertical space and was paid for with prose cuts, not
typesetting.

## Abstract (294 words, plain text)

**Do not retype this.** It is generated from `main.tex` by
`scripts/final_freeze.py` into **`paper/ABSTRACT_SUBMIT.txt`** — paste that
file. A hand-copied abstract drifts from the compiled paper, and the
submitted abstract is supposed to be the paper's.

If the form has a 300-word cap, this fits. If it has a 250-word cap, cut
from the enforcement sentence onward rather than reflowing the opening.

## The PDFs

| file | pages | build |
|---|---|---|
| `paper/main.pdf` | **8 main text + references on 9** | pdflatex → bibtex → pdflatex ×2 |
| `paper/supplement.pdf` | 11 (no page limit) | same, on `supplement.tex` |

```bash
cd paper
for d in main supplement; do
  pdflatex -interaction=nonstopmode $d.tex; bibtex $d
  pdflatex -interaction=nonstopmode $d.tex; pdflatex -interaction=nonstopmode $d.tex
done
```

**Verify you have the right paper**, not merely a paper of the right
length:

```bash
pdftotext main.pdf -       | shasum -a 256   # 3cb9712a40d2176034a309a4…
pdftotext supplement.pdf - | shasum -a 256   # 48f51c61629cf99e552b3722…
```

Byte hashes of a PDF change on every build — pdflatex embeds a wall-clock
timestamp — so they identify a build, not a paper. The text hash is the one
that answers "is this the same paper?".

## Area and keywords

Generative AI and Agents (GAAI). Secondary fit: COINE (organizations).

multi-agent systems; large language models; role specialization;
error recovery; ablation study; agent organization

## Supplementary material

`paper/supplement.pdf` — assembled, anonymous, gated. AAMAS requires
supplementary material to ship **inside the submission, never behind a
link**: *"Papers must not include pointers to any supplementary material
that is not provided as part of the submission."* The main paper is
readable without it and contains no link to it.

The data artifact in `hf_artifact/` is a separate, optional ≤25 MB anonymous
zip (see `RELEASE_PROCEDURE.md` §5). Include it only if you want reviewers
to have the rows.

## BELLA — MANUAL ACTIONS (no agent can do these)

1. **OpenReview profiles.** All authors need one; the author list must be
   complete at abstract submission.
2. **Submit the PDF by Oct 8 AoE** at
   `https://openreview.net/group?id=ifaamas.org/AAMAS/2027/Conference`
   (2026's URL pattern — verify the 2027 one).
3. **Paper tracking number.** AAMAS asks that the first page carry it in
   place of authors. It is assigned at submission, so add it after.
4. **Reciprocal reviewing.** Required in past years; check 2027.
5. **Do NOT publish the HuggingFace artifact before acceptance.** A public
   dataset matching the paper's numbers is a deanonymization path.
   `hf_artifact/scripts/preflight_public.py` fails by design until then.

None of items 1–4 could be agent-verified: `api.openreview.net` returned
**HTTP 403 on every call** — a 403 is the API refusing, **not** evidence a
profile is or is not there — and all three candidate AAMAS-2027 CFP
hostnames failed to resolve.

## Verify before submitting

AAMAS 2027 may publish its own author kit; ours is the 2026 kit with the
year advanced (`paper_support/aamas_official/PROVENANCE.md`). Re-check the
page limit, the anonymity rules and the copyright block against the 2027
instructions if they exist.

---

# SUBMISSION FREEZE — 2026-10-02 10:43

| | |
|---|---|
| title | From Feedback to Revision: When Do Multi-Agent Roles Look Load-Bearing? |
| GitHub HEAD | `57daaaf2c8cd` |
| Overleaf HEAD | **UNREACHABLE (access blocked)** — git access off, see `HANDOFF_CURRENT.md` |
| main text sha256 | `3cb9712a40d2176034a309a4…` (640,245 bytes) |
| supplement text sha256 | `48f51c61629cf99e552b3722…` |
| abstract sha256 (source) | `a497dba29f199e46f9965c4a…`, ~294 words |
| Figure 1 | `3c91da3e3ab4d9f61b979292…` |
| Figure 2 | `4525bb027304ef3c38181505…` |
| Omni-MATH data | 11,600 rows, 3 files, sha256 in `experiments/results/FROZEN/MANIFEST.json` |
| SciBench data | 2,296 rows, 574 problems, `10068f72cfd936d3…` |
| HF artifact | `AgentsSci/AAMAS2027-Roles` v1.1.0, **PRIVATE** |

**Gates: ALL PASS** (`FAILED_GATES` empty). Both documents build; main text
ends page 8; 0 undefined citations, 0 undefined references, 0 multiply
defined labels; 0 anonymity hits in either rendered PDF; 0 internal
condition codes in either PDF or in any shipped figure; 0 unrun
placeholders; `aamas.cls` byte-identical to the official kit; every
generated table matches its source.

**Reconstruction verified, not assumed.** A fresh clone of the GitHub repo,
building `paper/` and nothing else, produces both PDFs with text hashes
identical to the working copy.

## After this freeze

No scientific content changes without re-running the canonical chain in
`SOURCE_OF_TRUTH.md` and regenerating this freeze. `python3
scripts/final_freeze.py` must pass again before submitting.
