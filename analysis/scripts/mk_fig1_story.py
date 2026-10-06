# -*- coding: utf-8 -*-
"""FIGURE 1 -- the whole story in three panels.

THE SENTENCE THIS FIGURE MUST CARRY:
  Roles do not help a team produce its FIRST answer.  They help it turn an
  external "your answer is wrong" signal into an actual REVISION rather than a
  RESUBMISSION of the same candidate.

  Panel A  first-pass solving        -- roles removed, solving intact
  Panel B  recovery after feedback   -- the difference appears after failure
  Panel C  how the retry budget is spent (gemma-4) -- revision vs resubmission

TERMINOLOGY (paper/TERMINOLOGY.md, binding): the internal letters A/B/C are
DICT KEYS only.  Every rendered string is "role-structured" / "role-free" /
"structurally enforced".  mk_figstyle.save() refuses to write a file whose
rendered text contains an arm code, and that gate was proved to fire by
planting a violating label and confirming no file was written.

TWO POPULATIONS, NEVER CONFLATED.  This is defect class 3 in
FINAL_NUMBER_AUDIT.md and it is how a wrong pair of numbers enters a paper:
  * the BARS are MARGINAL rates -- each condition over its own
    first-pass-wrong set (n_fpw differs per condition).
  * the p-values are PAIRED -- computed only on problems first-pass-wrong
    under BOTH conditions (paired_recovery[*].n, a different, smaller set).
Both are stated on the figure, with their own n, so neither reads as the other
(since 2026-10-04 as a two-line note inside panel B, which is where the marks
are; the earlier five-line footnote under panel C repeated the caption).

HONESTY CONSTRAINT ON PANEL B.  Only gemma-4's role contrast survives pairing
(p=2e-08).  gpt-oss (p=0.208) and Llama-3.3 (p=0.375) do NOT.  The panel marks
resolvability per actor FROM THE DATA, so a reader cannot take three
descending bar pairs as three findings.  Membership is computed, never typed.

LAYOUT IS MEASURED, NOT GUESSED.  Axes rectangles are computed in inches and
converted, because the first build placed panel C's row labels in DATA
coordinates (they were clipped) and wrote a footnote line 3.356in wide onto a
3.337in column.  Both were invisible to the font-size and width asserts and
were caught only by rendering the figure and looking at it.

Every value is read from analysis/out/FIGDATA.json via mk_figstyle.figdata().
No numeric literal in this file is a result.  The only literals are geometry,
the proportion bounds 0 and 1, and ALPHA.

  v1  Panel C as a stacked retry budget      fig1_v1_story      (1 column)
  v2  Panel C as a two-track feedback flow   fig1_v2_story      (1 column)

Run:  python3 analysis/scripts/mk_fig1_story.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle

import mk_figstyle as S

S.apply_rc()
D = S.figdata()
ACTORS = D["actors"]
ALPHA = 0.05                 # conventional threshold, not a measurement
PR = D["paired_recovery"]
MAXCYC = D["max_cycles"]     # from the frozen budget record, not typed
FOCUS = "gemma-4-31B-it"     # the actor whose role contrast survives pairing

# ---- figure geometry, in inches, so every band is checked against the column
FIG_H   = 3.88              # was 4.40 with a 5-line footnote that duplicated the caption
L_AB    = 0.700              # left margin for panels A/B (two-line y label)
L_C     = 1.010              # left margin for panel C (row labels are text)
R_EDGE  = 3.270              # right edge of every plot box
H_A, H_B, H_C = 0.72, 0.80, 0.52


def _rect(left_in, bottom_in, right_in, height_in):
    return [left_in / S.COLWIDTH_IN, bottom_in / FIG_H,
            (right_in - left_in) / S.COLWIDTH_IN, height_in / FIG_H]


def paired_resolvable(a):
    """Is this actor's role-structured vs role-free recovery contrast
    resolvable at ALPHA when paired?  Read from the paired table so the
    annotation tracks the claim instead of restating a frozen opinion."""
    return f"{a}|AB" in PR and PR[f"{a}|AB"]["p"] < ALPHA


RESOLVED = [a for a in ACTORS if paired_resolvable(a)]


def err(cells, key):
    m = np.array([c[key] for c in cells], float)
    lo = np.array([c[key + "_lo"] for c in cells], float)
    hi = np.array([c[key + "_hi"] for c in cells], float)
    return m, np.vstack([m - lo, hi - m])


def pfmt(p):
    return f"p={p:.0e}" if p < 1e-3 else f"p={p:.2f}"


# ---------------------------------------------------------------- panel A
def panel_A(ax, arms=("A", "B")):
    """First-pass solving.  Message: removing roles leaves it intact.

    Compact by instruction, so this is the only panel without per-bar value
    labels -- the point is that the pairs COINCIDE, which is a shape, not a
    set of numbers.  gpt-oss, the one pair that does not coincide, is not
    hidden: the axis is the full 0-1 proportion range and its bars differ
    visibly."""
    x = np.arange(len(ACTORS), dtype=float)
    w = 0.30
    for k, arm in enumerate(arms):
        cells = [S.cell(a, arm) for a in ACTORS]
        m, e = err(cells, "firstpass")
        ax.bar(x + (k - 0.5) * w, m, w * 0.86, color=S.ARMC[arm], zorder=3,
               label=S.ARM_LONG[arm])
        ax.errorbar(x + (k - 0.5) * w, m, yerr=e, fmt="none", ecolor=S.INK,
                    elinewidth=0.7, capsize=1.2, capthick=0.7, zorder=4)
    S.clean(ax)
    ax.set_ylim(0, 1.0)                      # never truncated
    ax.set_yticks(np.arange(0, 1.01, 0.5))
    ax.set_xlim(-0.56, len(ACTORS) - 0.44)
    ax.set_xticks(x)
    ax.set_xticklabels([S.ACTOR_SHORT[a] for a in ACTORS])
    ax.set_ylabel("first-pass\naccuracy", labelpad=1.5)
    ax.set_title("A   Roles removed: first-pass solving intact",
                 fontsize=S.FS_TITLE, pad=2.5, loc="left")


# ---------------------------------------------------------------- panel B
def panel_B(ax, arms=("A", "B", "C")):
    """Recovery after a wrong-answer signal.  Message: the difference appears
    after failure.  Resolvability is marked per actor from the paired table."""
    x = np.arange(len(ACTORS), dtype=float)
    w = 0.26
    tops = {}
    for k, arm in enumerate(arms):
        cells = [S.cell(a, arm) for a in ACTORS]
        m, e = err(cells, "recovery")
        ax.bar(x + (k - 1) * w, m, w * 0.86, color=S.ARMC[arm], zorder=3,
               hatch=S.ARMHATCH[arm], edgecolor=S.SURFACE, linewidth=0.0,
               label=S.ARM_LONG[arm])
        ax.errorbar(x + (k - 1) * w, m, yerr=e, fmt="none", ecolor=S.INK,
                    elinewidth=0.7, capsize=1.2, capthick=0.7, zorder=4)
        tops[k] = m + e[1]
    # Bracket the ROLE contrast (first two bars) and state the paired verdict.
    for i, a in enumerate(ACTORS):
        top = max(tops[0][i], tops[1][i])
        xl, xr = x[i] - w, x[i]
        yb = top + 0.05
        ax.plot([xl, xl, xr, xr], [yb, yb + 0.024, yb + 0.024, yb],
                lw=0.6, color=S.INK2, zorder=5)
        res = paired_resolvable(a)
        ax.text((xl + xr) / 2, yb + 0.036, pfmt(PR[f"{a}|AB"]["p"]) if res else "n.s.",
                ha="center", va="bottom", fontsize=S.FS_ANNOT,
                color=S.INK if res else S.INK3, zorder=5)
    # Which population each mark draws, stated ON the panel that draws it.
    # The bars and brackets peak below 0.6, so the band above is empty; the
    # five-line footnote this replaces repeated the caption word for word.
    nf = "/".join(str(S.cell(a, "A")["n_fpw"]) for a in ACTORS)
    pn = PR[f"{FOCUS}|AB"]["n"]
    ax.text(0.012, 0.975,
            f"bars: marginal, role-structured n={nf}\n"
            f"brackets: paired p, gemma-4 n={pn}",
            transform=ax.transAxes, ha="left", va="top",
            fontsize=S.FS_ANNOT, color=S.INK3, linespacing=1.3, zorder=5)
    S.clean(ax)
    ax.set_ylim(0, 1.0)
    ax.set_yticks(np.arange(0, 1.01, 0.5))
    ax.set_xlim(-0.56, len(ACTORS) - 0.44)
    ax.set_xticks(x)
    ax.set_xticklabels([S.ACTOR_SHORT[a] for a in ACTORS])
    ax.set_ylabel("recovery after\n“answer is wrong”", labelpad=1.5)
    ax.set_title("B   The difference appears after failure",
                 fontsize=S.FS_TITLE, pad=2.5, loc="left")


# ---------------------------------------------------------------- panel C, v1
def panel_C_budget(ax):
    """Stacked retry budget.  Both teams hold the SAME budget, so the bars are
    nearly the same length and the SPLIT is the whole finding.

    Segments are direct-labelled rather than carrying a legend box: a legend
    placed inside this panel overlapped the lower bar, and 0.03 cycles cannot
    hold a label inside the segment at any size."""
    arms = ("A", "B")
    ys = np.arange(len(arms), dtype=float)[::-1]
    gap = 0.045                                   # 2px surface gap at this width
    for yi, arm in zip(ys, arms):
        d = S.cell(FOCUS, arm)
        sub, rev = d["submissions"], d["revising"]
        ax.barh(yi, sub, 0.42, color=S.ARMC[arm], zorder=3)
        ax.barh(yi, rev, 0.42, left=sub + gap, color=S.ARMC[arm], alpha=0.32,
                zorder=3)
        ax.text(sub / 2, yi, f"{sub:.2f}", ha="center", va="center",
                fontsize=S.FS_ANNOT, color=S.SURFACE, zorder=5)
        if rev > 0.9:
            ax.text(sub + gap + rev / 2, yi, f"{rev:.2f}", ha="center",
                    va="center", fontsize=S.FS_ANNOT, color=S.INK, zorder=5)
        else:
            # 0.03 cycles is far too thin to hold a label in place.  To the
            # RIGHT it leaves the axes; BELOW it collides with the x tick
            # labels; ABOVE it landed on the role-structured row and read as
            # that row's label (all three seen in rendered output).  So the
            # label sits INSIDE this row's own long bar, at its right end,
            # with a leader to the sliver -- the row it belongs to is then
            # the row it is printed on.
            ax.annotate(f"{rev:.2f} revising", xy=(sub + gap + rev / 2, yi),
                        xytext=(sub - 0.12, yi), textcoords="data",
                        ha="right", va="center", fontsize=S.FS_ANNOT,
                        color=S.SURFACE, zorder=6,
                        arrowprops=dict(arrowstyle="-", lw=0.6, color=S.SURFACE,
                                        shrinkA=0.5, shrinkB=0.5))
        # row label in AXES coords: in data coords it was clipped by the margin
        ax.text(-0.025, yi, S.ARM_LONG[arm], transform=ax.get_yaxis_transform(),
                ha="right", va="center", fontsize=S.FS_ANNOT, color=S.INK)
    ax.axvline(MAXCYC, color=S.INK2, lw=0.7, zorder=2)
    ax.text(MAXCYC - 0.07, ys[0] + 0.33, f"budget {MAXCYC}", ha="right",
            va="bottom", fontsize=S.FS_ANNOT, color=S.INK2)
    # direct segment labels, placed over the long bar where both fit
    dA = S.cell(FOCUS, "A")
    ax.annotate("submitting", xy=(dA["submissions"] / 2, ys[0] + 0.21),
                xytext=(0, 2.0), textcoords="offset points", ha="center",
                va="bottom", fontsize=S.FS_ANNOT, color=S.INK3)
    ax.annotate("revising", xy=(dA["submissions"] + gap + dA["revising"] / 2,
                                ys[0] + 0.21),
                xytext=(0, 2.0), textcoords="offset points", ha="center",
                va="bottom", fontsize=S.FS_ANNOT, color=S.INK3)
    ax.set_xlim(0, MAXCYC + 0.08)
    ax.set_ylim(-0.52, len(arms) - 0.14)
    ax.set_yticks([])
    S.clean(ax, grid_axis="x")
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("deliberation cycles, first-pass-wrong only", labelpad=1.5)


# ---------------------------------------------------------------- panel C, v2
def panel_C_flow(ax):
    """Two-track flow: what the feedback TURNS INTO.  One wrong-answer signal
    arrives and splits into a revision track and a resubmission track whose
    THICKNESS is proportional to cycles spent.

    Geometry is in axes coordinates with the right edge reserved for the two
    value labels; a first version let them run past the column edge.  A
    near-zero track is drawn at a hairline floor and labelled with its real
    value -- it is never rounded up to a visible thickness."""
    arms = ("A", "B")
    rows = {"A": 0.70, "B": 0.26}
    x_lab, x_a0, x_a1, x_l0, x_l1 = 0.00, 0.215, 0.285, 0.300, 0.560
    for arm in arms:
        d = S.cell(FOCUS, arm)
        sub, rev = d["submissions"], d["revising"]
        y = rows[arm]
        ax.text(x_lab, y, S.ARM_LONG[arm], ha="left", va="center",
                fontsize=S.FS_ANNOT, color=S.INK)
        ax.annotate("", xy=(x_a1, y), xytext=(x_a0, y),
                    arrowprops=dict(arrowstyle="-|>", lw=0.9, color=S.INK2,
                                    shrinkA=0, shrinkB=0, mutation_scale=5))
        tr = 0.150 * (rev / MAXCYC)
        ts = 0.150 * (sub / MAXCYC)
        ax.add_patch(Rectangle((x_l0, y + 0.030), x_l1 - x_l0, max(tr, 0.006),
                               color=S.ARMC[arm], alpha=0.32, zorder=3))
        ax.add_patch(Rectangle((x_l0, y - 0.030 - max(ts, 0.006)),
                               x_l1 - x_l0, max(ts, 0.006),
                               color=S.ARMC[arm], zorder=3))
        ax.text(x_l1 + 0.018, y + 0.030 + max(tr, 0.006) / 2,
                f"{rev:.2f} revising", ha="left", va="center",
                fontsize=S.FS_ANNOT, color=S.INK)
        ax.text(x_l1 + 0.018, y - 0.030 - max(ts, 0.006) / 2,
                f"{sub:.2f} submitting", ha="left", va="center",
                fontsize=S.FS_ANNOT, color=S.INK)
        ax.text(x_a0 - 0.008, y + 0.055, f"{sub + rev:.2f} of {MAXCYC}",
                ha="right", va="bottom", fontsize=S.FS_ANNOT, color=S.INK3)
    ax.text(x_a0, 0.985, "“your answer is wrong” →", ha="left",
            va="top", fontsize=S.FS_ANNOT, color=S.INK3)
    ax.set_xlim(0, 1.0)
    ax.set_ylim(0.0, 1.0)
    ax.axis("off")


# ---------------------------------------------------------------- assembly
def build(panel_c, stem):
    fig = plt.figure(figsize=(S.COLWIDTH_IN, FIG_H))

    yA = FIG_H - 0.34 - H_A
    axA = fig.add_axes(_rect(L_AB, yA, R_EDGE, H_A)); panel_A(axA)
    yB = yA - 0.40 - 0.16 - H_B
    axB = fig.add_axes(_rect(L_AB, yB, R_EDGE, H_B)); panel_B(axB)
    yC = yB - 0.44 - 0.16 - H_C
    lC = L_C if panel_c is panel_C_budget else 0.075
    axC = fig.add_axes(_rect(lC, yC, R_EDGE, H_C)); panel_c(axC)
    # Panel C's title is set as FIGURE text at the left margin: as an axes
    # title it started at the panel's left edge (1.010in) and ran past the
    # 3.337in column.  Measured, not guessed.
    fig.text(0.075 / S.COLWIDTH_IN, (yC + H_C + 0.175) / FIG_H,
             "C   Same retry budget, different use (gemma-4-31B)",
             fontsize=S.FS_TITLE, color=S.INK, ha="left", va="bottom")

    # Panel A draws two conditions and panel B three; a shared legend that
    # lists three above a two-bar panel was read as a missing bar, so the
    # third entry names the panel it belongs to.
    h = [Patch(facecolor=S.ARMC[a], hatch=S.ARMHATCH[a], edgecolor=S.SURFACE,
               label=S.ARM_LONG[a] + (" (panel B)" if a == "C" else ""))
         for a in ("A", "B", "C")]
    fig.legend(handles=h, ncol=3, loc="upper center", bbox_to_anchor=(0.52, 1.003),
               fontsize=S.FS_ANNOT, handlelength=0.9, columnspacing=0.6,
               handletextpad=0.3)

    return S.save(fig, stem, S.COLWIDTH_IN)


if __name__ == "__main__":
    print("Figure 1 -- " + S.provenance_line())
    print(f"  paired-resolvable role contrasts (computed, alpha={ALPHA}): {RESOLVED}")
    for a in ACTORS:
        print(f"    {a:<24} marginal {S.cell(a,'A')['recovery']:.3f} -> "
              f"{S.cell(a,'B')['recovery']:.3f}   paired p={PR[f'{a}|AB']['p']:.3g} "
              f"(n={PR[f'{a}|AB']['n']})")
    d, e = S.cell(FOCUS, "A"), S.cell(FOCUS, "B")
    print(f"  budget split {FOCUS}: structured {d['cycles']:.2f}="
          f"{d['submissions']:.2f}+{d['revising']:.2f}   "
          f"free {e['cycles']:.2f}={e['submissions']:.2f}+{e['revising']:.2f}")
    build(panel_C_budget, "fig1_v1_story")
    build(panel_C_flow,   "fig1_v2_story")
