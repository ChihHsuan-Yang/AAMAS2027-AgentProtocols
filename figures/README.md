# Figures — provenance and reproduction

**Owner: figure agent.** Everything in this directory is generated. Do not
hand-edit a PDF, a PNG, or a number.

## The rule this directory is built on

**Every numeric label in every figure is computed from data at render time.
There is no hand-typed numeric label anywhere in any figure or any figure
script.** The plotting scripts contain no result literals at all — only
geometry (positions, widths, font sizes), the structural bounds of a
proportion (0 and 1), colour codes, string format precision, and one
conventional significance threshold (`ALPHA = 0.05`, declared as such).

This is enforced structurally, not by discipline:

1. `analysis/scripts/FINAL_TABLES.py` section **[T28]** recomputes every
   quantity the figures draw, from the frozen snapshot, and writes
   `analysis/out/FIGDATA.json`.
2. Every `mk_fig*.py` reads that one file through `mk_figstyle.figdata()` /
   `cell()`. A figure that needs a quantity not in it is fixed by adding a
   computation to `FINAL_TABLES.py` and re-running — never by typing a number
   into a plotting script.
3. Text that *interprets* a number (the Llama annotation, the arm-C attrition
   note, the significance marks) is generated from predicates over the data,
   not asserted. See "Annotations that could go stale" below.

## Reproduce

```sh
python3 analysis/scripts/FINAL_TABLES.py          # writes analysis/out/FIGDATA.json
python3 analysis/scripts/mk_fig1_dissociation.py
python3 analysis/scripts/mk_fig2_mechanism.py
python3 analysis/scripts/mk_fig3_design.py
python3 analysis/scripts/mk_fig4_decomposition.py
```

`FINAL_TABLES.py` takes ~15 s; each figure script ~1 s.

## Frozen snapshot these figures derive from

`experiments/results/FROZEN/`, `frozen_at 2026-09-30T10:09:30.201557`,
11,600 trajectories.

| file | rows | sha256 |
|---|---|---|
| `actor3.jsonl` | 1,200 | `fa22a446d5314bb67b1c6a6444b511eeeae3eb8770419a36f182617eeccbf3b5` |
| `armCp.jsonl` | 800 | `038e08aec4d4aee166106a6325309dfe2301faf339c7d0bf82338a74576424d4` |
| `campaign_v2.jsonl` | 9,600 | `e4e53cb117d91129991ce2fe87e336e152fc9ee6ca826d363f2bd5dd240d7130` |

Intermediate: `analysis/out/FIGDATA.json`, sha256
`a4be829bdc65491c74cd89bcd8075cfe21f2ed2141a89a711fc3fb185029a0af`
(regenerate and the hash changes only if the frozen data or [T28] changes).

Two figure inputs are **not** in the frozen snapshot and are labelled as such
wherever used: the blinded-adjudication verdicts (`adjudication/`) and the
single-agent control (historical corpus). Neither is drawn in the current
figures — see the FINDING-25 note below.

## The figures

Each figure has 2–3 genuinely different designs. Pick one per slot; the others
can be deleted.

### Figure 1 — the phase dissociation (headline)
Script: `analysis/scripts/mk_fig1_dissociation.py`
Source: FIGDATA `cells[*].firstpass{,_lo,_hi}`, `recovery{,_lo,_hi}`,
`n_graded`, `n_fpw`, `attrition`, `paired_recovery[*].p`
— from FINAL_TABLES **[T1] [T3] [T4] [T7] [T28]**

| option | file | width | design |
|---|---|---|---|
| v1 | `fig1_v1_grouped.{pdf,png}` | 1 col | grouped columns, two stacked panels |
| v2 | `fig1_v2_slopes.{pdf,png}` | 1 col | small-multiple slopes, one column per actor |
| v3 | `fig1_v3_dumbbell.{pdf,png}` | 2 col | dumbbell rows on a shared value axis |

Intended manuscript number: **Figure 1**.

### Figure 2 — why recovery disappears (gemma-4)
Script: `analysis/scripts/mk_fig2_mechanism.py`
Source: FIGDATA `cells[gemma-4-31B-it|{A,B}]` `cycles`, `submissions`,
`revising`, `frozen_ans`, `recovery`, `n_fpw`; `budget`; `max_cycles`;
`funnel` — from FINAL_TABLES **[T5] [T24] [T28]**

| option | file | width | design |
|---|---|---|---|
| v1 | `fig2_v1_budget.{pdf,png}` | 1 col | one cycle budget, split submitting vs revising |
| v2 | `fig2_v2_panels.{pdf,png}` | 1 col | paired A→B slopes, one per measure, own axis each |
| v3 | `fig2_v3_funnel.{pdf,png}` | 1 col | strictly nested opportunity funnel |

Intended manuscript number: **Figure 2**.

