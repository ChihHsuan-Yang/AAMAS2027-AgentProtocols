#!/usr/bin/env python3
"""Verify the figure deliverables: no hand-typed numbers, no arm codes, vector text.

Three independent checks, each run against the SHIPPED PDF rather than the
source, because the source spells labels across f-strings and dicts:

  1. NUMBER TRACING  every number in the rendered PDF must be reproducible
     from a field of analysis/out/FIGDATA.json at one of the precisions the
     figures use.  Structural scale marks (axis ticks, model sizes) are
     allow-listed explicitly and the list is printed, so it cannot quietly
     grow to cover a real result.
  2. TERMINOLOGY     no "Arm A/B/C" in rendered text (paper/TERMINOLOGY.md).
  3. VECTOR TEXT     no raster image objects; text must be extractable.

SELF-TEST.  `--selftest` plants a number that is NOT in FIGDATA into a copy of
a real figure and asserts the audit flags it.  Without this the audit is only
known to pass on data it was written against -- and in fact an earlier version
of this check returned a clean result for a PDF THAT DID NOT EXIST, because a
failed build left no file and the reader treated absence as zero findings.
Missing files and empty text now abort instead of passing.

Usage:
  python3 analysis/scripts/check_figures.py [--selftest]
"""
import json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOT = "/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols"
FIGDIR = os.path.join(ROOT, "figures")
DATA = os.path.join(ROOT, "analysis", "out", "FIGDATA.json")

FIGURES = ["fig1_v1_story", "fig1_v2_story",
           "fig2_v1_xdomain", "fig2_v2_xdomain", "figS1_conditions"]

# Axis ticks, proportion bounds and model-name digits. Deliberately small and
# printed by the runner: an allow-list that absorbs a real number is the
# failure mode this check exists to prevent.
STRUCTURAL = {"0", "1", "2", "3", "4", "5", "6", "0.0", "0.5", "1.0",
              "0.2", "0.4", "31", "120", "3.3", "70", "4", "2"}

ARMCODE = re.compile(r"\b[Aa]rm\s*~?\s*[ABC]\b"
                     r"|(?<![A-Za-z])[ABC]\s+(?:soft roles|no roles|enforced)\b")
NUM = re.compile(r"\d+\.\d+|\d+e[-+]?\d+|\b\d+\b")


def traceable():
    D = json.load(open(DATA))
    ok = set()

    def add(v):
        for f in ("%.2f", "%.3f", "%.4f", "%.0e", "%d"):
            try: ok.add((f % v).strip())
            except Exception: pass
    for c in D["cells"].values():
        for fld in ("firstpass", "recovery", "cycles", "submissions",
                    "revising", "frozen_ans", "attrition"):
            if fld in c: add(c[fld])
        for fld in ("n", "n_judged", "n_fpw", "n_graded"): add(c[fld])
    for p in D["paired_recovery"].values():
        for fld in ("p", "n", "x_only", "y_only", "both_rec"): add(p[fld])
        # PAIRED recovery rates and their difference are derived from the
        # transition table at render time (Figure 2 draws paired, not
        # marginal), so the tracer must admit the same derivation.
        ra = (p["both_rec"] + p["x_only"]) / p["n"]
        rb = (p["both_rec"] + p["y_only"]) / p["n"]
        for v in (ra, rb, rb - ra, abs(rb - ra)): add(v)
    # SciBench, exported by [T28b] with the population named in every key.
    for sb in D.get("scibench", {}).values():
        for v in sb.values(): add(v)
        for pair in (("recovery_paired_B", "recovery_paired_A"),
                     ("firstpass_marginal_B", "firstpass_marginal_A"),
                     ("recovery_marginal_B", "recovery_marginal_A")):
            d_ = sb[pair[0]] - sb[pair[1]]
            add(d_); add(abs(d_))
    for m in D["mechanical"].values(): add(m["functional_collapse"])
    add(D["max_cycles"])
    for k in ("max_outer_rounds", "inner_rounds"): add(D["budget"][k])
    return ok


def text_of(stem):
    path = os.path.join(FIGDIR, stem + ".pdf")
    if not os.path.exists(path):
        raise SystemExit(f"ABORT: {path} does not exist. A missing figure is "
                         f"not a passing figure.")
    t = subprocess.run(["pdftotext", path, "-"], capture_output=True,
                       text=True).stdout
    if not t.strip():
        raise SystemExit(f"ABORT: {stem}.pdf yielded no extractable text "
                         f"(outlined fonts? rasterized?).")
    return path, t


def check(stem, ok, verbose=True):
    path, txt = text_of(stem)
    raw = open(path, "rb").read()
    untraced = [n for n in NUM.findall(txt)
                if n not in ok and n not in STRUCTURAL]
    arms = ARMCODE.findall(txt)
    images = len(re.findall(rb"/Subtype\s*/Image", raw))
    fonts = len(re.findall(rb"/FontFile", raw))
    if verbose:
        print(f"  {stem}")
        print(f"    numbers untraced to FIGDATA : {sorted(set(untraced)) or 'none'}")
        print(f"    arm codes in rendered text  : {sorted(set(arms)) or 'none'}")
        print(f"    raster image objects        : {images}")
        print(f"    embedded font programs      : {fonts}")
    return not untraced and not arms and images == 0 and fonts > 0


def selftest(ok):
    """Plant an untraceable number in a real figure; the audit must catch it."""
    src = os.path.join(ROOT, "analysis", "scripts", "mk_figS1_conditions.py")
    dst = os.path.join(ROOT, "analysis", "scripts", "_selftest_fig.py")
    s = open(src).read()
    planted = "0.7349"
    assert planted not in ok, "pick a value absent from FIGDATA"
    s = s.replace('"organization\\ncollapse"', f'"organization {planted}\\ncollapse"')
    s = s.replace('"figS1_conditions", S.COLWIDTH_IN', '"_selftest_fig", S.COLWIDTH_IN')
    open(dst, "w").write(s)
    try:
        r = subprocess.run([sys.executable, dst], capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit("SELFTEST ABORT: planted figure failed to build; "
                             "a control that did not run proves nothing.\n"
                             + r.stderr[-400:])
        caught = not check("_selftest_fig", ok, verbose=False)
        print(f"  planted {planted} into a real figure -> "
              f"{'CAUGHT (audit discriminates)' if caught else 'MISSED (AUDIT IS VOID)'}")
        return caught
    finally:
        for p in (dst, os.path.join(FIGDIR, "_selftest_fig.pdf"),
                  os.path.join(FIGDIR, "_selftest_fig.png")):
            if os.path.exists(p): os.remove(p)


if __name__ == "__main__":
    ok = traceable()
    print(f"FIGDATA provides {len(ok)} distinct renderable number strings.")
    print(f"Structural allow-list ({len(STRUCTURAL)}): {sorted(STRUCTURAL)}\n")
    if "--selftest" in sys.argv:
        print("SELF-TEST (does this audit detect a hand-typed number?)")
        if not selftest(ok):
            raise SystemExit(1)
        print()
    print("FIGURES")
    allok = all(check(f, ok) for f in FIGURES)
    print("\n" + ("ALL CHECKS PASS" if allok else "FAILURES PRESENT"))
    raise SystemExit(0 if allok else 1)
