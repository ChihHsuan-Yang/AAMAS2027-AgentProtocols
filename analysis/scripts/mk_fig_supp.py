# -*- coding: utf-8 -*-
"""SUPPLEMENT FIGURES S1, S2, S3, S4 -- the pictures behind four supplement sections.

Each figure carries one sentence of the supplement:

  S1  fig_supp_roles        Deleting the role clauses changes what the PLANNER
                            does; the Executor and Reviewer barely move.
  S2  fig_supp_verdicts     The role-free team recovers more because more of
                            its failed trajectories go on receiving verdicts;
                            per verdict received, the two teams recover alike.
  S3  fig_supp_robustness   No variant of the verdict-matched comparison puts
                            the role-free team ahead; and two of the three
                            pre-registered interaction nulls are uninformative
                            because the detectable effect exceeds the plausible one.
  S4  fig_supp_enforcement  Enforcement's accuracy effect flips sign between the
                            pre-registered scoring and the as-graded one; the
                            attrition that separates them is in the tick labels.

DATA.  No numeric literal in this file is a result.  Sources, all written by
repository scripts:
  * analysis/out/FINAL_TABLES_OUTPUT.txt  sections [T2], [T7], [T8], [T14]
    (FINAL_TABLES.py over the frozen snapshot), read the way mk_tables.py reads it;
  * analysis/out/FIGDATA_BF.json           verdict_curve (bf_numbers.py);
  * analysis/out/FIGDATA_GATE.json         verdict_robust_pooled (bf_gate.py);
  * paper/tables/prereg_endpoints.tex      the MDE column only, which mk_tables.py
    obtains by executing the power script; it is read back from the generated
    table because that script needs the raw trajectories.

STYLE.  mk_figstyle: Libertinus Sans when the TeX tree has it, the paper's
condition hues (purple role-structured, rose role-free, gold enforced), the
feedback-withheld condition hollow as in Figure 2 of the main paper.  Widths
are the printed widths (\\columnwidth or \\textwidth of aamas.cls); S.save()
asserts them and the minimum font size, and strips the PDF timestamp so a
regenerated figure is byte-identical.

Run:  python3 analysis/scripts/mk_fig_supp.py   -> figures/fig_supp_*.{pdf,png}
                                                   and paper/figures/fig_supp_*.pdf
"""
import json, os, re, shutil, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

import mk_figstyle as S

S.apply_rc()
FONT = S.use_paper_font()

OUT = os.path.join(S.ROOT, "analysis", "out")
CANON = os.path.join(OUT, "FINAL_TABLES_OUTPUT.txt")
PREREG_TEX = os.path.join(S.ROOT, "paper", "tables", "prereg_endpoints.tex")
ACTORS = ["gemma-4-31B-it", "gpt-oss-120b", "Llama-3.3-70B-Instruct"]
DOMAIN = {"omni": "Omni-MATH", "scibench": "SciBench"}
# Actor labels as the main paper's Table 1 prints them; the full ids are in the caption.
LABEL = {"gemma-4-31B-it": "gemma-4-31B", "gpt-oss-120b": "gpt-oss-120b",
         "Llama-3.3-70B-Instruct": "Llama-3.3-70B"}

# Condition styling.  Keys are the internal arm letters (never rendered).
COL = {"A": S.ARMC["A"], "B": S.ARMC["B"], "Bf": S.ARMC["B"], "C": S.ARMC["C"]}
LONG = {"A": "role-structured", "B": "role-free, feedback withheld",
        "Bf": "role-free, with feedback", "C": "structurally enforced"}
HOLLOW = {"B"}
FS_TEXT = 7.0            # row / tick labels (Libertinus runs small)
MS = 4.2                 # marker size, points (>= 8px at 400 dpi)


# ----------------------------------------------------------------- sources
def canonical():
    """FINAL_TABLES_OUTPUT.txt split into its [Tn] sections (as mk_tables.py)."""
    secs, cur = {}, None
    with open(CANON) as f:
        for line in f.read().splitlines():
            m = re.match(r"^\[(T\d+b?)\]", line)
            if m:
                cur = m.group(1); secs[cur] = []; continue
            if cur is not None:
                secs[cur].append(line)
    return secs


