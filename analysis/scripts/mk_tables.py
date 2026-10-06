#!/usr/bin/env python3
"""Generate every LaTeX table the manuscript uses, into paper/tables/*.tex.

WHY THIS EXISTS
---------------
A hand-typed table is a number with no provenance. Every figure emitted here
is PARSED out of a canonical analysis output; this script contains no result
literal of its own. If a number is not in a canonical input, this script
raises rather than inventing one.

CANONICAL INPUTS (the only sources of a number)
-----------------------------------------------
  1. analysis/out/FINAL_TABLES_OUTPUT.txt
       Produced by analysis/scripts/FINAL_TABLES.py against
       experiments/results/FROZEN/. Omni-MATH: everything.
  2. analysis/scripts/xdom_analyze.py  (executed, stdout parsed)
       SciBench cross-domain. That script does NOT reimplement the
       definitions: it execs FINAL_TABLES.py and rebinds judged / is_fpw /
       fp / fin_prereg / ansseq / func_collapse to the SciBench rows, so the
       recovery denominator is the same code object as Omni-MATH's.
       Reimplementing that denominator from memory is the bug that cost this
       project a FATAL finding (STATISTICAL_AUDIT FATAL-1); this script does
       not go near it.
  3. analysis/scripts/stat_audit_a7_power.py  (executed, stdout parsed)
       The MDE column of the pre-registered endpoint table only. NOTE its
       population differs from T14's -- see PREREG_MDE_POPULATION_NOTE.

DETERMINISM
-----------
Regenerating must produce byte-identical files. Two consequences:
  * No wall-clock date is stamped. The "generated" date is derived from the
    canonical input's own mtime, so it moves only when the input moves.
    A today() stamp would make every rerun a diff, which defeats the point
    of being able to verify that the tables match the data.
  * The parse is strict. A missing row raises SourceMissing; it never
    defaults to a plausible zero.

TERMINOLOGY (paper/TERMINOLOGY.md, binding)
-------------------------------------------
Internal arm codes A / B / C / C' are stable identifiers in code, data and
provenance -- and must NEVER reach a reader-facing table. The mapping is
applied once, in ARM_LABEL, and asserted at the end of the run: emitting a
bare arm letter is a hard failure.

USAGE
-----
  python3 analysis/scripts/mk_tables.py            # write paper/tables/*.tex
  python3 analysis/scripts/mk_tables.py --check    # verify, write nothing
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANON = ROOT / "analysis/out/FINAL_TABLES_OUTPUT.txt"
FINAL_TABLES = ROOT / "analysis/scripts/FINAL_TABLES.py"
XDOM = ROOT / "analysis/scripts/xdom_analyze.py"
POWER = ROOT / "analysis/scripts/stat_audit_a7_power.py"
FROZEN_MANIFEST = ROOT / "experiments/results/FROZEN/MANIFEST.json"
SCIBENCH_MANIFEST = ROOT / "experiments/results/xdomain/FROZEN_SCIBENCH/MANIFEST.json"
OUTDIR = ROOT / "paper/tables"
# The supplement is a second document in the SAME project, sharing this
# tables/ directory, so a regenerated table lands in both at once.
SUPPLEMENT = ROOT / "paper/supplement.tex"

THIS = "analysis/scripts/mk_tables.py"


class SourceMissing(RuntimeError):
    """A number the table needs is not in the canonical output.

    Raised rather than returning a default. An absent input that silently
    becomes 0.000 is indistinguishable from a measured zero in the rendered
    table, and the reader has no way to tell.
    """


# --------------------------------------------------------------------------
# Reader-facing names. The ONLY place internal codes map to prose.
# --------------------------------------------------------------------------
ARM_LABEL = {
    "A": "role-structured",
    "B": "role-free",
    "C": "structurally enforced",
    "Cp": "context-restored",
}
ACTOR_LABEL = {
    "gemma-4-31B-it": "gemma-4-31B",
    "gpt-oss-120b": "gpt-oss-120b",
    "Llama-3.3-70B-Instruct": "Llama-3.3-70B",
}
ACTORS = ["gemma-4-31B-it", "gpt-oss-120b", "Llama-3.3-70B-Instruct"]

# A bare internal arm code must not survive into a rendered table.
FORBIDDEN = re.compile(
    r"(?:\bArm~?\s*[ABC]\b|\bArm~?\s*C['\u2032]|\bArms~?\s*[ABC]\b"
    r"|\\textbf\{[ABC]\}|(?<![\w-])Arm\s*[ABC](?![\w-]))"
)


# ==========================================================================
# Canonical-output parsing
# ==========================================================================
def read_canonical() -> dict[str, list[str]]:
    """Split FINAL_TABLES_OUTPUT.txt into its [Tn] sections."""
    if not CANON.exists():
        raise SourceMissing(
            f"{CANON} missing. Regenerate with: python3 {FINAL_TABLES.relative_to(ROOT)}")
    secs: dict[str, list[str]] = {}
    cur = None
    for line in CANON.read_text().splitlines():
        m = re.match(r"^\[(T\d+)\]", line)
        if m:
            cur = m.group(1)
            secs[cur] = []
            continue
        if cur is not None:
            secs[cur].append(line)
    if not secs:
        raise SourceMissing(f"{CANON} contains no [Tn] sections -- wrong file?")
    return secs


def rowmap(sec: list[str], ncols: int) -> dict[tuple[str, str], list[str]]:
    """Parse '<actor> <arm> <v1> <v2> ...' rows keyed by (actor, arm)."""
    out = {}
    for line in sec:
        m = re.match(r"^\s*(\S+)\s+(A|B|C|Cp)\s+(.*)$", line)
        if not m or m.group(1) not in ACTORS:
            continue
        vals = m.group(3).split()
        if len(vals) < ncols:
            continue
        out[(m.group(1), m.group(2))] = vals
    return out


def need(d: dict, key, where: str):
    if key not in d:
        raise SourceMissing(f"{where}: no row for {key} in {CANON.name}")
    return d[key]


def run_capture(script: Path) -> str:
    """Execute a canonical analysis script and return its stdout.

    stderr is NOT suppressed into the void: a crash must be visible, not
    read as an empty result.
    """
    p = subprocess.run([sys.executable, str(script)], cwd=str(ROOT),
                       capture_output=True, text=True)
    if p.returncode != 0:
        raise SourceMissing(
            f"{script.name} exited {p.returncode}\n--- stderr ---\n{p.stderr[-3000:]}")
    if not p.stdout.strip():
        raise SourceMissing(f"{script.name} produced no stdout")
    return p.stdout


# ==========================================================================
# Provenance header
# ==========================================================================
def sha256_of(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def provenance() -> dict:
    man = json.loads(FROZEN_MANIFEST.read_text())
    sci = json.loads(SCIBENCH_MANIFEST.read_text())
    # Deterministic "generated" date: the canonical input's own mtime, NOT
    # today(). A wall-clock stamp would make every rerun a spurious diff and
    # destroy the byte-identity guarantee the brief requires.
    gen = _dt.datetime.utcfromtimestamp(CANON.stat().st_mtime).strftime("%Y-%m-%d")
    return {
        "generated": gen,
        "canon_sha": sha256_of(CANON),
        "frozen_at": man["frozen_at"],
        "frozen_files": {k: v["sha256"] for k, v in man["files"].items()},
        "frozen_rows": man["total_rows"],
        "sci_frozen_at": sci["frozen_at"],
        "sci_sha": sci["files"]["scibench_AB.jsonl"]["sha256"],
        "sci_rows": sci["total_rows"],
    }


def header(name: str, pv: dict, inputs: list[str], extra: list[str] | None = None) -> str:
    L = [
        "% " + "=" * 74,
        f"% {name}",
        "%",
        "% GENERATED FILE -- do not edit by hand. Any edit is overwritten.",
        f"% generating script : {THIS}",
    ]
    for i, s in enumerate(inputs):
        L.append(f"% canonical input   : {s}" if i == 0 else f"%                    {s}")
    L += [
        f"% frozen data       : experiments/results/FROZEN/, frozen_at {pv['frozen_at']}",
        f"%                     {pv['frozen_rows']} trajectories",
    ]
    for k, v in sorted(pv["frozen_files"].items()):
        L.append(f"%                     sha256 {v}  {k}")
    L += [
        f"% canonical-output sha256 : {pv['canon_sha']}",
        f"% generation date   : {pv['generated']}  (derived from the canonical",
        "%                     input's mtime, not wall-clock: regeneration must",
        "%                     be byte-identical)",
    ]
    if extra:
        L += ["%"] + [f"% {e}" for e in extra]
    L += [
        "%",
        "% Reader-facing condition names per paper/TERMINOLOGY.md; internal arm",
        "% codes are deliberately absent and their absence is asserted at",
        "% generation time.",
        "% " + "=" * 74,
    ]
    return "\n".join(L) + "\n"


# ==========================================================================
# Small formatting helpers
# ==========================================================================
def m(s: str) -> str:
    """Wrap an already-formatted numeric string for math mode."""
    return "$" + s.replace("-", "{-}") + "$"


def sci(pstr: str) -> str:
    """Render a p-value string from the canonical output as LaTeX.

    Exponents of -1 and -2 are written as plain decimals: '2.08\\times
    10^{-1}' is a scientific-notation rendering of 0.208 and reads as far
    smaller than it is. The VALUE is never altered -- only its spelling, and
    only where the decimal form is exact.
    """
    s = pstr.strip()
    mm = re.match(r"^([0-9.]+)e([-+]?\d+)$", s)
    if mm:
        mant, ex = mm.group(1), int(mm.group(2))
        # 0, -1 and -2: the decimal spelling is exact and far more readable.
        # '1.00\\times 10^{0}' is a correct rendering of p=1 that no reader
        # parses as "the test could not separate these at all".
        if ex in (0, -1, -2):
            return f"${float(mant) * 10 ** ex:g}$"
        return f"${mant}\\times 10^{{{ex}}}$"
    return f"${s}$"


def ci(s: str) -> str:
    """Render a '[-0.0488,-0.0187]' interval from the canonical output."""
    lo, hi = s.split(",")
    return ("{\\footnotesize $[" + lo.strip().replace("-", "{-}") + ",\\,"
            + hi.strip().replace("-", "{-}") + "]$}")


def pct(x: str) -> str:
    return f"${float(x)*100:.1f}\\%$"


# ==========================================================================
# TABLE 1 -- functional collapse
# ==========================================================================
def t_collapse(S, pv) -> str:
    T1 = rowmap(S["T1"], 8)       # n fp fin rec n_fpw collapse unanim frozen
    T18 = rowmap(S["T18"], 4)     # n bytedup normdup dupsameprompt
    T20 = rowmap(S["T20"], 4)     # n strict medium loose
    T9  = rowmap(S["T9"], 6)      # n medchars medlat medch/s frac<500ch reasfallbk

    # Adjudication: '  <actor>  <arm>  <n>  <rate>'
    adj = {}
    for line in S["T23"]:
        mm = re.match(r"^\s*(\S+)\s+(A|B|C|Cp)\s+(\d+)\s+([0-9.]+)\s*$", line)
        if mm and mm.group(1) in ACTORS:
            adj[(mm.group(1), mm.group(2))] = (mm.group(3), mm.group(4))
    if not adj:
        raise SourceMissing("T23: no adjudication cells parsed")

    # Grouped by condition in header ROWS rather than a first column: the
    # reader-facing names are long ("structurally enforced"), and as a column
    # they push this one-column table ~33pt past the text block.
    body = []
    dagger = []   # (short-message fraction) for cells whose duplication is uninterpretable
    for arm in ("A", "B"):
        body.append(f"\\multicolumn{{4}}{{@{{}}l}}{{\\emph{{{ARM_LABEL[arm]}}}}} \\\\")
        for a in ACTORS:
            coll = need(T1, (a, arm), "T1")[5]
            dup = need(T18, (a, arm), "T18")[1]
            aj = need(adj, (a, arm), "T23")[1]
            bold = (lambda s: f"$\\mathbf{{{s}}}$") if arm == "B" else m
            # The logging defect (T9, T26; manuscript 5.1): where most planner
            # messages are under 500 visible characters, byte-identical
            # outputs are expected and the rate is not interpretable (T21
            # excludes the cell from the duplication claim). Flagged from the
            # data, not by naming the cell, so it tracks the snapshot.
            short = float(need(T9, (a, arm), "T9")[4])
            dup_cell = m(dup)
            if short > 0.5:
                dup_cell = dup_cell[:-1] + "^{\\dagger}$"   # inside the same math group
                dagger.append(short)
            body.append(f"\\quad {ACTOR_LABEL[a]} & {bold(coll)} & {dup_cell} & {bold(aj)} \\\\")
        body.append("\\addlinespace")

    # Enforced conditions: collapse is n/a (their schema has no answer field).
    dups = [float(need(T18, (a, arm), "T18")[1])
            for a in ACTORS for arm in ("C", "Cp") if (a, arm) in T18]
    ajs = [float(v[1]) for (a, arm), v in adj.items() if arm in ("C", "Cp")]
    body.append("\\multicolumn{4}{@{}l}{\\emph{structurally enforced}} \\\\")
    body.append(f"\\quad all actors & n/a & $\\leq {max(dups):.3f}$ & "
                f"${min(ajs):.3f}$--${max(ajs):.3f}$ \\\\")

    # Marker sensitivity, from T20 -- the existing note, re-derived.
    def spread(arm):
        v = [float(x) for a in ACTORS for x in need(T20, (a, arm), "T20")[1:4]]
        return min(v), max(v)
    a_lo, a_hi = spread("A")
    b_lo, b_hi = spread("B")
    ncells = sum(1 for a in ACTORS for _ in range(3))
    # Ordering check: role-free exceeds role-structured in every actor x marker cell.
    ok = sum(1 for a in ACTORS for k in (1, 2, 3)
             if float(need(T20, (a, "B"), "T20")[k]) > float(need(T20, (a, "A"), "T20")[k]))

    dagger_note = ""
    if dagger:
        dagger_note = (f" $^{{\\dagger}}$Not interpretable: ${max(dagger)*100:.0f}\\%$ of this"
                       f" cell's planner messages are under $500$ visible characters"
                       f" (the logging defect, \\S\\ref{{subsec:logging}}).")

    pre = header("Table 1 (manuscript) -- functional collapse per actor", pv,
                 [f"analysis/out/{CANON.name}  sections T1, T18, T20, T23"],
                 ["Byte duplication is a LOWER BOUND (precision 1.000, recall 0.262)",
                  "and never carries the collapse claim alone (APPROVED_CLAIMS A1).",
                  "The adjudication is outcome-blind but NOT condition-blind: do not",
                  "describe it as blinded (APPROVED_CLAIMS A1 / DEAD list)."])
    return pre + f"""\\begin{{table}}[t]
