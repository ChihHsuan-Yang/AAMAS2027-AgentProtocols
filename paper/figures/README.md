# Figure index and provenance

**Every figure here is GENERATED.** No numeric label is hand-typed anywhere
in any figure or generator — every value is read at render time from
`analysis/out/FIGDATA.json`, written by section `[T28]`/`[T28b]` of
`analysis/scripts/FINAL_TABLES.py`.

Figures exist in two places. `figures/` at the repo root is where the
generators write. **`paper/figures/` is what LaTeX resolves and what the
Overleaf project needs** — copy root → `paper/figures/` after regenerating,
or the PDF builds locally and breaks on Overleaf.

---

## Figure 1 — Feedback to revision

| | |
|---|---|
| **manuscript** | Figure 1, `fig:dissociation`, `results.tex` §R1 |
| **purpose** | Removing roles leaves the first answer alone; recovery after a failed first answer depends on whether the evaluator's feedback reaches the team; and the two teams spend the six-cycle budget differently |
| **source script** | `analysis/scripts/mk_fig1_bf.py` |
| **intermediate data** | `analysis/out/FIGDATA.json` (frozen snapshot), `analysis/out/FIGDATA_BF.json` (feedback-matched cells, paired p), `analysis/out/FIGDATA_GATE.json` (Panel C: approvals and revisions) |
| **frozen dataset** | `experiments/results/FROZEN/` — 11,600 trajectories, sha256 in `MANIFEST.json`; feedback-matched runs in `experiments/results/bf/MANIFEST_BF.json` |
| **output** | `paper/figures/fig1_v3_story.pdf` (root copy `figures/fig1_v3_story.pdf`) |
| **regenerate** | `python3 analysis/scripts/mk_fig1_bf.py` (`mk_figstyle.save()` syncs `paper/figures/`) |

Three panels. **A** first-pass accuracy per actor and domain for the
role-structured team and both role-free teams. **B** recovery after a failed
first answer (marginal, each condition over its own first-pass-wrong set),
with the paired role-structured vs role-free-with-feedback McNemar p above
each group. **C** gemma-4 on Omni-MATH: cycles per failed trajectory spent
submitting (approvals; end-of-budget grading is not counted) versus
revising, in four conditions.

Earlier versions (`figures/fig1_v1_story.pdf`, `figures/fig1_v2_story.pdf`)
predate the feedback-matched condition and are kept under `figures/` only.

---

## Not in the manuscript

| file | status |
|---|---|
| `figures/fig2_v2_xdomain.pdf` | **removed from the manuscript** with the feedback-matched revision: the SciBench cells are now groups in Figure 1 and rows of Table 2. Kept under `figures/` only. |
| `figures/fig1_v1_story.pdf` | superseded by `fig1_v3_story`; kept under `figures/` only. |
| `figures/figS1_conditions.pdf` | supplement candidate — the three conditions as pipelines |
| `figures/fig1_v1_grouped.pdf` | **superseded** by `fig1_v1_story`, and **deleted from `paper/figures/` on 2026-10-02**. Leaving it there was not harmless: the copy in `paper/figures/` was the *uncorrected* one, still printing `A soft roles / B no roles / C enforced`, and it sat in the Overleaf-bound directory for a day while the terminology gate reported clean --- the gate was reading `figures/`, where the corrected copy lives. It survives only under `figures/`, where it is a draft variant. |
| `figures/fig3_*`, `fig4_*` | earlier exploratory designs, not for the paper |

---

## Gates

```bash
python3 scripts/check_terminology_pdfs.py     # exit 0: no condition codes in any figure
python3 scripts/check_terminology_pdfs.py --selftest   # plants a violation, must catch it
```

The terminology gate scans **rendered PDF text**, because the `.tex` grep in
`paper/TERMINOLOGY.md` is structurally unable to see inside a figure — and the
figure the paper included once printed "A soft roles / B no roles / C
enforced" while that grep reported clean.

**Both gates see strings, not glyphs.** Two defects were found only by looking
at rendered output after every check went green: a clipped label where a
margin had been sized for a short condition name, and a collided annotation.
Look at the figure.

---

## Three gates now stand between a figure and the PDF

Added 2026-10-02, each after a real failure rather than a hypothetical one.

**1. `paper/figures/` is synced automatically.** `mk_figstyle.save()` copies
a regenerated figure into `paper/figures/` whenever a file of that name is
already there. Only files already there: `paper/figures/` holds exactly what
the manuscript ships, and a draft variant must not land in it by being
generated. Before this, the copy was a manual step and skipping it left
LaTeX including the old image while every check inspected the new one.

**2. The terminology gate reads both directories, and compares them.**
`scripts/check_terminology_pdfs.py` previously scanned only `figures/` ---
where the generators write --- while LaTeX resolves `\includegraphics`
against `paper/figures/`. A gate that inspects the producer's output cannot
certify the consumer's input. It now scans both, fails if a figure present
in both differs between them, fails on a file in `paper/figures/` that no
document includes, and fails on a document reference with no file.

**3. Figure PDFs are byte-reproducible.** `savefig` was embedding a
wall-clock `CreationDate`, so every regeneration produced a different
sha256 even with identical data. The hash recorded in `FINAL_FREEZE.json`
could not then distinguish *the figure changed* from *the figure was
regenerated*. `metadata={"CreationDate": None}` strips it; regenerating from
the same frozen data is now byte-identical, so a changed hash means changed
data.

All three were positive-controlled by planting a violation in each one's own
shape --- a stray file, a missing file, a stale consumer copy --- and all
three fired.
