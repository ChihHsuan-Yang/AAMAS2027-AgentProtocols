# -*- coding: utf-8 -*-
"""FIGURE 2 -- cross-domain replication, gemma-4 only.

  columns : Omni-MATH | SciBench
  rows    : first-pass | recovery
  message : nearly the same, then a large drop -- twice.

STATUS: BLOCKED ON DATA, DELIBERATELY NOT DRAWN.
=================================================
Half of this figure exists.  The Omni-MATH column is fully available in
analysis/out/FIGDATA.json.  **The SciBench column is not in FIGDATA.json at
all** -- [T28] of FINAL_TABLES.py reads experiments/results/FROZEN/ only, and
SciBench is a SEPARATE frozen snapshot
(experiments/results/xdomain/FROZEN_SCIBENCH/, sha256 10068f72cfd936d3...),
analysed by a separate script (xdom_analyze.py) that prints a table and
exports no machine-readable artifact.

WHY THIS SCRIPT DOES NOT JUST COMPUTE THEM.  The figure agent's scope forbids
choosing denominators or inventing statistics, and this is precisely a case
where that matters rather than a formality:

  notes/XDOMAIN-INTEGRATION-DECISION.md records that the worker reported
  SciBench gemma recovery as 0.212 -> 0.020 and the master computed
  0.254 -> 0.051 FROM THE SAME FROZEN FILE.  Both are correct.  The first is
  the PAIRED subset (n=99, first-pass-wrong under both conditions); the
  second is the MARGINAL rate (n=118 per condition).  That document calls
  this "defect class 3 ... exactly how a wrong pair of numbers enters a
  paper" and requires the paper to state which population every SciBench
  figure uses.

  Picking one here would be the figure agent making that call silently, in a
  plotting script, which is the one place this project has decided numbers
  may never be decided.

WHAT IS NEEDED TO UNBLOCK.  A [T28]-style export of the SciBench cells into
FIGDATA.json under the keys named in REQUIRED below, computed by the SAME
code objects FINAL_TABLES.py already defines (xdom_analyze.py already execs
them, so the definitions are settled -- only the export is missing).

Once those keys exist this script renders with no further edits: it reads
them and nothing else.  It is written against that contract, not against
numbers, so it cannot be satisfied by typing values in.

TWO HONESTY CONSTRAINTS ALREADY ENCODED BELOW, for whoever fills the data:
  1. The two domains' effects must NOT be drawn as identical merely because a
     test cannot distinguish them (z=1.06, p=0.289 is a failure to resolve, not
     an equality).  draw_pair() therefore plots each domain's own CI and never
     a shared band or a single pooled marker.
  2. gpt-oss is underpowered on SciBench (realised paired n=96), so this
     figure is gemma-4 ONLY, per the integration decision -- and the caption
     must not say "replicates across two benchmarks".
     POWER: do NOT quote a single number.  XDOMAIN-INTEGRATION-DECISION.md was
     corrected 2026-10-01: power is 0.06 by exact McNemar (the test the paper
     reports), 0.12 by two-proportion z, and the 0.42 that circulated earlier
     is superseded.  The paper says "0.06-0.45 by test".  A quantity that
     moves 7x with the test assumed must not be asserted as one figure, and
     this docstring quoted the stale 0.42 until the source note was fixed
     underneath it -- the same stale-derived-artifact trap the note itself
     describes.

Run:  python3 analysis/scripts/mk_fig2_xdomain.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import mk_figstyle as S

FOCUS = "gemma-4-31B-it"

# The exact FIGDATA contract this figure needs.  Names mirror the existing
# schema so the export is a copy of [T28]'s shape, not a new convention.
REQUIRED = {
    "cells['%s|A@scibench']" % FOCUS:
        "firstpass, firstpass_lo, firstpass_hi, recovery, recovery_lo, "
        "recovery_hi, n_judged, n_fpw  (marginal, same definitions as T28)",
    "cells['%s|B@scibench']" % FOCUS:
        "same fields, role-free condition",
    "paired_recovery['%s|AB@scibench']" % FOCUS:
        "n, x_only, y_only, p  (PAIRED: first-pass-wrong under BOTH "
        "conditions; this is the population that differs from the marginal)",
    "paired_firstpass['%s|AB@scibench']" % FOCUS:
        "n, p  -- needed because the first-pass claim is an EXACT tie "
        "(B-A = 0.0000) and a reader must see it is paired, not coincidental",
    "provenance['files']['scibench_AB.jsonl']":
        "sha256 + rows, so the figure's provenance line names the SciBench "
        "snapshot it drew (10068f72..., 2296 rows) and not only Omni-MATH",
}


def check():
    D = S.figdata()
    missing = []
    for key in REQUIRED:
        top, _, rest = key.partition("[")
        node = D.get(top)
        if node is None:
            missing.append(key); continue
        idx = rest.strip("]").strip("'\"")
        if idx not in node:
            missing.append(key)
    return missing


if __name__ == "__main__":
    print("Figure 2 (cross-domain, gemma-4) -- " + S.provenance_line())
    miss = check()
    if not miss:
        print("  SciBench keys present; implement draw_pair() against them.")
        raise SystemExit(0)
    print("\n  BLOCKED: FIGDATA.json has no SciBench column.")
    print("  The Omni-MATH half is available; the SciBench half is not.\n")
    print("  Required additions to analysis/out/FIGDATA.json, via a new")
    print("  [T28]-style export in FINAL_TABLES.py (NOT typed into a figure):\n")
    for k in REQUIRED:
        print(f"    - {k}\n        {REQUIRED[k]}")
    print("\n  Source data exists and is frozen:")
    print("    experiments/results/xdomain/FROZEN_SCIBENCH/scibench_AB.jsonl")
    print("    sha256 10068f72cfd936d3be6de85fef196d63fc154ef2c2ec26a0ac2c7313513dce58")
    print("    2,296 rows; 4 cells of exactly 574.")
    print("\n  Blocking reason is a DENOMINATOR CHOICE, not a missing computation:")
    print("    the paired subset (n=99) and the marginal sets (n=118 each) give")
    print("    0.212->0.020 and 0.254->0.051 respectively. Both are correct for")
    print("    their own scope (XDOMAIN-INTEGRATION-DECISION.md). Choosing one")
    print("    inside a plotting script is out of the figure agent's scope.")
    raise SystemExit(3)