def t8_roles(secs):
    """[T8]: per-role share of first cycles in which the role asserts its own
    final answer, keyed (actor, arm) -> {planner, executor, reviewer}."""
    out = {}
    for line in secs["T8"]:
        m = re.match(r"^\s*(\S+)\s+(A|B|C|Cp)\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)\s*$", line)
        if m and m.group(1) in ACTORS:
            out[(m.group(1), m.group(2))] = dict(planner=float(m.group(4)), executor=float(m.group(5)),
                                                 reviewer=float(m.group(6)), n=int(m.group(3)))
    assert len(out) >= 6, "T8: expected a row per actor for A and B"
    return out


def t2_enforcement(secs):
    """[T2]: enforced minus role-structured final accuracy, both scorings, with
    95% bootstrap intervals.  Returns {scoring: {actor: (diff, lo, hi)}}."""
    out, scoring, block = {}, None, None
    for line in secs["T2"]:
        if "PREREG" in line and "---" in line:
            scoring = "prereg"
        elif "AS-GRADED" in line and "---" in line:
            scoring = "graded"
        elif re.match(r"^\s*(B-A|C-A):\s*$", line):
            block = line.strip().rstrip(":")
        else:
            m = re.match(r"^\s*(\S+)\s+([+-][\d.]+)\s+\[([+-][\d.]+),([+-][\d.]+)\]\s+n=(\d+)", line)
            if m and block == "C-A" and m.group(1) in ACTORS:
                out.setdefault(scoring, {})[m.group(1)] = (float(m.group(2)), float(m.group(3)), float(m.group(4)))
    assert set(out) == {"prereg", "graded"} and all(len(v) == 3 for v in out.values()), "T2: C-A rows missing"
    return out


def t7_attrition(secs):
    """[T7]: share of enforced trajectories that never finish, per actor."""
    out = {}
    for line in secs["T7"]:
        m = re.match(r"^\s*(\S+)\s+C\s+\d+\s+[\d.]+\s+[\d.]+\s+([\d.]+)", line)
        if m and m.group(1) in ACTORS:
            out[m.group(1)] = float(m.group(2))
    assert len(out) == 3, "T7: expected the enforced row for each actor"
    return out


def t14_did(secs):
    """[T14]: P4 difference-in-differences with 95% intervals, in table order."""
    rows = []
    for line in secs["T14"]:
        m = re.match(r"^\s*(\S+)\s+minus\s+(\S+)\s+([+-][\d.]+)\s+\[([+-][\d.]+),([+-][\d.]+)\]\s+p=([\d.e+-]+)", line)
        if m and m.group(1) in ACTORS:
            rows.append((m.group(1), m.group(2), float(m.group(3)), float(m.group(4)), float(m.group(5)), float(m.group(6))))
    assert len(rows) == 3, "T14: expected three contrasts"
    return rows


def prereg_mde():
    """MDE_80% per P4 contrast, from the generated pre-registration table.
    Rows look like:  \\quad gpt-oss-120b $-$ gemma-4-31B & ... & $0.0325$ & informative \\\\"""
    out = {}
    with open(PREREG_TEX) as f:
        for line in f:
            m = re.match(r"^\\quad\s+(\S+)\s+\$-\$\s+(\S+)\s+&.*&\s*\$([\d.]+)\$\s*&\s*(\w+)\s*\\\\", line)
            if m:
                out[(m.group(1), m.group(2))] = (float(m.group(3)), m.group(4))
    assert len(out) == 3, f"prereg_endpoints.tex: parsed {len(out)} MDE rows, expected 3"
    return out


def mde_for(mde, x, y):
    """Match the table's shortened actor labels to the canonical ids by prefix."""
    hits = [v for (kx, ky), v in mde.items() if {kx[:9], ky[:9]} == {x[:9], y[:9]}]
    assert len(hits) == 1, (x, y, sorted(mde))
    return hits[0]


with open(os.path.join(OUT, "FIGDATA_BF.json")) as _f:
    DB = json.load(_f)