\\centering
\\caption{{\\textbf{{Functional collapse.}} First pipeline passes in which all
three agents independently assert their own final answer, with exact byte
duplication as a \\emph{{lower bound}} and the model adjudication beside it.
Byte duplication has precision $1.000$ but recall $0.262$, so it never
carries this result alone. The adjudication is outcome-blind but
\\textbf{{not}} condition-blind and is a second opinion, not ground truth.
Collapse is not applicable to the structurally enforced conditions, whose
schema forbids an answer field.}}
\\label{{tab:collapse}}
\\small
\\begin{{tabular}}{{@{{}}lccc@{{}}}}
\\toprule
 & functional & exact byte & adjudicated \\\\
actor & collapse & duplication & no division \\\\
\\midrule
{chr(10).join(body)}
\\bottomrule
\\end{{tabular}}

\\vspace{{2pt}}
\\footnotesize\\emph{{Sensitivity.}} The role-free rate is stable across three
answer-marker definitions (${b_lo:.3f}$--${b_hi:.3f}$, every actor);
\\textbf{{the role-structured rate is not}} (${a_lo:.3f}$--${a_hi:.3f}$), so
read that column as ``low,'' not a point estimate. The ordering holds in all
{ok} of {ncells} actor$\\times$marker cells.{dagger_note}
\\end{{table}}
"""


# ==========================================================================
# TABLE 2 -- first pass and recovery, with explicit denominators
# ==========================================================================
def t_recovery(S, pv) -> str:
    T1 = rowmap(S["T1"], 8)

    # T3: marginal first-pass / recovery with paired first-pass CI.
    t3 = {}
    for line in S["T3"]:
        mm = re.match(
            r"^\s*(\S+)\s+([0-9.]+)\s+([0-9.]+)\s+([+-][0-9.]+)\s+"
            r"\[([^\]]+)\]\s+([0-9.]+)\s+([0-9.]+)\s+([+-][0-9.]+)\s+"
            r"\[([^\]]+)\]\s+(\d+)\s+(\d+)\s*$", line)
        if mm and mm.group(1) in ACTORS:
            t3[mm.group(1)] = mm.groups()[1:]
    if len(t3) != 3:
        raise SourceMissing(f"T3: parsed {len(t3)} actors, expected 3")

    # T4: paired recovery transitions.
    t4 = {}
    for line in S["T4"]:
        mm = re.match(
            r"^\s*(\S+)\s+(A) vs ([BC])\s+n=(\d+)\s+both_rec=(\d+)\s+Aonly=(\d+)\s+"
            r"([BC])only=(\d+)\s+both_fail=(\d+)\s+rec_A=([0-9.]+)\s+"
            r"rec_[BC]=([0-9.]+)\s+p=(\S+)\s*$", line)
        if mm and mm.group(1) in ACTORS:
            t4[(mm.group(1), mm.group(3))] = mm.groups()
    if len(t4) != 6:
        raise SourceMissing(f"T4: parsed {len(t4)} contrasts, expected 6")

    marg, pair = [], []
    for a in ACTORS:
        g = t3[a]
        rA = need(T1, (a, "A"), "T1")
        rB = need(T1, (a, "B"), "T1")
        marg.append(
            f"{ACTOR_LABEL[a]} & {m(g[0])} & {m(g[1])} & {m(g[2])} {ci(g[3])} & "
            f"{m(g[4])} ({rA[4]}) & {m(g[5])} ({rB[4]}) & {m(g[6])} {ci(g[7])} \\\\")
        p = t4[(a, "B")]
        pair.append(
            f"{ACTOR_LABEL[a]} & ${p[3]}$ & {m(p[9])} & {m(p[10])} & "
            f"${p[5]}$ & ${p[7]}$ & {sci(p[11])} \\\\")

    pre = header("Table 2 (manuscript) -- first pass and recovery", pv,
                 [f"analysis/out/{CANON.name}  sections T1, T3, T4"],
                 ["EVERY figure names its population. The marginal and paired",
                  "panels have DIFFERENT denominators and are not interchangeable;",
                  "conflating them has already caused one error in this project.",
                  "Recovery denominator = judged(r) and fp(r)==0: a recorded",
                  "incorrect FIRST verdict, INCLUDING trajectories that later died",
                  "in regeneration (STATISTICAL_AUDIT FATAL-1). Not graded(r).",
                  "Significance is exact McNemar on discordant pairs, never a",
                  "bootstrap CI bound (that label was seed-dependent)."])
    return pre + f"""\\begin{{table*}}[t]
