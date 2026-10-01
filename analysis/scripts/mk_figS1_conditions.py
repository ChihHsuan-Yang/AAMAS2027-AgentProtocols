# -*- coding: utf-8 -*-
"""FIGURE S1 -- the three conditions, conceptually.  Supplement unless it
earns main-text space.

  role-structured      Planner -> Executor -> Reviewer   (roles in prose)
  role-free            Solver  -> Solver   -> Solver     (one generic prompt)
  structurally enforced  typed interfaces                (schema has no answer
                                                          field; validator
                                                          rejects a leak)

WHAT IS STRUCTURE AND WHAT IS MEASURED.  Everything drawn as topology is fixed
BY DESIGN and verified in experiments/prompts.py and experiments/schemas.py:
all three conditions run the same three-agent loop, the same routing, and the
same budget.  The ONLY measured quantity on this figure is the mechanical
functional-collapse rate, read from FIGDATA.  Per FINDING-25 the adjudication
is outcome-blind but NOT condition-blind, so no arm-contrastive figure may
rest on the judge; the mechanical measure involves no judge at all.

TERMINOLOGY: no arm letters anywhere (paper/TERMINOLOGY.md); save() enforces it.

Run:  python3 analysis/scripts/mk_figS1_conditions.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

import mk_figstyle as S

S.apply_rc()
D = S.figdata()
ACTORS = D["actors"]
MECH = D["mechanical"]
BUD = D["budget"]
MAXCYC = D["max_cycles"]

ROLES = {"A": ["Planner", "Executor", "Reviewer"],
         "B": ["Solver", "Solver", "Solver"],
         "C": ["Planner", "Executor", "Reviewer"]}

# What the MANIPULATION is -- design facts, verified in the two source files.
MANIP = {"A": "roles named and described in prose",
         "B": "one generic prompt, identical for all three",
         "C": "typed interfaces; planner schema has no answer field"}


# The enforced condition's planner and reviewer schemas have NO answer field
# and a validator rejects a leak (experiments/schemas.py), so "all three
# agents assert an answer" is 0 BY CONSTRUCTION there.  T8 confirms it:
# planner 0.000 and reviewer 0.000 in every enforced cell, in all three
# actors.  That zero is therefore a STRUCTURAL FACT, not a measurement, and
# printing it as "0.000" beside role-free's measured 0.906 would invite the
# reader to conclude that enforcement *reduced* collapse on the same scale.
#
# This was a live defect in the first build of this figure: the guard tested
# `is None`, which never fires on a value of 0.0, so the undefined cell
# rendered as a confident measured zero.  Same shape as the project's
# "absent input defaults to a plausible zero" class.  The condition is now
# derived from the data (every cell exactly 0) AND from the schema fact,
# rather than from a hand-maintained list.
MEASURABLE = {"A", "B"}          # conditions where the measure can fire at all


def collapse_range(arm):
    """Per-actor mechanical functional collapse for a condition.

    Returns (min, max, n_actors) rather than a pooled point estimate.  Pooling
    hides that the role-structured condition is EXACTLY 0.000 in two actors and
    0.120 in the third -- a weighted mean of 0.053 reports a middle value that
    no actor exhibits.
    """
    vs = [MECH[f"{a}|{arm}"]["functional_collapse"]
          for a in ACTORS if f"{a}|{arm}" in MECH]
    if not vs:
        return None
    return min(vs), max(vs), len(vs)


def collapse_text(arm):
    if arm not in MEASURABLE:
        return "n/a"
    r = collapse_range(arm)
    if r is None:
        return "n/a"
    lo, hi, _ = r
    return f"{lo:.3f}" if abs(hi - lo) < 5e-4 else f"{lo:.3f}–{hi:.3f}"


def build():
    """Layout note: the first build placed rows and the footnote by eye and
    every band overlapped -- role names collided with the collapse column, and
    the footnote ran through the third row.  Geometry is now computed in
    INCHES from an explicit band stack, and the figure height is the sum of
    the bands rather than a guess."""
    # --- band stack, in inches (top to bottom)
    # h_foot sized from the footnote's own line count: 6 lines at
    # FS_ANNOT with linespacing 1.32 is 0.715in, and the last row's subtitle
    # sat 0.022in above that before this was widened.
    h_head, h_row, h_gap, h_foot = 0.20, 0.56, 0.10, 0.88
    rows_n = 3
    FIG_H = h_head + rows_n * h_row + (rows_n - 1) * h_gap + h_foot
    fig = plt.figure(figsize=(S.COLWIDTH_IN, FIG_H))
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
    ax.set_xlim(0, S.COLWIDTH_IN); ax.set_ylim(0, FIG_H); ax.axis("off")

    # --- horizontal plan, in inches: label column | pipeline | measure column
    x_lab = 0.055
    x_pipe0, x_pipe1 = 0.055, 2.620
    x_meas = S.COLWIDTH_IN - 0.055
    bw = 0.615                                   # box width
    gap = (x_pipe1 - x_pipe0 - 3 * bw) / 2

    ax.text(x_meas, FIG_H - 0.055, "organization\ncollapse", ha="right",
            va="top", fontsize=S.FS_ANNOT, color=S.INK, linespacing=1.15)

    for i, arm in enumerate(("A", "B", "C")):
        y_top = FIG_H - h_head - i * (h_row + h_gap)
        y_name = y_top - 0.075
        y_box  = y_top - 0.315                   # box CENTRE
        y_sub  = y_top - 0.520
        ax.text(x_lab, y_name, S.ARM_LONG[arm], ha="left", va="center",
                fontsize=S.FS_LABEL, color=S.INK)
        for j, r in enumerate(ROLES[arm]):
            x = x_pipe0 + j * (bw + gap)
            ax.add_patch(FancyBboxPatch((x, y_box - 0.090), bw, 0.180,
                                        boxstyle="round,pad=0.005,rounding_size=0.030",
                                        linewidth=0.7, edgecolor=S.ARMC[arm],
                                        facecolor=S.ARMC[arm] + "22"))
            ax.text(x + bw / 2, y_box, r, ha="center", va="center",
                    fontsize=S.FS_ANNOT, color=S.INK)
            if j < 2:
                xa = x + bw
                ax.annotate("", xy=(xa + gap - 0.012, y_box),
                            xytext=(xa + 0.012, y_box),
                            arrowprops=dict(arrowstyle="-|>", lw=0.8,
                                            color=S.INK2, shrinkA=0, shrinkB=0,
                                            mutation_scale=4))
        if arm == "C":
            xb = x_pipe0 + bw + gap / 2
            ax.plot([xb, xb], [y_box - 0.115, y_box + 0.115], lw=1.1,
                    color=S.ARMC["C"], linestyle=(0, (1.2, 1.0)))
            xb2 = x_pipe0 + 2 * (bw + gap) - gap / 2
            ax.plot([xb2, xb2], [y_box - 0.115, y_box + 0.115], lw=1.1,
                    color=S.ARMC["C"], linestyle=(0, (1.2, 1.0)))
        ax.text(x_lab, y_sub, MANIP[arm], ha="left", va="center",
                fontsize=S.FS_ANNOT, color=S.INK3)
        t = collapse_text(arm)
        ax.text(x_meas, y_box, t, ha="right", va="center",
                fontsize=S.FS_LABEL if t != "n/a" else S.FS_ANNOT,
                color=S.INK if t != "n/a" else S.INK3)

    ax.text(x_lab, 0.045,
            f"Same three-agent loop, routing and budget in all three "
            f"({BUD['max_outer_rounds']}×{BUD['inner_rounds']}={MAXCYC} cycles).\n"
            "Topology is design, verified in prompts.py / schemas.py.\n"
            "The collapse column is measured (mechanical, no judge), as the\n"
            "range over the three actors. “n/a”: the enforced schema has no\n"
            "answer field, so the measure cannot fire — a 0 there would not\n"
            "be a finding. Dotted rules mark the enforced typed interface.",
            ha="left", va="bottom", fontsize=S.FS_ANNOT, color=S.INK3,
            linespacing=1.32)
    return S.save(fig, "figS1_conditions", S.COLWIDTH_IN)


if __name__ == "__main__":
    print("Figure S1 -- " + S.provenance_line())
    for arm in ("A", "B", "C"):
        r = collapse_range(arm)
        note = "" if arm in MEASURABLE else "   (0 by construction: no answer field)"
        print(f"  {S.ARM_LONG[arm]:<22} per-actor collapse "
              f"{r[0]:.4f}-{r[1]:.4f} over {r[2]} actors -> "
              f"rendered {collapse_text(arm)!r}{note}")
    build()
