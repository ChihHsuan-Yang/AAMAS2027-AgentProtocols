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
`671ba20ea833d4387e88cefd539396c9d46794173e1a7cc31f0e8902bd26f918`
**as of Part 2; superseded — see Part 3**, where `[T28b]` appended the
SciBench export and moved it to `e267255d…`. The Omni-MATH values are
byte-identical across that change.

**CORRECTED 2026-10-01.** This line read `a4be829b…`, which no longer matched
the file or the committed blob. Re-running `FINAL_TABLES.py` reproduces
`671ba20e…` byte-for-byte and `git cat-file` shows that is also what is
committed, so the DATA never drifted — only this recorded hash went stale,
behind the `248ba19` export fix. A provenance hash that disagrees with its
artifact is worse than none, because it invites a reader to conclude the
snapshot changed.

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

---

# PART 2 — the three-panel story figures (figure agent, 2026-10-01)

These supersede the earlier slot-based figures for the manuscript's current
single-story framing. **They are additive: nothing above was deleted**, because
the earlier options are still referenced by `paper/sections/results.tex` and a
retraction is labelling, not deletion.

## The sentence these figures carry

> Roles do not help a team produce its first answer. They help it turn an
> external "your answer is wrong" signal into an actual **revision** rather
> than a **resubmission** of the same candidate.

## Frozen snapshot and intermediate

Unchanged and re-verified by regenerating it: `experiments/results/FROZEN/`,
`frozen_at 2026-09-30T10:09:30.201557`, 11,600 trajectories.

| file | rows | sha256 |
|---|---|---|
| `actor3.jsonl` | 1,200 | `fa22a446d5314bb67b1c6a6444b511eeeae3eb8770419a36f182617eeccbf3b5` |
| `armCp.jsonl` | 800 | `038e08aec4d4aee166106a6325309dfe2301faf339c7d0bf82338a74576424d4` |
| `campaign_v2.jsonl` | 9,600 | `e4e53cb117d91129991ce2fe87e336e152fc9ee6ca826d363f2bd5dd240d7130` |

`analysis/out/FIGDATA.json`, sha256 `671ba20ea833d4387e88cefd539396c9d46794173e1a7cc31f0e8902bd26f918`.

**The README previously recorded this hash as `a4be829b…`, which was stale.**
Re-running `FINAL_TABLES.py` reproduces `671ba20e…` byte-for-byte, and that
same value is what is committed in git (verified with `git cat-file`, after a
`git show` loop silently returned empty and was itself the lesson). The data
did not change; the recorded hash had simply not been refreshed.

## Figure 1 — the whole story, three panels

Script: `analysis/scripts/mk_fig1_story.py`
Intended manuscript number: **Figure 1**.

| option | file | sha256 | design |
|---|---|---|---|
| v1 | `fig1_v1_story.{pdf,png}` | `6ddf8e28d34439a3…` | panel C = stacked retry budget |
| v2 | `fig1_v2_story.{pdf,png}` | `7777f93c6888b3fd…` | panel C = two-track feedback flow |

**Recommended: v1.** Both carry the same numbers; v1 makes "same budget" a
*visible equality* — two bars of nearly equal length whose internal split
differs — which is the comparison the panel is about. v2's tracks encode the
same split as thickness, which reads well but makes the equal totals a label
rather than a shape.


**Hashes in this section were refreshed 2026-10-01.** These figures were
rebuilt when the shared style module gained the strengthened terminology
pattern (Part 3), so their bytes changed; their DATA and appearance did
not. A provenance hash that disagrees with its artifact is worse than
none — it invites the reader to conclude the figure changed.

Scientific purpose per panel, and the FIGDATA field each label reads:

| panel | purpose | FIGDATA fields |
|---|---|---|
| A | roles removed, first-pass solving intact | `cells[*|{A,B}].firstpass{,_lo,_hi}` |
| B | the difference appears after failure | `cells[*|{A,B,C}].recovery{,_lo,_hi}`, `paired_recovery[*|AB].p` |
| C | same retry budget, different use | `cells[gemma-4-31B-it|{A,B}].{submissions,revising,cycles}`, `max_cycles`, `budget` |

Footnote denominators read `cells[*].n_fpw` and `paired_recovery[*|AB].n`.

## Figure 2 — cross-domain replication — **BLOCKED, NOT DRAWN**

Script: `analysis/scripts/mk_fig2_xdomain.py` (exits **3** with a data contract).

