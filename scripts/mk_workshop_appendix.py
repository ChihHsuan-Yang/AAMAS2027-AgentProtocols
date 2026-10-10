#!/usr/bin/env python3
"""Build the AIAS 2026 workshop appendices that carry the supplementary material.

The workshop's submission form takes one PDF and no supplementary file, so the
AAMAS supplement (paper/supplement.tex) goes into the workshop PDF as
appendices after the ones that hold text moved out of the main paper.

Writes
  workshop_aias26/sections/appendix_supp.tex   the supplement's body, with the
      document front matter dropped, "main paper" read as "main text", section
      cross-references named as appendices, and figure widths set for the
      single-column EasyChair page (column-width figures at their printed
      width, page-wide figures scaled to the text width);
  workshop_aias26/tables/<name>.tex            for every table the supplement
      inputs: the generated file from paper/tables/ with its tabular wrapped in
      an adjustbox that only shrinks a table wider than the text block.

No number is typed here: every table body is the generated file, unchanged.
Run from anywhere:  python3 scripts/mk_workshop_appendix.py
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUPP = ROOT / "paper" / "supplement.tex"
WS = ROOT / "workshop_aias26"

src = SUPP.read_text()
body = src.split(r"\maketitle", 1)[1].split(r"\end{document}", 1)[0].strip()


def rep(s, old, new, count=1):
    n = s.count(old)
    assert n == count, (n, old[:70])
    return s.replace(old, new)


# Opening section: what these appendices are.
body = rep(body, r"\section*{What this document is}", r"\section*{Supplementary appendices}")
body = rep(body, r"""The main paper states every claim it makes and is complete without this
file. What it cannot carry in eight pages is the full numeric backing behind
some of its sentences, and that backing is here, in the order of the main
paper's results: the realized organization (R1), recovery (R2), the
submission gate (R3), and the second domain and structural enforcement
(R4), followed by the pre-registered endpoints and the single-agent
comparator.""", r"""The main text states every claim it makes and is complete without the
appendices that follow. They give the full numeric backing behind some of
its sentences, in the order of its results: the realized organization (R1,
Appendix~\ref{sec:collapse_full}), recovery (R2,
Appendix~\ref{sec:recovery}), the submission gate (R3,
Appendix~\ref{sec:gate}), and the second domain and structural enforcement
(R4, Appendices~\ref{sec:xdomain} and~\ref{sec:enforcement}), followed by
the pre-registered endpoints (Appendix~\ref{sec:prereg}) and the
single-agent comparator (Appendix~\ref{sec:singleagent}).""")
body = rep(body, "the same scripts and outputs as the main paper's tables",
           "the same scripts and outputs as the main text's tables")

# "main paper" is the main text of this one document.
body = body.replace("the main paper's", "the main text's")
body = body.replace("The main paper's", "The main text's")
body = body.replace("the main paper", "the main text")
body = body.replace("The main paper", "The main text")
body = re.sub(r"main\s+paper's", "main text's", body)
body = re.sub(r"main\s+paper", "main text", body)
assert "main paper" not in body
body = body.replace(r"Section~\ref{", r"Appendix~\ref{")

# Pointers to material that the workshop main text moved into Appendices A-C,
# and wording for files that are released with the code rather than shipped.
def resub(s, pat, new):
    out, n = re.subn(pat, lambda m: new, s)
    assert n == 1, (n, pat)
    return out
body = resub(body, r"drift check of the main text on the same",
             r"drift check of Appendix~\ref{app:details} on the same")
body = resub(body, r"An offline test in the supplementary material \(no model calls\)\s+checks",
             "An offline test (no model calls), to be released with the code,\nchecks")
body = resub(body, r"the prompt files in the supplementary material make the\s+difference checkable",
             "the prompt files, to be released with the code, make the\ndifference checkable")
body = resub(body, r"can check the files\.", "can check the files once they are released.")
body = resub(body, r"is null, and that the\s+\\Pone\{\} manipulation objective failed\.",
             "is null (\\S\\ref{subsec:prereg}), and Appendix~\\ref{app:details} that the\n\\Pone{} manipulation objective failed.")
body = rep(body, r"\section*{Supplementary appendices}", r"\section*{Detailed results and disclosures}")
# The excluded early campaign, stated as a disclosure.
i = body.index(r"\paragraph{An early campaign stopped for a truncation confound.}")
j = body.index(r"\paragraph{Accumulated context as a competing explanation.}")
body = body[:i] + r"""\paragraph{An excluded early campaign.} The main run was gated on a smoke
test requiring non-zero boundary rejections with reasons logged,
answer-bearing calls equal across conditions, and a pinned backend. An early
campaign of $121$ trajectories, run at half the main run's token limit, is
excluded: in it, $74\%$ of enforcement rejections were outputs cut off at
the token limit mid-JSON rather than role-boundary violations. Truncation
was not condition-specific but its cost was, because a prose condition
tolerates a truncated message where the enforced one rejects unparseable
JSON, so pooling those rows would have produced a spurious ``enforcement
lowers accuracy'' result. They were never pooled.

""" + body[j:]

# Figures: a column-width figure at its printed width (3.337 in), a page-wide
# one at the text width.
body = body.replace(r"\includegraphics[width=\columnwidth]", r"\includegraphics[width=0.585\textwidth]")

(WS / "sections" / "appendix_supp.tex").write_text(
    "% GENERATED by scripts/mk_workshop_appendix.py from paper/supplement.tex"
    " -- do not edit by hand.\n" + body + "\n")

# Tables the supplement inputs, wrapped so a wide one fits the text block.
names = re.findall(r"\\input\{tables/([^}]+)\}", body)
for name in names:
    t = (ROOT / "paper" / "tables" / (name + ".tex")).read_text()
    assert t.count(r"\begin{tabular}") == t.count(r"\end{tabular}") >= 1, name
    t = re.sub(r"main\s+paper", "main text", t)
    t = t.replace("(the main text's logging defect)", r"(the logging defect of Appendix~\ref{app:results})")
    t = t.replace(r"\begin{tabular}", r"\begin{adjustbox}{max width=\textwidth}\begin{tabular}")
    t = t.replace(r"\end{tabular}", r"\end{tabular}\end{adjustbox}")
    (WS / "tables" / (name + ".tex")).write_text(
        "% Workshop copy (scripts/mk_workshop_appendix.py): paper/tables/" + name +
        ".tex with its tabular in an adjustbox; numbers unchanged.\n" + t)
print("wrote sections/appendix_supp.tex and", len(names), "tables:", ", ".join(names))
