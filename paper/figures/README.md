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
| **manuscript** | Figure 1, `fig:dissociation`, `results.tex` |
| **purpose** | Roles do not buy the first answer; the difference appears after failure; and the two teams spend the same retry budget differently |
| **source script** | `analysis/scripts/mk_fig1_story.py` |
| **intermediate data** | `analysis/out/FIGDATA.json` (`cells`, `funnel`, `paired_recovery`) |
| **frozen dataset** | `experiments/results/FROZEN/` — 11,600 trajectories, sha256 in `MANIFEST.json` |
| **output** | `paper/figures/fig1_v1_story.pdf` (root copy `figures/fig1_v1_story.pdf`) |
| **regenerate** | `python3 analysis/scripts/mk_fig1_story.py && cp figures/fig1_v1_story.pdf paper/figures/` |

Three panels: **A** first-pass accuracy, role-structured vs role-free, all
three actors. **B** recovery after wrong-answer feedback, three conditions,
each contrast carrying its *paired* verdict so three descending bar pairs do
not read as three findings. **C** gemma-4's retry budget as two near-equal
stacked bars — 1.54 submit + 3.98 revise against 5.80 + 0.03.

**Panel B draws MARGINAL recovery** (each condition over its own
first-pass-wrong set). Figure 2 draws the same gemma-4 cell as **PAIRED**.
Both are correct and they are different numbers; each figure labels which it
uses. Do not describe them as contradicting.

Alternative design kept for reference: `figures/fig1_v2_story.pdf` renders
Panel C as a two-track flow. Rejected because it shows the split as track
thickness and demotes the equal totals — which is the comparison — to a label.

---

## Figure 2 — Cross-domain replication

| | |
|---|---|
| **manuscript** | Figure 2, `fig:xdomain`, `results.tex` §R4 |
| **purpose** | The same dissociation in a second, free-response science domain: flat first pass, then a large recovery drop — twice |
| **source script** | `analysis/scripts/mk_fig2_xdomain.py` |
| **intermediate data** | `analysis/out/FIGDATA.json` (`scibench`, `paired_recovery`) |
| **frozen datasets** | `experiments/results/FROZEN/` **and** `experiments/results/xdomain/FROZEN_SCIBENCH/` (2,296 rows, sha256 `10068f72cfd936d3…`) |
| **output** | `paper/figures/fig2_v2_xdomain.pdf` |
| **regenerate** | `python3 analysis/scripts/mk_fig2_xdomain.py && cp figures/fig2_v2_xdomain.pdf paper/figures/` |

gemma-4 only, deliberately: gpt-oss's SciBench cell is underpowered (0.06–0.42
depending on the test) and placing it alongside would invite the
across-the-board reading the paper refuses. Top row **marginal** first pass,
bottom row **paired** recovery, each labelled. No error bars — neither
contrast has CI fields, and an interval on one column only would read as
"SciBench is the exact one"; the discordant split and exact p carry the
uncertainty for both.

Alternative kept: `figures/fig2_v1_xdomain.pdf` (grouped bars).

---

## Not in the manuscript

| file | status |
|---|---|
| `figures/figS1_conditions.pdf` | supplement candidate — the three conditions as pipelines |
| `figures/fig1_v1_grouped.pdf` | **superseded** by `fig1_v1_story`. Still in `paper/figures/` and no longer referenced. It was the figure that printed bare condition codes before the terminology gate existed. |
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
