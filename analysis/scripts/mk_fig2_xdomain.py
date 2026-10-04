# -*- coding: utf-8 -*-
"""FIGURE 2 -- cross-domain replication, gemma-4 only.

  columns : Omni-MATH | SciBench
  rows    : first-pass (MARGINAL) | recovery (PAIRED)
  message : nearly the same, then a large drop -- twice.

UNBLOCKED 2026-10-01.  [T28b] of FINAL_TABLES.py now exports SciBench with the
POPULATION NAMED IN EVERY KEY, so a figure cannot silently draw the flattering
one.  This script was previously a failing data contract for exactly that
reason; it now reads the keys and nothing else.

WHICH POPULATION EACH ROW DRAWS -- stated here, and on the figure itself:
  * first-pass row : MARGINAL (every judged trajectory in the cell)
  * recovery row   : PAIRED   (problems first-pass-wrong under BOTH conditions)
This split is the coordinator's instruction and matches what R4 reports: the
paired set is the one carrying the p-value.  FIGDATA["scibench_note"] states
the same rule and is PRINTED BY THIS SCRIPT so the requirement travels with
the artifact.

A CROSS-FIGURE HAZARD, HANDLED EXPLICITLY.  Figure 1 panel B draws gemma-4's
Omni-MATH recovery as MARGINAL (0.222 -> 0.051).  This figure draws the same
actor and domain as PAIRED (0.160 -> 0.017).  Both are correct for their own
population and they are DIFFERENT NUMBERS for the same cell.  A reader who
compares the two figures without being told will think one is wrong, so each
row here is labelled with its population and its own n.

DO NOT IMPLY THE TWO EFFECT SIZES ARE IDENTICAL.  The two-proportion test on
the discordant rates (z=1.06, p=0.289) FAILS TO DISTINGUISH them; that is not
evidence that they match.  So this figure draws each domain's own effect and
its own discordant split, and never a shared band, a pooled marker, or an
equality claim.  Omni-MATH's delta is -0.143 and SciBench's is -0.192 -- shown
separately, as two replications of a direction, not one number measured twice.

gemma-4 ONLY, per notes/XDOMAIN-INTEGRATION-DECISION.md.  gpt-oss's SciBench
cell is underpowered (paired n=96; power 0.06 by exact McNemar, 0.12 by
two-proportion z -- the 0.42 that circulated earlier is superseded, and the
manuscript says "0.06-0.45 by test").  Putting it beside gemma's invites
exactly the "one of two actors failed" reading the project has refused.

UNCERTAINTY.  SciBench carries no bootstrap CI fields and the Omni paired
contrast has none either, so this figure does NOT draw error bars: an interval
on one column and not the other would read as "SciBench is exact".  Paired
evidence is instead the discordant split (A-only vs B-only) and the exact
McNemar p -- both present for both domains, both seed-free, and both read
directly from FIGDATA rather than recomputed here.

  v1  grouped bars, 2x2            fig2_v1_xdomain   (1 column)
  v2  paired slopes + discordant   fig2_v2_xdomain   (1 column)

Run:  python3 analysis/scripts/mk_fig2_xdomain.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

import mk_figstyle as S

S.apply_rc()
D = S.figdata()
FOCUS = "gemma-4-31B-it"
ARMS = ("A", "B")

REQUIRED = ("scibench", "scibench_note")
_missing = [k for k in REQUIRED if k not in D]
if _missing:
    raise SystemExit(
        f"BLOCKED: FIGDATA.json lacks {_missing}. Re-run FINAL_TABLES.py "
        f"[T28b]. This figure never computes SciBench itself: choosing "
        f"between the paired (n=99) and marginal (n=118) populations is a "
        f"denominator decision, not a plotting one.")

SB = D["scibench"][FOCUS]
PR = D["paired_recovery"][f"{FOCUS}|AB"]

# ---- the four cells, every value READ from FIGDATA ------------------------
# first pass: MARGINAL, both domains
FP = {
    "omni": (S.cell(FOCUS, "A")["firstpass"], S.cell(FOCUS, "B")["firstpass"],
             S.cell(FOCUS, "A")["n_judged"], S.cell(FOCUS, "B")["n_judged"]),
    "sci":  (SB["firstpass_marginal_A"], SB["firstpass_marginal_B"],
             SB["n_firstpass_A"], SB["n_firstpass_B"]),
}
# recovery: PAIRED, both domains.  Omni's paired rates are derived from the
# paired transition table the same way [T28b] derives SciBench's, so the two
# columns are the same estimator -- not one paired and one marginal.
REC = {
    "omni": ((PR["both_rec"] + PR["x_only"]) / PR["n"],
             (PR["both_rec"] + PR["y_only"]) / PR["n"],
             PR["n"], PR["x_only"], PR["y_only"], PR["p"]),
    "sci":  (SB["recovery_paired_A"], SB["recovery_paired_B"],
             SB["n_paired"], SB["discordant_A_only"], SB["discordant_B_only"],
             SB["mcnemar_p"]),
}
DOMAIN = [("omni", "Omni-MATH"), ("sci", "SciBench")]


def pfmt(p):
    return f"p={p:.0e}" if p < 1e-3 else f"p={p:.2f}"


# =====================================================================
def v1():
    """Grouped bars, 2x2.  Rows share a y scale within the row so the two
    domains are directly comparable; the two ROWS never share a scale,
    because a first-pass rate and a recovery rate are different quantities."""
    # 2.95in tall since 2026-10-04 (was 3.75): the in-figure subtitle and
    # four-line footnote repeated the caption and the row labels, and the
    # footnote sat directly under "37 vs 3 of n=237" so the two read as one
    # block.  Margins re-measured for the shorter figure.
    fig = plt.figure(figsize=(S.COLWIDTH_IN, 2.95))
    gs = fig.add_gridspec(2, 2, left=0.185, right=0.980, top=0.835,
                          bottom=0.235, hspace=1.10, wspace=0.14)
    x = np.arange(2, dtype=float)
    for ci, (dk, dname) in enumerate(DOMAIN):
        # --- row 1: first pass, MARGINAL
        ax = fig.add_subplot(gs[0, ci])
        a, b, na, nb = FP[dk]
        ax.bar(x, [a, b], 0.52, color=[S.ARMC["A"], S.ARMC["B"]], zorder=3)
        for xi, v in zip(x, (a, b)):
            ax.text(xi, v + 0.030, f"{v:.3f}", ha="center", va="bottom",
                    fontsize=S.FS_ANNOT, color=S.INK)
        ax.set_ylim(0, 1.0); ax.set_yticks(np.arange(0, 1.01, 0.5))
        ax.set_xlim(-0.62, 1.62); ax.set_xticks(x)
        ax.set_xticklabels([S.ARM_SHORT[k] for k in ARMS], fontsize=S.FS_ANNOT)
        S.clean(ax)
        ax.set_title(dname, fontsize=S.FS_TITLE, pad=3.0)
        if ci == 0:
            ax.set_ylabel("first-pass\n(marginal)", labelpad=1.5)
        ax.text(0.5, -0.62, f"Δ {b-a:+.4f}   n={na}", transform=ax.transAxes,
                ha="center", va="top", fontsize=S.FS_ANNOT, color=S.INK3)

        # --- row 2: recovery, PAIRED
        ax = fig.add_subplot(gs[1, ci])
        a, b, n, ao, bo, p = REC[dk]
        ax.bar(x, [a, b], 0.52, color=[S.ARMC["A"], S.ARMC["B"]], zorder=3)
        for xi, v in zip(x, (a, b)):
            ax.text(xi, v + 0.012, f"{v:.3f}", ha="center", va="bottom",
                    fontsize=S.FS_ANNOT, color=S.INK)
        ax.set_ylim(0, 0.42); ax.set_yticks([0, 0.2, 0.4])
        ax.set_xlim(-0.62, 1.62); ax.set_xticks(x)
        ax.set_xticklabels([S.ARM_SHORT[k] for k in ARMS], fontsize=S.FS_ANNOT)
        S.clean(ax)
        if ci == 0:
            ax.set_ylabel("recovery\n(paired)", labelpad=1.5)
        ax.text(0.5, -0.62, f"Δ {b-a:+.3f}   {pfmt(p)}\n{ao} vs {bo} of n={n}",
                transform=ax.transAxes, ha="center", va="top",
                fontsize=S.FS_ANNOT, color=S.INK3, linespacing=1.25)

    fig.text(0.006, 0.995,
             "Same first pass, then a large drop — twice",
             fontsize=S.FS_TITLE, ha="left", va="top", color=S.INK)
    # The population of each row is named in its y label ("marginal" /
    # "paired") and the caption; the discordant-count notation is defined in
    # the caption.  Neither is repeated here.
    h = [Patch(facecolor=S.ARMC[k], label=S.ARM_LONG[k]) for k in ARMS]
    fig.legend(handles=h, ncol=2, loc="upper left",
               bbox_to_anchor=(0.004, 0.952), fontsize=S.FS_ANNOT,
               handlelength=0.9, columnspacing=0.8, handletextpad=0.35)
    return S.save(fig, "fig2_v1_xdomain", S.COLWIDTH_IN)


# =====================================================================
def v2():
    """Paired slopes.  One line per domain per measure: the READER'S JOB is
    direction and steepness, and a slope states 'this moved' more directly
    than two bars whose difference must be estimated by eye.

    The recovery row additionally plots the discordant split as the paired
    evidence, because that -- not an interval -- is what the exact test uses."""
    # 2.95in tall since 2026-10-04 (was 3.75): the in-figure subtitle and
    # four-line footnote repeated the caption and the row labels, and the
    # footnote sat directly under "37 vs 3 of n=237" so the two read as one
    # block.  Margins re-measured for the shorter figure.
    fig = plt.figure(figsize=(S.COLWIDTH_IN, 2.95))
    gs = fig.add_gridspec(2, 2, left=0.185, right=0.980, top=0.835,
                          bottom=0.235, hspace=1.10, wspace=0.14)
    xs = np.array([0.0, 1.0])
    for ci, (dk, dname) in enumerate(DOMAIN):
        ax = fig.add_subplot(gs[0, ci])
        a, b, na, nb = FP[dk]
        ax.plot(xs, [a, b], "-", color=S.INK3, lw=1.0, zorder=2)
        for xi, v, k in zip(xs, (a, b), ARMS):
            ax.plot([xi], [v], "o", ms=4.0, mfc=S.ARMC[k], mec=S.SURFACE,
                    mew=0.9, zorder=4)
        # First-pass points sit at ~0.8 on a 0-1 axis, so a label ABOVE them
        # ran into the panel title (seen in rendered output); the band below
        # the points is empty, so the labels hang under them.
        ax.annotate(f"{a:.3f}", (xs[0], a), textcoords="offset points",
                    xytext=(-2.0, -5.0), ha="right", va="top",
                    fontsize=S.FS_ANNOT, color=S.INK)
        ax.annotate(f"{b:.3f}", (xs[1], b), textcoords="offset points",
                    xytext=(2.0, -5.0), ha="left", va="top",
                    fontsize=S.FS_ANNOT, color=S.INK)
        ax.set_ylim(0, 1.0); ax.set_yticks(np.arange(0, 1.01, 0.5))
        if ci == 1:
            ax.set_yticklabels([])        # same scale as the left column
        ax.set_xlim(-0.85, 1.85); ax.set_xticks(xs)
        ax.set_xticklabels([S.ARM_SHORT[k] for k in ARMS], fontsize=S.FS_ANNOT)
        S.clean(ax, grid_axis="y")
        ax.set_title(dname, fontsize=S.FS_TITLE, pad=3.0)
        if ci == 0:
            ax.set_ylabel("first-pass\n(marginal)", labelpad=1.5)
        ax.text(0.5, -0.62, f"Δ {b-a:+.4f}   n={na}", transform=ax.transAxes,
                ha="center", va="top", fontsize=S.FS_ANNOT, color=S.INK3)

        ax = fig.add_subplot(gs[1, ci])
        a, b, n, ao, bo, p = REC[dk]
        ax.plot(xs, [a, b], "-", color=S.INK3, lw=1.0, zorder=2)
        for xi, v, k in zip(xs, (a, b), ARMS):
            ax.plot([xi], [v], "o", ms=4.0, mfc=S.ARMC[k], mec=S.SURFACE,
                    mew=0.9, zorder=4)
        ax.annotate(f"{a:.3f}", (xs[0], a), textcoords="offset points",
                    xytext=(-2.0, 5.0), ha="right", va="bottom",
                    fontsize=S.FS_ANNOT, color=S.INK)
        ax.annotate(f"{b:.3f}", (xs[1], b), textcoords="offset points",
                    xytext=(2.0, 5.0), ha="left", va="bottom",
                    fontsize=S.FS_ANNOT, color=S.INK)
        ax.set_ylim(0, 0.42); ax.set_yticks([0, 0.2, 0.4])
        if ci == 1:
            ax.set_yticklabels([])
        ax.set_xlim(-0.85, 1.85); ax.set_xticks(xs)
        ax.set_xticklabels([S.ARM_SHORT[k] for k in ARMS], fontsize=S.FS_ANNOT)
        S.clean(ax, grid_axis="y")
        if ci == 0:
            ax.set_ylabel("recovery\n(paired)", labelpad=1.5)
        ax.text(0.5, -0.62, f"Δ {b-a:+.3f}   {pfmt(p)}\n{ao} vs {bo} of n={n}",
                transform=ax.transAxes, ha="center", va="top",
                fontsize=S.FS_ANNOT, color=S.INK3, linespacing=1.25)

    fig.text(0.006, 0.995,
             "Same first pass, then a large drop — twice",
             fontsize=S.FS_TITLE, ha="left", va="top", color=S.INK)
    # The population of each row is named in its y label ("marginal" /
    # "paired") and the caption; the discordant-count notation is defined in
    # the caption.  Neither is repeated here.
    h = [Patch(facecolor=S.ARMC[k], label=S.ARM_LONG[k]) for k in ARMS]
    fig.legend(handles=h, ncol=2, loc="upper left",
               bbox_to_anchor=(0.004, 0.952), fontsize=S.FS_ANNOT,
               handlelength=0.9, columnspacing=0.8, handletextpad=0.35)
    return S.save(fig, "fig2_v2_xdomain", S.COLWIDTH_IN)


if __name__ == "__main__":
    print("Figure 2 (cross-domain, gemma-4) -- " + S.provenance_line())
    print("  FIGDATA scibench_note: " + D["scibench_note"])
    if "scibench_AB.jsonl" not in D["provenance"]["files"]:
        print("  NOTE: provenance['files'] does not list the SciBench "
              "snapshot, so provenance_line() above names Omni-MATH only.\n"
              "        The figure therefore prints the SciBench sha256 from "
              "its own caption text, and the gap is reported to the "
              "coordinator rather than patched here.")
    for dk, dname in DOMAIN:
        a, b, na, nb = FP[dk]
        ra, rb, n, ao, bo, p = REC[dk]
        print(f"  {dname:<10} fp(marginal) {a:.4f}->{b:.4f} (Δ{b-a:+.4f}, n={na})"
              f"   rec(paired) {ra:.4f}->{rb:.4f} (Δ{rb-ra:+.4f}, "
              f"{ao} vs {bo}, n={n}, p={p:.2e})")
    print("  NOT drawn: gpt-oss (SciBench paired n=96, underpowered).")
    v1(); v2()