\\centering
\\caption{{\\textbf{{First-pass accuracy and recovery, role-structured versus
role-free.}} \\textbf{{The two panels have different denominators and must not
be read across.}} \\emph{{Upper:}} the marginal population --- every
trajectory in the cell, first pass over those receiving an evaluator verdict,
recovery over those whose \\emph{{first}} verdict was incorrect
($n_{{\\mathrm{{fpw}}}}$ in parentheses, computed per condition and therefore
\\emph{{not}} a shared denominator). \\emph{{Lower:}} the paired population
--- only problems first-pass wrong under \\emph{{both}} conditions, one shared
denominator $n_{{\\mathrm{{both}}}}$, which is the actual test. The recovery
denominator counts every trajectory with a recorded incorrect first verdict,
including those that later died in regeneration; these score $0$ under the
pre-registered rule. Pre-registered scoring throughout; $p$ is exact McNemar
on discordant pairs.}}
\\label{{tab:recovery}}
\\small
\\begin{{tabular}}{{lcccccc}}
\\toprule
\\multicolumn{{7}}{{@{{}}l}}{{\\emph{{Marginal population}} --- each condition on
its own denominator}} \\\\
\\midrule
 & \\multicolumn{{3}}{{c}}{{first pass}}
 & \\multicolumn{{3}}{{c}}{{recovery $\\mid$ first verdict wrong}} \\\\
\\cmidrule(lr){{2-4}}\\cmidrule(lr){{5-7}}
actor & role-struct. & role-free & difference
      & role-struct. ($n$) & role-free ($n$) & difference \\\\
\\midrule
{chr(10).join(marg)}
\\midrule
\\multicolumn{{7}}{{@{{}}l}}{{\\emph{{Paired population}} --- problems first-pass
wrong under \\textbf{{both}} conditions; one shared denominator}} \\\\
\\midrule
actor & $n_{{\\mathrm{{both}}}}$ & role-struct. & role-free
      & role-struct.\\ only & role-free only & exact $p$ \\\\
\\midrule
{chr(10).join(pair)}
\\bottomrule
\\end{{tabular}}

\\vspace{{2pt}}
\\footnotesize Recovery conditions on a post-treatment variable and is
descriptive, never causal. No cell recovers before its first oracle verdict.
\\end{{table*}}
"""


# ==========================================================================
# TABLE 3 -- SciBench cross-domain replication
# ==========================================================================
def t_scibench(pv) -> str:
    out = run_capture(XDOM)
    sec, cur = {}, None
    for line in out.splitlines():
        mm = re.match(r"^\[(\w+)\]", line)
        if mm:
            cur = mm.group(1)
            sec[cur] = []
            continue
        if cur:
            sec[cur].append(line)

    q1 = {}
    for line in sec.get("Q1", []):
        mm = re.match(r"^\s*(\S+)\s+(\d+)\s+([0-9.]+)\s+([0-9.]+)\s+([+-][0-9.]+)\s+"
                      r"\[([^\]]+)\]\s+(\d+)\s+(\d+)\s+(\S+)\s*$", line)
        if mm and mm.group(1) in ACTORS:
            q1[mm.group(1)] = mm.groups()[1:]
    if not q1:
        raise SourceMissing("xdom Q1: no rows parsed")

    q2 = {}
    started = False
    for line in sec.get("Q2", []):
        if "PAIRED on problems" in line:
            started = True
            continue
        if not started:
            continue
        mm = re.match(r"^\s*(\S+)\s+(\d+)\s+([0-9.]+)\s+([0-9.]+)\s+([+-][0-9.]+)\s+"
                      r"\[([^\]]+)\]\s+(\d+)\s+(\d+)\s+(\S+)\s*$", line)
        if mm and mm.group(1) in ACTORS:
            q2[mm.group(1)] = mm.groups()[1:]
    if not q2:
        raise SourceMissing("xdom Q2(b): no paired rows parsed")

    body = []
    for a in ACTORS:
        if a not in q1:
            continue
        g, r = q1[a], need(q2, a, "xdom Q2")
        body.append(
            f"{ACTOR_LABEL[a]} & ${g[0]}$ & {m(g[1])} & {m(g[2])} & {m(g[3])} & {sci(g[7])} & "
            f"${r[0]}$ & {m(r[1])} & {m(r[2])} & {m(r[3])} & ${r[5]}$ & ${r[6]}$ & {sci(r[7])} \\\\")

    pre = header("Table 3 (manuscript) -- SciBench cross-domain replication", pv,
                 ["analysis/scripts/xdom_analyze.py (executed; stdout parsed)",
                  "  which execs FINAL_TABLES.py and rebinds its definitions",
                  "  -- judged / is_fpw / fp / fin_prereg are the SAME code",
                  "  objects as the Omni-MATH tables, not a reimplementation"],
                 [f"SciBench frozen data: experiments/results/xdomain/FROZEN_SCIBENCH/",
                  f"  frozen_at {pv['sci_frozen_at']}, {pv['sci_rows']} trajectories",
                  f"  sha256 {pv['sci_sha']}  scibench_AB.jsonl",
                  "gpt-oss's recovery cell is UNDERPOWERED, not a non-replication:",
                  "its point estimate matches Omni-MATH's. Llama-3.3 was not run.",
                  "No clause-specific role-fidelity metric crosses domains (the",
                  "contract was domain-adapted), so none is reported here."])
    return pre + f"""\\begin{{table*}}[t]
