#!/usr/bin/env python3
"""Q1-Q4 for the SciBench cross-domain replication.

DEFINITIONS ARE NOT REIMPLEMENTED.  They are executed out of
analysis/scripts/FINAL_TABLES.py and rebound to the SciBench rows, so
`judged`, `is_fpw`, `fp`, `fin_prereg`, `boxed_all`, `jans`, `nrm`, `ansseq`,
`first3`, `routes`, `func_collapse`, `unanimous` and `boot` are the SAME code
objects the Omni-MATH tables use.  FINAL_TABLES.py is imported, never edited.

Why the exec dance: FINAL_TABLES.py is a script, not a module -- it prints all
its tables at import and hardcodes FROZEN as its source.  We exec it with a
stubbed stdout and a patched `load()` so we get its function objects bound to
our rows without running its Omni-MATH output or touching its files.

Reported per the brief:
  Q1 first-pass accuracy A vs B          (paired bootstrap CI + exact McNemar)
  Q2 recovery | first verdict wrong      (denominator = judged & fp==0,
                                          INCLUDING trajectories that later
                                          died -- FINAL_TABLES FATAL-1 fix)
  Q3 cycles vs submissions (resubmit vs revise)
  Q4 functional collapse (all three agents assert an answer)

NOT reported: P1a or any clause-specific fidelity metric.  The Arm A contract
was domain-adapted, so those clauses differ between domains and scoring
against them across domains would score an agent on an unreceived clause.
"""
from __future__ import annotations
import argparse, collections, io, json, glob, sys
from contextlib import redirect_stdout
from math import comb
from pathlib import Path

import numpy as np

ROOT = Path("/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols")
FT = ROOT / "analysis/scripts/FINAL_TABLES.py"


