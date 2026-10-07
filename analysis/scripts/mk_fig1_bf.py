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

Run:  python3 analysis/scripts/mk_fig1_bf.py      -> figures/fig1_v3_story.*
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

import mk_figstyle as S

S.apply_rc()
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
        "Bf": "role-free + feedback", "C": "structurally enforced"}
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
    """Two significant figures, as in the text."""
    return f"p={p:.1e}".replace("e-0", "e-") if p < 1e-3 else f"p={p:.2g}"


def draw_bar(ax, x, arm, c, key, w, dom="omni"):
    if c is None and arm == "C" and dom != "omni":
        return None          # enforcement was never run outside Omni-MATH
    if c is None:
        ax.text(x, 0.02, "pending", rotation=90, ha="center", va="bottom",
                fontsize=S.FS_ANNOT, color=S.INK3, zorder=5)
        return None
    m, lo, hi = c[key], c[key + "_lo"], c[key + "_hi"]
    if arm in HOLLOW:
        ax.bar(x, m, w, facecolor=S.SURFACE, edgecolor=COL[arm], linewidth=0.9, zorder=3)
    else:
        ax.bar(x, m, w, color=COL[arm], hatch=HATCH.get(arm, ""), edgecolor=S.SURFACE,
               linewidth=0.0, zorder=3)
    ax.errorbar(x, m, yerr=[[m - lo], [hi - m]], fmt="none", ecolor=S.INK,
                elinewidth=0.6, capsize=1.0, capthick=0.6, zorder=4)
    return hi


def axes_common(ax, ylabel, title):
    S.clean(ax)
    ax.set_ylim(0, 1.0)
    ax.set_yticks(np.arange(0, 1.01, 0.5))
    ax.set_xlim(-0.64, len(GROUPS) - 0.45)
    ax.set_xticks(np.arange(len(GROUPS)))
    ax.set_xticklabels([S.ACTOR_SHORT[a] for _, a in GROUPS])
    ax.set_ylabel(ylabel, labelpad=1.5)
    ax.set_title(title, fontsize=S.FS_TITLE, pad=2.5, loc="left")
    # domain separators and labels under the actor names
    doms = [d for d, _ in GROUPS]
    for i in range(1, len(doms)):
        if doms[i] != doms[i - 1]:
            ax.axvline(i - 0.5, color=S.INK3, lw=0.6, ls=(0, (2, 2)), zorder=1)
    for d in dict.fromkeys(doms):
        idx = [i for i, dd in enumerate(doms) if dd == d]
        ax.annotate(DOMAIN_LABEL[d], xy=((idx[0] + idx[-1]) / 2, 0),
                    xycoords=ax.get_xaxis_transform(), xytext=(0, -20.5),
                    textcoords="offset points", ha="center", va="top",
                    fontsize=S.FS_ANNOT, color=S.INK3)


def panel_A(ax):
    arms = ("A", "Bf", "B")
    w = 0.25
    for gi, (dom, a) in enumerate(GROUPS):
        for k, arm in enumerate(arms):
            draw_bar(ax, gi + (k - 1) * w, arm, cell(dom, a, arm), "firstpass", w * 0.86, dom)
    axes_common(ax, "first-pass\naccuracy", "A   Roles removed: first answer no worse")


def panel_B(ax):
    arms = ("A", "Bf", "B", "C")
    w = 0.205
    for gi, (dom, a) in enumerate(GROUPS):
        tops = {}
        for k, arm in enumerate(arms):
            tops[arm] = draw_bar(ax, gi + (k - 1.5) * w, arm, cell(dom, a, arm),
                                 "recovery", w * 0.86, dom)
        pr = DB["paired_recovery"].get(f"{dom}|{a}|A-Bf")
        if pr and tops["Bf"] is not None and tops["A"] is not None:
            xl, xr = gi - 1.5 * w, gi - 0.5 * w
            yb = max(tops["Bf"], tops["A"]) + 0.045
            ax.plot([xl, xl, xr, xr], [yb, yb + 0.022, yb + 0.022, yb],
                    lw=0.6, color=S.INK2, zorder=5)
            ok = pr["p"] < ALPHA
            # left-aligned at the bracket so no label crosses a domain divider
            ax.text(xl - 0.10, yb + 0.032, pfmt(pr["p"]) if ok else "n.s.",
                    ha="left", va="bottom", fontsize=S.FS_ANNOT,
                    color=S.INK if ok else S.INK3, zorder=5)
    axes_common(ax, "recovery after\na failed answer",
                "B   Recovery after a failed first answer")