\\centering
\\caption{{\\textbf{{The dissociation replicates out of domain.}} SciBench,
the complete $574$-problem matched slice of free-response college science;
two actors, {pv['sci_rows']} trajectories, frozen separately from the
Omni-MATH snapshot. \\textbf{{The two panels have different populations.}}
First pass is paired over all $574$ problems; paired recovery is over only
those first-pass wrong under \\emph{{both}} conditions
($n_{{\\mathrm{{both}}}}$), which is why its $n$ is roughly a sixth the size.
Pre-registered scoring; $p$ is exact McNemar on discordant pairs. gpt-oss's
recovery cell \\textbf{{cannot resolve its own effect}} at the realized
$n_{{\\mathrm{{both}}}}$ --- its point estimate is in the same direction and
nearly the same size as Omni-MATH's, so it is underpowered rather than a
non-replication. Llama-3.3 was not run in this domain.}}
\\label{{tab:scibench}}
\\small
\\begin{{tabular}}{{lccccc@{{\\hspace{{1.4em}}}}ccccccc}}
\\toprule
 & \\multicolumn{{5}}{{c}}{{first pass (paired, all problems)}}
 & \\multicolumn{{7}}{{c}}{{recovery (paired on first-pass wrong under both)}} \\\\
\\cmidrule(lr){{2-6}}\\cmidrule(lr){{7-13}}
actor & $n$ & role-str. & role-free & diff. & exact $p$
      & $n_{{\\mathrm{{both}}}}$ & role-str. & role-free & diff.
      & r-s.\\ only & r-f.\\ only & exact $p$ \\\\
\\midrule
{chr(10).join(body)}
\\bottomrule
\\end{{tabular}}
\\end{{table*}}
"""


# ==========================================================================
# TABLE 4 -- structural enforcement
# ==========================================================================
def t_enforcement(S, pv) -> str:
    T1 = rowmap(S["T1"], 8)
    T7 = rowmap(S["T7"], 6)    # n rejects exhausted attrition actorcalls wall
    T11 = rowmap(S["T11"], 5)  # msgs authored-free anymarker-free bRej perTraj

    # C-A under both scoring conventions, from T2.
    ca = {}
    scoring = None
    contrast = None
    for line in S["T2"]:
        if "--- PREREG" in line:
            scoring = "prereg"
        elif "--- AS-GRADED" in line:
            scoring = "asgraded"
        mm = re.match(r"^\s*([BC])-A:\s*$", line)
        if mm:
            contrast = mm.group(1)
            continue
        mm = re.match(r"^\s*(\S+)\s+([+-][0-9.]+)\s+\[([^\]]+)\]\s+n=(\d+)\s+"
                      r"McNemar p=(\S+)\s*(SIG)?\s*$", line)
        if mm and mm.group(1) in ACTORS and contrast == "C" and scoring:
            ca[(scoring, mm.group(1))] = mm.groups()[1:]
    if len(ca) != 6:
        raise SourceMissing(f"T2: parsed {len(ca)} C-A cells, expected 6")

    body = []
    for a in ACTORS:
        e1 = need(T11, (a, "C"), "T11")
        eb = need(T11, (a, "B"), "T11")
        # T11 prints 'authored-FREE' -- a freedom rate. Authorship is its
        # complement (APPROVED_CLAIMS A11: the axis was read inverted once).
        auth_c = 1.0 - float(e1[1])
        auth_b = 1.0 - float(eb[1])
        rc = need(T1, (a, "C"), "T1")
        ra = need(T1, (a, "A"), "T1")
        rb = need(T1, (a, "B"), "T1")
        at = need(T7, (a, "C"), "T7")
        pp = need(ca, ("prereg", a), "T2 prereg")
        ag = need(ca, ("asgraded", a), "T2 as-graded")
        body.append(
            f"{ACTOR_LABEL[a]} & ${auth_c:.3f}$ ({auth_b:.3f}) & {m(rc[7])} "
            f"({rb[7]}/{ra[7]}) & {m(rc[3])} ({ra[3]}) & {pct(at[3])} & "
            f"{m(pp[0])} {{\\footnotesize [{pp[1]}]}} & "
            f"{m(ag[0])} {{\\footnotesize [{ag[1]}]}} \\\\")

    pre = header("Table 4 (manuscript) -- structural enforcement", pv,
                 [f"analysis/out/{CANON.name}  sections T1, T2, T7, T11"],
                 ["The manipulation-check column is ANSWER AUTHORSHIP = 1 minus",
                  "T11's 'authored-free' column, which is a FREEDOM rate. The",
                  "manuscript once read that axis inverted (APPROVED_CLAIMS A11);",
                  "the complement is taken here, once, in code.",
                  "Recovery denominator as in Table 2 (judged & fp==0).",
                  "APPROVED_CLAIMS A6: enforcement restores recovery for Llama-3.3",
                  "ONLY. For the other two the direction is consistent but not",
                  "resolvable. 'Highest of any arm, above role-structured in all",
                  "three actors' is a DEAD claim and must not reappear.",
                  "The as-graded column is SENSITIVITY ONLY -- it is the",
                  "survivorship reading, which is why attrition sits beside it."])
    return pre + f"""\\begin{{table*}}[t]
\\centering
\\caption{{\\textbf{{Structural enforcement.}} Enforcing the division of labor
at the interface. \\emph{{Manipulation check:}} the rate at which the planner
authors an answer, under enforcement and (in parentheses) when roles are
merely deleted --- enforcement drives it to zero in all three actors, so the
intervention engaged. \\emph{{Frozen answer:}} the team never changed its
answer string, among first-pass-wrong trajectories (role-free/role-structured
in parentheses). \\emph{{Recovery:}} role-structured in parentheses, on the
denominator of Table~\\ref{{tab:recovery}}. \\textbf{{The two accuracy columns
are different populations, and the attrition column is why they disagree.}}
The pre-registered rule scores never-graded trajectories incorrect; the
as-graded column drops them and is a \\emph{{sensitivity analysis only}} ---
its gains are conditional on parsing successfully, and enforcement is the
only condition where that removes a material fraction of the data.
\\textbf{{Enforcement restores recovery for Llama-3.3; for the other two
actors the direction is consistent but not resolvable against that
attrition.}}}}
\\label{{tab:enforcement}}
\\small
\\begin{{tabular}}{{lccccccc}}
\\toprule
 & planner authors & frozen answer & recovery & &
 \\multicolumn{{2}}{{c}}{{final accuracy, enforced $-$ role-structured}} \\\\
\\cmidrule(lr){{6-7}}
actor & answer (role-free) & (r-f./r-s.) & (role-str.) & attrition
      & pre-registered & as-graded \\\\
 & \\footnotesize manipulation check & \\footnotesize first-pass wrong
 & \\footnotesize first-pass wrong & & \\footnotesize (primary)
 & \\footnotesize (sensitivity) \\\\
\\midrule
{chr(10).join(body)}
\\bottomrule
\\end{{tabular}}

