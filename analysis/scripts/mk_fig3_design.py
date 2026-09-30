# -*- coding: utf-8 -*-
"""FIGURE 3 -- the A/B/C design schematic.

A conceptual diagram of the manipulation, plus a one-line outcome note per arm.
It replaces several paragraphs of prose, so it must be readable without the text.

WHAT IS FIXED BY DESIGN (not measured, and so legitimately drawn as structure):
  - all three arms run the SAME Planner -> Executor -> Reviewer topology,
    the SAME information routing and the SAME budget (A4: max_outer_rounds x
    inner_rounds, read from the frozen budget record)
  - A  soft role prompts: roles asserted rhetorically, in prose
  - B  one generic prompt, byte-identical for all three agents; role names
       survive only as turn-routing labels inside the runner
  - C  architectural enforcement: the planner's JSON schema has NO answer field,
       and a validator rejects an answer leak
  (verified in experiments/prompts.py and experiments/schemas.py)

THE OUTCOME NOTES ARE MEASURED and are read from FIGDATA.json -- never typed.
Per FINDING-25 the adjudication is outcome-blind but NOT condition-blind, so the
organization line uses the MECHANICAL functional-collapse measure (A1's primary
evidence as of 2026-09-30), which involves no judge.  The judge number is not
drawn in this figure at all.

  v1  three columns, pipeline + notes      fig3_v1_columns
  v2  one shared pipeline, arms as rows    fig3_v2_rows

Run:  python3 analysis/scripts/mk_fig3_design.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

import mk_figstyle as S

S.apply_rc()
D = S.figdata()
ARMS = ["A", "B", "C"]
MAXCYC = D["max_cycles"]
BUD = D["budget"]

ROLE_A = ["Planner", "Executor", "Reviewer"]
ROLE_B = ["Agent 1", "Agent 2", "Agent 3"]

MANIP = {
    "A": "role prompts,\nin prose",
    "B": "one generic\nprompt for all 3",
    "C": "planner schema:\nno answer field",
}
MECH = {
    "A": "roles asserted\n(rhetorical)",
    "B": "no role info\nin any prompt",
    "C": "roles enforced\n(architectural)",
}


def pooled_collapse(arm):
    """Mechanical functional collapse, pooled over actors, weighted by cell n.
    A1's primary evidence -- no judge involved."""
    M = D["mechanical"]
    num = den = 0.0
    for a in D["actors"]:
        e = M.get(f"{a}|{arm}")
        if not e:
            continue
        num += e["functional_collapse"] * e["n"]
        den += e["n"]
    return num / den


def outcome_lines(arm):
    """One measured line per arm.  Every number interpolated from FIGDATA."""
    acts = D["actors"]
    fp = [S.cell(a, arm)["firstpass"] for a in acts]
    rec = [S.cell(a, arm)["recovery"] for a in acts]
    att = [S.cell(a, arm)["attrition"] for a in acts]
    L = [f"first pass {min(fp):.2f}–{max(fp):.2f}",
         f"recovery {min(rec):.3f}–{max(rec):.3f}"]
    if arm == "C":
        L.append(f"attrition {min(att)*100:.0f}–{max(att)*100:.0f}%")
    else:
        L.append(f"collapse {pooled_collapse(arm):.2f}")
    return L


# Verdicts must carry ACTOR SCOPE. APPROVED_CLAIMS opens with "actor scope is
# part of the claim"; A3 is "GEMMA-4 CLEAN; GPT-OSS WEAKER; LLAMA NOT".
# Unscoped, these were false for one actor each: arm A "repairs" is
# contradicted by Llama's 0.014, printed two lines above in the same panel;
# arm B "no repair" asserts more than A3 permits for gpt-oss (0.247, paired
# p=0.246, which A3 requires be called weaker and not significant).
VERDICT = {
    "A": "organized;\nrepairs (1 of 3)",
    "B": "same answers;\nrepair falls",
    "C": "organized,\nbut brittle",
}


