#!/usr/bin/env python3
"""PRE-FREEZE GATE: no bare arm code may appear inside any shipped figure PDF.

WHY THIS EXISTS.  paper/TERMINOLOGY.md rule 4 greps `paper/*.tex`, which is
structurally incapable of seeing inside a PDF.  On 2026-10-01 that gap was
real, not hypothetical: five shipped figures printed "A soft roles / B no
roles / C enforced", including `fig1_v1_grouped.pdf`, the figure the
manuscript referenced.  The prose was clean the whole time, so the existing
grep passed.

WHAT IT CHECKS.  Every *.pdf under figures/ is read with `pdftotext` and
matched against the arm-code pattern.  Exits non-zero on any hit.

WHY IT CANNOT PASS VACUOUSLY.  Three ways this check could look clean while
testing nothing, each defended:
  * pdftotext missing          -> abort, do not report success
  * a PDF yields no text       -> reported as UNREADABLE and fails the gate
                                  (outlined or rasterized text would hide a
                                  violation from any text-based scan)
  * no PDFs found at all       -> abort; an empty sweep is not a pass
`--selftest` additionally plants a violating label into a real figure and
requires the gate to catch it, so the pattern is known to discriminate rather
than merely to have matched nothing.

Usage:
  python3 scripts/check_terminology_pdfs.py            # gate
  python3 scripts/check_terminology_pdfs.py --selftest # prove it can fail
"""
import glob, hashlib, os, re, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# BOTH figure directories, and the second one is the important one.
#
# DEFECT FOUND 2026-10-02: this gate scanned only figures/ -- where the
# GENERATORS write -- while LaTeX resolves \includegraphics against
# paper/figures/. Those are different files. paper/figures/ held a stale
# pre-fix copy of fig1_v1_grouped.pdf still printing "A soft roles / B no
# roles" while the gate reported all clean, because it was reading the
# corrected copy one directory up. A gate that inspects the producer's
# output cannot certify the consumer's input.
FIGDIRS = [os.path.join(ROOT, "figures"), os.path.join(ROOT, "paper", "figures")]
FIGDIR = FIGDIRS[0]            # selftest plants here; generators write here

# "Arm A" / "arm~B" / "A soft roles" / "B no roles" / "C enforced".
# Deliberately NOT a bare \b[ABC]\b: a lone capital letter is a legitimate
# panel tag ("A", "B", "C" as subfigure labels), and banning it would make the
# gate unusable and invite someone to switch it off.
#   3. a bare letter used as a CONDITION in a comparison -- "A 0.014 = B
#      0.015", "but C 0.139", "A vs B", "n = A / B / C".  This form carried
#      the violation that survived the first fix of fig1_v1_grouped: the
#      legend was corrected while the annotation still read "A 0.014 = B
#      0.015, but C 0.139", and the first version of this gate did not see it
#      because it only looked for the word "arm" or the old long labels.
ARMCODE = re.compile(
    r"\b[Aa]rm\s*~?\s*[ABC]\b"
    r"|(?<![A-Za-z])[ABC]\s+(?:soft roles|no roles|enforced)\b"
    # "A 0.014 = B 0.015": the letter LABELS a number, then an operator
    # follows. The letter is followed by a VALUE, not by the operator,
    # which is why the operator-adjacent alternative below missed it.
    r"|(?<![A-Za-z])[ABC]\s+[\d.]+\s*(?:[=\u2248<>]|vs\.?\s)"
    r"|(?<![A-Za-z])[ABC]\s*(?:[=\u2248]|vs\.?\s)\s*[ABC]?\s*\d"
    r"|(?<![A-Za-z])but\s+[ABC]\s+\d"
    r"|(?<![A-Za-z])[ABC]\s*/\s*[ABC]\s*/\s*[ABC](?![A-Za-z])")


def pdf_text(path):
    r = subprocess.run(["pdftotext", path, "-"], capture_output=True, text=True)
    return r.stdout


def scan(paths, verbose=True):
    bad, unreadable = [], []
    for p in sorted(paths):
        t = pdf_text(p)
        if not t.strip():
            unreadable.append(p)
            continue
        hits = sorted(set(m.group(0) for m in ARMCODE.finditer(t)))
        if hits:
            bad.append((p, hits))
    if verbose:
        for p, hits in bad:
            print(f"  FAIL {os.path.relpath(p, ROOT)}")
            for h in hits:
                print(f"         contains {h!r}")
        for p in unreadable:
            print(f"  FAIL {os.path.relpath(p, ROOT)}: no extractable text "
                  f"(outlined or rasterized? a text scan cannot clear it)")
    return bad, unreadable