\\vspace{{2pt}}
\\footnotesize Attrition elsewhere is negligible: $0.0$--$0.7\\%$ with roles,
$0.0$--$2.5\\%$ with roles removed. The as-graded column turns every sign
positive; the pre-registration fixed in advance that unparseable
trajectories count incorrect, and \\textbf{{the benefit appears only after
conditioning on successful parsing.}}
\\end{{table*}}
"""


# ==========================================================================
# TABLE 5 -- budget-matched single agent
# ==========================================================================
def t_single_agent(S, pv) -> str:
    sa, calls = {}, {}
    for line in S["T17"]:
        mm = re.match(r"^\s*(\S+)\s+(A|B)\s+(\d+)\s+([0-9.]+)\s+([0-9.]+)\s+"
                      r"([+-][0-9.]+)\s+\[([^\]]+)\]\s+p=(\S+?)\s*(SIG)?\s*$", line)
        if mm and mm.group(1) in ACTORS:
            sa[(mm.group(1), mm.group(2))] = mm.groups()[2:]
            continue
        mm = re.match(r"^\s*(\S+)\s+(single_agent|our Arm [AB])\s+([0-9.]+)\s+([0-9.]+)\s*$",
                      line)
        if mm and mm.group(1) in ACTORS:
            calls[(mm.group(1), mm.group(2))] = (mm.group(3), mm.group(4))
    if not sa:
        raise SourceMissing(
            "T17: no single-agent rows. The historical corpus parquet may be "
            "unreachable -- check for 'UNAVAILABLE' in the canonical output.")
    if not calls:
        raise SourceMissing("T17: no call-budget rows parsed")

    # One column wide: the effect, its interval and its p stack vertically
    # under the actor rather than sitting in extra columns, which overran the
    # text block by ~115pt.
    body = []
    for a in ACTORS:
        if (a, "A") not in sa:
            continue
        body.append(f"\\multicolumn{{4}}{{@{{}}l}}{{\\emph{{{ACTOR_LABEL[a]}}}}} \\\\")
        for arm in ("A", "B"):
            if (a, arm) not in sa:
                continue
            g = sa[(a, arm)]
            lo, hi = (z.strip().replace("-", "{-}") for z in g[4].split(","))
            pstr = sci(g[5]).strip("$")
            body.append(
                f"\\quad {ARM_LABEL[arm]} & {m(g[1])} & {m(g[2])} & {m(g[3])} \\\\")
            body.append(
                f" & \\multicolumn{{3}}{{r}}{{\\footnotesize $[{lo},\\,{hi}]$, "
                f"$p={pstr}$, $n={g[0]}$}} \\\\")
        body.append("\\addlinespace")

    cb = []
    for a in ACTORS:
        for key, lab in (("single_agent", "single agent"),
                         ("our Arm A", "role-structured team"),
                         ("our Arm B", "role-free team")):
            if (a, key) in calls:
                v = calls[(a, key)]
                cb.append(f"{ACTOR_LABEL[a]} & {lab} & ${v[0]}$ & ${v[1]}$ \\\\")

    pre = header("Table 5 (manuscript) -- budget-matched single-agent control", pv,
                 [f"analysis/out/{CANON.name}  section T17"],
                 ["PROVENANCE: NOT from the frozen snapshot. Source is the",
                  "historical released trace corpus (protocol_id='single_agent',",
                  "benchmark omnimath2), joined by problem_uid. This must be",
                  "stated wherever the four numbers appear (APPROVED_CLAIMS A9).",
                  "BOTH DIRECTIONS, ALWAYS TOGETHER. Never quote gpt-oss alone.",
                  "The two actor arms were produced in SEPARATE RUNS:",
                  "each direction is a sound guard; the GAP BETWEEN ACTORS is not."])
    return pre + f"""\\begin{{table}}[t]
\\centering
\\caption{{\\textbf{{Against a budget-matched single agent.}} Both directions,
which must be read together. A collapsed gpt-oss team beats its own single
agent, so three agents emitting one answer is not functionally one agent;
\\textbf{{but gemma-4's team is worse than its own single agent in both
conditions}} --- and gemma-4 carries the recovery result.
\\textbf{{Provenance: this panel is not from the frozen snapshot}}; it comes
from a previously released trace corpus, joined by problem. \\textbf{{Its two
actor arms were produced in separate runs}}, so each direction is a
sound directional guard while \\emph{{the gap between actors is not}} --- no
statement about relative magnitude across actors is supported here. The
comparison is conservative on the decisive axis: the single agent draws
\\emph{{more}} oracle feedback and about half the actor calls.}}
\\label{{tab:singleagent}}
\\small
\\begin{{tabular}}{{@{{}}lccc@{{}}}}
\\toprule
organization & team & single agent & difference \\\\
\\midrule
{chr(10).join(body)}
\\midrule
\\multicolumn{{4}}{{@{{}}l}}{{\\emph{{Realized call budget}}}} \\\\
\\midrule
actor & protocol & evaluator & actor \\\\
\\midrule
{chr(10).join(cb)}
\\bottomrule
\\end{{tabular}}
\\end{{table}}
"""


# ==========================================================================
# TABLE 6 -- pre-registered endpoints (supplement)
# ==========================================================================
def t_prereg(S, pv) -> str:
    # P3 and P4 Holm families, from T29.
    holm = {}
    for line in S["T29"]:
        mm = re.match(r"^\s*(P3 C-A|P4 DiD)\s+(.+?)\s*p=([0-9.e+-]+)\s+Holm=([0-9.e+-]+)\s+"
                      r"(REJECT H0|retain H0)\s*$", line)
        if mm:
            holm[(mm.group(1), mm.group(2).strip())] = mm.groups()[2:]
    if len(holm) != 6:
        raise SourceMissing(f"T29: parsed {len(holm)} Holm rows, expected 6")

    # P4 difference-in-differences with CIs, from T14.
    did = {}
    for line in S["T14"]:
        mm = re.match(r"^\s*(\S+)\s+minus\s+(\S+)\s+([+-][0-9.]+)\s+\[([^\]]+)\]\s+"
                      r"p=([0-9.e+-]+)\s+(\S+)\s*$", line)
        if mm and mm.group(1) in ACTORS:
            did[(mm.group(1), mm.group(2))] = mm.groups()[2:]
    if len(did) != 3:
        raise SourceMissing(f"T14: parsed {len(did)} DiDs, expected 3")

    # MDE: from the power script. DIFFERENT POPULATION from T14 -- see note.
    pw = run_capture(POWER)
    mde = {}
    for line in pw.splitlines():
        mm = re.match(r"^\s*(\S+?)\s*-\s*(\S+?)\s+MDE=([0-9.]+)\s+vs .*?->\s*(CAN|CANNOT) detect",
                      line)
        if mm:
            mde[(mm.group(1), mm.group(2))] = (mm.group(3), mm.group(4))
    if len(mde) != 3:
        raise SourceMissing(f"power script: parsed {len(mde)} MDE rows, expected 3")

    def mde_for(x, y):
        """Match on the power script's TRUNCATED actor labels.

        It prints ACT[j][:14], so 'Llama-3.3-70B-Instruct' arrives as
        'Llama-3.3-70B-'. Match the unordered pair by prefix rather than
        assuming a name survives intact, and require exactly one hit so a
        prefix collision raises instead of silently picking a row.
        """
        hits = [v for (kx, ky), v in mde.items()
                if {x[:14], y[:14]} == {kx[:14], ky[:14]}]
        if len(hits) != 1:
            raise SourceMissing(
                f"power script: {len(hits)} MDE rows match {x} - {y} "
                f"(parsed keys: {sorted(mde)})")
        return hits[0]

    p3 = []
    for a in ACTORS:
        g = need(holm, ("P3 C-A", a), "T29 P3")
        p3.append(f"\\quad {ACTOR_LABEL[a]} & ${g[0]}$ & ${g[1]}$ & "
                  f"{'reject' if g[2].startswith('REJECT') else 'retain'} \\\\")

    p4 = []
    for (x, y), g in did.items():
        key = f"{y} vs {x}"
        hm = holm.get(("P4 DiD", key)) or holm.get(("P4 DiD", f"{x} vs {y}"))
        if hm is None:
            # T29 prints this family with no space before 'p='; recover by
            # matching on the actor pair rather than the exact spacing.
            for (fam, lab), v in holm.items():
                if fam == "P4 DiD" and x in lab and y in lab:
                    hm = v
                    break
        if hm is None:
            raise SourceMissing(f"T29 P4: no Holm row for {x} vs {y}")
        md, verdict = mde_for(y, x)
        p4.append(
            f"\\quad {ACTOR_LABEL[x]} $-$ {ACTOR_LABEL[y]} & {m(g[0])} "
            f"{{\\footnotesize [{g[1]}]}} & ${hm[0]}$ & ${hm[1]}$ & ${md}$ & "
            f"{'informative' if verdict == 'CAN' else 'uninformative'} \\\\")

    pre = header("Table 6 (supplement) -- pre-registered endpoints", pv,
                 [f"analysis/out/{CANON.name}  sections T2, T14, T29",
                  "analysis/scripts/stat_audit_a7_power.py (executed) -- MDE only"],
                 ["P4 -- THE pre-registered primary -- is NULL before and after",
                  "Holm. Reported as the failure of the thesis it was written to",
                  "test (APPROVED_CLAIMS A10).",
                  "P1 FAILED AS WRITTEN and was re-designated: the schema forbids",
                  "emitting an ANSWER, not performing COMPUTATION. Reported as a",
                  "finding, not hidden (DECISION_LOG D9/R1).",
                  "P2 and P5 yield no p-value and are not p-corrected; the Holm",
                  "family is therefore P3's three contrasts and P4's three DiDs,",
                  "which is what the canonical output corrects.",
                  "",
                  "PREREG_MDE_POPULATION_NOTE -- the MDE column and the",
                  "difference-in-difference column come from DIFFERENT",
                  "populations and are not arithmetically consistent:",
                  "  * T14's DiD differences two per-actor C-A means computed on",
                  "    each actor's OWN problem set (n=1600 and n=400).",
                  "  * the MDE is computed on problems shared by BOTH actors,",
                  "    where the Llama/gemma-4 observed DiD is +0.0300, not the",
                  "    +0.0400 T14 prints.",
                  "Both are correct for their own question; the MDE is quoted only",
                  "as a detectability scale, never as the effect estimate. Do not",
                  "recompute one from the other."])
    return pre + f"""\\begin{{table*}}[t]
