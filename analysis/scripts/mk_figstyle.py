"""Shared style + data loader for every AAMAS figure.  Import, never copy.

RULE OBEYED BY EVERY mk_fig*.py: no manuscript number is typed into a plotting
script.  All of them call `figdata()`, which reads analysis/out/FIGDATA.json,
written by section [T28] of analysis/scripts/FINAL_TABLES.py from the frozen
snapshot in experiments/results/FROZEN/.  If a figure needs a quantity that is
not in that file, the fix is to add it to FINAL_TABLES.py and rerun -- not to
type it here.

TARGET GEOMETRY.  Measured from the official class, not assumed:
    \\columnwidth = 241.147pt = 3.337in   (aamas.cls, sigconf, after \\maketitle)
    \\textwidth   = 506.295pt = 7.004in   (figure*)
    body font    = 9pt
Reproduce with:  pdflatex on a stub that \\typeout{\\the\\columnwidth}.
"""
import json, os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT    = "/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols"
FIGDIR  = os.path.join(ROOT, "figures")
DATA    = os.path.join(ROOT, "analysis", "out", "FIGDATA.json")

COLWIDTH_PT   = 241.147          # \columnwidth, aamas.cls sigconf
TEXTWIDTH_PT  = 506.295          # \textwidth
COLWIDTH_IN   = COLWIDTH_PT / 72.27
TEXTWIDTH_IN  = TEXTWIDTH_PT / 72.27

# ---------------------------------------------------------------- typography
# Every size here is in points and is the size ON THE PAGE, because each figure
# is saved at its final printed width and inserted at [width=\columnwidth].
# The SMALLEST of these is the figure's minimum rendered font size; it is
# asserted at save time by `save()`.
FS_TICK   = 6.5
FS_LABEL  = 7.5
FS_LEGEND = 7.0
FS_ANNOT  = 6.5
FS_TITLE  = 8.0
FS_MIN    = 6.5

# ---------------------------------------------------------------- palette
# Okabe-Ito. Checked with the dataviz validator, categorical, --pairs all,
# light surface: lightness band PASS, chroma floor PASS, CVD separation PASS
# (worst adjacent pair deltaE 11.0 deutan / 8.6 tritan), normal-vision floor
# PASS (18.7), contrast vs surface PASS.  Arm identity is ALSO carried by
# position, by the A/B/C tick label, and by hatch on arm C -- never by hue
# alone.
ARMC = {"A": "#0072B2", "B": "#D55E00", "C": "#009E73"}
ARMHATCH = {"A": "", "B": "", "C": "///"}      # C = secondary, non-colour channel
INK      = "#1a1a1a"
INK2     = "#4d4d4d"
INK3     = "#767676"
GRID     = "#d9d9d9"
SURFACE  = "#ffffff"

ARM_LONG = {"A": "A  soft roles", "B": "B  no roles", "C": "C  enforced"}

# Short actor labels. The full model ids live in the caption and the README.
ACTOR_SHORT = {"gemma-4-31B-it": "gemma-4\n31B",
               "gpt-oss-120b": "gpt-oss\n120B",
               "Llama-3.3-70B-Instruct": "Llama-3.3\n70B"}
ACTOR_1LINE = {"gemma-4-31B-it": "gemma-4-31B",
               "gpt-oss-120b": "gpt-oss-120B",
               "Llama-3.3-70B-Instruct": "Llama-3.3-70B"}


def apply_rc():
    plt.rcParams.update({
        "pdf.fonttype": 42,          # TrueType: text stays real text, never traced
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans"],
        "font.size": FS_TICK,
        "axes.labelsize": FS_LABEL,
        "axes.titlesize": FS_TITLE,
        "xtick.labelsize": FS_TICK,
        "ytick.labelsize": FS_TICK,
        "legend.fontsize": FS_LEGEND,
        "axes.linewidth": 0.6,
        "axes.edgecolor": INK2,
        "axes.labelcolor": INK,
        "axes.titlecolor": INK,
        "text.color": INK,
        "xtick.color": INK2, "ytick.color": INK2,
        "xtick.labelcolor": INK, "ytick.labelcolor": INK,
        "xtick.major.width": 0.6, "ytick.major.width": 0.6,
        "xtick.major.size": 2.0,  "ytick.major.size": 2.0,
        "grid.color": GRID, "grid.linewidth": 0.5, "grid.linestyle": "-",
        "legend.frameon": False,
        "legend.handlelength": 1.2,
        "legend.handletextpad": 0.5,
        "legend.columnspacing": 1.0,
        "legend.borderaxespad": 0.2,
        "lines.linewidth": 1.2,
        "figure.dpi": 110,
        "savefig.dpi": 400,
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
    })


def clean(ax, grid_axis="y"):
    """Hairline recessive grid, no top/right spines, grid behind the marks."""
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    if grid_axis:
        ax.grid(True, axis=grid_axis, lw=0.5, color=GRID, zorder=0)
        ax.set_axisbelow(True)


_D = None
def figdata():
    """The ONLY numeric source a plotting script may read."""
    global _D
    if _D is None:
        with open(DATA) as f:
            _D = json.load(f)
    return _D


def cell(actor, arm):
    return figdata()["cells"][f"{actor}|{arm}"]


def provenance_line():
    p = figdata()["provenance"]
    shas = " ".join(f"{k.split('.')[0]}:{v['sha256'][:8]}" for k, v in sorted(p["files"].items()))
    return f"frozen {p['frozen_at'][:19]}Z  n={p['total_rows']}  {shas}"


def save(fig, stem, width_in):
    """Save PDF (for LaTeX) + PNG (for review) and verify the two hard rules:
    the figure is at its final printed width, and no text is below FS_MIN."""
    fig.set_size_inches(width_in, fig.get_size_inches()[1])
    got = fig.get_size_inches()[0]
    assert abs(got - width_in) < 1e-6, f"{stem}: width drifted to {got}in"

    small = []
    for ax in fig.get_axes():
        for t in ([ax.title, ax.xaxis.label, ax.yaxis.label]
                  + list(ax.get_xticklabels()) + list(ax.get_yticklabels())
                  + list(ax.texts)):
            if t.get_text() and t.get_size() < FS_MIN - 1e-9:
                small.append((t.get_text()[:28], t.get_size()))
    for t in fig.texts:
        if t.get_text() and t.get_size() < FS_MIN - 1e-9:
            small.append((t.get_text()[:28], t.get_size()))
    for ax in fig.get_axes():
        lg = ax.get_legend()
        if lg:
            for t in lg.get_texts():
                if t.get_size() < FS_MIN - 1e-9:
                    small.append((t.get_text()[:28], t.get_size()))
    assert not small, f"{stem}: text below {FS_MIN}pt: {small}"

    os.makedirs(FIGDIR, exist_ok=True)
    pdf = os.path.join(FIGDIR, stem + ".pdf")
    png = os.path.join(FIGDIR, stem + ".png")
    # bbox_inches is deliberately NOT 'tight': tight silently changes the width,
    # which would invalidate the point sizes above.
    fig.savefig(pdf)
    fig.savefig(png, dpi=400)
    plt.close(fig)
    print(f"  wrote {stem}.pdf / .png   {width_in:.3f}in wide   min font {FS_MIN}pt")
    return pdf
