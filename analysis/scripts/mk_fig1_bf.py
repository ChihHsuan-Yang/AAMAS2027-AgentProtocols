# -*- coding: utf-8 -*-
"""FIGURE 1 (v3, after the feedback-matched control) -- the corrected story.

THE SENTENCE THIS FIGURE MUST CARRY:
  Removing roles leaves the first answer alone. What a team does after a
  wrong answer depends first on whether the verifier's feedback reaches it:
  the original role-free team never saw it and resubmitted; the same team
  given the feedback recovers MORE than the role-structured team. Roles change
  how the six-cycle budget is spent, not whether a team can revise.

  Panel A  first-pass accuracy        role-free / role-free + feedback / role-structured
  Panel B  recovery after a FAIL      + structurally enforced; bracket = paired
                                      role-structured vs role-free + feedback
  Panel C  budget allocation (gemma-4, Omni-MATH): submitting vs revising

Groups: the three actors on Omni-MATH, then the SciBench cells. A cell that
has not been run is left empty and labelled "pending", never interpolated.

ENCODING. Hue = organization (purple role-structured, rose role-free, gold
enforced). Fill = feedback: the one condition whose agents never saw the
verifier's feedback (the original role-free run) is drawn HOLLOW. Identity is
also carried by position and the legend, never by hue alone.

DATA. Omni-MATH role-structured / role-free / enforced cells come from
analysis/out/FIGDATA.json (FINAL_TABLES.py, the frozen snapshot). Every
feedback-matched cell, every SciBench cell drawn here, and every paired p
comes from analysis/out/FIGDATA_BF.json (bf_numbers.py, whose positive control
asserts that it reproduces FIGDATA.json exactly). No numeric literal in this
file is a result.

LAYOUT. A and B share one actor axis (names set once, under B); text is set
in Libertinus Sans, the sans companion of the paper's Libertine face, when the
local TeX tree has it (mk_figstyle.use_paper_font), else in the default face.

Run:  python3 analysis/scripts/mk_fig1_bf.py      -> figures/fig1_v3_story.*
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import Patch

import mk_figstyle as S

S.apply_rc()
FONT = S.use_paper_font()
D = S.figdata()
with open(os.path.join(S.ROOT, "analysis", "out", "FIGDATA_BF.json")) as _f:
    DB = json.load(_f)
# Panel C: approvals (submissions) and declines per first-pass-wrong trajectory,
# counted over Reviewer turns (bf_gate.py). bf_numbers' "submits" also counts the
# one grading at the end of the budget of a trajectory that never submitted.
with open(os.path.join(S.ROOT, "analysis", "out", "FIGDATA_GATE.json")) as _f:
    DG = json.load(_f)
MAXCYC = D["max_cycles"]
FOCUS = "gemma-4-31B-it"
ALPHA = 0.05

# condition styling; "Bf" is the feedback-matched role-free condition
LONG = {"A": "role-structured", "B": "role-free, feedback withheld",
        "Bf": "role-free, with feedback", "C": "structurally enforced"}
COL = {"A": S.ARMC["A"], "B": S.ARMC["B"], "Bf": S.ARMC["B"], "C": S.ARMC["C"]}
HOLLOW = {"B"}
HATCH = {"C": "///"}

GROUPS = [("omni", a) for a in D["actors"]] + \
         [("scibench", a) for a in D["actors"] if f"scibench|{a}|A" in DB["cells"]]
DOMAIN_LABEL = {"omni": "Omni-MATH", "scibench": "SciBench"}


def cell(dom, actor, arm):
    """One source per cell: frozen Omni-MATH cells from FIGDATA.json, the rest
    from FIGDATA_BF.json. None if the cell has not been run."""
    if dom == "omni" and arm in ("A", "B", "C"):
        return D["cells"].get(f"{actor}|{arm}")
    if arm == "Bf" and DB.get("status", {}).get(f"{dom}|{actor}") != "complete":
        return None          # a run still in progress is drawn as pending, never as a bar
    return DB["cells"].get(f"{dom}|{actor}|{arm}")


def pfmt(p):
    """Two significant figures, as in the text; powers of ten set as exponents."""
    if p >= 1e-3:
        return rf"${p:.2g}$"
    m, e = f"{p:.1e}".split("e")
    return rf"${m}\times10^{{{int(e)}}}$"


# Light tints for the "revising" segment of panel C: each condition's own hue.
TINT = {"A": "#CFC5E2", "Bf": "#F2CFE0", "B": "#F2CFE0", "C": "#F1DDBF"}
FS_SMALL = S.FS_MIN          # p values and in-bar numbers: the class minimum
FS_TEXT = 7.0                # tick and row labels (Libertinus runs small)


def bar_kw(arm):
    if arm in HOLLOW:
        return dict(facecolor=S.SURFACE, edgecolor=COL[arm], linewidth=0.8)
    return dict(facecolor=COL[arm], hatch=HATCH.get(arm, ""),
                edgecolor=S.SURFACE if arm in HATCH else COL[arm], linewidth=0.0)


def draw_bars(ax, key, arms, w):
    """Grouped bars with bootstrap 95% intervals; returns {group: {arm: (x, hi)}}."""
    tops = {}
    for gi, (dom, a) in enumerate(GROUPS):
        tops[gi] = {}
        for k, arm in enumerate(arms):
            c = cell(dom, a, arm)
            x = gi + (k - (len(arms) - 1) / 2) * w
            if c is None:
                if not (arm == "C" and dom != "omni"):   # enforcement never ran off Omni-MATH
                    ax.text(x, 0.02, "pending", rotation=90, ha="center", va="bottom",
                            fontsize=FS_SMALL, color=S.INK3, zorder=5)
                continue
            m, lo, hi = c[key], c[key + "_lo"], c[key + "_hi"]
            ax.bar(x, m, w * 0.84, zorder=3, **bar_kw(arm))
            ax.errorbar(x, m, yerr=[[m - lo], [hi - m]], fmt="none", ecolor=S.INK2,
                        elinewidth=0.55, capsize=0.9, capthick=0.55, zorder=4)
            tops[gi][arm] = (x, hi)
    return tops


def frame(ax, ylabel, title, ymax, yticks):
    S.clean(ax)
    ax.set_ylim(0, ymax)
    ax.set_yticks(yticks)
    ax.set_yticklabels([f"{v:g}" for v in yticks])
    ax.set_xlim(-0.55, len(GROUPS) - 0.45)
    ax.set_ylabel(ylabel, labelpad=2)
    ax.annotate(title, xy=(0.0, 1.0), xycoords="axes fraction",
                xytext=(0, TITLE_PAD_PT), textcoords="offset points",
                ha="left", va="bottom", fontsize=S.FS_TITLE, fontweight="bold",
                color=S.INK)
    doms = [d for d, _ in GROUPS]
    for i in range(1, len(doms)):
        if doms[i] != doms[i - 1]:
            ax.axvline(i - 0.5, color=S.INK3, lw=0.5, ls=(0, (2, 2)), zorder=1)


def group_labels(ax):
    """Actor names once, under panel B, set line by line on a shared baseline
    (matplotlib aligns multi-line tick labels by their ink, which staggers a
    name with a descender against one without)."""
    ax.set_xticks(np.arange(len(GROUPS)))
    ax.set_xticklabels([""] * len(GROUPS))
    tr = ax.get_xaxis_transform()
    for i, (_, a) in enumerate(GROUPS):
        top, bottom = S.ACTOR_SHORT[a].split("\n")
        ax.annotate(top, xy=(i, 0), xycoords=tr, xytext=(0, -9), textcoords="offset points",
                    ha="center", va="baseline", fontsize=FS_TEXT, color=S.INK)
        ax.annotate(bottom, xy=(i, 0), xycoords=tr, xytext=(0, -17), textcoords="offset points",
                    ha="center", va="baseline", fontsize=FS_TEXT, color=S.INK2)
    doms = [d for d, _ in GROUPS]
    for d in dict.fromkeys(doms):
        idx = [i for i, dd in enumerate(doms) if dd == d]
        ax.annotate(DOMAIN_LABEL[d], xy=((idx[0] + idx[-1]) / 2, 0), xycoords=tr,
                    xytext=(0, -26), textcoords="offset points", ha="center",
                    va="baseline", fontsize=FS_SMALL, color=S.INK3, fontstyle="italic")


def panel_A(ax):
    draw_bars(ax, "firstpass", ("A", "Bf", "B"), 0.26)
    frame(ax, "first-pass\naccuracy", "A  First answer: no worse without roles",
          1.08, [0, 0.5, 1.0])
    plt.setp(ax.get_xticklabels(), visible=False)
    ax.tick_params(axis="x", length=0)


def panel_B(ax):
    tops = draw_bars(ax, "recovery", ("A", "Bf", "B", "C"), 0.205)
    frame(ax, "recovery after\na failed answer", "B  Recovery after a failed first answer",
          0.82, [0, 0.25, 0.5, 0.75])
    for gi, (dom, a) in enumerate(GROUPS):
        pr = DB["paired_recovery"].get(f"{dom}|{a}|A-Bf")
        t = tops[gi]
        if not pr or "A" not in t or "Bf" not in t:
            continue
        (xl, hl), (xr, hr) = t["A"], t["Bf"]
        yb = max(hl, hr) + 0.04
        ax.plot([xl, xl, xr, xr], [yb, yb + 0.02, yb + 0.02, yb], lw=0.55, color=S.INK2, zorder=5)
        ok = pr["p"] < ALPHA
        # the first group's label is anchored at its bracket so it clears the y axis
        x_lab, ha = ((xl - 0.04, "left") if gi == 0 else ((xl + xr) / 2, "center"))
        ax.text(x_lab, yb + 0.028, pfmt(pr["p"]) if ok else "n.s.", ha=ha,
                va="bottom", fontsize=FS_SMALL, color=S.INK if ok else S.INK3, zorder=6)
    group_labels(ax)


def panel_C(ax):
    arms = ("A", "C", "Bf", "B")
    ys = np.arange(len(arms), dtype=float)[::-1]
    gap = 0.05
    for yi, arm in zip(ys, arms):
        d = DG.get(f"omni|{FOCUS}|{arm}")
        if d is None:
            continue
        sub, rev = d["approvals"], d["declines"]
        ax.barh(yi, sub, 0.64, zorder=3, **bar_kw(arm))
        ax.barh(yi, rev, 0.64, left=sub + gap, color=TINT[arm], linewidth=0.0, zorder=3)
        if arm in ("A", "Bf"):
            ax.text(sub / 2, yi, f"{sub:.2f}", ha="center", va="center", fontsize=FS_SMALL,
                    color=S.SURFACE, zorder=6)
        else:
            # on the hatch, a halo in the bar's own colour keeps the digits clean;
            # inside the hollow bar the white face already does
            halo = [pe.withStroke(linewidth=2.8, foreground=COL[arm])] if arm in HATCH else None
            ax.text(sub / 2, yi, f"{sub:.2f}", ha="center", va="center", fontsize=FS_SMALL,
                    color=S.INK, zorder=6, path_effects=halo)
        if rev >= 0.6:
            ax.text(sub + gap + rev / 2, yi, f"{rev:.2f}", ha="center", va="center",
                    fontsize=FS_SMALL, color=S.INK, zorder=6)
        else:
            ax.text(sub - 0.12, yi, f"+ {rev:.2f} revising", ha="right", va="center",
                    fontsize=FS_SMALL, color=S.INK2, zorder=6)
        ax.text(-0.03, yi, LONG[arm], transform=ax.get_yaxis_transform(),
                ha="right", va="center", fontsize=FS_TEXT, color=S.INK)
    ax.axvline(MAXCYC, color=S.INK2, lw=0.6, ls=(0, (1.5, 1.5)), zorder=2)
    dA = DG[f"omni|{FOCUS}|A"]
    ax.text(dA["approvals"] / 2, ys[0] + 0.40, "submitting", ha="center", va="bottom",
            fontsize=FS_SMALL, color=S.INK3, fontstyle="italic")
    ax.text(dA["approvals"] + gap + dA["declines"] / 2, ys[0] + 0.40, "revising",
            ha="center", va="bottom", fontsize=FS_SMALL, color=S.INK3, fontstyle="italic")
    ax.text(MAXCYC - 0.05, ys[0] + 0.40, f"budget {MAXCYC}", ha="right", va="bottom",
            fontsize=FS_SMALL, color=S.INK2)
    ax.set_xlim(0, MAXCYC + 0.1)
    ax.set_ylim(-0.5, len(arms) - 0.25)
    # the axes top is raised to the top of the row of annotations above the
    # first bar, so the panel title clears the panel's ink by TITLE_PAD like A and B
    ax.figure.canvas.draw()
    inv = ax.transData.inverted()
    top = max(inv.transform((0, t.get_window_extent().y1))[1]
              for t in ax.texts if t.get_position()[1] > ys[0])
    ax.set_ylim(-0.5, top)
    ax.set_yticks([])
    ax.set_xticks(range(0, MAXCYC + 1, 2))
    S.clean(ax, grid_axis="x")
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("cycles per first-pass-wrong trajectory", labelpad=1.5)


# Laid out from the bottom up, in inches. A and B share the actor axis, so the
# actor names are set once, under B.
L_AB, L_C, R_EDGE = 0.50, 1.30, 3.28
H_A, H_B, H_C = 0.62, 0.86, 0.62
# Every panel title sits the same distance above its axes: TITLE_PAD above
# the top spine (A, B) or above the top of the bar area (C).  The gap between
# B's actor labels and C's title is set separately, so C's title belongs to C.
TITLE_PAD = 0.05                       # inches, between the panel's top ink and its title
TITLE_PAD_PT = TITLE_PAD * 72
TITLE_H = 0.12                         # the 8pt bold title line
LABELS_B = 0.42                        # actor and domain labels below B
Y_C = 0.34
Y_B = Y_C + H_C + TITLE_PAD + TITLE_H + 0.10 + LABELS_B
Y_A = Y_B + H_B + TITLE_PAD + TITLE_H + 0.06
FIG_H = Y_A + H_A + TITLE_PAD + TITLE_H + 0.34


def _rect(l, b, r, h):
    return [l / S.COLWIDTH_IN, b / FIG_H, (r - l) / S.COLWIDTH_IN, h / FIG_H]


def build(stem="fig1_v3_story"):
    fig = plt.figure(figsize=(S.COLWIDTH_IN, FIG_H))
    axA = fig.add_axes(_rect(L_AB, Y_A, R_EDGE, H_A))
    axB = fig.add_axes(_rect(L_AB, Y_B, R_EDGE, H_B), sharex=axA)
    panel_A(axA)
    panel_B(axB)
    axC = fig.add_axes(_rect(L_C, Y_C, R_EDGE, H_C)); panel_C(axC)
    fig.text(0.04 / S.COLWIDTH_IN, (Y_C + H_C + TITLE_PAD) / FIG_H,
             f"C  Same budget, spent differently ({S.ACTOR_SHORT[FOCUS].split(chr(10))[0]}, Omni-MATH)",
             fontsize=S.FS_TITLE, fontweight="bold", color=S.INK, ha="left", va="bottom")
    h = []
    for arm in ("A", "Bf", "B", "C"):    # column-major fill: rows read A, B / Bf, C
        h.append(Patch(label=LONG[arm] + (" (panels B, C)" if arm == "C" else ""), **bar_kw(arm)))
    fig.legend(handles=h, ncol=2, loc="upper center", bbox_to_anchor=(0.53, 1.005),
               fontsize=FS_TEXT, handlelength=1.0, handleheight=0.8, columnspacing=1.2,
               handletextpad=0.4, labelspacing=0.3, frameon=False)
    return S.save(fig, stem, S.COLWIDTH_IN)


if __name__ == "__main__":
    print("Figure 1 v3 -- " + S.provenance_line() + "  font: " + FONT)
    for dom, a in GROUPS:
        row = []
        for arm in ("B", "Bf", "A", "C"):
            c = cell(dom, a, arm)
            row.append(f"{arm} " + ("pending" if c is None else
                       f"fp {c['firstpass']:.3f} rec {c['recovery']:.3f}"))
        print(f"  {dom:<9}{a:<24}" + " | ".join(row))
    build()
