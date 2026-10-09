# -*- coding: utf-8 -*-
"""Pipeline and feedback-channel schematic (main text, Section 4).

One deliberation cycle, the submission gate, and the channel through which a
FAIL verdict and repair hint reach the agents in each condition.

DESIGN FACTS ONLY.  Nothing on this figure is measured, and no number is
drawn.  Every statement is a property of the templates and the runner, as the
manuscript states them in sections/method.tex and results.tex ("What a cycle
is"), checked against experiments/runner.py:
  * the context map gives every agent of the role-structured and enforced
    conditions the `advice` slot; the role-free template interpolates no
    advice slot;
  * role-free with feedback shows the same advice string to all three agents
    for the next cycle as a trailing "[Evaluator]" entry of the shared
    history, with the one-cycle lifetime the advice slot has;
  * in every prose condition the third agent's [Agree] is approval and the
    latest boxed answer is submitted; under enforcement the Reviewer's
    `accept` promotes the Executor's answer;
  * on approval the answer goes to the evaluator: PASS ends the trajectory,
    FAIL returns a verdict and repair hint; without approval nothing is
    submitted and the next cycle revises.

Who approves is the same mechanism in every condition (the third agent) and
is stated in the caption, so the key below the diagram lists only what
differs between conditions: where the feedback enters.

Condition colours and fills match Figure "dissociation" (mk_fig1_bf.py):
role-structured solid purple, role-free feedback withheld hollow rose,
role-free with feedback solid rose, structurally enforced hatched gold.

GEOMETRY.  The axes run in inches, so every coordinate below is a position
on the printed page.  Every arrow stops at the outer edge of the box it
meets (shrink = half the box line width plus a hairline), never inside it;
the icons are drawn in the same coordinates and never leave their box.

TERMINOLOGY: no condition codes are rendered (paper/TERMINOLOGY.md);
mk_figstyle.save() enforces it.

Run:  python3 analysis/scripts/mk_fig_pipeline.py   -> figures/fig_pipeline.*
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle

import mk_figstyle as S

S.apply_rc()
S.use_paper_font()

STEM = "fig_pipeline"
FS = 7.0                       # box and row labels (Libertinus runs small)
FS_S = S.FS_ANNOT              # annotations, 6.5pt = the class minimum

FIG_W = S.COLWIDTH_IN
FIG_H = 1.72
XT = 0.05                      # the feedback trunk, down the left margin
X0, X1 = 0.16, FIG_W - 0.06    # inner margins of the boxes and the key, inches

BOX_LW = 0.7                   # pt
EDGE_PT = BOX_LW / 2 + 0.5     # arrow clearance from a box's nominal edge, pt
EDGE_IN = EDGE_PT / 72

# --------------------------------------------------------------- band 1: cycle
BOX_W, BOX_H = 0.52, 0.40
Y_BOX = 1.19                   # box centre
STAGES = ["Planner", "Executor", "Reviewer", "Evaluator"]
GAP = (X1 - X0 - len(STAGES) * BOX_W) / (len(STAGES) - 1)
XS = [X0 + i * (BOX_W + GAP) for i in range(len(STAGES))]      # left edges
XC = [x + BOX_W / 2 for x in XS]                               # centres
Y_TOP, Y_BOT = Y_BOX + BOX_H / 2, Y_BOX - BOX_H / 2
Y_FB = Y_TOP + 0.15            # feedback line, above the boxes
Y_NO = Y_BOT - 0.13            # no-approval loop, below the boxes

# --------------------------------------------------------------- band 2: key
SW_W, SW_H = 0.10, 0.075       # swatch size
Y_HEAD = 0.64
ROW_DY = 0.135
ROWS = [  # (key, condition, where the FAIL feedback enters)
    ("A",  "role-structured",              "each agent's advice slot"),
    ("C",  "structurally enforced",        "each agent's advice slot"),
    ("Bf", "role-free with feedback",      "[Evaluator] entry after the shared history"),
    ("B",  "role-free, feedback withheld", "none: the prompt has no slot"),
]
COL = {"A": S.ARMC["A"], "B": S.ARMC["B"], "Bf": S.ARMC["B"], "C": S.ARMC["C"]}


def arrow(ax, x0, y0, x1, y1, color=S.INK2, lw=0.7, shrinkA=0.0, shrinkB=EDGE_PT):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle="-|>", lw=lw, color=color,
                                shrinkA=shrinkA, shrinkB=shrinkB, mutation_scale=5))


def swatch(ax, key, x, y):
    if key == "B":
        kw = dict(facecolor=S.SURFACE, edgecolor=COL[key], linewidth=0.8)
    elif key == "C":
        kw = dict(facecolor=COL[key], edgecolor=S.SURFACE, hatch="////", linewidth=0.0)
    else:
        kw = dict(facecolor=COL[key], edgecolor=COL[key], linewidth=0.0)
    ax.add_patch(Rectangle((x, y - SW_H / 2), SW_W, SW_H, **kw))


# ------------------------------------------------------------------ robots
# One small robot per stage, drawn in the same inch coordinates as the boxes.
# They are decoration for the eye, not data.  The three agents differ by
# colour and by one feature each (antenna bulb, visor, glasses); the
# Evaluator, also a model but the grader, is grey with a tick on its chest.
# Agent colours are deliberately outside the condition palette (purple, rose,
# gold), which stays reserved for conditions here and in Figure 2.
AGENTC = {"Planner": "#5A8BBF", "Executor": "#3E9E9A", "Reviewer": "#78A85A",
          "Evaluator": "#8A8A98"}
BOX_TINT = {"Planner": "#EEF3F9", "Executor": "#EAF5F4", "Reviewer": "#EFF5EA",
            "Evaluator": "#EEEEF2"}
FAILC = "#B9534F"              # the FAIL feedback path, a muted red
ROBOT_LW = 0.6


def robot(ax, cx, cy, s, name):
    """A robot of height about s, centred horizontally on cx; cy is the
    centre of its head."""
    c = AGENTC[name]
    W = S.SURFACE
    hw, hh = 0.78 * s, 0.54 * s                     # head
    ax.add_patch(FancyBboxPatch((cx - hw / 2, cy - hh / 2), hw, hh,
                                boxstyle="round,pad=0,rounding_size=0.016",
                                linewidth=0, facecolor=c))
    # antenna
    ax.plot([cx, cx], [cy + hh / 2, cy + hh / 2 + 0.14 * s], color=c, lw=ROBOT_LW * 1.4,
            solid_capstyle="butt")
    ax.add_patch(Circle((cx, cy + hh / 2 + 0.17 * s), 0.055 * s, linewidth=0, facecolor=c))
    # body, a lighter block with the agent's outline
    bw, bh = 0.56 * s, 0.30 * s
    ax.add_patch(FancyBboxPatch((cx - bw / 2, cy - hh / 2 - 0.06 * s - bh), bw, bh,
                                boxstyle="round,pad=0,rounding_size=0.012",
                                linewidth=ROBOT_LW, edgecolor=c, facecolor=W))
    # neck
    ax.plot([cx, cx], [cy - hh / 2 - 0.06 * s, cy - hh / 2], color=c, lw=ROBOT_LW * 1.4)
    # arms
    for sgn in (-1, 1):
        ax.plot([cx + sgn * bw / 2, cx + sgn * (bw / 2 + 0.11 * s)],
                [cy - hh / 2 - 0.12 * s, cy - hh / 2 - 0.20 * s], color=c,
                lw=ROBOT_LW * 1.4, solid_capstyle="round")
    ex, ey, er = 0.19 * s, cy + 0.06 * s, 0.075 * s  # eyes
    if name == "Executor":
        # a visor instead of two eyes
        ax.add_patch(FancyBboxPatch((cx - 0.27 * s, ey - 0.07 * s), 0.54 * s, 0.14 * s,
                                    boxstyle="round,pad=0,rounding_size=0.008",
                                    linewidth=0, facecolor=W))
    else:
        for sgn in (-1, 1):
            ax.add_patch(Circle((cx + sgn * ex, ey), er, linewidth=0, facecolor=W))
        if name == "Reviewer":
            # round glasses: rings around the eyes and a bridge
            for sgn in (-1, 1):
                ax.add_patch(Circle((cx + sgn * ex, ey), er + 0.045 * s, linewidth=ROBOT_LW,
                                    edgecolor=W, facecolor="none"))
            ax.plot([cx - ex + er + 0.045 * s, cx + ex - er - 0.045 * s], [ey, ey],
                    color=W, lw=ROBOT_LW)
    # mouth
    ax.plot([cx - 0.12 * s, cx + 0.12 * s], [cy - 0.14 * s, cy - 0.14 * s], color=W,
            lw=ROBOT_LW, solid_capstyle="round")
    if name == "Evaluator":
        # a tick on the chest: this robot grades
        by = cy - hh / 2 - 0.06 * s - bh / 2
        ax.plot([cx - 0.12 * s, cx - 0.03 * s, cx + 0.14 * s],
                [by, by - 0.09 * s, by + 0.10 * s], color=c, lw=ROBOT_LW * 1.5,
                solid_capstyle="round", solid_joinstyle="round")


def text_width(ax, s, fs):
    """Rendered width of a string, in inches (axes run in inches)."""
    t = ax.text(0, 0, s, fontsize=fs)
    fig = ax.figure
    fig.canvas.draw()
    bb = t.get_window_extent(renderer=fig.canvas.get_renderer())
    t.remove()
    return bb.width / fig.dpi


def columns(ax):
    """Column left edges from the measured cell widths, with one gutter.
    Fails rather than letting a cell run into its neighbour or the margin."""
    w = [max(text_width(ax, row[k], FS) for row in ROWS) for k in (1, 2)]
    start = X0 + SW_W + 0.04
    right = X1 - 0.01 - w[1]               # the second column ends inside X1
    gutter = right - (start + w[0])
    assert gutter >= 0.10, f"table too wide: gutter {gutter:.3f}in"
    return [start, right]


def build():
    fig = plt.figure(figsize=(FIG_W, FIG_H))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, FIG_W); ax.set_ylim(0, FIG_H); ax.axis("off")
    ax.set_aspect("equal")
    COLS = columns(ax)

    # one cycle: Planner -> Executor -> Reviewer -> (approval) -> Evaluator
    for i, (x, name) in enumerate(zip(XS, STAGES)):
        ax.add_patch(FancyBboxPatch((x, Y_BOT), BOX_W, BOX_H,
                                    boxstyle="round,pad=0,rounding_size=0.035",
                                    linewidth=BOX_LW, edgecolor=AGENTC[name],
                                    facecolor=BOX_TINT[name]))
        robot(ax, XC[i], Y_TOP - 0.135, 0.19, name)
        ax.text(XC[i], Y_BOT + 0.07, name, ha="center", va="center",
                fontsize=FS, color=S.INK)
    for i in range(2):
        arrow(ax, XS[i] + BOX_W, Y_BOX, XS[i + 1], Y_BOX, shrinkA=EDGE_PT)
    # the submission gate: Reviewer -> Evaluator only on approval
    xg0, xg1 = XS[2] + BOX_W, XS[3]
    arrow(ax, xg0, Y_BOX, xg1, Y_BOX, color=S.INK, lw=0.9, shrinkA=EDGE_PT)
    xm = (xg0 + xg1) / 2
    ax.plot([xm, xm], [Y_BOX - 0.045, Y_BOX + 0.045], color=S.ARMC["A"], lw=1.6,
            solid_capstyle="butt", zorder=4)
    # the gate labels sit between two boxes: they must clear both edges
    assert GAP >= text_width(ax, "approve", FS_S) + 0.04, "gate labels touch the boxes"
    ax.text(xm, Y_BOX + 0.07, "approve", ha="center", va="bottom",
            fontsize=FS_S, color=S.INK)
    ax.text(xm, Y_BOX - 0.07, "submit", ha="center", va="top",
            fontsize=FS_S, color=S.INK)
    ax.text(XC[3], Y_BOT - 0.045, "PASS ends\nthe trajectory",
            ha="center", va="top", fontsize=FS_S, color=S.INK2, linespacing=1.1)

    # FAIL: verdict and hint reach all three agents in the next cycle
    y_last = Y_HEAD - 0.065 - (len(ROWS) - 0.5) * ROW_DY
    ax.plot([XC[3], XC[3], XT, XT], [Y_TOP + EDGE_IN, Y_FB, Y_FB, y_last],
            color=FAILC, lw=0.7, solid_joinstyle="miter", solid_capstyle="butt")
    for i in range(3):
        arrow(ax, XC[i], Y_FB, XC[i], Y_TOP, color=FAILC)
    ax.text(XT + 0.03, Y_FB + 0.04,
            "FAIL: verdict and repair hint, returned for the next cycle",
            ha="left", va="bottom", fontsize=FS_S, color=FAILC)

    # no approval: nothing is submitted; the next cycle revises
    ax.plot([XC[2], XC[2], XC[0]], [Y_BOT - EDGE_IN, Y_NO, Y_NO], color=S.INK3, lw=0.7,
            linestyle=(0, (2.0, 1.4)), solid_joinstyle="miter")
    arrow(ax, XC[0], Y_NO, XC[0], Y_BOT, color=S.INK3)
    ax.text(XC[0] + 0.07, Y_NO - 0.035,
            "no approval: nothing submitted, the next cycle revises",
            ha="left", va="top", fontsize=FS_S, color=S.INK2)

    # where the feedback enters, per condition
    heads = ["condition", "where the FAIL feedback enters"]
    for x, h, c in zip([X0, COLS[1]], heads, (S.INK2, FAILC)):
        ax.text(x, Y_HEAD, h, ha="left", va="center", fontsize=FS_S,
                color=c, fontstyle="italic")
    ax.plot([X0, X1], [Y_HEAD - 0.065, Y_HEAD - 0.065], color=S.GRID, lw=0.6)
    texts = []
    for r, (key, cond, chan) in enumerate(ROWS):
        y = Y_HEAD - 0.065 - (r + 0.5) * ROW_DY
        # the withheld condition's stub is dotted: the feedback never arrives
        ax.plot([XT, X0 - 0.02], [y, y], color=FAILC, lw=0.7, solid_capstyle="butt",
                linestyle=(0, (1.0, 1.2)) if key == "B" else "-")
        swatch(ax, key, X0, y)
        for x, s in zip(COLS, (cond, chan)):
            texts.append((x, ax.text(x, y, s, ha="left", va="center",
                                     fontsize=FS, color=S.INK)))

    # geometry gate: no cell may run into the next column or the margin, and
    # nothing may leave the figure
    fig.canvas.draw()
    inv = ax.transData.inverted()
    limits = {COLS[0]: COLS[1], COLS[1]: X1 + 0.03}
    for x, t in texts:
        bb = t.get_window_extent(renderer=fig.canvas.get_renderer())
        right = inv.transform((bb.x1, bb.y1))[0]
        assert right < limits[x] - 0.03, f"cell overruns its column: {t.get_text()!r} ends at {right:.3f}in"
    for t in ax.texts:
        bb = t.get_window_extent(renderer=fig.canvas.get_renderer())
        x0, y0 = inv.transform((bb.x0, bb.y0)); x1, y1 = inv.transform((bb.x1, bb.y1))
        assert x0 > -1e-3 and x1 < FIG_W + 1e-3 and y0 > -1e-3 and y1 < FIG_H + 1e-3, \
            f"text leaves the figure: {t.get_text()!r}"

    return S.save(fig, STEM, FIG_W)


if __name__ == "__main__":
    build()
