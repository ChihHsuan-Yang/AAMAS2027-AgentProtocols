"""FIGURE 1 -- the phase dissociation.  THREE alternative designs, same numbers.

Claims visualised: A2 (first-pass parity, all three actors), A3 (recovery cost --
gemma-4 clean, gpt-oss weaker, Llama a floor), A6 (arm C restores recovery),
A7 (arm C attrition 8-17%).  Nothing else.

Every value is read from analysis/out/FIGDATA.json via mk_figstyle.figdata().
No numeric literal in this file is a result.  The only literals are geometry
(positions, widths) and the y-limits 0 and 1, which are the bounds of a
proportion, not a measurement.

  v1  grouped columns, two stacked panels        fig1_v1_grouped    (1 column)
  v2  small-multiple slopes, one column/actor    fig1_v2_slopes     (1 column)
  v3  dumbbell rows on a shared value axis       fig1_v3_dumbbell   (2 columns)

Run:  python3 analysis/scripts/mk_fig1_dissociation.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

import mk_figstyle as S

S.apply_rc()
D = S.figdata()
ACTORS = D["actors"]
ARMS = ["A", "B", "C"]


def floor_actors():
    """Which cells sit at a recovery FLOOR is computed, never asserted.

    An actor is flagged when the upper confidence limit of its recovery in BOTH
    arm A and arm B falls below the mean arm-A recovery of the other actors --
    i.e. it had no headroom to lose in the first place.  A3 names Llama-3.3;
    this rederives that from the data so the annotation cannot drift.
    """
    out = []
    for a in ACTORS:
        ref = float(np.mean([S.cell(b, "A")["recovery"] for b in ACTORS if b != a]))
        if S.cell(a, "A")["recovery_hi"] < ref and S.cell(a, "B")["recovery_hi"] < ref:
            out.append(a)
    return out


FLOOR = floor_actors()
ATTR = [S.cell(a, "C")["attrition"] for a in ACTORS]
ATTR_TXT = f"{min(ATTR)*100:.0f}–{max(ATTR)*100:.0f}%"


def err(cells, key):
    m = np.array([c[key] for c in cells], float)
    lo = np.array([c[key + "_lo"] for c in cells], float)
    hi = np.array([c[key + "_hi"] for c in cells], float)
    return m, np.vstack([m - lo, hi - m])


def floor_text(a):
    return (f"Llama A {S.cell(a,'A')['recovery']:.3f} ≈ B {S.cell(a,'B')['recovery']:.3f}:\n"
            f"a floor, not “roles don’t matter”").replace(
        "Llama", S.ACTOR_1LINE[a].split("-3.3")[0])


# =====================================================================
def v1():
    """Grouped columns: arms clustered inside each actor, two stacked panels."""
    fig, ax = plt.subplots(2, 1, figsize=(S.COLWIDTH_IN, 4.05), sharex=True,
                           gridspec_kw={"hspace": 0.26, "left": 0.150, "right": 0.988,
                                        "top": 0.915, "bottom": 0.135})
    x = np.arange(len(ACTORS), dtype=float)
    w = 0.26
    for pi, (key, nkey) in enumerate((("firstpass", "n_graded"), ("recovery", "n_fpw"))):
        A = ax[pi]
        tops = {}
        for k, arm in enumerate(ARMS):
            cells = [S.cell(a, arm) for a in ACTORS]
            m, e = err(cells, key)
            off = (k - 1) * w
            A.bar(x + off, m, w * 0.86, color=S.ARMC[arm], zorder=3,
                  hatch=S.ARMHATCH[arm], edgecolor=S.SURFACE, linewidth=0.0)
            A.errorbar(x + off, m, yerr=e, fmt="none", ecolor=S.INK, elinewidth=0.7,
                       capsize=1.3, capthick=0.7, zorder=4)
            # denominator ABOVE the interval, so it can never collide with the
            # actor tick labels.  Required by the brief: recovery n differs per cell.
            tops[k] = m + e[1]
        # One denominator string per actor group: per-bar labels collide once a
        # cell n reaches four digits.  Order is A / B / C, stated in the footnote.
        for i, a in enumerate(ACTORS):
            ns = " / ".join(str(S.cell(a, arm)[nkey]) for arm in ARMS)
            A.text(i, max(t[i] for t in tops.values()) + 0.028, ns,
                   ha="center", va="bottom", fontsize=S.FS_ANNOT, color=S.INK3)
        S.clean(A)
        A.set_ylim(0, 1.0)                 # full proportion range; never truncated
        A.set_yticks(np.arange(0, 1.01, 0.25))
        A.set_xlim(-0.56, len(ACTORS) - 0.44)
    ax[0].set_ylabel("first-pass accuracy")
    ax[1].set_ylabel("recovery | first pass wrong")
    ax[0].set_title("Removing roles: no cost on the first answer…",
                    fontsize=S.FS_TITLE, pad=3, loc="left")
    ax[1].set_title("…but it can destroy repair of a wrong one",
                    fontsize=S.FS_TITLE, pad=3, loc="left")
    ax[1].set_xticks(x)
    ax[1].set_xticklabels([S.ACTOR_SHORT[a] for a in ACTORS])

    h = [Patch(facecolor=S.ARMC[a], hatch=S.ARMHATCH[a], edgecolor=S.SURFACE,
               label=S.ARM_LONG[a]) for a in ARMS]
    ax[1].legend(handles=h, ncol=1, loc="upper left", fontsize=S.FS_LEGEND,
                 handlelength=1.0, borderaxespad=0.15)
    for a in FLOOR:                        # upper right of panel B, free space
        i = ACTORS.index(a)
        ax[1].annotate(floor_text(a), xy=(i, 0.105),
                       xytext=(len(ACTORS) - 0.47, 0.72),
                       fontsize=S.FS_ANNOT, color=S.INK, ha="right", va="bottom",
                       arrowprops=dict(arrowstyle="-", lw=0.5, color=S.INK2,
                                       shrinkA=2.0, shrinkB=2.0))
    fig.text(0.010, 0.018, f"grey digits = cell n, A / B / C.   "
                           f"arm C hatched: {ATTR_TXT} attrition.",
             fontsize=S.FS_ANNOT, color=S.INK3, ha="left", va="bottom")
    return S.save(fig, "fig1_v1_grouped", S.COLWIDTH_IN)


# =====================================================================
def v2():
    """Small multiples: the A->B->C path, one column per actor."""
    fig, ax = plt.subplots(2, len(ACTORS), figsize=(S.COLWIDTH_IN, 3.70),
                           sharey="row", sharex=True,
                           gridspec_kw={"hspace": 0.26, "wspace": 0.18,
                                        "left": 0.175, "right": 0.988,
                                        "top": 0.845, "bottom": 0.150})
    xs = np.arange(len(ARMS), dtype=float)
    for j, a in enumerate(ACTORS):
        for pi, (key, nkey, dec) in enumerate((("firstpass", "n_graded", 2),
                                               ("recovery", "n_fpw", 3))):
            A = ax[pi][j]
            cells = [S.cell(a, arm) for arm in ARMS]
            m, e = err(cells, key)
            A.plot(xs, m, "-", color=S.INK3, lw=0.9, zorder=2)
            A.errorbar(xs, m, yerr=e, fmt="none", ecolor=S.INK2, elinewidth=0.7,
                       capsize=1.2, capthick=0.7, zorder=3)
            for k, arm in enumerate(ARMS):
                A.plot([xs[k]], [m[k]], marker=("D" if arm == "C" else "o"),
                       ms=3.4, mfc=S.ARMC[arm], mec=S.SURFACE, mew=0.8, zorder=4)
            S.clean(A)
            A.set_ylim(0, 1.0)
            A.set_yticks(np.arange(0, 1.01, 0.25))
            A.set_xlim(-0.48, len(ARMS) - 0.52)
            A.set_xticks(xs); A.set_xticklabels(ARMS)
            if pi == 0:
                A.set_title(S.ACTOR_1LINE[a], fontsize=S.FS_ANNOT, pad=2)
            # label only arms A and B -- the contrast the claim is about.
            # always ABOVE the marker, so a near-zero value cannot sit on the axis.
            for k in (0, 1):
                A.annotate(f"{m[k]:.{dec}f}", (xs[k], m[k] + e[1][k]),
                           textcoords="offset points", xytext=(0, 3.2), ha="center",
                           fontsize=S.FS_ANNOT, color=S.INK)
            A.text(0.03, 0.97, f"n {min(c[nkey] for c in cells)}–"
                               f"{max(c[nkey] for c in cells)}",
                   transform=A.transAxes, fontsize=S.FS_ANNOT, color=S.INK3,
                   ha="left", va="top")
    ax[0][0].set_ylabel("first-pass\naccuracy")
    ax[1][0].set_ylabel("recovery |\nfirst pass wrong")
    fig.text(0.5, 0.993, "First pass: flat across arms.   Recovery: not.",
             fontsize=S.FS_TITLE, ha="center", va="top", color=S.INK)
    for a in FLOOR:
        j = ACTORS.index(a)
        ax[1][j].text(0.97, 0.97, "floor:\nboth ≈ 0\nno room\nto fall",
                      transform=ax[1][j].transAxes, fontsize=S.FS_ANNOT,
                      color=S.INK, ha="right", va="top", linespacing=1.15)
    fig.text(0.5, 0.062, "arm", fontsize=S.FS_LABEL, ha="center", color=S.INK)
    fig.text(0.010, 0.016, f"A soft roles / B no roles / C enforced (◆, "
                           f"{ATTR_TXT} attrition).",
             fontsize=S.FS_ANNOT, color=S.INK3, ha="left", va="bottom")
    return S.save(fig, "fig1_v2_slopes", S.COLWIDTH_IN)


# =====================================================================
def v3():
    """Dumbbell: actor-major rows, all three arms on one shared value axis."""
    fig, ax = plt.subplots(1, 2, figsize=(S.TEXTWIDTH_IN, 2.05), sharey=True,
                           gridspec_kw={"wspace": 0.10, "left": 0.108,
                                        "right": 0.984, "top": 0.855, "bottom": 0.275})
    ys = np.arange(len(ACTORS), dtype=float)[::-1]
    for pi, (key, nkey, ttl) in enumerate((
            ("firstpass", "n_graded", "First-pass accuracy  —  the arms coincide"),
            ("recovery", "n_fpw", "Recovery | first pass wrong  —  the arms diverge"))):
        A = ax[pi]
        for yi, a in zip(ys, ACTORS):
            cells = [S.cell(a, arm) for arm in ARMS]
            vals = [c[key] for c in cells]
            A.plot([min(vals), max(vals)], [yi, yi], "-", color=S.GRID, lw=2.2,
                   zorder=1, solid_capstyle="round")
            for arm, c in zip(ARMS, cells):
                A.plot([c[key + "_lo"], c[key + "_hi"]], [yi, yi], "-",
                       color=S.INK2, lw=0.6, zorder=2)
                A.plot([c[key]], [yi], marker=("D" if arm == "C" else "o"),
                       ms=4.4, mfc=S.ARMC[arm], mec=S.SURFACE, mew=1.0, zorder=4)
            A.text(0.012, yi + 0.26, "n = " + " / ".join(str(c[nkey]) for c in cells),
                   ha="left", va="bottom", fontsize=S.FS_ANNOT, color=S.INK3)
        S.clean(A, grid_axis="x")
        A.set_xlim(0, 1.0)                 # full proportion range; never truncated
        A.set_xticks(np.arange(0, 1.01, 0.25))
        A.set_ylim(-0.62, len(ACTORS) - 0.30)
        A.set_title(ttl, fontsize=S.FS_TITLE, pad=3, loc="left")
        A.set_xlabel("proportion", fontsize=S.FS_LABEL, labelpad=1.5)
    ax[0].set_yticks(ys)
    ax[0].set_yticklabels([S.ACTOR_1LINE[a] for a in ACTORS])
    for a in FLOOR:
        yi = ys[ACTORS.index(a)]
        ax[1].annotate(f"floor: A {S.cell(a,'A')['recovery']:.3f} ≈ "
                       f"B {S.cell(a,'B')['recovery']:.3f} ≈ 0, nothing to lose",
                       xy=(S.cell(a, "B")["recovery"], yi - 0.12), xytext=(0.22, yi - 0.50),
                       fontsize=S.FS_ANNOT, color=S.INK, ha="left", va="center",
                       arrowprops=dict(arrowstyle="-", lw=0.5, color=S.INK2,
                                       shrinkA=1.0, shrinkB=3.5))
    h = [Line2D([], [], ls="none", marker=("D" if a == "C" else "o"), ms=4.4,
                mfc=S.ARMC[a], mec=S.SURFACE, mew=1.0, label=S.ARM_LONG[a]) for a in ARMS]
    fig.legend(handles=h, ncol=3, loc="lower center", bbox_to_anchor=(0.60, 0.010),
               fontsize=S.FS_LEGEND)
    fig.text(0.008, 0.020, f"n = A / B / C.   arm C (◆): {ATTR_TXT} attrition.",
             fontsize=S.FS_ANNOT, color=S.INK3, ha="left", va="bottom")
    return S.save(fig, "fig1_v3_dumbbell", S.TEXTWIDTH_IN)


if __name__ == "__main__":
    print("Figure 1 -- " + S.provenance_line())
    print(f"  floor-effect actors (computed from CIs, not asserted): {FLOOR}")
    print(f"  arm C attrition span (computed): {ATTR_TXT}")
    v1(); v2(); v3()