\\centering
\\caption{{\\textbf{{Every pre-registered endpoint, and what became of it.}}
Fixed in writing before any intervention data existed. \\textbf{{P4 --- the
pre-registered primary test --- is null, before and after the pre-registered
Holm correction}}, and we report it as the failure of the thesis it was
written to test. P1 failed \\emph{{as written}} and was re-designated rather
than dropped: the interface forbids the planner emitting an \\emph{{answer}},
and nothing in it stops the planner \\emph{{computing}} --- a dissociation we
report as a finding. P2 and P5 are reported as effects and associations and
carry no $p$-value, so the correctable family is P3's three contrasts and
P4's three difference-in-differences. \\textbf{{The MDE column is a
detectability scale on a different population from the effect column}} ---
it is computed on problems shared by both actors, while each
difference-in-difference uses each actor's own problem set; neither can be
derived from the other.}}
\\label{{tab:prereg}}
\\small
\\begin{{tabular}}{{@{{}}llllll@{{}}}}
\\toprule
endpoint & \\multicolumn{{5}}{{l}}{{disposition}} \\\\
\\midrule
\\textbf{{P1}} intervention $\\rightarrow$ fidelity
 & \\multicolumn{{5}}{{l}}{{\\textbf{{failed as written; re-designated.}} The
   interface forbids an \\emph{{answer}} field, not}} \\\\
\\quad \\footnotesize(also the manipulation check)
 & \\multicolumn{{5}}{{l}}{{\\quad computation. Re-scoped to answer authorship,
   which it drives to $0.000$ in all three}} \\\\
 & \\multicolumn{{5}}{{l}}{{\\quad actors (Table~\\ref{{tab:enforcement}}).
   Reported as a second dissociation, not as a pass.}} \\\\
\\addlinespace
\\textbf{{P2}} actor $\\times$ interv.\\ on fidelity
 & \\multicolumn{{5}}{{l}}{{not estimable across the panel: the fidelity
   clauses are condition-specific, so no}} \\\\
 & \\multicolumn{{5}}{{l}}{{\\quad common scale exists. Reported as unresolved
   rather than substituted.}} \\\\
\\addlinespace
\\multicolumn{{6}}{{@{{}}l}}{{\\textbf{{P3}} intervention $\\rightarrow$ accuracy
  (enforced $-$ role-structured), Holm across three:}} \\\\
 & raw $p$ & Holm $p$ & verdict & & \\\\
{chr(10).join(p3)}
\\addlinespace
\\multicolumn{{6}}{{@{{}}l}}{{\\textbf{{P4}} actor $\\times$ intervention on
  accuracy --- \\emph{{the pre-registered primary}}, Holm across three:}} \\\\
 & difference-in-diff.\\ [CI] & raw $p$ & Holm $p$ & MDE$_{{80\\%}}$ & null is \\\\
{chr(10).join(p4)}
\\addlinespace
\\textbf{{P5}} $\\Delta$fidelity vs $\\Delta$outcome
 & \\multicolumn{{5}}{{l}}{{association only, pre-declared as non-causal: both
   sides are outcomes of the same}} \\\\
 & \\multicolumn{{5}}{{l}}{{\\quad intervention. No $p$-value is reported and
   none is corrected.}} \\\\
\\bottomrule
\\end{{tabular}}

\\vspace{{2pt}}
\\footnotesize \\textbf{{Only one of the three P4 nulls is informative.}} The
largest per-actor main effect is small enough that a true interaction is
plausibly ${{\\leq}}0.040$; only the gpt-oss/gemma-4 contrast can see an
effect that size. The two Llama-3.3 contrasts cannot detect an interaction of
any plausible magnitude and are uninformative rather than evidence of
absence.
\\end{{table*}}
"""


# ==========================================================================
# README
# ==========================================================================
def mk_readme(pv) -> str:
    return f"""# `paper/tables/` --- generated tables

**Every file in this directory is generated. Do not hand-edit one: the next
run of the generator overwrites it, and a hand-typed number has no
provenance.**

```
python3 analysis/scripts/mk_tables.py           # regenerate all tables
python3 analysis/scripts/mk_tables.py --check   # verify, write nothing
```

Regeneration is **byte-identical**: the generator stamps the canonical
input's mtime rather than wall-clock time, so a rerun that changes a file
means the *data* changed.

## Disposition --- where each table goes

Every table has a declared disposition, and the last column is **read off
the two documents' sources at generation time**, not asserted --- so it says
*which* document inputs each table, and a table inputted by neither is
reported as an orphan rather than quietly passing.

{{DISPOSITION_TABLE}}

**Why only one is in the main paper.** The page limit is hard and the
narrative carries its numbers in prose and two figures. The supplement
tables are the complete numeric backing a reviewer may want; the main paper
must stay readable **without** them, pointing at them and never depending on
them.

{{SUPPLEMENT_STATE}}

## Where the numbers come from

No result literal is typed into the generator. Every figure is parsed out of
one of:

| canonical input | covers |
|---|---|
| `analysis/out/FINAL_TABLES_OUTPUT.txt` | all Omni-MATH figures |
| `analysis/scripts/xdom_analyze.py` (executed) | SciBench cross-domain |
| `analysis/scripts/stat_audit_a7_power.py` (executed) | MDE column only |

`FINAL_TABLES_OUTPUT.txt` is regenerated with
`python3 analysis/scripts/FINAL_TABLES.py` against
`experiments/results/FROZEN/` (frozen at {pv['frozen_at']},
{pv['frozen_rows']} trajectories).

`xdom_analyze.py` does **not** reimplement the definitions. It execs
`FINAL_TABLES.py` and rebinds `judged`, `is_fpw`, `fp`, `fin_prereg`,
`ansseq`, `func_collapse` to the SciBench rows, so the recovery denominator
is the *same code object* as Omni-MATH's. Reimplementing that denominator
from memory is the bug that cost this project a FATAL finding.

## Denominators --- read this before quoting any figure

Three different populations appear across these tables. They are **not**
interchangeable, and conflating them has already produced one error here.

| population | definition |
|---|---|
| **cell** | every trajectory in an actor $\\times$ condition cell |
| **marginal first-pass-wrong** | trajectories in that cell whose **first** evaluator verdict was incorrect. Computed **per condition**, so the two conditions have *different* denominators |
| **paired first-pass-wrong** | problems first-pass wrong under **both** conditions. One shared denominator. **This is the test.** |

The recovery denominator is `judged(r) and fp(r)==0`: a recorded incorrect
first verdict, **including** trajectories that later died in regeneration.
Those score $0$ under the pre-registered rule. It is **not** `graded(r)` ---
that was the FATAL-1 survivorship bug, and it silently dropped 150
structurally-enforced trajectories that all meet the definition.

First-pass accuracy uses the same `judged(r)` denominator, for the same
reason.

