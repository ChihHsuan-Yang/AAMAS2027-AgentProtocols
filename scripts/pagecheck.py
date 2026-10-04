#!/usr/bin/env python3
"""THE page-limit check for this project. Two earlier versions were broken.

v1  compared y-coordinates against the REFERENCES heading. COLUMN-BLIND: the
    heading sat at the top of the RIGHT column, so every word in the LEFT
    column had a LARGER y and was never counted. It reported "11 words"
    (the running heads) while 539 words of main text sat on the page.

v2  ordered by (column, y) -- correct as far as it went, but once a
    \clearpage was added before the bibliography, "main-text words before
    REFERENCES ON THE HEADING'S OWN PAGE" is structurally zero for EVERY
    input. It passed a deliberately padded 10-page paper.

v3 (this file) asks the question directly: what is the last page carrying
    any main text? Positive-controlled BOTH ways -- exits 1 on a padded
    10-page build and on a +1-sentence build, exits 0 as submitted.

Run it with no pipe: `python3 scripts/pagecheck.py paper/main.pdf; echo $?`.
Piping to `tail` makes $? report tail's status, not this script's -- which
cost me a false PASS while testing the predecessor.
"""
import subprocess, re, sys

PDF = sys.argv[1] if len(sys.argv) > 1 else "main.pdf"
LIMIT = int(sys.argv[2]) if len(sys.argv) > 2 else 8
MID = 306.0

pages = int(subprocess.run(["pdfinfo", PDF], capture_output=True, text=True
            ).stdout.split("Pages:")[1].split()[0])
# Running-head vocabulary. This is DERIVED FROM THE PDF's own /Title plus the
# venue block, not hand-maintained: a hardcoded list silently goes stale the
# moment the title or the venue changes, and a stale entry makes the check
# count a running-head word as main text (which is exactly what a title change
# and the Paphos->Hanoi venue fix had already done to the previous list).
_title = subprocess.run(["pdfinfo", PDF], capture_output=True, text=True).stdout
_title = _title.split("Title:")[1].split("\n")[0].strip() if "Title:" in _title else ""
# 2026-10-03: the AAMAS-2027 class prints "Research Paper Track" (left) and
# "AAMAS 2027, 3–7 May 2027, Hanoi, Vietnam" (right) as the running head; the
# older "AAMAS ’27, May 2027" words are kept so the check still reads an old
# build correctly.
RUNHEAD = set(_title.split()) | {"Anon.", "AAMAS", "’27,", "May", "2027,",
                                 "Hanoi,", "Vietnam",
                                 "Research", "Paper", "Track", "3–7"}

ref_page = ref_col = ref_y = None
for p in range(1, pages + 1):
    out = subprocess.run(["pdftotext", "-bbox", "-f", str(p), "-l", str(p), PDF, "-"],
                         capture_output=True, text=True).stdout
    for x, y, X, Y, t in re.findall(
        r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>',
        out, re.S):
        if t.strip().upper() == "REFERENCES":
            ref_page, ref_col, ref_y = p, (0 if float(x) < MID else 1), float(y)
            break
    if ref_page: break
assert ref_page, "REFERENCES heading not located -- check is vacuous"

last_main = 0
for p in range(1, pages + 1):
    out = subprocess.run(["pdftotext", "-bbox", "-f", str(p), "-l", str(p), PDF, "-"],
                         capture_output=True, text=True).stdout
    for x, y, X, Y, t in re.findall(
        r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>',
        out, re.S):
        s = t.strip()
        if not s or s.isdigit() or s in RUNHEAD: continue
        if p > ref_page: continue
        if p == ref_page and ((0 if float(x) < MID else 1), float(y)) >= (ref_col, ref_y):
            continue
        last_main = max(last_main, p)

print(f"REFERENCES starts page {ref_page} ({'LEFT' if ref_col==0 else 'RIGHT'} col)")
print(f"last page carrying main text: {last_main}   limit: {LIMIT}")
if last_main > LIMIT:
    print(f"\nRESULT: main text runs to page {last_main} -> OVER the {LIMIT}-page limit")
    sys.exit(1)
print(f"\nRESULT: main text ends by page {last_main} -> within the {LIMIT}-page limit")