def panel_C(ax):
    arms = ("A", "C", "Bf", "B")
    ys = np.arange(len(arms), dtype=float)[::-1]
    gap = 0.045
    for yi, arm in zip(ys, arms):
        d = DG.get(f"omni|{FOCUS}|{arm}")
        if d is None:
            continue
        sub, rev = d["approvals"], d["declines"]
        kw = dict(facecolor=S.SURFACE, edgecolor=COL[arm], linewidth=0.9) if arm in HOLLOW \
            else dict(color=COL[arm], hatch=HATCH.get(arm, ""), edgecolor=S.SURFACE, linewidth=0.0)
        ax.barh(yi, sub, 0.56, zorder=3, **kw)
        ax.barh(yi, rev, 0.56, left=sub + gap, color=COL[arm], alpha=0.30, zorder=3,
                linewidth=0.0)
        tc = S.INK if (arm in HOLLOW or arm == "C") else S.SURFACE
        ax.text(sub / 2 if rev >= 0.6 else sub * 0.30, yi, f"{sub:.2f}",
                ha="center", va="center", fontsize=S.FS_ANNOT, color=tc, zorder=6,
                bbox=(dict(facecolor=S.SURFACE, edgecolor="none", pad=0.4, alpha=0.9)
                      if arm == "C" else None))
        if rev >= 0.6:
            ax.text(sub + gap + rev / 2, yi, f"{rev:.2f}", ha="center", va="center",
                    fontsize=S.FS_ANNOT, color=S.INK, zorder=6)
        else:
            ax.text(sub - 0.15, yi, f"+ {rev:.2f} revising", ha="right",
                    va="center", fontsize=S.FS_ANNOT, color=tc, zorder=6)
        ax.text(-0.025, yi, LONG[arm], transform=ax.get_yaxis_transform(),
                ha="right", va="center", fontsize=S.FS_ANNOT, color=S.INK)
    ax.axvline(MAXCYC, color=S.INK2, lw=0.7, zorder=2)
    dA = DG[f"omni|{FOCUS}|A"]
    ax.text(dA["approvals"] / 2, ys[0] + 0.42, "submitting", ha="center", va="bottom",
            fontsize=S.FS_ANNOT, color=S.INK3)
    ax.text(dA["approvals"] + gap + dA["declines"] / 2, ys[0] + 0.42, "revising",
            ha="center", va="bottom", fontsize=S.FS_ANNOT, color=S.INK3)
    ax.text(MAXCYC - 0.07, ys[0] + 0.42, f"budget {MAXCYC}", ha="right", va="bottom",
            fontsize=S.FS_ANNOT, color=S.INK2)
    ax.set_xlim(0, MAXCYC + 0.08)
    ax.set_ylim(-0.55, len(arms) - 0.2)
    ax.set_yticks([])
    S.clean(ax, grid_axis="x")
    ax.spines["left"].set_visible(False)
    ax.set_xlabel("cycles per first-pass-wrong trajectory", labelpad=1.5)


# Laid out from the bottom up, in inches: panel C's x label needs 0.36in.
L_AB, L_C, R_EDGE = 0.70, 1.38, 3.27
H_A, H_B, H_C = 0.70, 0.82, 0.70
Y_C = 0.36
Y_B = Y_C + H_C + 0.78
Y_A = Y_B + H_B + 0.74
FIG_H = Y_A + H_A + 0.45


def _rect(l, b, r, h):
    return [l / S.COLWIDTH_IN, b / FIG_H, (r - l) / S.COLWIDTH_IN, h / FIG_H]


def build(stem="fig1_v3_story"):
    fig = plt.figure(figsize=(S.COLWIDTH_IN, FIG_H))
    yA, yB, yC = Y_A, Y_B, Y_C
    axA = fig.add_axes(_rect(L_AB, yA, R_EDGE, H_A)); panel_A(axA)
    axB = fig.add_axes(_rect(L_AB, yB, R_EDGE, H_B)); panel_B(axB)
    axC = fig.add_axes(_rect(L_C, yC, R_EDGE, H_C)); panel_C(axC)
    fig.text(0.075 / S.COLWIDTH_IN, (yC + H_C + 0.20) / FIG_H,
             "C   Same budget, different allocation (gemma-4)",
             fontsize=S.FS_TITLE, color=S.INK, ha="left", va="bottom")
    h = []
    for arm in ("A", "B", "Bf", "C"):    # column-major fill: rows read A, Bf / B, C
        if arm in HOLLOW:
            h.append(Patch(facecolor=S.SURFACE, edgecolor=COL[arm], linewidth=0.9, label=LONG[arm]))
        else:
            h.append(Patch(facecolor=COL[arm], hatch=HATCH.get(arm, ""), edgecolor=S.SURFACE,
                           label=LONG[arm] + (" (panels B, C)" if arm == "C" else "")))
    fig.legend(handles=h, ncol=2, loc="upper center", bbox_to_anchor=(0.50, 1.004),
               fontsize=S.FS_ANNOT, handlelength=0.9, columnspacing=0.9,
               handletextpad=0.3, labelspacing=0.25)
    return S.save(fig, stem, S.COLWIDTH_IN)


if __name__ == "__main__":
    print("Figure 1 v3 -- " + S.provenance_line())
    for dom, a in GROUPS:
        row = []
        for arm in ("B", "Bf", "A", "C"):
            c = cell(dom, a, arm)
            row.append(f"{arm} " + ("pending" if c is None else
                       f"fp {c['firstpass']:.3f} rec {c['recovery']:.3f}"))
        print(f"  {dom:<9}{a:<24}" + " | ".join(row))
    build()