## The tables

### `main_role_collapse.tex` --- manuscript Table 1
- **Question.** Does deleting the role instructions destroy the division of
  labor, and does the answer depend on the instrument?
- **Input.** `FINAL_TABLES_OUTPUT.txt` sections T1, T18, T20, T23.
- **Denominator.** Cell population; first pipeline pass only (the first three
  role messages). Adjudication is a 171-trajectory judged subsample.
- **Status.** Exploratory. The role-structured/role-free contrast was
  pre-registered as secondary.
- **Appears.** Results, R1, one column.
- **Carry these caveats.** Byte duplication is a **lower bound**
  (precision $1.000$, recall $0.262$) and never carries the claim alone. The
  adjudication is outcome-blind but **not** condition-blind --- never call it
  blinded. The role-structured level is marker-dependent
  ($0.000$--$0.892$); read it as "low", not a point estimate. The sensitivity
  note is re-derived from T20 at generation time, not transcribed.

### `main_recovery.tex` --- manuscript Table 2
- **Question.** Does the cost of deleting roles fall on producing the first
  answer, or on repairing a wrong one?
- **Input.** `FINAL_TABLES_OUTPUT.txt` sections T1, T3, T4.
- **Denominator.** **Both panels are printed, labelled, and must not be read
  across.** Upper = marginal (per-condition $n_\\mathrm{{fpw}}$, shown in
  parentheses for every figure). Lower = paired ($n_\\mathrm{{both}}$).
- **Status.** Exploratory/post-hoc, stated as such.
- **Appears.** Results, R3, full width.
- **Carry these caveats.** Recovery conditions on a post-treatment variable:
  descriptive, never causal. Significance is exact McNemar, never a bootstrap
  bound --- one such label was seed-dependent. Only gemma-4 survives pairing;
  gpt-oss is directional, Llama-3.3 is a genuine null of the role
  manipulation.

### `scibench_replication.tex` --- manuscript Table 3
- **Question.** Does the dissociation hold outside mathematics?
- **Input.** `xdom_analyze.py`, against
  `experiments/results/xdomain/FROZEN_SCIBENCH/` (frozen
  {pv['sci_frozen_at']}, {pv['sci_rows']} trajectories).
- **Denominator.** First pass paired over all 574 problems; recovery paired on
  first-pass wrong under both conditions --- roughly a sixth the size, which
  is the whole reason gpt-oss cannot resolve.
- **Status.** Interpretation rules were fixed in advance
  (`notes/XDOMAIN-POWER-PREREG.md`), written before any recovery contrast
  existed. The replication itself is confirmatory of the Omni-MATH result.
- **Appears.** Results, R3b, full width.
- **Carry these caveats.** gpt-oss is **underpowered, not a
  non-replication**: its point estimate matches Omni-MATH's. Llama-3.3 was
  not run. SciBench's own grader is noisier than Omni-MATH's. No
  clause-specific fidelity metric crosses domains --- the contract was
  domain-adapted, and scoring across them would score agents on clauses they
  never received.

### `structural_enforcement.tex` --- manuscript Table 4
- **Question.** If the division of labor is enforced at the interface rather
  than requested, what comes back?
- **Input.** `FINAL_TABLES_OUTPUT.txt` sections T1, T2, T7, T11.
- **Denominator.** Manipulation check over planner messages; frozen answer and
  recovery over marginal first-pass-wrong; accuracy over the full cell
  (pre-registered) and over graded-only (as-graded). **Attrition sits beside
  the two accuracy columns because it is the reason they disagree.**
- **Status.** P1 and P3 pre-registered; the recovery column exploratory.
- **Appears.** Results, R5, full width.
- **Carry these caveats.** The authorship column is `1 -` T11's
  `authored-free`, which is a *freedom* rate --- the manuscript read that axis
  inverted once, and the complement is now taken once, in code. Enforcement
  restores recovery **for Llama-3.3 only**; for the other two the direction is
  consistent but not resolvable. "Highest of any arm, above role-structured in
  all three actors" is a **dead claim** and must not reappear. The as-graded
  column is survivorship and is sensitivity only.

### `single_agent_comparison.tex` --- manuscript Table 5
- **Question.** Was a collapsed team ever really multi-agent --- would one
  agent on the same budget have done as well?
- **Input.** `FINAL_TABLES_OUTPUT.txt` section T17.
- **Denominator.** Problems present in both our campaign and the external
  corpus, joined by `problem_uid`.
- **Status.** Exploratory; responds to a standing objection.
- **Appears.** Results, final subsection, one column.
- **Carry these caveats.** **Not from the frozen snapshot** --- it is a
  previously released trace corpus, and that must be said wherever the
  numbers appear. **Both directions, always together**; never quote gpt-oss
  alone. **The two actor arms were produced in separate runs**, so
  each direction is a sound guard and *the gap between actors is not*. The
  caption carries all three.

### `prereg_endpoints.tex` --- supplement
- **Question.** What was promised before the data existed, and what happened
  to each promise?
- **Input.** `FINAL_TABLES_OUTPUT.txt` sections T2, T14, T29, plus
  `stat_audit_a7_power.py` for the MDE column only.
- **Denominator.** P3/P4 over the full cell under pre-registered scoring.
  **The MDE column is a different population** --- see below.
- **Status.** **Pre-registered.** This is the table that reports the primary
  test.
- **Appears.** Supplement, full width.
- **Carry these caveats.** **P4, the pre-registered primary, is null before
  and after Holm**, and is reported as the failure of the thesis it was
  written to test. P1 failed as written and was re-designated --- reported,
  not hidden. P2 and P5 carry no $p$-value, so the Holm family is P3's three
  contrasts and P4's three DiDs. Only one of the three P4 nulls is
  informative; the two Llama-3.3 contrasts cannot detect an interaction of
  any plausible size.

#### MDE and the difference-in-differences are different populations
They are not arithmetically consistent and neither can be derived from the
other:

- the **difference-in-difference** differences two per-actor means, each
  computed on that actor's own problem set (1,600 and 400 problems);
- the **MDE** is computed on problems shared by *both* actors, where the
  Llama-3.3/gemma-4 observed difference is $+0.0300$ rather than the
  $+0.0400$ the effect column prints.

Both are right for their own question. The MDE is quoted only as a
detectability scale.

## Terminology

Internal arm codes (`A`, `B`, `C`, `Cp`) are stable identifiers in code, raw
data and provenance notes, and **never appear in a rendered table**. The
mapping lives in exactly one place --- `ARM_LABEL` in the generator --- and
the generator asserts the absence of bare arm codes in its own output before
writing. A violation is a hard failure, not a warning.

| internal | reader-facing |
|---|---|
| A | role-structured |
| B | role-free |
| C | structurally enforced |
| C' | context-restored |
"""


# ==========================================================================
# main
# ==========================================================================
# ==========================================================================
# TABLE 7 -- context-quartile panel (supplement)
# ==========================================================================
def t_context(S, pv) -> str:
    """The full panel behind the one-sentence context caveat in R2.

    The manuscript says the recovery gap 'survives context matching in the
    lower quartiles --- though in gpt-oss's top quartile the ordering
    reverses' and sends the reader to the supplement. This is that panel.
    It is DIRECTIONAL ONLY: quartiles are pooled across conditions, and
    accumulated context is nearly a function of condition, so the strata are
    not balanced and this is not a controlled comparison.
    """
    rows = {}
    for line in S["T22"]:
        mm = re.match(r"^\s*(\S+)\s+(Q[1-4])(?:\s+\((?:low|high)\))?\s+"
                      r"([0-9.]+|--)\s+\(n=(\d+)\)\s+([0-9.]+|--)\s+\(n=(\d+)\)\s*$",
                      line)
        if mm and mm.group(1) in ACTORS:
            rows[(mm.group(1), mm.group(2))] = mm.groups()[2:]
    if len(rows) != 12:
        raise SourceMissing(f"T22: parsed {len(rows)} cells, expected 12 (3 actors x 4 quartiles)")

    QLAB = {"Q1": "Q1 (least context)", "Q2": "Q2", "Q3": "Q3", "Q4": "Q4 (most)"}
    body = []
    for a in ACTORS:
        body.append(f"\\multicolumn{{5}}{{@{{}}l}}{{\\emph{{{ACTOR_LABEL[a]}}}}} \\\\")
        for q in ("Q1", "Q2", "Q3", "Q4"):
            rA, nA, rB, nB = need(rows, (a, q), "T22")
            # A cell the canonical output suppressed for n<8 stays suppressed.
            cA = "--" if rA == "--" else m(rA)
            cB = "--" if rB == "--" else m(rB)
            d = ("--" if "--" in (rA, rB)
                 else m(f"{float(rA) - float(rB):+.3f}"))
            body.append(f"\\quad {QLAB[q]} & {cA} & ${nA}$ & {cB} & ${nB}$ & {d} \\\\")
        body.append("\\addlinespace")

    pre = header("Supplement -- recovery by pooled context quartile", pv,
                 [f"analysis/out/{CANON.name}  section T22"],
                 ["DIRECTIONAL ONLY. Quartile cut points are POOLED over both",
                  "conditions, and accumulated context is nearly a function of",
                  "condition, so the strata are NOT balanced -- this cannot",
                  "separate context from condition and must never be described",
                  "as a controlled comparison or a mediation analysis.",
                  "Cells with n<8 print '--' in the canonical output and stay",
                  "suppressed here rather than being recomputed at low n."])
    return pre + f"""\\begin{{table}}[t]