with open(os.path.join(OUT, "FIGDATA_GATE.json")) as _f:
    DG = json.load(_f)
SECS = canonical()


def publish(stem):
    """S.save() refreshes paper/figures/ only for a file already there; a new
    figure is placed there once, explicitly, so LaTeX finds it."""
    src = os.path.join(S.FIGDIR, stem + ".pdf")
    dst = os.path.join(S.ROOT, "paper", "figures", stem + ".pdf")
    if not os.path.exists(dst):
        os.makedirs(os.path.dirname(dst), exist_ok=True)   # absent in a fresh checkout
        shutil.copyfile(src, dst)
        print(f"  placed paper/figures/{stem}.pdf")


def marker_kw(arm, hollow=None):
    hollow = (arm in HOLLOW) if hollow is None else hollow
    if hollow:
        return dict(marker="o", ms=MS, mfc=S.SURFACE, mec=COL[arm], mew=0.9)
    return dict(marker="o", ms=MS, mfc=COL[arm], mec=S.SURFACE, mew=0.6)


# ================================================================ S1: roles
def fig_roles(stem="fig_supp_roles"):
    roles = [("planner", "Planner"), ("executor", "Executor"), ("reviewer", "Reviewer")]
    T8 = t8_roles(SECS)
    W, H = S.COLWIDTH_IN, 1.55
    L0, GAP, PW, BOT, PH = 0.52, 0.10, 0.82, 0.30, 0.78
    fig = plt.figure(figsize=(W, H))
    for i, actor in enumerate(ACTORS):
        left = L0 + i * (PW + GAP)
        ax = fig.add_axes([left / W, BOT / H, PW / W, PH / H])
        S.clean(ax, grid_axis="x")
        ys = [2, 1, 0]
        for (key, name), y in zip(roles, ys):
            a, b = T8[(actor, "A")][key], T8[(actor, "B")][key]
            ax.plot([a, b], [y, y], color=S.INK3, lw=1.0, zorder=2, solid_capstyle="round")
            ax.plot([a], [y], ls="none", zorder=4, **marker_kw("A"))
            ax.plot([b], [y], ls="none", zorder=4, **marker_kw("B"))
            if key == "planner":     # the headline row carries its two values
                ax.text(a + 0.03, y + 0.30, f"{a:.3f}", fontsize=S.FS_ANNOT, color=COL["A"],
                        ha="left", va="bottom")
                ax.text(b - 0.03, y + 0.30, f"{b:.3f}", fontsize=S.FS_ANNOT, color=COL["B"],
                        ha="right", va="bottom")
        ax.set_xlim(-0.04, 1.04); ax.set_ylim(-0.6, 2.6)
        ax.set_xticks([0, 0.5, 1]); ax.set_xticklabels(["0", "0.5", "1"], fontsize=S.FS_TICK)
        ax.set_yticks(ys)
        if i == 0:
            ax.set_yticklabels([n for _, n in roles], fontsize=FS_TEXT)
        else:
            ax.set_yticklabels([])
            ax.tick_params(axis="y", length=0)
        ax.set_title(LABEL[actor], fontsize=S.FS_TITLE, pad=3, color=S.INK)
        ax.tick_params(axis="x", pad=1.5)
    fig.text((L0 + 1.5 * PW + GAP) / W, 0.03 / H,
             "share of first cycles in which the agent asserts its own final answer",
             ha="center", va="bottom", fontsize=S.FS_LABEL, color=S.INK)
    h = [Line2D([], [], ls="none", label=LONG["A"], **marker_kw("A")),
         Line2D([], [], ls="none", label=LONG["B"], **marker_kw("B"))]
    fig.legend(handles=h, ncol=2, loc="upper center", bbox_to_anchor=(0.56, 1.01),
               fontsize=FS_TEXT, handletextpad=0.3, columnspacing=1.4, frameon=False)
    S.save(fig, stem, W); publish(stem)


