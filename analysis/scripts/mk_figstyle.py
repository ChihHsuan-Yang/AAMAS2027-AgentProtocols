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
import json, os, shutil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Repository root, resolved from this file (analysis/scripts/mk_figstyle.py)
# so the scripts run from any checkout; a hard-coded path only ran on one
# machine.
ROOT    = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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
# Deep purple / rose / warm gold (2026-10-04; replaced Okabe-Ito blue/orange/
# green at the PI's request for a pink-purple family).  Checked with the
# dataviz validator, categorical, --pairs all, light surface: lightness band
# PASS, chroma floor PASS, CVD separation PASS (worst pair gold-rose deltaE
# 15.1 deutan / 8.1 tritan; purple-rose 18.8 protan / 27.7 tritan),
# normal-vision floor PASS (worst 18.8; purple-rose 25.5), contrast vs
# surface: purple and rose PASS, gold 2.43:1 (WARN -- relief is the hatch,
# the tick label and the legend).  A third colour INSIDE the pink-purple
# family (lilac, plum, magenta) fails the normal-vision floor against one of
# the other two in every variant tried, so the supporting condition takes a
# warm accent instead.  Arm identity is ALSO carried by position, by the
# tick label, and by hatch on arm C -- never by hue alone.
ARMC = {"A": "#5B3F8C", "B": "#D4689A", "C": "#D8973C"}
ARMHATCH = {"A": "", "B": "", "C": "///"}      # C = secondary, non-colour channel
# Neutrals: slate rather than pure black (text 11.2:1, secondary 6.5:1,
# tertiary 4.6:1 on white -- every text colour clears 4.5:1).
INK      = "#3A3A4A"
INK2     = "#5C5C6E"
INK3     = "#74747E"
GRID     = "#E6E6EE"
SURFACE  = "#ffffff"

# ---------------------------------------------------------------- terminology
# BINDING: paper/TERMINOLOGY.md.  No figure may print "Arm A/B/C" -- a reader
# who meets "Arm B" carries an arbitrary mapping for eight pages.  The internal
# letters stay as DICT KEYS (stable identifiers that match the data columns and
# FIGDATA keys); only these strings are ever rendered.
#
# A pre-existing violation this replaced: every figure built before 2026-10-01
# printed "A soft roles / B no roles / C enforced", and `pdftotext` finds the
# bare letters in 7 of 10 shipped PDFs, including the one the manuscript
# includes.  Checked with the tool rather than by reading the source, because
# the source spells the label across a dict and an f-string.
ARM_LONG = {"A": "role-structured", "B": "role-free", "C": "structurally enforced"}
# Short forms for tick labels, where the long name will not fit.  Still never a
# bare letter -- a truncation that reads as a code defeats the point.
ARM_SHORT = {"A": "role-\nstructured", "B": "role-\nfree", "C": "structurally\nenforced"}
ARM_TICK  = {"A": "role-structured", "B": "role-free", "C": "enforced"}


def assert_no_arm_codes(*strings):
    """Fail the build if a rendered string carries a bare arm code.

    Written to FAIL on the old labels first (`A  soft roles`, `arm B`), so the
    check is known to discriminate rather than merely passing on good input.
    """
    import re as _re
    # Kept in sync with scripts/check_terminology_pdfs.py, which is the
    # pre-freeze gate over shipped PDFs.  The comparison forms below were
    # added after a real miss: fig1_v1_grouped's LEGEND was fixed while its
    # annotation still read "A 0.014 = B 0.015, but C 0.139", and the
    # first version of this pattern saw neither.
    bad = _re.compile(
        r"\b[Aa]rm\s*~?\s*[ABC]\b"
        r"|(?<![A-Za-z])[ABC]\s+(?:soft roles|no roles|enforced)\b"
        r"|(?<![A-Za-z])[ABC]\s+[\d.]+\s*(?:[=\u2248<>]|vs\.?\s)"
        r"|(?<![A-Za-z])[ABC]\s*(?:[=\u2248]|vs\.?\s)\s*[ABC]?\s*\d"
        r"|(?<![A-Za-z])but\s+[ABC]\s+\d"
        r"|(?<![A-Za-z])[ABC]\s*/\s*[ABC]\s*/\s*[ABC](?![A-Za-z])")
    hits = [t for t in strings if t and bad.search(str(t))]
    if hits:
        raise AssertionError(f"arm code in rendered text (TERMINOLOGY.md): {hits}")
    return True

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
        "grid.color": GRID, "grid.linewidth": 0.5, "grid.linestyle": (0, (3, 2)),
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


PAPER_FONT = "Libertinus Sans"