### Figure 3 — the A/B/C design schematic
Script: `analysis/scripts/mk_fig3_design.py`
Structure verified in `experiments/prompts.py` and `experiments/schemas.py`;
outcome notes from FIGDATA `cells`, `mechanical`, `budget`
— from FINAL_TABLES **[T8] [T24] [T28]**

| option | file | width | design |
|---|---|---|---|
| v1 | `fig3_v1_columns.{pdf,png}` | 1 col | three columns, each with its own pipeline |
| v2 | `fig3_v2_rows.{pdf,png}` | 2 col | pipeline drawn once, arms as rows beneath |

Intended manuscript number: **Figure 3**.

### Figure S1 — outcome decomposition (§19 prototype)
Script: `analysis/scripts/mk_fig4_decomposition.py`
Source: FIGDATA `cells[*].decomp`, `final_prereg` — from **[T1] [T28]**

| option | file | width | design |
|---|---|---|---|
| v1 | `fig4_v1_stacked.{pdf,png}` | 1 col | stacked columns, arms grouped within actor |
| v2 | `fig4_v2_rows.{pdf,png}` | 2 col | one 100% band per actor-arm row |

Intended manuscript number: **Figure S1**, or merged into Figure 1 if preferred.

`first pass correct + recovered + never recovered + never judged = 1` is an
**arithmetic identity**, not a causal equation, and both variants say so on the
figure. The script asserts the partition holds in all 11 cells and fails loudly
if it does not.

## Format and legibility

- Vector PDF for LaTeX, 400 dpi PNG for review. Verified programmatically:
  **0 raster images and extractable (not outlined) text in every PDF**;
  `pdf.fonttype 42`, all fonts embedded.
- One-column figures are authored at exactly **241.147 pt = 3.337 in**
  (`\columnwidth` measured from `paper/aamas.cls`, sigconf, after
  `\maketitle`); two-column at **506.295 pt = 7.006 in** (`\textwidth`).
  Insert at `width=\columnwidth` / `width=\textwidth` — **do not rescale**, or
  the point sizes below stop being true.
- **Minimum rendered font size: 6.5 pt** (annotations and tick labels), against
  a 9 pt body. Larger elements: 7.0 pt legends, 7.5 pt axis labels, 8.0 pt
  titles. `mk_figstyle.save()` asserts nothing renders below 6.5 pt and that
  the figure width has not drifted, so a violation fails the build rather than
  shipping.
- Legibility was verified by compiling every figure into the real `aamas.cls`
  two-column layout at final size and reading the rendered pages, not by
  inspecting the PNGs alone.
- Colour: Okabe-Ito (`#0072B2` A, `#D55E00` B, `#009E73` C), checked with the
  dataviz validator (categorical, `--pairs all`, light surface): lightness
  band, chroma floor, CVD separation, normal-vision floor and contrast all
  PASS. **Nothing is encoded by colour alone** — arm identity is also carried
  by position, by the A/B/C tick label, and by hatch/marker shape on arm C.

## Annotations that could go stale — and why they cannot

The interpretive text is derived, so it tracks the claims instead of restating
a frozen opinion:

- **Llama-3.3's recovery null.** Membership is computed by
  `null_but_restorable()`: A-vs-B paired p > α **and** A-vs-C paired p < α.
  The figure therefore says the repair channel exists and role labels do not
  open it. It does **not** say "floor effect" — that is a DEAD claim
  (STATISTICAL_AUDIT SERIOUS-2), because arm C restores recovery in that same
  actor.
- **Arm C attrition range** (`ATTR_TXT`) is computed from
  `cells[*|C].attrition`, not typed.
- **Organization in Figure 3** uses the **mechanical** functional-collapse
  rate, which involves no judge. Per **FINDING-25** the adjudication is
  outcome-blind but *not* condition-blind, so no figure rests an
  arm-contrastive organization claim on the judge.

## Two defects found and fixed while building these

Recorded because both were invisible to the checks that existed:

1. **`FINAL_TABLES.py` [T28] shipped a decomposition that was not a
   partition.** The exported dict carried `ungraded` (no *final* grade) while
   the assert two lines above checked `unjudged` (no *first* verdict). These
   differ in arm C — a trajectory can be judged once and then die in
   regeneration — so the five fields summed to more than n (gemma-4 C: 1682 vs
   1600) while the assert passed. Fixed by exporting the partition the assert
   validates, and by re-asserting over the **exported dict** rather than local
   variables.
2. **`fig1_dissociation.{pdf,png}` were stale and have been deleted.** They
   were built from `experiments/results/main/` (not the frozen snapshot) by an
   earlier script, and encoded organizational collapse with the byte-duplication
   metric that F22/A1 demoted to a lower bound.

## Files that are inputs, not outputs

`analysis/scripts/mk_figstyle.py` is the shared style and data loader. It owns
the palette, the page geometry, the rc settings, and `save()` with its two
assertions. Import it; never copy its contents into a figure script.