**SciBench is not in `FIGDATA.json` at all.** `[T28]` reads
`experiments/results/FROZEN/` only; SciBench is a separate frozen snapshot
(`experiments/results/xdomain/FROZEN_SCIBENCH/`, sha256 `10068f72cfd936d3…`,
2,296 rows) analysed by `xdom_analyze.py`, which prints a table and exports
no machine-readable artifact.

This was **not** resolved by computing the numbers in the plotting script,
because the missing piece is a **denominator choice**, not a computation:
`notes/XDOMAIN-INTEGRATION-DECISION.md` records that the same frozen file
yields `0.212 → 0.020` (paired, n=99) and `0.254 → 0.051` (marginal, n=118),
calls the confusion "exactly how a wrong pair of numbers enters a paper", and
requires the paper to state which population every SciBench figure uses.
Making that call silently inside a figure script is out of scope.

Run the script for the exact list of FIGDATA keys needed to unblock it.

## Figure S1 — the three conditions

Script: `analysis/scripts/mk_figS1_conditions.py`
File: `figS1_conditions.{pdf,png}`, sha256 `64a6ee0610923b16…`
Intended manuscript number: **Figure S1** (supplement unless it earns main-text space).

Topology is **design**, verified in `experiments/prompts.py` and
`experiments/schemas.py`. The only measured column is mechanical functional
collapse, `mechanical[*].functional_collapse` — never the judge, per
FINDING-25.

## No label is hand-typed, and here is how that was verified

`python3 analysis/scripts/check_figures.py --selftest`

It reads the **shipped PDF**, not the source, and asserts three things per
figure: every number is reproducible from a FIGDATA field at one of the
precisions used; no arm code appears; zero raster objects with fonts embedded.
Current result: **29 / 25 / 8 numbers rendered, 0 untraced**.

**The audit is proved to discriminate rather than merely to pass.**
`--selftest` plants `0.7349` — a value absent from FIGDATA — into a copy of a
real figure and requires the audit to flag it. It does.

Two defects were found by doing this honestly, and both are recorded because
each passed a check that already existed:

1. **A missing file read as a clean result.** The first self-test build failed
   on an import path, wrote no PDF, and the audit reported zero untraced
   numbers — a void control that looked like a pass. The checker now aborts on
   a missing file or empty text instead of treating absence as zero findings.
2. **A structural zero rendered as a measured one.** Figure S1 first printed
   the enforced condition's organization collapse as `0.000`. That zero is
   **structural**: the planner and reviewer schemas have no answer field
   (T8 confirms planner 0.000 / reviewer 0.000 in every enforced cell), so the
   measure cannot fire. Printed beside role-free's measured 0.906 it would
   invite the reader to conclude enforcement *reduced* collapse on a shared
   scale. It now renders `n/a`. The guard that should have caught this tested
   `is None`, which never fires on `0.0`.

## Terminology is enforced at save time, not by discipline

`mk_figstyle.save()` collects every string the figure actually renders and
refuses to write the file if one carries an arm code. Proved to fire by
planting `arm B no roles` and confirming no file was written.

**This surfaced a pre-existing violation outside these three figures.**
`pdftotext` finds bare arm codes in **5 shipped PDFs**, including
`fig1_v1_grouped.pdf`, the figure `paper/sections/results.tex` currently
includes:

| file | status |
|---|---|
| `fig1_v1_grouped.pdf` | **in the manuscript**, prints `A soft roles / B no roles / C enforced` |
| `fig1_v2_slopes.pdf`, `fig1_v3_dumbbell.pdf` | arm codes in footnote |
| `fig2_v1_budget.pdf`, `fig2_v3_funnel.pdf` | arm codes in legend |

Their scripts (`mk_fig1_dissociation.py`, `mk_fig2_mechanism.py`,
`mk_fig3_design.py`) now **fail the gate** rather than rebuild silently. They
were left failing rather than rewritten: they are outside this task's three
figures, and `mk_fig4_decomposition.py` already passes. A grep of
`paper/sections/*.tex` finds the violation only in the figure, not the prose,
so `TERMINOLOGY.md` rule 4's grep would not have caught it.

## Format and legibility — measured, not assumed

- `\columnwidth` re-measured from `paper/aamas.cls` by compiling a stub
  **after `\maketitle`**: **241.147pt = 3.337in**, matching the authored
  width exactly. (Measured *before* `\maketitle` it reads 506.295pt, which is
  how a one-column figure gets authored at two-column width.)