# ============================================================ S2: verdicts
def fig_verdict_curve(stem="fig_supp_verdicts"):
    VC = DB["verdict_curve"]
    groups = [("omni", a) for a in ACTORS] + [("scibench", a) for a in ACTORS[:2]]
    ks = [1, 2, 3, 4, 5, 6]
    W = S.TEXTWIDTH_IN
    L0, R0, GAP, TOP, BOT, VGAP = 0.50, 0.08, 0.16, 0.42, 0.36, 0.30
    PH = 0.95
    H = BOT + 2 * PH + VGAP + TOP
    PW = (W - L0 - R0 - 4 * GAP) / 5
    fig = plt.figure(figsize=(W, H))
    style = {"A": dict(color=COL["A"], ls="-"), "Bf": dict(color=COL["Bf"], ls="-"),
             "B": dict(color=COL["B"], ls=(0, (2.2, 1.6)))}
    for gi, (dom, actor) in enumerate(groups):
        left = L0 + gi * (PW + GAP)
        ax_top = fig.add_axes([left / W, (BOT + PH + VGAP) / H, PW / W, PH / H])
        ax_bot = fig.add_axes([left / W, BOT / H, PW / W, PH / H])
        for ax in (ax_top, ax_bot):
            S.clean(ax, grid_axis="y")
            ax.set_xlim(0.7, 6.3); ax.set_xticks(ks)
            ax.tick_params(axis="both", pad=1.5)
        for arm in ("B", "Bf", "A"):
            v = VC.get(f"{dom}|{actor}|{arm}")
            if v is None:
                continue
            n = v["n_fpw"]
            reach = [v["reached"][str(k)] / n for k in ks]
            cum = [v["cum"][str(k)] for k in ks]
            ax_top.plot(ks, reach, lw=1.2, zorder=3, **style[arm])
            ax_top.plot(ks, reach, ls="none", zorder=4, **marker_kw(arm))
            ax_bot.plot(ks, cum, lw=1.2, zorder=3, **style[arm])
            ax_bot.plot(ks, cum, ls="none", zorder=4, **marker_kw(arm))
            # End labels sit above the curve; the withheld-feedback curve, usually
            # the lowest, is labelled below it, or to the left when it hugs zero.
            dy, x, va = 0.035, 5.85, "bottom"
            if arm == "B":
                dy, va = -0.035, "top"
                if cum[-1] < 0.06:
                    dy, x, va = 0.035, 4.9, "bottom"
            ax_bot.text(x, cum[-1] + dy, f"{cum[-1]:.2f}", fontsize=S.FS_ANNOT, color=COL[arm],
                        ha="right", va=va, clip_on=False)
        ax_top.set_ylim(0, 1.06); ax_top.set_yticks([0, 0.5, 1.0])
        ax_bot.set_ylim(-0.02, 0.72); ax_bot.set_yticks([0, 0.2, 0.4, 0.6])
        ax_top.set_xticklabels([]); ax_top.tick_params(axis="x", length=0)
        ax_top.set_title(f"{DOMAIN[dom]}, {LABEL[actor]}", fontsize=S.FS_TITLE, pad=3, color=S.INK)
        if gi == 0:
            ax_top.set_ylabel("share receiving\na k-th verdict", fontsize=S.FS_LABEL)
            ax_bot.set_ylabel("cumulative recovery\nby the k-th verdict", fontsize=S.FS_LABEL)
        else:
            ax_top.set_yticklabels([]); ax_bot.set_yticklabels([])
            ax_top.tick_params(axis="y", length=0); ax_bot.tick_params(axis="y", length=0)
    fig.text(0.5 + (L0 - R0) / (2 * W), 0.04 / H, "k, the number of evaluator verdicts received",
             ha="center", va="bottom", fontsize=S.FS_LABEL, color=S.INK)
    h = [Line2D([], [], lw=1.2, label=LONG[a], **style[a], **marker_kw(a)) for a in ("A", "Bf", "B")]
    fig.legend(handles=h, ncol=3, loc="upper center", bbox_to_anchor=(0.5 + (L0 - R0) / (2 * W), 1.005),
               fontsize=FS_TEXT, handlelength=2.2, handletextpad=0.5, columnspacing=1.8, frameon=False)
    S.save(fig, stem, W); publish(stem)


