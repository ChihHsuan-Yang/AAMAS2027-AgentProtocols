#!/usr/bin/env python3
"""Workshop (AIAS 2026) copy of manuscript Table 1 with a shorter caption.

Reads the generated AAMAS table paper/tables/main_role_collapse.tex
(mk_tables.py), replaces only its caption, asserts that the header and every
table row are unchanged, and writes workshop_aias26/tables/main_role_collapse.tex.
No number is typed here.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
src = (ROOT / "paper/tables/main_role_collapse.tex").read_text()

CAPTION_WS = r"""\caption{\textbf{Functional collapse on the Omni-MATH benchmark.} Share of
first cycles (the first pass of the three agents) in which all three assert
their own final answer, per actor; bold: without roles. RS: role-structured; RF$^{-}$ and RF: role-free with the evaluator's
feedback withheld or shown. \emph{Adjudicated no division}: share of a
judged sample of first cycles in which a model judge with a fixed rubric
(outcome-blind, not condition-blind) finds no division of labor.}"""

i = src.index(r"\caption{")
j = src.index(r"\label{tab:collapse}")
ws = src[:i] + CAPTION_WS + "\n" + src[j:]
ws = ws.replace("% Table 1 (manuscript)", "% Table 1 (AIAS 2026 workshop copy; caption shortened by\n"
                "% analysis/scripts/mk_table_collapse_ws.py)", 1)
assert ws[ws.index(r"\label{tab:collapse}"):] == src[src.index(r"\label{tab:collapse}"):]
dst = ROOT / "workshop_aias26/tables/main_role_collapse.tex"
dst.write_text(ws)
print("wrote", dst.relative_to(ROOT), "(rows unchanged)")