- **Minimum rendered font size: 6.5 pt** against a 9 pt body. `save()` asserts
  nothing renders below it.
- Legibility verified by compiling all three figures into the real `aamas.cls`
  two-column layout at `width=\columnwidth` with no rescaling, rasterizing at
  300 dpi, and reading the page — not by inspecting PNGs alone. Three layout
  defects were found that way and only that way: a footnote line 3.356in wide
  on a 3.337in column, panel C's title overflowing, and a 0.03-cycle callout
  colliding first with the axis labels and then with the tick row.
- Colour: Okabe-Ito, re-validated with the dataviz validator (categorical,
  `--pairs all`, light surface): lightness band, chroma floor, CVD separation
  (worst pair ΔE 11.0 deutan / 8.6 tritan), normal-vision floor (18.7) and
  contrast all **PASS**. **Nothing is encoded by colour alone** — condition
  identity is also carried by position, by the written condition name, and by
  hatch on the enforced condition.
- Axes start at 0; no truncated proportion axis anywhere.

## One thing in the data that made a panel awkward to draw honestly

Panel B shows three actors' recovery, but **only gemma-4's role contrast
survives pairing** (p=2e-08; gpt-oss p=0.208, Llama-3.3 p=0.375). Drawn
plainly, three descending bar pairs read as three findings. The panel
therefore marks each contrast's paired verdict, and `n.s.` is computed from
`paired_recovery[*|AB].p`, not asserted — so the annotation cannot outlive the
claim. The bars are **marginal** rates and the p-values are **paired** on a
smaller population; both are labelled with their own n.

---

# PART 3 — Figure 2 unblocked, and the terminology gate (2026-10-01)

## FIGDATA has moved

`analysis/out/FIGDATA.json` is now sha256 `e267255da317b4fe68522c82c6c9bd35e0f09e95ca1396a12e4fd2f9b35c5c7c`
(was `671ba20e…` in Part 2). The change is **additive**: `[T28b]` of
`FINAL_TABLES.py` appended `scibench` and `scibench_note`. The Omni-MATH
values are byte-identical, so every Part 1 / Part 2 figure is unaffected.

## Figure 2 — cross-domain replication, now drawn

Script: `analysis/scripts/mk_fig2_xdomain.py`
Intended manuscript number: **Figure 2**.

| option | file | sha256 | design |
|---|---|---|---|
| v1 | `fig2_v1_xdomain.{pdf,png}` | `03c4d1e8903e698e…` | grouped bars, 2x2 |
| v2 | `fig2_v2_xdomain.{pdf,png}` | `57337cc48f5c93c5…` | paired slopes, 2x2 |

**Recommended: v2.** The message is *flat, then steep — twice*. A slope states
"this moved" as a single visual gesture, so the top row reads as two flat
lines and the bottom as two parallel dives. v1's bars force the reader to
difference two heights by eye, which is the comparison the figure is making.
v1 remains the safer choice if a reviewer prefers bars for proportions.

**Populations, stated on the figure.** First-pass row is **marginal**;
recovery row is **paired**. `FIG["scibench_note"]` requires a figure to say
which it draws, and the script prints that note at build time so the
requirement travels with the artifact.

| what | FIGDATA field |
|---|---|
| Omni first-pass | `cells[gemma-4-31B-it|{A,B}].firstpass`, `.n_judged` |
| SciBench first-pass | `scibench[gemma-4-31B-it].firstpass_marginal_{A,B}`, `.n_firstpass_A` |
| Omni recovery (paired) | derived from `paired_recovery[gemma-4-31B-it|AB]` |
| SciBench recovery (paired) | `scibench[…].recovery_paired_{A,B}`, `.n_paired`, `.discordant_*`, `.mcnemar_p` |

**A cross-figure hazard, handled rather than hidden.** Figure 1 panel B draws
gemma-4's Omni-MATH recovery as **marginal** (0.222 → 0.051); Figure 2 draws
the same actor and domain as **paired** (0.160 → 0.017). Both are correct for
their own population and they are different numbers for the same cell. Each
row is labelled with its population and its own n so the two figures cannot
be read as contradicting each other.

**No error bars, deliberately.** Neither the SciBench export nor the Omni
paired contrast carries bootstrap CI fields. Drawing an interval on one
column and not the other would read as "SciBench is exact". Paired evidence
is the discordant split and the exact McNemar p — both present for both
domains, both seed-free.

