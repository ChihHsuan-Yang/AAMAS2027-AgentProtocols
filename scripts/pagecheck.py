#!/usr/bin/env python3
"""CORRECT page-limit check for a two-column layout.

The obvious check -- "words with y < REFERENCES y" -- is COLUMN-BLIND and
passes vacuously when REFERENCES lands at the top of the RIGHT column: every
word in the left column then has y GREATER than the heading and is not
counted. That check reported "11 words above REFERENCES" (two running heads)
while 545 words of main text sat in the left column of the same page.

Reading order in a 2-column page is: left column top->bottom, THEN right
column top->bottom. A word is "before" REFERENCES iff
    (its column index, its y) < (REFERENCES column index, REFERENCES y)
"""
import subprocess, re, sys

PDF = sys.argv[1] if len(sys.argv) > 1 else "main.pdf"
MID = 306.0  # letter 612pt / 2

pages = int(subprocess.run(["pdfinfo", PDF], capture_output=True, text=True
            ).stdout.split("Pages:")[1].split()[0])
found = None
for p in range(1, pages + 1):
    out = subprocess.run(["pdftotext", "-bbox", "-f", str(p), "-l", str(p), PDF, "-"],
                         capture_output=True, text=True).stdout
    w = [(float(x), float(y), t) for x, y, X, Y, t in re.findall(
         r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>',
         out, re.S)]
    hit = [(x, y) for x, y, t in w if t.strip().upper() == "REFERENCES"]
    if hit:
        found = (p, hit[0], w)
        break
assert found, "REFERENCES heading not located in any page -- check is vacuous"
page, (rx, ry), words = found
rcol = 0 if rx < MID else 1
RUNHEAD = {"When", "Is", "Multi-Agent", "Organization", "Load-Bearing?",
           "AAMAS", "’27,", "May", "2027,", "Paphos,", "Cyprus"}
after = [(x, y, t) for x, y, t in words
         if (0 if x < MID else 1, y) < (rcol, ry)
         and not t.strip().isdigit() and t.strip() not in RUNHEAD]
print(f"REFERENCES on page {page}, column {'LEFT' if rcol==0 else 'RIGHT'}, y={ry:.1f}")
print(f"main-text words BEFORE it in reading order on that page: {len(after)}")
if after:
    print("  first 25:", " ".join(t for _, _, t in after[:25]))
    print(f"\nRESULT: main text occupies {page} pages -> OVER the 8-page limit")
    sys.exit(1)
print(f"\nRESULT: main text ends by page {page-1}; references start page {page}")