def selftest():
    """Plant a violating label in a real figure; the gate must catch it."""
    src = os.path.join(ROOT, "analysis", "scripts", "mk_figS1_conditions.py")
    dst = os.path.join(ROOT, "analysis", "scripts", "_termgate_selftest.py")
    out = os.path.join(FIGDIR, "_termgate_selftest.pdf")
    s = open(src).read()
    # Bypass save()'s own gate deliberately: we are testing THIS scanner, and a
    # control blocked upstream would prove only that the other check works.
    s = s.replace("import mk_figstyle as S",
                  "import mk_figstyle as S\nS.assert_no_arm_codes = lambda *a, **k: True")
    s = s.replace('"organization\\ncollapse"', '"Arm B no roles"')
    s = s.replace('"figS1_conditions", S.COLWIDTH_IN', '"_termgate_selftest", S.COLWIDTH_IN')
    open(dst, "w").write(s)
    try:
        r = subprocess.run([sys.executable, dst], capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(out):
            print("  SELFTEST ABORT: the planted figure did not build, so the "
                  "control proves nothing.")
            print("  " + r.stderr.strip()[-300:])
            return False
        bad, _ = scan([out], verbose=False)
        print(f"  planted 'Arm B no roles' into a real figure -> "
              f"{'CAUGHT' if bad else 'MISSED — GATE IS VOID'}")
        return bool(bad)
    finally:
        for p in (dst, out, out.replace(".pdf", ".png")):
            if os.path.exists(p):
                os.remove(p)


def main():
    if not shutil.which("pdftotext"):
        print("ABORT: pdftotext not on PATH. Cannot verify; refusing to "
              "report success.")
        return 2
    if "--selftest" in sys.argv:
        print("SELF-TEST (can this gate fail?)")
        if not selftest():
            return 1
        print()
    pdfs = []
    for d in FIGDIRS:
        found = glob.glob(os.path.join(d, "*.pdf"))
        if not found:
            print(f"ABORT: no PDFs under {d}. An empty sweep is not a pass.")
            return 2
        pdfs += found
    print(f"TERMINOLOGY GATE — scanning {len(pdfs)} PDFs under "
          + " and ".join(os.path.relpath(d, ROOT) + "/" for d in FIGDIRS))
    bad, unreadable = scan(pdfs)

    # Divergence check. A figure present in both directories under one name
    # must be the same bytes; if it is not, the copy step was skipped and
    # the PDF ships something other than what was regenerated and inspected.
    diverged = []
    for f in sorted(set(os.path.basename(p) for p in pdfs)):
        a, b = (os.path.join(d, f) for d in FIGDIRS)
        if os.path.exists(a) and os.path.exists(b):
            ha, hb = (hashlib.sha256(open(x, "rb").read()).hexdigest() for x in (a, b))
            if ha != hb:
                diverged.append((f, ha[:16], hb[:16]))
    for f, ha, hb in diverged:
        print(f"  FAIL {f}: figures/ is {ha} but paper/figures/ is {hb} "
              f"-- the copy into paper/figures/ was skipped; LaTeX ships the "
              f"latter")

    # paper/figures/ must hold EXACTLY what the manuscript includes. A file
    # that is there but unreferenced is not harmless: the stale
    # fig1_v1_grouped.pdf that prompted the divergence check above was
    # unreferenced, which is precisely why nobody regenerated it, and it sat
    # in the Overleaf-bound directory printing bare condition codes.
    src = ""
    for f in sorted(glob.glob(os.path.join(ROOT, "paper", "sections", "*.tex"))) \
             + [os.path.join(ROOT, "paper", "main.tex"),
                os.path.join(ROOT, "paper", "supplement.tex")]:
        if os.path.exists(f):
            src += open(f, errors="ignore").read()
    used = set(re.findall(r"\\includegraphics\[[^\]]*\]\{figures/([^}]+)\}", src))
    shipped = set(os.path.basename(p) for p in glob.glob(
        os.path.join(ROOT, "paper", "figures", "*.pdf")))
    stray = sorted(shipped - used)
    absent = sorted(used - shipped)
    for f in stray:
        print(f"  FAIL paper/figures/{f}: in the Overleaf-bound directory but "
              f"included by no document. Delete it or include it -- an "
              f"unreferenced figure is one nobody regenerates.")
    for f in absent:
        print(f"  FAIL paper/figures/{f}: included by a document but not "
              f"present. The build cannot be reproduced from this tree.")

    n = len(bad) + len(unreadable) + len(diverged) + len(stray) + len(absent)
    if n:
        print(f"\n{n} of {len(pdfs)} FAIL. paper/TERMINOLOGY.md forbids arm "
              f"codes in reader-facing output.\nRegenerate via the mk_fig*.py "
              f"scripts; mk_figstyle.save() blocks new violations at write "
              f"time.")
        return 1
    print(f"  all {len(pdfs)} clean")
    print("\nPASS: no arm codes in any shipped figure.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