**Effect sizes are not implied to be equal.** Omni Δ = −0.143, SciBench
Δ = −0.192, each shown with its own discordant split. The two-proportion test
(z=1.06, p=0.289) *fails to distinguish* them, which is not evidence that
they match; the footnote says so.

gemma-4 only. gpt-oss's SciBench cell is underpowered (paired n=96; power
0.06 exact McNemar / 0.12 two-proportion z — the **0.42 that circulated
earlier is superseded**, per the 2026-10-01 correction in
`XDOMAIN-INTEGRATION-DECISION.md`; the manuscript says "0.06–0.45 by test").
This script's own docstring quoted the stale 0.42 until that note was fixed
underneath it — the same stale-derived-artifact trap the note describes.

## A provenance gap, reported not patched

`provenance["files"]` lists only the three Omni-MATH files, so
`provenance_line()` does not name the SciBench snapshot this figure draws
(`scibench_AB.jsonl`, sha256 `10068f72cfd936d3…`, 2,296 rows — verified
unchanged on disk). The script **prints a warning** rather than writing the
hash itself: provenance belongs in the export, not in a plotting script.
**Suggested fix for the coordinator:** add that file to `provenance["files"]`
in `[T28b]`.

## The terminology gate — `scripts/check_terminology_pdfs.py`

```sh
python3 scripts/check_terminology_pdfs.py            # gate, exits non-zero on a hit
python3 scripts/check_terminology_pdfs.py --selftest # proves it can fail first
```

Scans every `figures/*.pdf` with `pdftotext`. **Current state: 15/15 clean.**

It cannot pass vacuously: a missing `pdftotext`, a PDF with no extractable
text, or an empty sweep each **abort or fail** rather than report success —
because outlined or rasterized text would hide a violation from any
text-based scan, and "nothing found" in an empty directory is not a pass.

**The pattern is tested in both directions**, and this mattered. The first
version caught `Arm B` and the old long labels but **missed**
`A 0.014 ≈ B 0.015, but C 0.139` — which is exactly what survived in
`fig1_v1_grouped` after its legend was fixed. A letter labelling a *number*
is an arm code just as much as one labelling a prose phrase. The pattern now
covers five forms (10 positive cases) and is checked against 12 strings it
must NOT flag — panel tags `A`/`B`/`C`, `37 vs 3 of n=237`, `gemma-4 31B` —
because a gate with false positives gets switched off. `mk_figstyle.save()`
carries the same pattern so new violations are blocked at write time.

## Legacy figures regenerated — all four scripts

| script | outputs | what changed |
|---|---|---|
| `mk_fig1_dissociation.py` | `fig1_v1_grouped`, `fig1_v2_slopes`, `fig1_v3_dumbbell` | legend, footnotes, tick labels, Llama annotation, axis title `arm`→`condition` |
| `mk_fig2_mechanism.py` | `fig2_v1_budget`, `fig2_v2_panels`, `fig2_v3_funnel` | row labels, legend, slope ticks, funnel title, footnote |
| `mk_fig3_design.py` | `fig3_v1_columns`, `fig3_v2_rows` | column headings; the row swatch now carries colour only |
| `mk_fig4_decomposition.py` | `fig4_v1_stacked`, `fig4_v2_rows` | already compliant; regenerated unchanged |

Two defects surfaced **only by looking at the regenerated output**, after the
automated gates passed:

1. **A clipped label.** `fig2_v1_budget` rendered `tructured` — the long
   condition name overflowed a left margin sized for `arm A`. Both the
   terminology gate and `pdftotext` saw the *string*; neither sees that the
   glyphs fall outside the axes.
2. **A collided annotation.** `fig1_v1_grouped`'s Llama note grew when it
   stopped using letters and ran into the legend. Shortened.

Generic prose (`across arms`, `every arm`, the axis title `arm`) was also
changed to *condition*. Those were never arm *codes* — no reader has to hold
a mapping — but `TERMINOLOGY.md` asks that figures not read like an internal
experiment log. **Zero occurrences of "arm" now appear in any shipped PDF.**

## Defect class worth naming: a guard that cannot fire

The S1 structural zero (Part 2) and the void self-test share one shape: **a
guard written for a value that never occurs.** `if v is None` cannot fire on
`0.0`; an audit that reads a nonexistent file finds no violations in it. Both
*passed*, and both were empty. The rule that catches this class is to ask not
"did the check pass?" but **"what input would make it fail, and have I fed it
one?"** — which is why every check in this directory now ships a
`--selftest` that plants the defect it claims to detect.
