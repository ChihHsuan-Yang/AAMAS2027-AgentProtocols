# -*- coding: utf-8 -*-
"""FIGURE 2 -- why recovery disappears.  gemma-4, the cleanest actor.

Claims visualised: A4 (same budget, MORE feedback in arm B -- not premature
stopping and not less feedback) and A5 (the mechanism is failure to produce a
distinct second candidate).  Nothing else.

THE POINT: same budget, opposite spending.

DESCRIPTIVE ONLY.  Per A5 this is post-treatment conditioning -- every quantity
is measured on trajectories selected for being first-pass wrong, and the
frozen-answer rate is itself an outcome.  So there are NO arrows between panels
and no mediation language anywhere in this figure: nothing here licenses a causal
path from cycles to frozen answers to recovery.  Each panel is a separate
marginal description of the same trajectories, and the caption says so.

Every value is read from analysis/out/FIGDATA.json via mk_figstyle.figdata().
No numeric literal here is a result; the literals are geometry, and the budget
ceiling, which is read from the frozen budget record (max_outer_rounds *
inner_rounds), not typed.

  v1  budget-split bars: one cycle budget, spent two ways   fig2_v1_budget
  v2  three small panels: opportunity / use / outcome       fig2_v2_panels
  v3  nested funnel, first-pass-wrong -> recovered          fig2_v3_funnel

Run:  python3 analysis/scripts/mk_fig2_mechanism.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

import mk_figstyle as S

S.apply_rc()
D = S.figdata()

ACTOR = "gemma-4-31B-it"          # the cleanest actor, per the brief
ARMS = ["A", "B"]                 # the contrast A5 is about
MAXCYC = D["max_cycles"]          # 6, read from the frozen budget record


def c(arm):
    return S.cell(ACTOR, arm)


def budget_note():
    b = D["budget"]
    return (f"Budget identical by construction: max_outer_rounds="
            f"{b['max_outer_rounds']} × inner_rounds={b['inner_rounds']} "
            f"= {MAXCYC} cycles in every arm.")


# =====================================================================
def v1():
    """One budget, spent two ways.  Stacked horizontal bars of the SAME length
    (cycles used), split into submitting vs revising."""
    fig, ax = plt.subplots(2, 1, figsize=(S.COLWIDTH_IN, 2.95),
                           gridspec_kw={"hspace": 0.95, "left": 0.135, "right": 0.985,
                                        "top": 0.800, "bottom": 0.215,
                                        "height_ratios": [1.0, 0.80]})
    # --- panel 1: how the cycles were spent
    A = ax[0]
    ys = np.arange(len(ARMS), dtype=float)[::-1]
    for yi, arm in zip(ys, ARMS):
        d = c(arm)
        sub, rev = d["submissions"], d["revising"]
        A.barh(yi, sub, 0.52, color=S.ARMC[arm], zorder=3)
        # 2px surface gap between the two segments, not a stroke
        A.barh(yi, rev, 0.52, left=sub + 0.045, color=S.ARMC[arm], alpha=0.30,
               zorder=3, edgecolor=S.SURFACE, linewidth=0.0)
        A.text(sub / 2, yi, f"{sub:.2f}", ha="center", va="center",
               fontsize=S.FS_ANNOT, color=S.SURFACE, zorder=5)
        if rev > 0.6:                      # only label a segment the text fits in
            A.text(sub + 0.045 + rev / 2, yi, f"{rev:.2f}", ha="center", va="center",
                   fontsize=S.FS_ANNOT, color=S.INK, zorder=5)
        else:
            A.text(sub + rev - 0.08, yi - 0.30, f"\u2191 {rev:.2f} revising",
                   ha="right", va="top", fontsize=S.FS_ANNOT, color=S.INK, zorder=5)
        A.text(-0.10, yi, f"arm {arm}", ha="right", va="center",
               fontsize=S.FS_LABEL, color=S.INK)
        A.text(d["cycles"], yi + 0.33, f"{d['cycles']:.2f} cycles used",
               ha="right", va="bottom", fontsize=S.FS_ANNOT, color=S.INK3)
    A.axvline(MAXCYC, color=S.INK2, lw=0.7, ls="-", zorder=2)
    A.text(MAXCYC - 0.05, ys[0] + 0.62, f"budget {MAXCYC}", ha="right", va="bottom",
           fontsize=S.FS_ANNOT, color=S.INK2)
    A.set_xlim(0, MAXCYC + 0.12)
    A.set_ylim(-0.72, len(ARMS) + 0.10)
    A.set_yticks([])
    A.set_xlabel("deliberation cycles per first-pass-wrong trajectory", labelpad=1.5)
    S.clean(A, grid_axis="x")
    A.spines["left"].set_visible(False)
    A.set_title("Same budget, opposite spending", fontsize=S.FS_TITLE, pad=2, loc="left")
    h = [Patch(facecolor=S.ARMC["A"], label="arm A  soft roles"),
         Patch(facecolor=S.ARMC["B"], label="arm B  no roles"),
         Patch(facecolor=S.INK3, label="submitting"),
         Patch(facecolor=S.INK3, alpha=0.30, label="revising")]
    fig.legend(handles=h, ncol=4, loc="upper center", bbox_to_anchor=(0.52, 1.005),
               fontsize=S.FS_LEGEND, handlelength=0.9, columnspacing=0.8)

    # --- panel 2: what came of it
    B = ax[1]
    keys = [("frozen_ans", "answer never\nchanged"), ("recovery", "recovered")]
    x = np.arange(len(keys), dtype=float)
    w = 0.33
    for k, arm in enumerate(ARMS):
        d = c(arm)
        vals = [d[kk] for kk, _ in keys]
        B.bar(x + (k - 0.5) * w, vals, w * 0.86, color=S.ARMC[arm], zorder=3)
        for xi, v in zip(x + (k - 0.5) * w, vals):
            B.text(xi, v + 0.025, f"{v:.3f}", ha="center", va="bottom",
                   fontsize=S.FS_ANNOT, color=S.INK)
    B.set_xticks(x); B.set_xticklabels([lab for _, lab in keys])
    B.set_ylim(0, 1.0)
    B.set_yticks(np.arange(0, 1.01, 0.5))
    B.set_xlim(-0.55, len(keys) - 0.45)
    S.clean(B)
    B.set_ylabel("proportion", labelpad=1.5)

    fig.text(0.008, 0.006,
             f"gemma-4-31B, first-pass-wrong only (n={c('A')['n_fpw']} A / "
             f"{c('B')['n_fpw']} B).\nDescriptive; the panels are not a causal chain.",
             fontsize=S.FS_ANNOT, color=S.INK3, ha="left", va="bottom")
    return S.save(fig, "fig2_v1_budget", S.COLWIDTH_IN)


# =====================================================================
def v2():
    """Paired slopes: each measure is one A->B line on its own small axis.

    The reader's job here is DIRECTION, not magnitude -- which quantities go up
    when roles are removed and which go down.  Each measure therefore gets its
    own axis scaled to its own unit; nothing shares a scale, so a cycle count is
    never read against a proportion.  Deliberately no arrows between panels:
    per A5 this is post-treatment description, not a mediation path.
    """
    measures = [("cycles", "cycles used", "cyc", MAXCYC),
                ("submissions", "evaluator\nsubmissions", "cyc", MAXCYC),
                ("revising", "cycles spent\nrevising", "cyc", MAXCYC),
                ("frozen_ans", "answer never\nchanged", "prop", 1.0),
                ("recovery", "recovered", "prop", 1.0)]
    fig, ax = plt.subplots(1, len(measures), figsize=(S.COLWIDTH_IN, 2.05),
                           gridspec_kw={"wspace": 0.42, "left": 0.055, "right": 0.935,
                                        "top": 0.660, "bottom": 0.300})
    xs = np.array([0.0, 1.0])
    for mi, (key, lab, unit, cap) in enumerate(measures):
        A = ax[mi]
        vals = [c(arm)[key] for arm in ARMS]
        A.plot(xs, vals, "-", color=S.INK3, lw=0.9, zorder=2)
        for k, arm in enumerate(ARMS):
            A.plot([xs[k]], [vals[k]], marker="o", ms=3.6, mfc=S.ARMC[arm],
                   mec=S.SURFACE, mew=0.8, zorder=4)
        fmt = (lambda v: f"{v:.2f}") if unit == "cyc" else (lambda v: f"{v:.3f}")
        # Put each endpoint label on the OUTSIDE of the slope (A to the left,
        # B to the right) and always ABOVE its marker, so a value near zero
        # cannot land on the arm tick labels below the axis.
        A.annotate(fmt(vals[0]), (xs[0], vals[0]), textcoords="offset points",
                   xytext=(-2.5, 4.0), ha="right", va="bottom",
                   fontsize=S.FS_ANNOT, color=S.INK)
        A.annotate(fmt(vals[1]), (xs[1], vals[1]), textcoords="offset points",
                   xytext=(2.5, 4.0), ha="left", va="bottom",
                   fontsize=S.FS_ANNOT, color=S.INK)
        A.set_ylim(0, cap * 1.13)
        A.set_xlim(-0.95, 1.95)
        A.set_xticks(xs); A.set_xticklabels(["A", "B"])
        A.set_yticks([])
        S.clean(A, grid_axis=None)
        A.spines["left"].set_visible(False)
        A.set_title(lab, fontsize=S.FS_ANNOT, pad=2.5, linespacing=1.15)
        A.text(0.5, -0.30, "of %d" % MAXCYC if unit == "cyc" else "of 1",
               transform=A.transAxes, ha="center", va="top",
               fontsize=S.FS_ANNOT, color=S.INK3)
    fig.text(0.008, 0.990,
             "Same opportunity, opposite use, opposite outcome",
             fontsize=S.FS_TITLE, ha="left", va="top", color=S.INK)
    fig.text(0.008, 0.905,
             "gemma-4-31B, first-pass wrong.  Each measure on its own axis;\n"
             "cycles and proportions never share a scale.",
             fontsize=S.FS_ANNOT, ha="left", va="top", color=S.INK3)
    fig.text(0.008, 0.006,
             f"A = soft roles, B = no roles; n={c('A')['n_fpw']} / {c('B')['n_fpw']}.\n"
             f"Five marginal views of the same trajectories \u2014 not a causal chain.",
             fontsize=S.FS_ANNOT, color=S.INK3, ha="left", va="bottom")
    return S.save(fig, "fig2_v2_panels", S.COLWIDTH_IN)


# =====================================================================
def v3():
    """Nested funnel.  Every stage is a subset of the one above, so the bars can
    only shrink; the two arms sit side by side on one shared stage axis."""
    F = D["funnel"]
    stages = [("stage1_first_pass_wrong", "first pass wrong"),
              ("stage2_resubmitted", "asked the evaluator again"),
              ("stage3_distinct_second_candidate", "held a 2nd distinct answer"),
              ("stage4_recovered", "recovered")]
    fig, ax = plt.subplots(figsize=(S.COLWIDTH_IN, 2.45),
                           gridspec_kw={"left": 0.435, "right": 0.905,
                                        "top": 0.815, "bottom": 0.255})
    ys = np.arange(len(stages), dtype=float)[::-1]
    h = 0.34
    base = max(F[f"{ACTOR}|{a}"]["stage1_first_pass_wrong"] for a in ARMS)
    for k, arm in enumerate(ARMS):
        f = F[f"{ACTOR}|{arm}"]
        off = (0.5 - k) * h
        vals = [f[key] for key, _ in stages]
        ax.barh(ys + off, vals, h * 0.86, color=S.ARMC[arm], zorder=3,
                label=f"arm {arm}  {S.ARM_LONG[arm].split('  ')[1]}")
        for yi, v in zip(ys + off, vals):
            ax.text(v + base * 0.015, yi, f"{v}", ha="left", va="center",
                    fontsize=S.FS_ANNOT, color=S.INK)
    ax.set_yticks(ys)
    ax.set_yticklabels([lab for _, lab in stages])
    ax.set_ylim(-0.55, len(stages) - 0.45)
    ax.set_xlim(0, base * 1.16)
    S.clean(ax, grid_axis="x")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("trajectories", labelpad=1.5)
    ax.legend(ncol=1, loc="lower right", fontsize=S.FS_LEGEND, handlelength=1.0,
              borderaxespad=0.25)
    fig.text(0.008, 0.988,
             "Arm B asks again far more often, and\nalmost never has a new answer to give",
             fontsize=S.FS_TITLE, ha="left", va="top", color=S.INK, linespacing=1.2)
    off_ = [F[f"{ACTOR}|{a}"]["recovered_outside_funnel"] for a in ARMS]
    fig.text(0.008, 0.006,
             f"gemma-4-31B.  Stages strictly nested by construction.\n"
             f"Recovered outside the funnel: {off_[0]} (A), {off_[1]} (B).\n"
             f"Stage order is not a causal sequence.",
             fontsize=S.FS_ANNOT, color=S.INK3, ha="left", va="bottom")
    return S.save(fig, "fig2_v3_funnel", S.COLWIDTH_IN)


if __name__ == "__main__":
    print("Figure 2 -- " + S.provenance_line())
    print("  " + budget_note())
    for arm in ARMS:
        d = c(arm)
        print(f"  arm {arm}: n_fpw={d['n_fpw']} cycles={d['cycles']:.2f} "
              f"submits={d['submissions']:.2f} revising={d['revising']:.2f} "
              f"frozen={d['frozen_ans']:.3f} recovery={d['recovery']:.3f}")
    v1(); v2(); v3()