def _box(ax, x, y, w, h, text, fc, ec, fs, tc=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle="round,pad=0,rounding_size=0.018",
                                linewidth=0.7, facecolor=fc, edgecolor=ec,
                                zorder=3, mutation_aspect=1))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, color=tc or S.INK, zorder=4, linespacing=1.1)


def _arrow(ax, x0, y0, x1, y1, color):
    ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>",
                                 mutation_scale=4.5, lw=0.7, color=color,
                                 shrinkA=0, shrinkB=0, zorder=2))


# =====================================================================
def v1():
    """Three columns side by side: each shows its own pipeline and notes."""
    fig, ax = plt.subplots(figsize=(S.COLWIDTH_IN, 3.60))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    fig.subplots_adjust(left=0.005, right=0.995, top=0.995, bottom=0.005)

    colw, gap = 0.320, 0.020
    for i, arm in enumerate(ARMS):
        x0 = i * (colw + gap)
        col = S.ARMC[arm]
        ax.text(x0 + colw / 2, 0.992, f"Arm {arm}", ha="center", va="top",
                fontsize=S.FS_LABEL, color=col)
        ax.text(x0 + colw / 2, 0.943, MECH[arm], ha="center", va="top",
                fontsize=S.FS_ANNOT, color=S.INK, linespacing=1.1)

        # the pipeline: identical topology in every arm
        names = ROLE_B if arm == "B" else ROLE_A
        bh, bx = 0.068, x0 + 0.012
        bw = colw - 0.024
        top = 0.790
        for j, nm in enumerate(names):
            y = top - j * (bh + 0.042)
            # arm C: the planner box is the one the manipulation acts on
            hi = (arm == "C" and j == 0)
            _box(ax, bx, y, bw, bh, nm, fc=col if hi else S.SURFACE,
                 ec=col, fs=S.FS_ANNOT, tc=S.SURFACE if hi else S.INK)
            if j < len(names) - 1:
                _arrow(ax, bx + bw / 2, y, bx + bw / 2, y - 0.042, col)
        # the manipulation, called out under the pipeline
        ax.text(x0 + colw / 2, 0.545, MANIP[arm], ha="center", va="top",
                fontsize=S.FS_ANNOT, color=S.INK, linespacing=1.15, style="italic")
        # measured outcome
        ax.plot([x0 + 0.012, x0 + colw - 0.012], [0.437, 0.437],
                "-", color=S.GRID, lw=0.7)
        for k, line in enumerate(outcome_lines(arm)):
            ax.text(x0 + colw / 2, 0.402 - k * 0.052, line, ha="center", va="top",
                    fontsize=S.FS_ANNOT, color=S.INK3)
        ax.text(x0 + colw / 2, 0.222, VERDICT[arm], ha="center", va="top",
                fontsize=S.FS_ANNOT, color=col, linespacing=1.15)

    ax.text(0.5, 0.155,
            f"Identical in all arms: topology, routing and budget\n"
            f"({BUD['max_outer_rounds']}×{BUD['inner_rounds']}={MAXCYC} cycles, "
            f"max_evaluator_calls={BUD['max_evaluator_calls']}, "
            f"temperature={BUD['temperature']:g}).\n"
            f"Only the prompt or schema differs.\n"
            f"Ranges span the three actors; ‘collapse’ is the\n"
            f"mechanical functional-collapse rate (no judge).",
            ha="center", va="top", fontsize=S.FS_ANNOT, color=S.INK, linespacing=1.3)
    return S.save(fig, "fig3_v1_columns", S.COLWIDTH_IN)


