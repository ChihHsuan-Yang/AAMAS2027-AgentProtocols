# -*- coding: utf-8 -*-
"""FIGURE S1 (§19 prototype) -- the outcome decomposition per arm and actor.

    first-pass success + recovered + unrecovered + ungraded = 1

This is a PROBABILITY DECOMPOSITION, not a causal equation.  The four bands are
a partition of the trajectories in a cell, and they sum to n by construction --
the identity is arithmetic, and it says nothing about what caused what.  The
figure says so in the subtitle, not only in the caption.

The fifth logical category, first-pass-correct-then-lost, is verified to be
EMPTY in every cell by an assert in FINAL_TABLES.py [T28] (the loop halts on a
correct first verdict), so no band is drawn for it.  If it ever becomes
non-zero, that assert fires and this figure must gain a band rather than
silently drop the rows.

`unjudged` (never received a first evaluator verdict) is drawn because it is
part of arm C's attrition, which pre-registered scoring counts as incorrect
(A7) -- hiding it would make arm C look better than the primary analysis says.
Note this is NOT the same as `ungraded_no_final_grade`: a trajectory can be
judged once and then die in regeneration, and those rows are already inside
`recovered`/`unrecovered` because they belong to the recovery denominator.

Every value is read from analysis/out/FIGDATA.json via mk_figstyle.figdata().

  v1  stacked bars, arms grouped within actor   fig4_v1_stacked
  v2  same partition as a 100% band per row     fig4_v2_rows

Run:  python3 analysis/scripts/mk_fig4_decomposition.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

import mk_figstyle as S

S.apply_rc()
D = S.figdata()
ACTORS = D["actors"]
ARMS = ["A", "B", "C"]

# Band order is the trajectory's story: succeeded outright, repaired, failed,
# never produced a graded answer.  Colour is ordinal here (one hue, light to
# dark, for the two "ended correct" bands vs the two "ended wrong"), and each
# band is ALSO labelled, so nothing is carried by hue alone.
BANDS = [("held",        "first pass correct",    "#0072B2", ""),
         ("recovered",   "recovered after error", "#56B4E9", ""),
         ("unrecovered", "never recovered",       "#E8E8E8", ""),
         ("unjudged",    "never judged",          "#BDBDBD", "///")]


def frac(actor, arm):
    d = S.cell(actor, arm)
    n = d["n"]
    return [d["decomp"][k] / n for k, _, _, _ in BANDS], n, d


def check_partition():
    """The identity must hold in every cell, or the figure is not a partition."""
    for a in ACTORS:
        for arm in ARMS:
            f, n, d = frac(a, arm)
            assert abs(sum(f) - 1.0) < 1e-9, (a, arm, sum(f))
            # and the top two bands must equal the PREREG final accuracy
            assert abs((f[0] + f[1]) - d["final_prereg"]) < 1e-9, (a, arm)
    return True


# =====================================================================
def v1():
    """Stacked columns, arms grouped within actor."""
    fig, ax = plt.subplots(figsize=(S.COLWIDTH_IN, 2.75),
                           gridspec_kw={"left": 0.135, "right": 0.988,
                                        "top": 0.700, "bottom": 0.250})
    xs, labels, ticks = [], [], []
    pos = 0.0
    for ai, a in enumerate(ACTORS):
        for arm in ARMS:
            xs.append((pos, a, arm)); labels.append(arm); pos += 1.0
        ticks.append((pos - len(ARMS) / 2 - 0.5 + 0.5, a))
        pos += 0.55
    for x, a, arm in xs:
        f, n, d = frac(a, arm)
        bot = 0.0
        for v, (key, lab, col, hatch) in zip(f, BANDS):
            ax.bar(x, v, 0.80, bottom=bot, color=col, hatch=hatch, zorder=3,
                   edgecolor=S.SURFACE, linewidth=0.6)
            bot += v
        # direct-label the final accuracy (= the two lower bands), the quantity
        # the decomposition is FOR.  Not every band gets a number.
        ax.text(x, d["final_prereg"] + 0.018, f"{d['final_prereg']:.2f}",
                ha="center", va="bottom", fontsize=S.FS_ANNOT, color=S.INK)
    ax.set_xticks([x for x, _, _ in xs])
    ax.set_xticklabels(labels)
    for xt, a in ticks:
        ax.text(xt, -0.135, S.ACTOR_1LINE[a], ha="center", va="top",
                transform=ax.get_xaxis_transform(), fontsize=S.FS_ANNOT, color=S.INK)
    ax.set_ylim(0, 1.0)
    ax.set_yticks(np.arange(0, 1.01, 0.25))
    ax.set_xlim(-0.75, pos - 0.80)
    S.clean(ax)
    ax.set_ylabel("share of trajectories in the cell")
    h = [Patch(facecolor=col, hatch=hh, edgecolor=S.SURFACE, label=lab)
         for _, lab, col, hh in BANDS]
    ax.legend(handles=h, ncol=2, loc="lower center", bbox_to_anchor=(0.45, 1.02),
              fontsize=S.FS_LEGEND, handlelength=1.0, columnspacing=0.9)
    fig.text(0.008, 0.990,
             "Outcome decomposition: an identity, not a causal model",
             fontsize=S.FS_TITLE, ha="left", va="top", color=S.INK)
    fig.text(0.008, 0.008,
             "first pass correct + recovered + never recovered + never judged = 1\n"
             "by construction.  Numbers above the bars are final accuracy\n"
             "under pre-registered scoring.",
             fontsize=S.FS_ANNOT, color=S.INK3, ha="left", va="bottom")
    return S.save(fig, "fig4_v1_stacked", S.COLWIDTH_IN)


# =====================================================================
def v2():
    """One 100% band per actor-arm row: easier to read the small bands."""
    rows = [(a, arm) for a in ACTORS for arm in ARMS]
    fig, ax = plt.subplots(figsize=(S.TEXTWIDTH_IN, 2.50),
                           gridspec_kw={"left": 0.145, "right": 0.930,
                                        "top": 0.790, "bottom": 0.245})
    ys = np.arange(len(rows), dtype=float)[::-1]
    for yi, (a, arm) in zip(ys, rows):
        f, n, d = frac(a, arm)
        left = 0.0
        for v, (key, lab, col, hatch) in zip(f, BANDS):
            ax.barh(yi, v, 0.62, left=left, color=col, hatch=hatch, zorder=3,
                    edgecolor=S.SURFACE, linewidth=0.6)
            # label a band only when the text fits inside it
            if v >= 0.085:
                ax.text(left + v / 2, yi, f"{v:.2f}", ha="center", va="center",
                        fontsize=S.FS_ANNOT, zorder=5,
                        color=S.SURFACE if key == "held" else S.INK)
            left += v
        ax.text(1.008, yi, f"n={n}", ha="left", va="center",
                fontsize=S.FS_ANNOT, color=S.INK3)
    ax.set_yticks(ys)
    ax.set_yticklabels([f"{S.ACTOR_1LINE[a]}  {arm}" for a, arm in rows])
    ax.set_xlim(0, 1.0)
    ax.set_xticks(np.arange(0, 1.01, 0.25))
    ax.set_ylim(-0.6, len(rows) - 0.4)
    S.clean(ax, grid_axis="x")
    ax.set_xlabel("share of trajectories in the cell", labelpad=1.5)
    h = [Patch(facecolor=col, hatch=hh, edgecolor=S.SURFACE, label=lab)
         for _, lab, col, hh in BANDS]
    ax.legend(handles=h, ncol=4, loc="lower center", bbox_to_anchor=(0.42, 1.01),
              fontsize=S.FS_LEGEND, handlelength=1.0, columnspacing=1.0)
    fig.text(0.004, 0.992,
             "Outcome decomposition per cell — a probability identity, not a causal equation",
             fontsize=S.FS_TITLE, ha="left", va="top", color=S.INK)
    fig.text(0.004, 0.008,
             "The four bands partition the cell and sum to 1 by construction; the first two "
             "together are final accuracy under pre-registered scoring.\n"
             "Bands below 0.085 are left unlabelled rather than clipped.",
             fontsize=S.FS_ANNOT, color=S.INK3, ha="left", va="bottom")
    return S.save(fig, "fig4_v2_rows", S.TEXTWIDTH_IN)


if __name__ == "__main__":
    print("Figure S1 -- " + S.provenance_line())
    print(f"  partition identity holds in every cell: {check_partition()}")
    for a in ACTORS:
        for arm in ARMS:
            f, n, d = frac(a, arm)
            print(f"  {a:24s}{arm}  n={n:<5} " +
                  "  ".join(f"{lab.split()[0]}={v:.3f}" for v, (_, lab, _, _) in zip(f, BANDS)) +
                  f"   final={d['final_prereg']:.3f}")
    v1(); v2()