def use_paper_font():
    """Opt-in: set figure text in Libertinus Sans, the sans companion of the
    Libertine face the ACM/AAMAS class sets the body in.

    The font is read from the local TeX installation (kpsewhich), never shipped
    in this repository. Its OpenType files carry CFF outlines, which
    matplotlib embeds with a font-type mismatch that some PDF tools reject, so
    each face is converted once to TrueType outlines (fontTools, a matplotlib
    dependency) in a cache directory outside the repository; the figure PDF
    then embeds a clean TrueType subset. Conversion is deterministic, so a
    regenerated figure stays byte-identical. Without the font this falls back
    to the default face and says so; it never fails the build.
    Returns the family name in use.
    """
    import subprocess, tempfile
    from matplotlib import font_manager as fm
    cache = os.path.join(tempfile.gettempdir(), "aamas_fig_fonts")
    os.makedirs(cache, exist_ok=True)
    faces = []
    for face in ("Regular", "Bold", "Italic"):
        name = f"LibertinusSans-{face}"
        ttf = os.path.join(cache, name + ".ttf")
        if not os.path.exists(ttf):
            try:
                otf = subprocess.run(["kpsewhich", name + ".otf"], capture_output=True,
                                     text=True).stdout.strip()
            except OSError:
                otf = ""
            if not otf:
                print(f"  [font] {name}.otf not found in the TeX tree; using {plt.rcParams['font.sans-serif'][0]}")
                return plt.rcParams["font.sans-serif"][0]
            _otf_to_ttf(otf, ttf)
        faces.append(ttf)
    for f in faces:
        fm.fontManager.addfont(f)
    plt.rcParams.update({
        "font.sans-serif": [PAPER_FONT, "DejaVu Sans"],
        "mathtext.fontset": "custom", "mathtext.rm": PAPER_FONT,
        "mathtext.it": PAPER_FONT + ":italic", "mathtext.bf": PAPER_FONT + ":bold",
    })
    return PAPER_FONT


def _otf_to_ttf(src, dst):
    """CFF outlines -> quadratic TrueType outlines (fontTools cu2qu)."""
    from fontTools.ttLib import TTFont, newTable
    from fontTools.pens.cu2quPen import Cu2QuPen
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    f = TTFont(src, recalcTimestamp=False)   # keep head.modified: byte-identical output
    order, gset, glyf = f.getGlyphOrder(), f.getGlyphSet(), {}
    for g in order:
        pen = TTGlyphPen(gset)
        gset[g].draw(Cu2QuPen(pen, 1.0, reverse_direction=True))
        glyf[g] = pen.glyph()
    f["loca"] = newTable("loca")
    f["glyf"] = t = newTable("glyf")
    t.glyphOrder, t.glyphs = order, glyf
    del f["CFF "]
    if "VORG" in f:
        del f["VORG"]
    f["maxp"] = m = newTable("maxp")
    m.tableVersion = 0x00010000
    m.maxZones = 1
    for k in ("maxTwilightPoints", "maxStorage", "maxFunctionDefs", "maxInstructionDefs",
              "maxStackElements", "maxSizeOfInstructions", "maxComponentElements"):
        setattr(m, k, 0)
    post = f["post"]
    post.formatType, post.extraNames, post.mapping, post.glyphOrder = 2.0, [], {}, order
    f["head"].glyphDataFormat = 0
    f.sfntVersion = "\x00\x01\x00\x00"
    f.save(dst)


def clean(ax, grid_axis="y"):
    """Hairline recessive grid, no top/right spines, grid behind the marks."""
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    if grid_axis:
        ax.grid(True, axis=grid_axis, lw=0.5, color=GRID, ls=(0, (3, 2)), zorder=0)
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

    # TERMINOLOGY GATE (paper/TERMINOLOGY.md).  Collect every string this
    # figure actually renders and refuse to write a file that prints an arm
    # code.  Gathered from the artist objects rather than from the source, so
    # a label assembled inside an f-string is still caught.
    rendered = []
    for ax in fig.get_axes():
        rendered += [ax.get_title(), ax.get_xlabel(), ax.get_ylabel()]
        rendered += [t.get_text() for t in ax.get_xticklabels()]
        rendered += [t.get_text() for t in ax.get_yticklabels()]
        rendered += [t.get_text() for t in ax.texts]
        lg = ax.get_legend()
        if lg:
            rendered += [t.get_text() for t in lg.get_texts()]
    rendered += [t.get_text() for t in fig.texts]
    for lg in getattr(fig, "legends", []):
        rendered += [t.get_text() for t in lg.get_texts()]
    assert_no_arm_codes(*rendered)

    os.makedirs(FIGDIR, exist_ok=True)
    pdf = os.path.join(FIGDIR, stem + ".pdf")
    png = os.path.join(FIGDIR, stem + ".png")
    # bbox_inches is deliberately NOT 'tight': tight silently changes the width,
    # which would invalidate the point sizes above.
    # metadata CreationDate=None strips the wall-clock stamp matplotlib
    # otherwise embeds. Without it a figure PDF has a different sha256 on
    # every run even when nothing changed, which makes the hash recorded in
    # FINAL_FREEZE.json useless: it cannot distinguish "the figure changed"
    # from "the figure was regenerated". With it, regeneration from the same
    # frozen data is byte-identical and a changed hash means changed data.
    fig.savefig(pdf, metadata={"CreationDate": None})
    fig.savefig(png, dpi=400)
    plt.close(fig)

    # Keep the CONSUMER's copy in step with the producer's.
    #
    # LaTeX resolves \includegraphics against paper/figures/, not here. For a
    # figure the paper ships, regenerating it and forgetting the copy leaves
    # the PDF carrying the OLD image while every check inspects the new one:
    # that is exactly how a stale fig1_v1_grouped.pdf kept printing bare
    # condition codes inside paper/figures/ while the terminology gate,
    # reading figures/, reported all clean.
    #
    # Only files ALREADY there are refreshed: paper/figures/ holds what the
    # manuscript uses, and a draft variant must not land in it by being
    # generated.
    consumer = os.path.join(os.path.dirname(FIGDIR), "paper", "figures", stem + ".pdf")
    if os.path.exists(consumer):
        shutil.copyfile(pdf, consumer)
        print(f"  synced paper/figures/{stem}.pdf (the copy LaTeX actually uses)")

    print(f"  wrote {stem}.pdf / .png   {width_in:.3f}in wide   min font {FS_MIN}pt")
    return pdf