# =====================================================================
def v2():
    """One pipeline drawn once, with the arms as rows underneath it: emphasises
    that the topology is shared and only the prompt/schema layer changes."""
    fig, ax = plt.subplots(figsize=(S.TEXTWIDTH_IN, 2.70))
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis("off")
    fig.subplots_adjust(left=0.004, right=0.996, top=0.996, bottom=0.004)

    # --- shared pipeline across the top
    ax.text(0.005, 0.965, "Shared by every arm", ha="left", va="top",
            fontsize=S.FS_LABEL, color=S.INK)
    bw, bh, y = 0.118, 0.115, 0.775
    xs = [0.075, 0.245, 0.415]
    for nm, x in zip(ROLE_A, xs):
        _box(ax, x, y, bw, bh, nm, fc=S.SURFACE, ec=S.INK2, fs=S.FS_ANNOT)
    for a, b in zip(xs, xs[1:]):
        _arrow(ax, a + bw, y + bh / 2, b, y + bh / 2, S.INK2)
    _box(ax, 0.600, y, 0.135, bh, "Evaluator\n(oracle)", fc=S.SURFACE,
         ec=S.INK2, fs=S.FS_ANNOT)
    _arrow(ax, xs[-1] + bw, y + bh / 2, 0.600, y + bh / 2, S.INK2)
    # feedback loop back to the planner
    ax.annotate("", xy=(xs[0] + bw / 2, y), xytext=(0.6675, y - 0.075),
                arrowprops=dict(arrowstyle="-|>", lw=0.7, color=S.INK2,
                                mutation_scale=4.5,
                                connectionstyle="angle,angleA=0,angleB=90,rad=0"))
    ax.text(0.352, y - 0.098, f"up to {MAXCYC} cycles, identical budget in every arm",
            ha="center", va="top", fontsize=S.FS_ANNOT, color=S.INK3)
    ax.text(0.755, y + bh / 2, "same topology,\nrouting and budget",
            ha="left", va="center", fontsize=S.FS_ANNOT, color=S.INK3,
            linespacing=1.15)

    # --- what differs, one row per arm
    ax.text(0.005, 0.590, "What differs", ha="left", va="top",
            fontsize=S.FS_LABEL, color=S.INK)
    ax.text(0.545, 0.590, "measured", ha="left", va="top",
            fontsize=S.FS_ANNOT, color=S.INK3)
    ax.text(0.996, 0.590, "verdict", ha="right", va="top",
            fontsize=S.FS_ANNOT, color=S.INK3)
    rh = 0.132
    for i, arm in enumerate(ARMS):
        yy = 0.400 - i * (rh + 0.020)
        col = S.ARMC[arm]
        _box(ax, 0.075, yy, 0.052, rh, arm, fc=col, ec=col, fs=S.FS_LABEL,
             tc=S.SURFACE)
        ax.text(0.142, yy + rh / 2, MECH[arm].replace("\n", " "), ha="left",
                va="center", fontsize=S.FS_ANNOT, color=S.INK)
        ax.text(0.350, yy + rh / 2, MANIP[arm].replace("\n", " "), ha="left",
                va="center", fontsize=S.FS_ANNOT, color=S.INK, style="italic")
        ol = outcome_lines(arm)
        ax.text(0.545, yy + rh / 2, ol[0] + "\n" + " · ".join(ol[1:]), ha="left",
                va="center", fontsize=S.FS_ANNOT, color=S.INK3, linespacing=1.25)
        ax.text(0.996, yy + rh / 2, VERDICT[arm], ha="right", va="center",
                fontsize=S.FS_ANNOT, color=col, linespacing=1.25)
    ax.text(0.005, 0.008,
            "Ranges span the three actors.  ‘collapse’ = mechanical functional-collapse "
            "rate — no judge, because per FINDING-25\nthe adjudication is not condition-blind.",
            ha="left", va="bottom", fontsize=S.FS_ANNOT, color=S.INK3)
    return S.save(fig, "fig3_v2_rows", S.TEXTWIDTH_IN)


if __name__ == "__main__":
    print("Figure 3 -- " + S.provenance_line())
    for arm in ARMS:
        print(f"  arm {arm}: " + " | ".join(outcome_lines(arm)))
    v1(); v2()