# ========================================================== S3: robustness
VARIANTS = [("main", "all paired\nproblems"),
            ("informative", "two or more\nRS verdicts"),
            ("symmetric", "both cut at\nsmaller count"),
            ("symmetric_informative", "both cut,\ntwo or more"),
            ("recoded", "scoring defect\nrecoded"),
            ("recoded_informative", "recoded,\ntwo or more")]


def bar_kw(arm, hollow=False, hatch=""):
    if hollow:
        return dict(facecolor=S.SURFACE, edgecolor=COL[arm], linewidth=0.9)
    return dict(facecolor=COL[arm], edgecolor=S.SURFACE if hatch else COL[arm], linewidth=0.0, hatch=hatch)


def errbar(ax, x, m, lo, hi):
    ax.errorbar(x, m, yerr=[[m - lo], [hi - m]], fmt="none", ecolor=S.INK2, elinewidth=0.6,
                capsize=1.4, capthick=0.6, zorder=5)


def fig_robustness(stem="fig_supp_robustness"):
    did = t14_did(SECS)
    mde = prereg_mde()
    W = S.TEXTWIDTH_IN
    LA, WA = 0.55, 3.75            # panel a: left edge, plot width (inches)
    LB, WB = 5.00, 1.98            # panel b
    BOT, PH, TOP = 0.62, 1.42, 0.42
    H = BOT + PH + TOP
    fig = plt.figure(figsize=(W, H))

    # --- (a) verdict-matched, six variants x {all cells, without Llama-3.3}
    ax = fig.add_axes([LA / W, BOT / H, WA / W, PH / H])
    S.clean(ax, grid_axis="y")
    band = 0.05
    ax.axhspan(-band, band, color=S.GRID, alpha=0.55, lw=0, zorder=0)
    ax.axhline(0, color=S.INK3, lw=0.6, ls=(0, (2, 2)), zorder=1)
    w = 0.34
    for i, (key, label) in enumerate(VARIANTS):
        for sub, dx, hollow in (("all", -w / 2 - 0.02, False), ("noLlama", w / 2 + 0.02, True)):
            r = DG[f"verdict_robust_pooled|{key}|{sub}"]
            lo, hi = r["ci95"]
            ax.bar(i + dx, r["diff"], w, zorder=3, **bar_kw("A", hollow=hollow))
            errbar(ax, i + dx, r["diff"], lo, hi)
    ax.set_xticks(range(len(VARIANTS))); ax.set_xticklabels([l for _, l in VARIANTS], fontsize=S.FS_TICK)
    ax.set_xlim(-0.6, len(VARIANTS) - 0.4)
    ax.set_ylim(-0.08, 0.10); ax.set_yticks([-0.05, 0, 0.05, 0.10])
    ax.set_yticklabels(["−0.05", "0", "+0.05", "+0.10"], fontsize=S.FS_TICK)
    ax.set_ylabel("recovery difference,\nRS minus RF, verdict-matched", fontsize=S.FS_LABEL)
    ax.text(len(VARIANTS) - 0.45, 0.097, "favors roles", fontsize=S.FS_ANNOT, color=S.INK2, ha="right", va="top")
    ax.text(len(VARIANTS) - 0.45, -0.077, "favors role-free", fontsize=S.FS_ANNOT, color=S.INK2, ha="right", va="bottom")
    ax.set_title("a   The verdict-matched contrast, six variants", fontsize=S.FS_TITLE,
                 loc="left", pad=4, color=S.INK, fontweight="bold")
    ax.tick_params(axis="both", pad=1.5)

    # --- (b) P4 interaction, three contrasts, with the detectable size
    ax = fig.add_axes([LB / W, BOT / H, WB / W, PH / H])
    S.clean(ax, grid_axis="y")
    ax.axhline(0, color=S.INK3, lw=0.6, ls=(0, (2, 2)), zorder=1)
    labels = []
    for i, (x, y_, d, lo, hi, p) in enumerate(did):
        m, verdict = mde_for(mde, x, y_)
        ax.bar(i, 2 * m, 0.62, bottom=-m, color=COL["C"], alpha=0.28, lw=0, zorder=2)
        ax.bar(i, d, 0.34, zorder=3, **bar_kw("C"))
        errbar(ax, i, d, lo, hi)
        labels.append(f"{LABEL[x].split(chr(45))[0]} vs\n{LABEL[y_].split(chr(45))[0]}\n({verdict})")
    ax.set_xticks(range(3)); ax.set_xticklabels(labels, fontsize=S.FS_TICK)
    ax.set_xlim(-0.6, 2.6)
    ax.set_ylim(-0.10, 0.10); ax.set_yticks([-0.05, 0, 0.05, 0.10])
    ax.set_yticklabels(["−0.05", "0", "+0.05", "+0.10"], fontsize=S.FS_TICK)
    ax.set_ylabel("difference between two actors\nin enforcement's accuracy effect", fontsize=S.FS_LABEL)
    ax.set_title("b   Pre-registered interaction P4", fontsize=S.FS_TITLE, loc="left", pad=4,
                 color=S.INK, fontweight="bold")
    ax.tick_params(axis="both", pad=1.5)

    h = [Patch(label="all five cells", **bar_kw("A")),
         Patch(label="without Llama-3.3", **bar_kw("A", hollow=True)),
         Patch(facecolor=S.GRID, alpha=0.55, lw=0, label="±0.05, the equivalence margin (a)"),
         Patch(facecolor=COL["C"], alpha=0.28, lw=0, label="smallest interaction detectable at 80% power (b)")]
    fig.legend(handles=h, ncol=4, loc="upper center", bbox_to_anchor=(0.52, 1.005), fontsize=FS_TEXT,
               handlelength=1.1, handleheight=0.8, handletextpad=0.4, columnspacing=1.6, frameon=False)
    S.save(fig, stem, W); publish(stem)