def load_defs():
    """Exec FINAL_TABLES.py, suppress its output, return its namespace."""
    ns = {"__name__": "ft", "__file__": str(FT)}
    src = FT.read_text()
    with redirect_stdout(io.StringIO()):
        exec(compile(src, str(FT), "exec"), ns)
    return ns


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(ROOT / "experiments/results/xdomain/FROZEN_SCIBENCH"),
                    help="directory of .jsonl, or a single .jsonl")
    ap.add_argument("--boot", type=int, default=20000)
    args = ap.parse_args()

    ns = load_defs()
    # The exact definitions, as code objects from FINAL_TABLES.
    actor, ev, fp = ns["actor"], ns["ev"], ns["fp"]
    judged, is_fpw = ns["judged"], ns["is_fpw"]
    graded, fin_prereg = ns["graded"], ns["fin_prereg"]
    ansseq, routes = ns["ansseq"], ns["routes"]
    func_collapse, unanimous = ns["func_collapse"], ns["unanimous"]
    first3, boxed_all = ns["first3"], ns["boxed_all"]
    RNG = np.random.default_rng(20261008)

    p = Path(args.src)
    files = sorted(glob.glob(str(p / "*.jsonl"))) if p.is_dir() else [str(p)]
    rows = []
    for f in files:
        for l in open(f):
            try:
                rows.append(json.loads(l))
            except Exception:
                pass
    print("=" * 92)
    print("SCIBENCH CROSS-DOMAIN REPLICATION — Q1-Q4")
    print("source: {}".format(args.src))
    for f in files:
        print("  {}  {} rows".format(Path(f).name, sum(1 for _ in open(f))))
    print("definitions: executed from {} (judged/is_fpw/ansseq/... are FINAL_TABLES objects)".format(FT.name))
    print("=" * 92)

    ACT = sorted({actor(r) for r in rows})
    print("\n[X0] CENSUS")
    print(f"{'actor':<20}{'arm':<5}{'n':>7}{'judged':>8}{'graded':>8}{'err':>6}{'fpw':>7}")
    for a in ACT:
        for arm in ("A", "B"):
            g = [r for r in rows if actor(r) == a and r["arm"] == arm]
            if not g:
                continue
            print(f"{a:<20}{arm:<5}{len(g):>7}{sum(judged(r) for r in g):>8}"
                  f"{sum(graded(r) for r in g):>8}"
                  f"{sum(1 for r in g if r.get('error')):>6}"
                  f"{sum(is_fpw(r) for r in g):>7}")

    def boot_d(d, n):
        d = np.asarray(d, float)
        if len(d) < 5:
            return (np.nan, np.nan)
        return tuple(np.percentile(
            [RNG.choice(d, len(d)).mean() for _ in range(n)], [2.5, 97.5]))

    def mcnemar_paired(pairs):
        """pairs = list of (x,y) binary. Exact two-sided binomial on discordants."""
        b = sum(1 for x, y in pairs if y - x == 1)
        c = sum(1 for x, y in pairs if y - x == -1)
        m = b + c
        if m == 0:
            return 1.0, b, c
        return min(1.0, 2 * sum(comb(m, i) for i in range(min(b, c) + 1)) / 2 ** m), b, c

    # ---------------------------------------------------------------- Q1
    print("\n[Q1] FIRST-PASS ACCURACY  (does deleting roles leave it intact?)")
    print("     paired within problem_uid; exact McNemar on discordant pairs")
    print(f"{'actor':<20}{'n_pair':>8}{'fp_A':>8}{'fp_B':>8}{'B-A':>9}{'  95% CI':<22}"
          f"{'B>A':>6}{'A>B':>6}{'exact p':>10}")
    for a in ACT:
        FA = {r["problem_uid"]: fp(r) for r in rows
              if actor(r) == a and r["arm"] == "A" and judged(r)}
        FB = {r["problem_uid"]: fp(r) for r in rows
              if actor(r) == a and r["arm"] == "B" and judged(r)}
        cm = sorted(set(FA) & set(FB))
        if len(cm) < 30:
            continue
        pairs = [(FA[u], FB[u]) for u in cm]
        d = np.array([y - x for x, y in pairs], float)
        lo, hi = boot_d(d, args.boot)
        pv, b, c = mcnemar_paired(pairs)
        print(f"{a:<20}{len(cm):>8}{np.mean([x for x,_ in pairs]):>8.3f}"
              f"{np.mean([y for _,y in pairs]):>8.3f}{d.mean():>+9.4f}"
              f"  [{lo:+.4f},{hi:+.4f}]  {b:>4}{c:>6}{pv:>10.2e}")

    # ---------------------------------------------------------------- Q2
    print("\n[Q2] RECOVERY | FIRST EVALUATOR VERDICT WRONG   (the central claim)")
    print("     denominator = judged(r) and fp(r)==0  — INCLUDES trajectories that")
    print("     later died in regeneration (FINAL_TABLES FATAL-1); PREREG scoring.")
    print("\n  (a) unpaired, per arm")
    print(f"{'actor':<20}{'arm':<5}{'n_fpw':>7}{'recovery':>10}")
    for a in ACT:
        for arm in ("A", "B"):
            g = [r for r in rows if actor(r) == a and r["arm"] == arm and is_fpw(r)]
            if not g:
                continue
            print(f"{a:<20}{arm:<5}{len(g):>7}{np.mean([fin_prereg(r) for r in g]):>10.3f}")

    print("\n  (b) PAIRED on problems first-pass-wrong under BOTH arms  <- the test")
    print(f"{'actor':<20}{'n_both':>8}{'rec_A':>8}{'rec_B':>8}{'B-A':>9}{'  95% CI':<22}"
          f"{'Aonly':>7}{'Bonly':>7}{'exact p':>10}")
    for a in ACT:
        P_ = {r["problem_uid"]: (fp(r), fin_prereg(r)) for r in rows
              if actor(r) == a and r["arm"] == "A" and judged(r)}
        Q_ = {r["problem_uid"]: (fp(r), fin_prereg(r)) for r in rows
              if actor(r) == a and r["arm"] == "B" and judged(r)}
        both = sorted(u for u in set(P_) & set(Q_)
                      if P_[u][0] == 0 and Q_[u][0] == 0)
        if len(both) < 20:
            print(f"{a:<20}{len(both):>8}   (n<20, not reported)")
            continue
        pairs = [(P_[u][1], Q_[u][1]) for u in both]
        d = np.array([y - x for x, y in pairs], float)
        lo, hi = boot_d(d, args.boot)
        pv, b, c = mcnemar_paired(pairs)
        print(f"{a:<20}{len(both):>8}{np.mean([x for x,_ in pairs]):>8.3f}"
              f"{np.mean([y for _,y in pairs]):>8.3f}{d.mean():>+9.4f}"
              f"  [{lo:+.4f},{hi:+.4f}]  {c:>5}{b:>7}{pv:>10.2e}")

    # ---------------------------------------------------------------- Q3
    print("\n[Q3] RESUBMIT vs REVISE  (first-pass-wrong trajectories)")
    print("     cycles = inner_used; submits = len(evaluator_history)")
    print("     frozen = the team never changed its answer string at all")
    print(f"{'actor':<20}{'arm':<5}{'n_fpw':>7}{'cycles':>8}{'submits':>9}{'revising':>10}"
          f"{'agree@t1':>10}{'never_refuse':>14}{'frozen':>8}{'recovery':>10}")
    for a in ACT:
        for arm in ("A", "B"):
            g = [r for r in rows if actor(r) == a and r["arm"] == arm and is_fpw(r)]
            if len(g) < 20:
                continue
            cy = np.array([r.get("inner_used") or 0 for r in g], float)
            su = np.array([len(ev(r)) for r in g], float)
            rr = [routes(r) for r in g]
            t1 = np.mean([v[0] == "agree" for v in rr if v]) if any(rr) else np.nan
            nv = np.mean([not any(z != "agree" for z in v) for v in rr])
            fz = np.mean([len(set(ansseq(r))) <= 1 for r in g])
            print(f"{a:<20}{arm:<5}{len(g):>7}{cy.mean():>8.2f}{su.mean():>9.2f}"
                  f"{(cy-su).mean():>10.2f}{t1:>10.3f}{nv:>14.3f}{fz:>8.3f}"
                  f"{np.mean([fin_prereg(r) for r in g]):>10.3f}")

    print("\n  paired frozen-rate contrast (all judged trajectories):")
    print(f"{'actor':<20}{'n_pair':>8}{'frozen_A':>10}{'frozen_B':>10}{'B-A':>9}"
          f"{'  95% CI':<22}{'exact p':>10}")
    for a in ACT:
        FA = {r["problem_uid"]: int(len(set(ansseq(r))) <= 1) for r in rows
              if actor(r) == a and r["arm"] == "A" and judged(r)}
        FB = {r["problem_uid"]: int(len(set(ansseq(r))) <= 1) for r in rows
              if actor(r) == a and r["arm"] == "B" and judged(r)}
        cm = sorted(set(FA) & set(FB))
        if len(cm) < 30:
            continue
        pairs = [(FA[u], FB[u]) for u in cm]
        d = np.array([y - x for x, y in pairs], float)
        lo, hi = boot_d(d, args.boot)
        pv, _, _ = mcnemar_paired(pairs)
        print(f"{a:<20}{len(cm):>8}{np.mean([x for x,_ in pairs]):>10.3f}"
              f"{np.mean([y for _,y in pairs]):>10.3f}{d.mean():>+9.4f}"
              f"  [{lo:+.4f},{hi:+.4f}]{pv:>10.2e}")

    # ---------------------------------------------------------------- Q4
    print("\n[Q4] FUNCTIONAL COLLAPSE  (do all three agents independently assert an answer?)")
    print("     func_collapse: all of the first three role messages contain \\boxed")
    print("     unanimous: all three assert the SAME normalized answer")
    print(f"{'actor':<20}{'arm':<5}{'n_def':>7}{'collapse':>10}{'n_unan_def':>12}{'unanimous':>11}")
    for a in ACT:
        for arm in ("A", "B"):
            g = [r for r in rows if actor(r) == a and r["arm"] == arm]
            if not g:
                continue
            fc = [func_collapse(r) for r in g]
            fc = [x for x in fc if x is not None]
            un = [unanimous(r) for r in g]
            un = [x for x in un if x is not None]
            if not fc:
                continue
            print(f"{a:<20}{arm:<5}{len(fc):>7}{np.mean(fc):>10.3f}"
                  f"{len(un):>12}{(np.mean(un) if un else np.nan):>11.3f}")

    print("\n  paired collapse contrast:")
    print(f"{'actor':<20}{'n_pair':>8}{'coll_A':>9}{'coll_B':>9}{'B-A':>9}{'  95% CI':<22}{'exact p':>10}")
    for a in ACT:
        FA = {r["problem_uid"]: int(func_collapse(r)) for r in rows
              if actor(r) == a and r["arm"] == "A" and func_collapse(r) is not None}
        FB = {r["problem_uid"]: int(func_collapse(r)) for r in rows
              if actor(r) == a and r["arm"] == "B" and func_collapse(r) is not None}
        cm = sorted(set(FA) & set(FB))
        if len(cm) < 30:
            continue
        pairs = [(FA[u], FB[u]) for u in cm]
        d = np.array([y - x for x, y in pairs], float)
        lo, hi = boot_d(d, args.boot)
        pv, _, _ = mcnemar_paired(pairs)
        print(f"{a:<20}{len(cm):>8}{np.mean([x for x,_ in pairs]):>9.3f}"
              f"{np.mean([y for _,y in pairs]):>9.3f}{d.mean():>+9.4f}"
              f"  [{lo:+.4f},{hi:+.4f}]{pv:>10.2e}")

    # ------------------------------------------- Q4 marker sensitivity
    # FINDING-14 established that a collapse measure keyed on an answer marker
    # must be shown not to depend on that choice. Same three definitions.
    print("\n  [Q4b] MARKER SENSITIVITY of the collapse measure")
    print("        (FINDING-14 requires this: the measure keys on '\\\\boxed')")
    import re as _re
    MARK = {
        "boxed": _re.compile(r"\\boxed\s*\{"),
        "boxed|answer is": _re.compile(r"\\boxed\s*\{|answer is", _re.I),
        "boxed|final answer": _re.compile(r"\\boxed\s*\{|final answer", _re.I),
    }
    print(f"{'actor':<20}{'arm':<5}" + "".join(f"{k:>22}" for k in MARK) + f"{'spread':>9}")
    for a in ACT:
        for arm in ("A", "B"):
            g = [r for r in rows if actor(r) == a and r["arm"] == arm]
            if not g:
                continue
            vals = []
            for _, rx in MARK.items():
                v = []
                for r in g:
                    f = first3(r)
                    if len(f) != 3:
                        continue
                    v.append(all(rx.search(m.get("text") or "") for m in f))
                vals.append(np.mean(v) if v else np.nan)
            print(f"{a:<20}{arm:<5}" + "".join(f"{x:>22.3f}" for x in vals)
                  + f"{(max(vals)-min(vals)):>9.3f}")

    # ------------------------------------------------- final accuracy (context)
    print("\n[X1] FINAL ACCURACY (context; PREREG scoring, paired)")
    print(f"{'actor':<20}{'n_pair':>8}{'acc_A':>8}{'acc_B':>8}{'B-A':>9}{'  95% CI':<22}{'exact p':>10}")
    for a in ACT:
        FA = {r["problem_uid"]: fin_prereg(r) for r in rows
              if actor(r) == a and r["arm"] == "A"}
        FB = {r["problem_uid"]: fin_prereg(r) for r in rows
              if actor(r) == a and r["arm"] == "B"}
        cm = sorted(set(FA) & set(FB))
        if len(cm) < 30:
            continue
        pairs = [(FA[u], FB[u]) for u in cm]
        d = np.array([y - x for x, y in pairs], float)
        lo, hi = boot_d(d, args.boot)
        pv, _, _ = mcnemar_paired(pairs)
        print(f"{a:<20}{len(cm):>8}{np.mean([x for x,_ in pairs]):>8.3f}"
              f"{np.mean([y for _,y in pairs]):>8.3f}{d.mean():>+9.4f}"
              f"  [{lo:+.4f},{hi:+.4f}]{pv:>10.2e}")

    # ------------------------------------------- FINDING-18 exposure, both ways
    print("\n[X2] FINDING-18 EXPOSURE (graded on last SUBMITTED, not last HELD answer)")
    print("     The runner records correct=grade of last submission but")
    print("     final_answer=last answer held. Inherited from runner.py unchanged.")
    print("     Conservative floor: rows recorded WRONG whose HELD answer exactly")
    print("     matches gold after normalization.")
    nrm = ns["nrm"]
    import pandas as pd
    PQ = ("/Users/bellayang/Documents/note/projects/IEEE-BigData-SciAgentTrace/"
          "analysis/hf_cache/release/data/problems/part-00000.parquet")
    try:
        gold = pd.read_parquet(PQ)
        gold = dict(zip(gold.problem_uid, gold.answer))
    except Exception as e:
        gold = {}
        print("     (gold unavailable: {})".format(e))
    print(f"{'actor':<20}{'arm':<5}{'n_fpw':>7}{'mismatch':>10}{'floor_misscored':>17}")
    for a in ACT:
        for arm in ("A", "B"):
            g = [r for r in rows if actor(r) == a and r["arm"] == arm and is_fpw(r)]
            if not g:
                continue
            mism = 0
            floor = 0
            for r in g:
                e = ev(r)
                last_sub = e[-1].get("candidate") if e else None
                held = r.get("final_answer")
                if held is not None and last_sub is not None and nrm(held) != nrm(last_sub):
                    mism += 1
                    gv = gold.get(r["problem_uid"])
                    if gv is not None and fin_prereg(r) == 0 and nrm(held) == nrm(gv):
                        floor += 1
            print(f"{a:<20}{arm:<5}{len(g):>7}{mism/len(g):>10.3f}{floor:>17}")

    print("\n" + "=" * 92)
    print("NOT COMPUTED, DELIBERATELY: P1a and clause-specific role-fidelity metrics.")
    print("The Arm A contract was domain-adapted, so its clauses differ from")
    print("Omni-MATH's. Scoring across domains would score unreceived clauses.")
    print("=" * 92)


if __name__ == "__main__":
    raise SystemExit(main())