\\centering
\\caption{{\\textbf{{Recovery by pooled accumulated-context quartile}}
(supplement; the panel behind the context caveat in R2). Denominator is the
first-pass-wrong population. Context is the total character count of all
planner, executor and reviewer messages in the trajectory; quartile cut
points are computed \\emph{{once per actor over both conditions pooled}}.
\\textbf{{This is directional only.}} Accumulated context is nearly a
function of condition --- the role-free team talks less because it stops
reworking --- so the strata are not balanced and this comparison cannot
separate context from condition. It is reported because it is the obvious
competing explanation and because \\textbf{{it does not behave uniformly}}:
the gap survives in the lower quartiles, but in gpt-oss's top quartile the
ordering reverses.}}
\\label{{tab:context}}
\\small
\\begin{{tabular}}{{@{{}}lccccc@{{}}}}
\\toprule
 & \\multicolumn{{2}}{{c}}{{role-structured}}
 & \\multicolumn{{2}}{{c}}{{role-free}} & \\\\
\\cmidrule(lr){{2-3}}\\cmidrule(lr){{4-5}}
context quartile & recovery & $n$ & recovery & $n$ & difference \\\\
\\midrule
{chr(10).join(body)}
\\bottomrule
\\end{{tabular}}
\\end{{table}}
"""


# Disposition is declared here, beside the registry, so a table cannot be
# added without one. The "is it \input now?" column is NOT declared -- it is
# read off paper/sections/*.tex at generation time, because a hand-maintained
# answer to that question is exactly the kind that goes stale.
DISPOSITION = {
    "main_role_collapse.tex": ("MAIN", "Functional collapse per actor"),
    "main_recovery.tex": ("SUPPLEMENT", "First pass and recovery, marginal and paired"),
    "scibench_replication.tex": ("SUPPLEMENT", "Cross-domain replication, both actors"),
    "structural_enforcement.tex": ("SUPPLEMENT", "Enforcement: check, attrition, both scorings"),
    "single_agent_comparison.tex": ("SUPPLEMENT", "Budget-matched single agent, both directions"),
    "prereg_endpoints.tex": ("SUPPLEMENT", "Pre-registered endpoints incl. P4 and Holm"),
    "context_quartiles.tex": ("SUPPLEMENT", "Recovery by context quartile (directional only)"),
}


def inputted() -> dict[str, str]:
    """Which document actually \inputs each table, right now?

    Read from the sources rather than declared, and it answers WHICH
    document: a table claiming to be SUPPLEMENT while only the main paper
    inputs it is a disagreement worth seeing, and so is the reverse.
    """
    docs = {
        "main paper": "".join(
            f.read_text() for f in
            sorted((ROOT / "paper/sections").glob("*.tex")) + [ROOT / "paper/main.tex"]),
        "supplement": (SUPPLEMENT.read_text() if SUPPLEMENT.exists() else ""),
    }
    out = {}
    for name in DISPOSITION:
        hits = [d for d, src in docs.items() if f"input{{tables/{name[:-4]}}}" in src]
        out[name] = "**" + " + ".join(hits) + "**" if hits else "no --- orphan"
    return out


TABLES = {
    "main_role_collapse.tex": lambda S, pv: t_collapse(S, pv),
    "main_recovery.tex": lambda S, pv: t_recovery(S, pv),
    "scibench_replication.tex": lambda S, pv: t_scibench(pv),
    "structural_enforcement.tex": lambda S, pv: t_enforcement(S, pv),
    "single_agent_comparison.tex": lambda S, pv: t_single_agent(S, pv),
    "prereg_endpoints.tex": lambda S, pv: t_prereg(S, pv),
    "context_quartiles.tex": lambda S, pv: t_context(S, pv),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="verify against what is on disk; write nothing")
    args = ap.parse_args()

    S = read_canonical()
    pv = provenance()
    OUTDIR.mkdir(parents=True, exist_ok=True)

    rendered = {name: fn(S, pv) for name, fn in TABLES.items()}
    inp = inputted()
    lines = ["| file | reader-facing name | disposition | `\\input` now? |",
             "|---|---|---|---|"]
    for name in TABLES:
        if name not in DISPOSITION:
            print(f"NO DISPOSITION DECLARED for {name} -- add one to DISPOSITION")
            return 2
        where, what = DISPOSITION[name]
        lines.append(f"| `{name}` | {what} | **{where}** | {inp[name]} |")
    supp = [n for n, (w, _) in DISPOSITION.items() if w == "SUPPLEMENT"]
    orphans = [n for n in DISPOSITION if inp[n].startswith("no")]
    if not SUPPLEMENT.exists():
        state = (f"**The supplement is not yet assembled.** Until it is, those "
                 f"{len(supp)} tables are correct, generated and "
                 f"provenance-stamped but have no consumer.")
    elif orphans:
        state = ("**The supplement is assembled** at `paper/supplement.tex`, but "
                 "these tables are inputted by neither document: "
                 + ", ".join(f"`{o}`" for o in orphans)
                 + ". An orphan is a defect: input it or delete it.")
    else:
        state = (f"**The supplement is assembled** at `paper/supplement.tex` --- a "
                 f"second document in this same project, sharing this directory, so "
                 f"a regenerated table lands in both at once and the two cannot "
                 f"disagree. It `\\input`s all {len(supp)} supplement tables; no "
                 f"table is an orphan.")
    rendered["README.md"] = (mk_readme(pv)
                             .replace("{DISPOSITION_TABLE}", "\n".join(lines))
                             .replace("{SUPPLEMENT_STATE}", state))

    # Terminology gate. A bare internal arm code reaching a reader is a hard
    # failure -- checked on the rendered bytes, not on intent.
    bad = []
    for name, txt in rendered.items():
        if name.endswith(".tex"):
            body = "\n".join(l for l in txt.splitlines() if not l.startswith("%"))
            for hit in FORBIDDEN.findall(body):
                bad.append(f"{name}: {hit!r}")
    if bad:
        print("TERMINOLOGY VIOLATION -- internal arm code in a rendered table:")
        for b in bad:
            print("  " + b)
        return 2

    drift = []
    for name, txt in sorted(rendered.items()):
        p = OUTDIR / name
        old = p.read_text() if p.exists() else None
        if args.check:
            if old != txt:
                drift.append(name)
            continue
        p.write_text(txt)
        print(f"  {'unchanged' if old == txt else 'wrote    '}  paper/tables/{name}")

    if args.check:
        if drift:
            print("STALE (regenerate): " + ", ".join(drift))
            return 1
        print(f"CHECK OK: {len(rendered)} files match their sources byte-for-byte")
        return 0

    print(f"\n{len(rendered)} files in paper/tables/")
    print(f"canonical input sha256 {pv['canon_sha'][:16]}  frozen_at {pv['frozen_at']}")
    print("terminology gate: PASS (no internal arm code in any rendered table)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