# ======================================================= S4: enforcement
def fig_enforcement(stem="fig_supp_enforcement"):
    E = t2_enforcement(SECS)
    AT = t7_attrition(SECS)
    W, H = S.COLWIDTH_IN, 1.72
    LA, WA = 0.52, 2.72
    BOT, PH = 0.48, 0.92
    fig = plt.figure(figsize=(W, H))
    ax = fig.add_axes([LA / W, BOT / H, WA / W, PH / H])
    S.clean(ax, grid_axis="y")
    ax.axhline(0, color=S.INK3, lw=0.6, ls=(0, (2, 2)), zorder=1)
    w = 0.30
    for i, actor in enumerate(ACTORS):
        for scoring, dx, hollow in (("prereg", -w / 2 - 0.02, False), ("graded", w / 2 + 0.02, True)):
            d, lo, hi = E[scoring][actor]
            ax.bar(i + dx, d, w, zorder=3, **bar_kw("C", hollow=hollow))
            errbar(ax, i + dx, d, lo, hi)
    ax.set_xticks(range(3))
    ax.set_xticklabels([f"{LABEL[a]}\n{100 * AT[a]:.1f}% never finish" for a in ACTORS], fontsize=S.FS_TICK)
    ax.set_xlim(-0.6, 2.6)
    ax.set_ylim(-0.06, 0.10); ax.set_yticks([-0.05, 0, 0.05, 0.10])
    ax.set_yticklabels(["−0.05", "0", "+0.05", "+0.10"], fontsize=S.FS_TICK)
    ax.set_ylabel("final accuracy,\nSE minus RS", fontsize=S.FS_LABEL)
    ax.tick_params(axis="both", pad=1.5)
    h = [Patch(label="pre-registered scoring (unfinished = incorrect)", **bar_kw("C")),
         Patch(label="as graded (unfinished dropped)", **bar_kw("C", hollow=True))]
    fig.legend(handles=h, ncol=1, loc="upper left", bbox_to_anchor=(0.02, 1.02), fontsize=S.FS_ANNOT,
               handlelength=1.1, handleheight=0.8, handletextpad=0.3, labelspacing=0.2, frameon=False)
    S.save(fig, stem, W); publish(stem)


if __name__ == "__main__":
    print("Supplement figures -- font: " + FONT)
    fig_roles()
    fig_verdict_curve()
    fig_robustness()
    fig_enforcement()
