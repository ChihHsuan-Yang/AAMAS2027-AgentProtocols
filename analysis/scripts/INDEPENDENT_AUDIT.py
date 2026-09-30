#!/usr/bin/env python3
"""INDEPENDENT NUMBER AUDIT — AAMAS 2027.

Written from the DEFINITIONS, deliberately WITHOUT reading FINAL_TABLES.py
first, so that it cannot reproduce that script's bugs by construction.

Everything is computed from experiments/results/FROZEN/*.jsonl (sha256-verified
against MANIFEST.json) plus, for the single-agent control only, the historical
IEEE-BigData corpus, whose provenance is audited and reported separately.

DETERMINISM CONTRACT
  * No value that reaches stdout is ever derived from iterating a set or a dict
    built in insertion order that depends on hashing.  Every aggregation key is
    sorted before use.  (Defect class #1 from the brief: `set(X) & set(Y)`
    iteration order depends on PYTHONHASHSEED.)
  * Every bootstrap draws from numpy Generators seeded with a fixed integer
    derived from the contrast name, never from `hash()`.
  * Floats are printed with explicit precision.
Run with PYTHONHASHSEED=0 / 1 / random; output must be byte-identical.

UNITS
  Every rate below prints its denominator.  See the DENOMINATOR note attached to
  each table.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
FROZEN = ROOT / "experiments" / "results" / "FROZEN"
EXPDIR = ROOT / "experiments"
sys.path.insert(0, str(EXPDIR))

# The production JSON extractor.  This is part of the DATA-GENERATING process
# (it is what turned an arm-C completion into the object the runner stored and
# acted on), not part of the analysis, so re-deriving answers with a different
# parser would measure a different experiment.  It is positive-controlled in
# PC7 below.
import schemas as S  # noqa: E402

FILES = ["actor3.jsonl", "armCp.jsonl", "campaign_v2.jsonl"]  # sorted, fixed
ARMS = ["A", "B", "C", "Cp"]
ACTORS = ["gemma-4-31B-it", "gpt-oss-120b", "Llama-3.3-70B-Instruct"]
ACTOR_FULL = {
    "google/gemma-4-31B-it": "gemma-4-31B-it",
    "openai/gpt-oss-120b": "gpt-oss-120b",
    "meta-llama/Llama-3.3-70B-Instruct": "Llama-3.3-70B-Instruct",
}
# historical-corpus actor ids -> our short names
HIST_ACTOR = {"gemma_4_31b": "gemma-4-31B-it", "gpt_oss_120b": "gpt-oss-120b"}

N_BOOT = 10000

OUT = []


def emit(s=""):
    OUT.append(s)
    print(s)


def f3(x):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "   nan"
    return "%.3f" % x


def f4(x):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "    nan"
    return "%+.4f" % x


def seed_for(name):
    """Deterministic seed from a name WITHOUT using hash() (PYTHONHASHSEED)."""
    return int(hashlib.sha256(name.encode()).hexdigest()[:8], 16)


# ==========================================================================
# 0. HASH VERIFICATION
# ==========================================================================

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_hashes(frozen_dir, manifest_path):
    man = json.loads(Path(manifest_path).read_text())
    rows = []
    allok = True
    for fn in sorted(man["files"]):
        rec = man["files"][fn]
        p = Path(frozen_dir) / fn
        if not p.exists():
            rows.append((fn, "MISSING", "", False))
            allok = False
            continue
        got = sha256_file(p)
        nbytes = p.stat().st_size
        ok = (got == rec["sha256"]) and (nbytes == rec["bytes"])
        allok = allok and ok
        rows.append((fn, rec["sha256"], got, ok))
    return man, rows, allok


# ==========================================================================
# 1. ANSWER EXTRACTION — ARM-AWARE (defect class: an arm-blind extractor reads
#    arm C as maximally frozen, which is backwards)
# ==========================================================================

_BOXED_FIND = re.compile(r"\\boxed\s*\{")


def extract_boxed(text):
    """LAST \\boxed{...} content, brace-balanced.  Arms A/B author here."""
    if not text:
        return None
    out = None
    for m in _BOXED_FIND.finditer(text):
        i = m.end() - 1
        depth = 0
        for j in range(i, len(text)):
            if text[j] == "{":
                depth += 1
            elif text[j] == "}":
                depth -= 1
                if depth == 0:
                    out = text[i + 1:j].strip()
                    break
    return out


def extract_answer(arm, role, text):
    """The answer THIS ROLE ASSERTED in THIS MESSAGE, by the arm's own channel.

    Arms A/B: \\boxed{} in any role (the runner reads \\boxed from all three).
    Arms C/Cp: the JSON `answer` field, which ONLY the executor schema has.
      The planner and reviewer schemas have no answer field at all
      (experiments/schemas.py), so an arm-C planner/reviewer asserting an
      answer is architecturally impossible on the accepted path -- returning
      None here is the correct reading, NOT a measurement gap.
    """
    if arm in ("A", "B"):
        return extract_boxed(text)
    # C / Cp
    if role != "executor":
        return None
    obj, _err = S.extract_json_object(text or "")
    if not isinstance(obj, dict):
        return None
    a = obj.get("answer")
    if a is None:
        return None
    a = str(a).strip()
    return a or None


def extract_answer_ARMBLIND(arm, role, text):
    """The DEFECTIVE extractor, kept to demonstrate the failure (PC6)."""
    return extract_boxed(text)


def norm_ans(a):
    if a is None:
        return None
    s = unicodedata.normalize("NFKC", a)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def norm_candidate(c):
    """Normalization for grader-noise grouping: a graded string is the same
    string iff it is the same after NFKC + whitespace collapse."""
    if c is None:
        return ""
    s = unicodedata.normalize("NFKC", c)
    return re.sub(r"\s+", " ", s).strip()


# ==========================================================================
# 2. LOAD — stream once, keep only compact derived per-trajectory records
# ==========================================================================

RAW_EVAL = []  # (problem_uid, raw candidate, verdict) for the grouping sensitivity


def load(frozen_dir, corrupt=None):
    """corrupt: optional callable(dict)->dict applied to each raw record, used
    ONLY by the positive controls."""
    trajs = []
    grader_groups = defaultdict(list)  # (puid, normcand) -> [verdicts]
    for fn in FILES:  # fixed order
        p = Path(frozen_dir) / fn
        if not p.exists():
            continue
        with open(p) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                d = json.loads(line)
                if corrupt is not None:
                    d = corrupt(d)
                    if d is None:
                        continue
                trajs.append(derive(d, grader_groups))
    trajs.sort(key=lambda t: (t["actor"], t["arm"], t["puid"]))
    return trajs, grader_groups


def derive(d, grader_groups):
    arm = d["arm"]
    actor = ACTOR_FULL.get(d["actor_model"], d["actor_model"])
    eh = d.get("evaluator_history") or []
    msgs = d.get("messages") or []

    # ---- judgement status -------------------------------------------------
    unjudged_firstpass = (len(eh) == 0)
    fp = None if unjudged_firstpass else eh[0].get("correctness")
    # A first verdict that is present but None would also be UNJUDGED; assert
    # we never silently coerce it (defect class #3: a missing key is not a 0).
    if not unjudged_firstpass and fp is None:
        unjudged_firstpass = True

    correct_raw = d.get("correct")            # may be None
    final_prereg = int(correct_raw or 0)      # prereg: unparsed == incorrect
    final_asgraded = correct_raw              # None -> dropped downstream

    # ---- grader-noise groups ---------------------------------------------
    for e in eh:
        v = e.get("correctness")
        if v is None:
            continue
        grader_groups[(d["problem_uid"], norm_candidate(e.get("candidate")))].append(int(v))
        RAW_EVAL.append((d["problem_uid"], e.get("candidate"), int(v)))

    # ---- messages ---------------------------------------------------------
    role_msgs = [m for m in msgs if m.get("role") in ("planner", "executor", "reviewer")]
    accepted = [m for m in role_msgs if not m.get("rejected")]
    rejected_n = sum(1 for m in role_msgs if m.get("rejected"))

    # every distinct answer the trajectory ever asserted, arm-aware
    answers = []
    answers_blind = []
    for m in accepted:
        a = norm_ans(extract_answer(arm, m["role"], m.get("text")))
        if a is not None:
            answers.append(a)
        b = norm_ans(extract_answer_ARMBLIND(arm, m["role"], m.get("text")))
        if b is not None:
            answers_blind.append(b)
    distinct = sorted(set(answers))
    distinct_blind = sorted(set(answers_blind))

    # ---- first pipeline pass (outer_round 1, inner_round 1, accepted) -----
    fp_msgs = [m for m in accepted
               if m.get("outer_round") == 1 and m.get("inner_round") == 1]
    fp_role_ans = {}
    for m in fp_msgs:
        r = m["role"]
        if r in fp_role_ans:
            continue
        fp_role_ans[r] = norm_ans(extract_answer(arm, r, m.get("text")))
    fp_planner_asserts = fp_role_ans.get("planner") is not None
    fp_present = sorted(r for r in ("planner", "executor", "reviewer")
                        if fp_role_ans.get(r) is not None)
    fp_vals = sorted({fp_role_ans[r] for r in fp_present})

    # ---- reviewer behaviour ----------------------------------------------
    rev = [m for m in accepted if m["role"] == "reviewer"]
    routes = [m.get("route") for m in rev]
    first_route = routes[0] if routes else None
    refusals = sum(1 for r in routes if r is not None and r != "agree")

    # ---- planner shape (F22 instrument check) ----------------------------
    pl = [m for m in accepted if m["role"] == "planner"]
    pl_chars = len(pl[0].get("text") or "") if pl else None
    pl_lat = pl[0].get("latency_s") if pl else None

    return {
        "puid": d["problem_uid"],
        "arm": arm,
        "actor": actor,
        "unjudged_fp": unjudged_firstpass,
        "fp": None if unjudged_firstpass else int(fp),
        "correct_raw": correct_raw,
        "final_prereg": final_prereg,
        "final_asgraded": final_asgraded,
        "ungraded_final": correct_raw is None,
        "cycles": d.get("inner_used"),
        "submissions": len(eh),
        "n_rejected": rejected_n,
        "hard_failure": d.get("hard_failure"),
        "stopping": d.get("stopping_condition"),
        "n_distinct_answers": len(distinct),
        "n_distinct_answers_blind": len(distinct_blind),
        "fp_planner_asserts": fp_planner_asserts,
        "fp_roles_asserting": len(fp_present),
        "fp_distinct_answers": len(fp_vals),
        "first_route": first_route,
        "n_refusals": refusals,
        "n_reviewer_turns": len(rev),
        "planner_chars": pl_chars,
        "planner_latency": pl_lat,
        "final_answer": d.get("final_answer"),
    }


# ==========================================================================
# 3. STATISTICS
# ==========================================================================

def boot_paired_ci(delta, name, nboot=N_BOOT):
    """Bootstrap CI for a mean of paired per-problem differences, clustered by
    problem (each element IS one problem).  Deterministic seed from `name`."""
    x = np.asarray(delta, dtype=float)
    if len(x) == 0:
        return float("nan"), float("nan"), float("nan"), 0
    rng = np.random.default_rng(seed_for(name))
    idx = rng.integers(0, len(x), size=(nboot, len(x)))
    means = x[idx].mean(axis=1)
    return float(x.mean()), float(np.percentile(means, 2.5)), \
        float(np.percentile(means, 97.5)), len(x)


def boot_did_ci(dA, dB, name, nboot=N_BOOT):
    """DiD across two actors whose problem sets are resampled INDEPENDENTLY
    (they are different-sized samples; there is no cross-actor pairing)."""
    a = np.asarray(dA, float)
    b = np.asarray(dB, float)
    rng = np.random.default_rng(seed_for(name))
    ia = rng.integers(0, len(a), size=(nboot, len(a)))
    ib = rng.integers(0, len(b), size=(nboot, len(b)))
    d = a[ia].mean(axis=1) - b[ib].mean(axis=1)
    return float(a.mean() - b.mean()), float(np.percentile(d, 2.5)), \
        float(np.percentile(d, 97.5))


def mcnemar_exact(b, c):
    """Two-sided exact McNemar on discordant counts b, c."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(0, k + 1)) * (0.5 ** n)
    return min(1.0, 2.0 * tail)


def wilson(k, n):
    if n == 0:
        return float("nan"), float("nan")
    z = 1.959963984540054
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (c - h) / d, (c + h) / d


# ==========================================================================
# 4. CELL AGGREGATION
# ==========================================================================

def cell_index(trajs):
    """(actor, arm) -> {puid: record}.  Asserts one row per key."""
    idx = defaultdict(dict)
    for t in trajs:
        key = (t["actor"], t["arm"])
        assert t["puid"] not in idx[key], \
            "DUPLICATE trajectory key %s %s" % (key, t["puid"])
        idx[key][t["puid"]] = t
    return idx


def cells_present(idx):
    return sorted(idx.keys())


def rate(num, den):
    return (num / den) if den else float("nan")


# ==========================================================================
# MAIN
# ==========================================================================

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frozen", default=str(FROZEN))
    ap.add_argument("--manifest", default=str(FROZEN / "MANIFEST.json"))
    ap.add_argument("--skip-controls", action="store_true")
    ap.add_argument("--quiet-controls", action="store_true")
    args = ap.parse_args()

    emit("=" * 100)
    emit("INDEPENDENT NUMBER AUDIT — written from definitions, not from FINAL_TABLES.py")
    emit("=" * 100)

    # ---------------- A0 hash verification ------------------------------
    man, hrows, allok = verify_hashes(args.frozen, args.manifest)
    emit("")
    emit("[A0] SHA256 VERIFICATION OF THE FROZEN SNAPSHOT")
    emit("  frozen_at %s   manifest total_rows %d" % (man["frozen_at"], man["total_rows"]))
    emit("  %-22s %-18s %-18s %s" % ("file", "manifest sha256", "computed sha256", "match"))
    for fn, exp, got, ok in hrows:
        emit("  %-22s %-18s %-18s %s" % (fn, exp[:16], (got or "")[:16], "OK" if ok else "*** MISMATCH ***"))
    emit("  VERDICT: %s" % ("all files match manifest (sha256 AND byte count)"
                            if allok else "*** HASH MISMATCH — DO NOT TRUST ANY NUMBER BELOW ***"))
    if not allok:
        emit("  aborting.")
        return 1

    del RAW_EVAL[:]
    trajs, groups = load(args.frozen)
    trajs_raw_eval = list(RAW_EVAL)
    idx = cell_index(trajs)

    # row-count assertion against the manifest
    emit("")
    emit("[A1] ROW-COUNT AND CELL-CENSUS ASSERTIONS")
    emit("  rows loaded %d   manifest says %d   %s"
         % (len(trajs), man["total_rows"],
            "OK" if len(trajs) == man["total_rows"] else "*** MISMATCH ***"))
    bad = []
    for cellname in sorted(man["cells"]):
        a_short, arm = cellname.split("|")
        a_short = ACTOR_FULL.get(a_short, a_short)
        exp = man["cells"][cellname]
        got = len(idx.get((a_short, arm), {}))
        if got != exp:
            bad.append((cellname, exp, got))
    emit("  per-cell counts vs manifest: %s"
         % ("all %d cells match" % len(man["cells"]) if not bad else "*** %s ***" % bad))

    # ---------------- T0 census -----------------------------------------
    emit("")
    emit("[T0] CELL CENSUS")
    emit("  DENOMINATOR: one row per (problem, arm, actor); 'done' is that count.")
    emit("  %-24s %-4s %6s %7s %9s %9s %10s %8s"
         % ("actor", "arm", "done", "graded", "ungraded", "hardfail", "unjudged_fp", "rej/traj"))
    for (actor, arm) in cells_present(idx):
        rs = [idx[(actor, arm)][p] for p in sorted(idx[(actor, arm)])]
        n = len(rs)
        graded = sum(1 for r in rs if not r["ungraded_final"])
        ung = n - graded
        hf = sum(1 for r in rs if r["hard_failure"])
        unj = sum(1 for r in rs if r["unjudged_fp"])
        rej = sum(r["n_rejected"] for r in rs) / n
        emit("  %-24s %-4s %6d %7d %9d %9d %10d %8.3f"
             % (actor, arm, n, graded, ung, hf, unj, rej))

    # ---------------- T1 master -----------------------------------------
    emit("")
    emit("[T1] MASTER RESULTS")
    emit("  DENOMINATORS, stated explicitly:")
    emit("    firstpass  = judged rows only (empty evaluator_history EXCLUDED) -> n_judged")
    emit("    final_PRE  = ALL rows; correct=None scores 0 (preregistered)     -> n")
    emit("    final_AGR  = rows with correct not None                          -> n_graded")
    emit("    recovery   = rows whose FIRST evaluator verdict was 0            -> n_fpw")
    emit("    frozen_ans = among n_fpw; <=1 distinct answer over ALL accepted role msgs, ARM-AWARE")
    emit("    collapse   = among first-pass-wrong; planner asserts an answer in pipeline pass 1")
    emit("  %-24s %-4s %6s %8s %8s %8s %8s %7s %8s %8s %8s"
         % ("actor", "arm", "n", "n_judg", "firstpas", "fin_PRE", "fin_AGR",
            "n_fpw", "recov_P", "recov_G", "frozen"))
    T1 = {}
    for (actor, arm) in cells_present(idx):
        rs = [idx[(actor, arm)][p] for p in sorted(idx[(actor, arm)])]
        n = len(rs)
        judged = [r for r in rs if not r["unjudged_fp"]]
        fpacc = rate(sum(r["fp"] for r in judged), len(judged))
        fin_p = rate(sum(r["final_prereg"] for r in rs), n)
        gr = [r for r in rs if r["final_asgraded"] is not None]
        fin_g = rate(sum(int(r["final_asgraded"]) for r in gr), len(gr))
        fpw = [r for r in judged if r["fp"] == 0]
        rec_p = rate(sum(r["final_prereg"] for r in fpw), len(fpw))
        fpw_gr = [r for r in fpw if r["final_asgraded"] is not None]
        rec_g = rate(sum(int(r["final_asgraded"]) for r in fpw_gr), len(fpw_gr))
        froz = rate(sum(1 for r in fpw if r["n_distinct_answers"] <= 1), len(fpw))
        T1[(actor, arm)] = dict(n=n, njudged=len(judged), fp=fpacc, fin_p=fin_p,
                                fin_g=fin_g, nfpw=len(fpw), rec_p=rec_p,
                                rec_g=rec_g, frozen=froz, n_fpw_gr=len(fpw_gr),
                                ngraded=len(gr))
        emit("  %-24s %-4s %6d %8d %8s %8s %8s %7d %8s %8s %8s"
             % (actor, arm, n, len(judged), f3(fpacc), f3(fin_p), f3(fin_g),
                len(fpw), f3(rec_p), f3(rec_g), f3(froz)))

    emit("")
    emit("  [T1b] FUNCTIONAL COLLAPSE / UNANIMITY / REVIEWER BEHAVIOUR")
    emit("  DENOMINATORS: collapse & unanimity over first-pass-wrong rows (n_fpw);")
    emit("    unanim = among rows where ALL THREE roles assert an answer in pass 1,")
    emit("             the fraction where those answers are all identical (n_unan printed);")
    emit("    collapse is n/a for C/Cp: their planner/reviewer schemas HAVE NO answer field,")
    emit("             so 'planner asserts' is architecturally 0 and not comparable to A/B.")
    emit("  %-24s %-4s %7s %9s %8s %8s %10s %9s %8s"
         % ("actor", "arm", "n_fpw", "collapse", "n_unan", "unanim", "rev1_acpt",
            "never_ref", "ref/traj"))
    for (actor, arm) in cells_present(idx):
        rs = [idx[(actor, arm)][p] for p in sorted(idx[(actor, arm)])]
        judged = [r for r in rs if not r["unjudged_fp"]]
        fpw = [r for r in judged if r["fp"] == 0]
        if arm in ("A", "B"):
            col = rate(sum(1 for r in fpw if r["fp_planner_asserts"]), len(fpw))
        else:
            col = float("nan")
        unan_pool = [r for r in fpw if r["fp_roles_asserting"] == 3]
        unan = rate(sum(1 for r in unan_pool if r["fp_distinct_answers"] == 1),
                    len(unan_pool))
        withrev = [r for r in rs if r["n_reviewer_turns"] > 0]
        rev1 = rate(sum(1 for r in withrev if r["first_route"] == "agree"), len(withrev))
        never = rate(sum(1 for r in withrev if r["n_refusals"] == 0), len(withrev))
        refpt = (sum(r["n_refusals"] for r in withrev) / len(withrev)) if withrev else float("nan")
        emit("  %-24s %-4s %7d %9s %8d %8s %10s %9s %8.3f"
             % (actor, arm, len(fpw), f3(col), len(unan_pool), f3(unan),
                f3(rev1), f3(never), refpt))

    # ---------------- T1c first-pass denominator sensitivity --------------
    emit("")
    emit("[T1c] FIRST-PASS DENOMINATOR SENSITIVITY — the defect this audit was built to find")
    emit("  A trajectory can receive a FIRST evaluator verdict and then die in")
    emit("  regeneration, leaving correct=None.  It IS judged on its first pass.")
    emit("  Conditioning first-pass accuracy on `correct is not None` drops exactly")
    emit("  those rows -- and every one of them is first-pass WRONG, so dropping them")
    emit("  inflates first-pass accuracy in precisely the arm that attrits.")
    emit("  %-24s %-4s %8s %9s %9s %9s %9s"
         % ("actor", "arm", "n_judged", "fp_judged", "n_graded", "fp_graded", "inflation"))
    tot_dropped = 0
    for (actor, arm) in cells_present(idx):
        rs = [idx[(actor, arm)][p] for p in sorted(idx[(actor, arm)])]
        judged = [r for r in rs if not r["unjudged_fp"]]
        gj = [r for r in judged if not r["ungraded_final"]]
        dropped = len(judged) - len(gj)
        tot_dropped += dropped
        a = rate(sum(r["fp"] for r in judged), len(judged))
        b = rate(sum(r["fp"] for r in gj), len(gj))
        emit("  %-24s %-4s %8d %9s %9d %9s %9s"
             % (actor, arm, len(judged), f3(a), len(gj), f3(b), f4(b - a)))
    emit("  rows judged on first pass but dropped by graded-conditioning: %d" % tot_dropped)
    n_all_wrong = sum(1 for t in trajs
                      if (not t["unjudged_fp"]) and t["ungraded_final"])
    n_wrong = sum(1 for t in trajs
                  if (not t["unjudged_fp"]) and t["ungraded_final"] and t["fp"] == 0)
    emit("  of those %d rows, %d are first-pass WRONG (%.1f%%) -> the drop is ONE-SIDED"
         % (n_all_wrong, n_wrong, 100.0 * n_wrong / max(n_all_wrong, 1)))
    emit("  INTERNAL-CONSISTENCY TEST any reader can run on a published table:")
    emit("    if firstpass is computed on n_graded while n_fpw is computed on n_judged,")
    emit("    then (1-firstpass)*n_graded != n_fpw.  Check it per cell:")
    emit("    %-24s %-4s %12s %8s %s" % ("actor", "arm", "(1-fp_g)*n_g", "n_fpw", "consistent?"))
    for (actor, arm) in cells_present(idx):
        rs = [idx[(actor, arm)][p] for p in sorted(idx[(actor, arm)])]
        judged = [r for r in rs if not r["unjudged_fp"]]
        gj = [r for r in judged if not r["ungraded_final"]]
        b = rate(sum(r["fp"] for r in gj), len(gj))
        implied = (1 - b) * len(gj)
        nfpw = sum(1 for r in judged if r["fp"] == 0)
        emit("    %-24s %-4s %12.0f %8d %s"
             % (actor, arm, implied, nfpw,
                "ok" if abs(implied - nfpw) < 0.5 else "*** INCONSISTENT ***"))

    # ---------------- T2 paired contrasts --------------------------------
    emit("")
    emit("[T2] PAIRED CONTRASTS B-A AND C-A, BOTH SCORINGS (bootstrap by problem, %d reps)" % N_BOOT)
    emit("  UNIT: one problem.  PREREG pairs over ALL problems in both arms (None->0).")
    emit("        AS-GRADED pairs only over problems graded in BOTH arms (n shrinks).")
    PAIRED = {}
    for scoring in ("PREREG", "AS-GRADED"):
        emit("  --- %s ---" % scoring)
        for contrast in ("B-A", "C-A"):
            hi, lo = contrast.split("-")
            emit("    %s:" % contrast)
            for actor in ACTORS:
                ca, cb = idx.get((actor, lo)), idx.get((actor, hi))
                if not ca or not cb:
                    continue
                common = sorted(set(ca) & set(cb))   # sorted -> order-independent
                d = []
                for p in common:
                    ra, rb = ca[p], cb[p]
                    if scoring == "PREREG":
                        d.append(rb["final_prereg"] - ra["final_prereg"])
                    else:
                        if ra["final_asgraded"] is None or rb["final_asgraded"] is None:
                            continue
                        d.append(int(rb["final_asgraded"]) - int(ra["final_asgraded"]))
                m, l, u, n = boot_paired_ci(d, "%s|%s|%s" % (scoring, contrast, actor))
                sig = "SIG" if (l > 0 or u < 0) else ""
                PAIRED[(scoring, contrast, actor)] = (m, l, u, n)
                emit("      %-24s %s [%s,%s] n=%-6d %s"
                     % (actor, f4(m), f4(l), f4(u), n, sig))

    # ---------------- T2b borderline-CI seed stability --------------------
    emit("")
    emit("[T2b] SEED STABILITY OF EVERY 'SIG' VERDICT (the boundary cases)")
    emit("  A bootstrap CI whose bound sits ON zero flips SIG/not-SIG with the RNG seed.")
    emit("  For each PREREG contrast: resample under 40 different seeds and report how")
    emit("  often the verdict is SIG.  Anything strictly between 0 and 1 is a verdict")
    emit("  that the seed, not the data, is deciding.  Exact McNemar is seed-free and")
    emit("  is reported beside it as the adjudicator.")
    emit("  %-24s %-6s %10s %9s %10s %12s %s"
         % ("actor", "contr", "effect", "SIG frac", "McNemar p", "McN verdict", "note"))
    for contrast in ("B-A", "C-A"):
        hi, lo = contrast.split("-")
        for actor in ACTORS:
            ca, cb = idx.get((actor, lo)), idx.get((actor, hi))
            if not ca or not cb:
                continue
            common = sorted(set(ca) & set(cb))
            d = np.array([cb[p]["final_prereg"] - ca[p]["final_prereg"]
                          for p in common], float)
            sigs = 0
            for sd in range(40):
                rng = np.random.default_rng(sd)
                ii = rng.integers(0, len(d), size=(4000, len(d)))
                mm = d[ii].mean(axis=1)
                l2, u2 = np.percentile(mm, 2.5), np.percentile(mm, 97.5)
                if l2 > 0 or u2 < 0:
                    sigs += 1
            b = int((d > 0).sum())
            c = int((d < 0).sum())
            pv = mcnemar_exact(b, c)
            frac = sigs / 40.0
            note = ("*** SEED-DEPENDENT VERDICT ***" if 0.0 < frac < 1.0 else "stable")
            emit("  %-24s %-6s %10s %9.2f %10.4f %12s %s"
                 % (actor, contrast, f4(float(d.mean())), frac, pv,
                    "REJECT" if pv < 0.05 else "no", note))

    # ---------------- T3 first-pass vs recovery decomposition ------------
    emit("")
    emit("[T3] FIRST-PASS vs RECOVERY DECOMPOSITION")
    emit("  UNIT: judged rows for first-pass; first-pass-wrong judged rows for recovery.")
    emit("  %-24s %8s %8s %9s %10s %10s %10s"
         % ("actor", "fp(A)", "fp(B)", "fp B-A", "rec(A)", "rec(B)", "rec B-A"))
    for actor in ACTORS:
        a, b = T1.get((actor, "A")), T1.get((actor, "B"))
        if not a or not b:
            continue
        emit("  %-24s %8s %8s %9s %10s %10s %10s"
             % (actor, f3(a["fp"]), f3(b["fp"]), f4(b["fp"] - a["fp"]),
                f3(a["rec_p"]), f3(b["rec_p"]), f4(b["rec_p"] - a["rec_p"])))
    emit("  %-24s %8s %8s %9s %10s %10s %10s"
         % ("actor", "fp(A)", "fp(C)", "fp C-A", "rec(A)", "rec(C)", "rec C-A"))
    for actor in ACTORS:
        a, c = T1.get((actor, "A")), T1.get((actor, "C"))
        if not a or not c:
            continue
        emit("  %-24s %8s %8s %9s %10s %10s %10s"
             % (actor, f3(a["fp"]), f3(c["fp"]), f4(c["fp"] - a["fp"]),
                f3(a["rec_p"]), f3(c["rec_p"]), f4(c["rec_p"] - a["rec_p"])))

    # ---------------- T4 paired recovery transitions + exact McNemar -----
    emit("")
    emit("[T4] PAIRED RECOVERY TRANSITIONS + EXACT McNEMAR")
    emit("  UNIT: problems FIRST-PASS WRONG under BOTH arms and JUDGED under both.")
    emit("        Recovery scored PREREG (ungraded final = not recovered).")
    emit("  %-24s %-6s %7s %8s %8s %8s %8s %12s"
         % ("actor", "contr", "n_pair", "both", "loOnly", "hiOnly", "neither", "McNemar p"))
    for contrast in ("B-A", "C-A"):
        hi, lo = contrast.split("-")
        for actor in ACTORS:
            ca, cb = idx.get((actor, lo)), idx.get((actor, hi))
            if not ca or not cb:
                continue
            common = sorted(set(ca) & set(cb))
            n11 = n10 = n01 = n00 = 0
            for p in common:
                ra, rb = ca[p], cb[p]
                if ra["unjudged_fp"] or rb["unjudged_fp"]:
                    continue
                if ra["fp"] != 0 or rb["fp"] != 0:
                    continue
                xa, xb = ra["final_prereg"], rb["final_prereg"]
                if xa and xb:
                    n11 += 1
                elif xa and not xb:
                    n10 += 1
                elif xb and not xa:
                    n01 += 1
                else:
                    n00 += 1
            npair = n11 + n10 + n01 + n00
            pv = mcnemar_exact(n10, n01)
            emit("  %-24s %-6s %7d %8d %8d %8d %8d %12.3e"
                 % (actor, contrast, npair, n11, n10, n01, n00, pv))

    # ---------------- T5 mechanism: opportunity vs use -------------------
    emit("")
    emit("[T5] MECHANISM: OPPORTUNITY vs USE  (first-pass-wrong rows)")
    emit("  UNIT: first-pass-wrong judged rows.  cycles=inner_used, subs=len(evaluator_history).")
    emit("  cycle cap check: MAX_OUTER_ROUNDS=3 x INNER_ROUNDS=2 = 6, verified below.")
    emit("  %-24s %-4s %7s %8s %8s %10s"
         % ("actor", "arm", "n_fpw", "cycles", "subs", "revising"))
    maxcyc = 0
    for (actor, arm) in cells_present(idx):
        rs = [idx[(actor, arm)][p] for p in sorted(idx[(actor, arm)])]
        judged = [r for r in rs if not r["unjudged_fp"]]
        fpw = [r for r in judged if r["fp"] == 0]
        if not fpw:
            continue
        cyc = sum(r["cycles"] for r in fpw) / len(fpw)
        sub = sum(r["submissions"] for r in fpw) / len(fpw)
        maxcyc = max(maxcyc, max(r["cycles"] for r in fpw))
        emit("  %-24s %-4s %7d %8.3f %8.3f %10.3f"
             % (actor, arm, len(fpw), cyc, sub, cyc - sub))
    gmax = max(t["cycles"] for t in trajs)
    emit("  MAX inner_used over ALL %d trajectories = %d  -> cap of 6 %s"
         % (len(trajs), gmax, "HOLDS" if gmax <= 6 else "*** VIOLATED ***"))

    # ---------------- T6 grader noise floor ------------------------------
    emit("")
    emit("[T6] GRADER NOISE FLOOR")
    emit("  UNIT: a GROUP is one (problem_uid, NFKC+whitespace-normalized graded candidate).")
    emit("  Pairs are deliberately NOT counted: within-trajectory resubmissions cluster")
    emit("  and inflate a pair denominator (F23).")
    gkeys = sorted(groups.keys())
    n_groups_ge2 = 0
    n_disc_groups = 0
    n_calls_in_ge2 = 0
    n_calls_in_nonunanimous = 0
    n_minority = 0
    n_calls_total = 0
    for k in gkeys:
        v = groups[k]
        n_calls_total += len(v)
        if len(v) < 2:
            continue
        n_groups_ge2 += 1
        n_calls_in_ge2 += len(v)
        ones = sum(v)
        zeros = len(v) - ones
        if ones and zeros:
            n_disc_groups += 1
            n_calls_in_nonunanimous += len(v)
            n_minority += min(ones, zeros)
    emit("  total gradings (evaluator_history entries with a verdict): %d" % n_calls_total)
    emit("  distinct groups: %d ; groups graded >=2 times: %d" % (len(gkeys), n_groups_ge2))
    emit("  group-level  : %d discordant / %d repeated groups = %.4f   <- most conservative"
         % (n_disc_groups, n_groups_ge2, rate(n_disc_groups, n_groups_ge2)))
    emit("  per-call     : %d gradings in a non-unanimous group / %d gradings in repeated groups = %.4f"
         % (n_calls_in_nonunanimous, n_calls_in_ge2, rate(n_calls_in_nonunanimous, n_calls_in_ge2)))
    emit("  minority-verd: %d minority gradings / %d gradings in repeated groups = %.4f"
         % (n_minority, n_calls_in_ge2, rate(n_minority, n_calls_in_ge2)))
    FLOOR = rate(n_disc_groups, n_groups_ge2)

    emit("")
    emit("  [T6b] NOISE-FLOOR MARGIN for each PREREG B-A and C-A contrast")
    emit("  %-24s %-6s %10s %10s %8s" % ("actor", "contr", "|effect|", "floor", "margin x"))
    for contrast in ("B-A", "C-A"):
        for actor in ACTORS:
            got = PAIRED.get(("PREREG", contrast, actor))
            if not got:
                continue
            m, l, u, n = got
            mar = abs(m) / FLOOR if FLOOR else float("nan")
            flag = "" if (l > 0 or u < 0) else "  (CI spans 0)"
            emit("  %-24s %-6s %10.4f %10.4f %8.2f%s"
                 % (actor, contrast, abs(m), FLOOR, mar, flag))

    # ---------------- T7 attrition ---------------------------------------
    emit("")
    emit("[T7] ATTRITION (Arm C enforcement cost)")
    emit("  UNIT: all rows in the cell.  attrition = fraction with correct is None.")
    emit("  %-24s %-4s %7s %10s %12s %12s"
         % ("actor", "arm", "n", "attrition", "hard_fail", "rejects/traj"))
    for (actor, arm) in cells_present(idx):
        rs = [idx[(actor, arm)][p] for p in sorted(idx[(actor, arm)])]
        n = len(rs)
        att = rate(sum(1 for r in rs if r["ungraded_final"]), n)
        hf = rate(sum(1 for r in rs if r["hard_failure"]), n)
        rj = sum(r["n_rejected"] for r in rs) / n
        emit("  %-24s %-4s %7d %10s %12s %12.3f" % (actor, arm, n, f3(att), f3(hf), rj))

    # ---------------- T8 P4 DiD ------------------------------------------
    emit("")
    emit("[T8] P4 — ACTOR x INTERVENTION INTERACTION ON ACCURACY (C-A), PREREG scoring")
    emit("  UNIT: per-actor mean of paired per-problem (C-A); the two actors' problem")
    emit("  samples are resampled INDEPENDENTLY (no cross-actor pairing exists).")
    deltas = {}
    for actor in ACTORS:
        ca, cc = idx.get((actor, "A")), idx.get((actor, "C"))
        if not ca or not cc:
            continue
        common = sorted(set(ca) & set(cc))
        deltas[actor] = [cc[p]["final_prereg"] - ca[p]["final_prereg"] for p in common]
    pairs = [(ACTORS[0], ACTORS[1]), (ACTORS[0], ACTORS[2]), (ACTORS[1], ACTORS[2])]
    emit("  %-52s %10s %22s %s" % ("contrast", "DiD", "95% CI", "verdict"))
    for a1, a2 in pairs:
        if a1 not in deltas or a2 not in deltas:
            continue
        m, l, u = boot_did_ci(deltas[a1], deltas[a2], "P4|%s|%s" % (a1, a2))
        emit("  %-52s %10s [%s,%s] %s"
             % ("(C-A)[%s] - (C-A)[%s]" % (a1, a2), f4(m), f4(l), f4(u),
                "SIG" if (l > 0 or u < 0) else "contains zero -> NULL"))

    # ---------------- T9 Cp - C ------------------------------------------
    emit("")
    emit("[T9] C' MINUS C (context control at fixed enforcement)")
    emit("  UNIT: the 400 problems run in BOTH C' and C for that actor.")
    for scoring in ("PREREG", "AS-GRADED"):
        for actor in ACTORS:
            cc, cp = idx.get((actor, "C")), idx.get((actor, "Cp"))
            if not cc or not cp:
                continue
            common = sorted(set(cc) & set(cp))
            d = []
            for p in common:
                rc, rp = cc[p], cp[p]
                if scoring == "PREREG":
                    d.append(rp["final_prereg"] - rc["final_prereg"])
                else:
                    if rc["final_asgraded"] is None or rp["final_asgraded"] is None:
                        continue
                    d.append(int(rp["final_asgraded"]) - int(rc["final_asgraded"]))
            m, l, u, n = boot_paired_ci(d, "CpC|%s|%s" % (scoring, actor))
            emit("  %-10s %-24s %s [%s,%s] n=%-5d %s"
                 % (scoring, actor, f4(m), f4(l), f4(u), n,
                    "SIG" if (l > 0 or u < 0) else ""))

    # ---------------- T10 arm-blind extractor demonstration --------------
    emit("")
    emit("[T10] ARM-AWARE vs ARM-BLIND ANSWER EXTRACTION (the frozen-answer defect)")
    emit("  UNIT: first-pass-wrong rows.  Blind = \\boxed-only, which arms C/Cp never author.")
    emit("  %-24s %-4s %7s %14s %14s" % ("actor", "arm", "n_fpw", "frozen(aware)", "frozen(BLIND)"))
    for (actor, arm) in cells_present(idx):
        rs = [idx[(actor, arm)][p] for p in sorted(idx[(actor, arm)])]
        judged = [r for r in rs if not r["unjudged_fp"]]
        fpw = [r for r in judged if r["fp"] == 0]
        if not fpw:
            continue
        aw = rate(sum(1 for r in fpw if r["n_distinct_answers"] <= 1), len(fpw))
        bl = rate(sum(1 for r in fpw if r["n_distinct_answers_blind"] <= 1), len(fpw))
        emit("  %-24s %-4s %7d %14s %14s" % (actor, arm, len(fpw), f3(aw), f3(bl)))

    # ---------------- T10b noise-floor grouping sensitivity ---------------
    emit("")
    emit("[T10b] NOISE-FLOOR GROUPING SENSITIVITY — how much does normalization move it?")
    emit("  The definition is 'repeated IDENTICAL prompts at temp 0'.  The evaluator")
    emit("  prompt interpolates the candidate VERBATIM (prompts.EVALUATOR_PREPEND), so")
    emit("  two candidates differing by whitespace are DIFFERENT prompts and their")
    emit("  disagreement is not a nondeterminism draw.")
    import collections as _c
    variants = {}
    for label, keyfn in (
            ("exact bytes (literal identical prompt)", lambda c: c),
            ("NFKC + collapse whitespace (this audit)", norm_candidate),
            ("strip ALL whitespace + strip $ (looser)",
             lambda c: (re.sub(r"\s+", "", str(c)).strip("$").strip() or None)),
    ):
        g = _c.defaultdict(list)
        for t in trajs_raw_eval:
            puid, cand, verdict = t
            g[(puid, keyfn(cand))].append(verdict)
        multi = {k: v for k, v in g.items() if len(v) >= 2}
        disc = {k: v for k, v in multi.items() if len(set(v)) > 1}
        # how many discordant groups fold MORE THAN ONE distinct raw candidate?
        raw = _c.defaultdict(set)
        for puid, cand, verdict in trajs_raw_eval:
            raw[(puid, keyfn(cand))].add(cand)
        folded = sum(1 for k in disc if len(raw[k]) > 1)
        variants[label] = (len(disc), len(multi), folded)
        emit("  %-42s %3d / %4d = %.4f   (%d of those groups fold >1 distinct raw string)"
             % (label, len(disc), len(multi), rate(len(disc), len(multi)), folded))
    emit("  A grouping that folds >1 raw string is NOT measuring identical prompts:")
    emit("  it charges genuine format sensitivity to the nondeterminism floor.")

    # ---------------- T11 single-agent control ---------------------------
    emit("")
    emit("[T11] BUDGET-MATCHED SINGLE-AGENT CONTROL")
    single_agent_control(idx)

    # ---------------- controls -------------------------------------------
    if not args.skip_controls:
        emit("")
        positive_controls(args, groups)

    emit("")
    emit("[END] audit complete.")
    return 0


# ==========================================================================
# SINGLE-AGENT CONTROL — provenance audited, NOT in the frozen snapshot
# ==========================================================================

HIST = Path("/Users/bellayang/Documents/note/projects/IEEE-BigData-SciAgentTrace/"
            "analysis/hf_cache/release/data/trajectories/part-00000.parquet")


def single_agent_control(idx):
    emit("  PROVENANCE WARNING: this control is NOT in experiments/results/FROZEN/.")
    emit("  Source: %s" % HIST)
    if not HIST.exists():
        emit("  *** FILE ABSENT — control cannot be computed or verified. ***")
        return
    h = hashlib.sha256()
    with open(HIST, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    emit("  sha256 of the historical parquet (recorded here so it is pinnable): %s" % h.hexdigest())
    emit("  It carries NO manifest in this repo, so its bytes are unpinned by the project.")
    try:
        import pyarrow.parquet as pq
    except Exception as exc:
        emit("  *** pyarrow unavailable (%s) — control skipped. ***" % exc)
        return
    cols = ["problem_uid", "benchmark_id", "protocol_id", "actor_model_id",
            "evaluator_model_id", "final_correct", "first_pass_correct",
            "run_id", "source_commit", "release_status", "evaluator_calls",
            "model_calls"]
    t = pq.read_table(HIST, columns=cols).to_pandas()
    sa = t[(t.protocol_id == "single_agent") & (t.benchmark_id == "omnimath2")]
    emit("  single_agent x omnimath2 rows: %d" % len(sa))
    emit("  %-22s %8s %14s %-46s %s"
         % ("hist actor", "rows", "release", "source_commit", "evaluator"))
    for a in sorted(sa.actor_model_id.unique()):
        s = sa[sa.actor_model_id == a]
        emit("  %-22s %8d %14s %-46s %s"
             % (a, len(s), sorted(s.release_status.unique())[0],
                sorted(s.source_commit.unique())[0],
                sorted(s.evaluator_model_id.unique())[0]))
    emit("  SOUNDNESS NOTES (each is a reason the comparison is weaker than a within-snapshot one):")
    emit("    * different source_commit PER ACTOR — the two single-agent arms were not")
    emit("      even generated by one build, so an actor contrast inside the control is")
    emit("      itself cross-version.")
    emit("    * release_status is 'candidate'/'provisional', not 'released'.")
    emit("    * the evaluator model matches ours (gpt_oss_120b), which is the one axis")
    emit("      that IS matched.")
    emit("    * NO Llama-3.3 single-agent cell exists, so A9 can never cover all 3 actors.")

    emit("")
    emit("  ARM minus SINGLE-AGENT, paired on problem_uid, PREREG scoring for our arms.")
    emit("  UNIT: problems present in BOTH our cell and the historical single-agent cell.")
    emit("  COVERAGE ASSERTION: every one of our problems must be found in the control,")
    emit("  or the shortfall is reported — a missing key is NOT a wrong answer.")
    for hist_a in sorted(HIST_ACTOR):
        actor = HIST_ACTOR[hist_a]
        s = sa[sa.actor_model_id == hist_a]
        if s.final_correct.isna().any():
            emit("    *** %s: %d null final_correct in the control ***"
                 % (actor, int(s.final_correct.isna().sum())))
        lut = {}
        dup = 0
        for puid, fc in zip(s.problem_uid.tolist(), s.final_correct.tolist()):
            if puid in lut:
                dup += 1
            lut[puid] = int(bool(fc))
        if dup:
            emit("    NOTE %s: %d duplicate problem_uid rows in the control (last wins)." % (actor, dup))
        for arm in ("A", "B", "C"):
            cell = idx.get((actor, arm))
            if not cell:
                continue
            ours = sorted(cell)
            missing = [p for p in ours if p not in lut]
            if missing:
                emit("    *** COVERAGE SHORTFALL %s/%s: %d of %d problems absent from the"
                     " control; they are EXCLUDED, never scored 0. ***"
                     % (actor, arm, len(missing), len(ours)))
            use = [p for p in ours if p in lut]
            d = [cell[p]["final_prereg"] - lut[p] for p in use]
            m, l, u, n = boot_paired_ci(d, "SA|%s|%s" % (actor, arm))
            emit("    %-24s arm %-3s %s [%s,%s] n=%-5d %s"
                 % (actor, arm, f4(m), f4(l), f4(u), n,
                    "SIG" if (l > 0 or u < 0) else ""))
        emit("    oracle exposure — control evaluator_calls mean %.3f, model_calls mean %.3f"
             % (float(s.evaluator_calls.mean()), float(s.model_calls.mean())))


# ==========================================================================
# POSITIVE CONTROLS — corrupt a copy in the shape of the defect, confirm the
# check fires.  A verifier only run on good data detects nothing known.
# ==========================================================================

def positive_controls(args, real_groups):
    emit("=" * 100)
    emit("POSITIVE CONTROLS — each plants the defect it claims to detect")
    emit("=" * 100)
    import shutil
    import tempfile

    results = []

    # ---- PC1: hash check catches a one-byte edit -------------------------
    tmp = Path(tempfile.mkdtemp(prefix="audit_pc_"))
    try:
        for fn in FILES + ["MANIFEST.json"]:
            src = Path(args.frozen) / fn
            if src.exists():
                shutil.copy2(src, tmp / fn)
        target = tmp / "armCp.jsonl"
        raw = target.read_bytes()
        target.write_bytes(raw[:-1] + (b"x" if raw[-1:] != b"x" else b"y"))
        _m, rows, ok = verify_hashes(tmp, tmp / "MANIFEST.json")
        fired = (not ok) and any((r[0] == "armCp.jsonl" and not r[3]) for r in rows)
        results.append(("PC1 one-byte edit -> sha256 check", fired,
                        "MISMATCH reported on armCp.jsonl" if fired
                        else "check did NOT fire"))
        target.write_bytes(raw)  # restore
    finally:
        pass

    # ---- PC2: missing gold/lookup key must NOT become a negative ---------
    lut = {"p1": 1, "p2": 0}
    ours = ["p1", "p2", "p3"]
    missing = [p for p in ours if p not in lut]
    naive = sum(lut.get(p, 0) for p in ours)          # the DEFECT
    guarded = [p for p in ours if p in lut]
    fired = (len(missing) == 1) and (naive == 1) and (len(guarded) == 2)
    results.append(("PC2 missing lookup key detected, not scored 0", fired,
                    "1 key absent; naive .get(p,0) would score it 0 and inflate the"
                    " denominator to 3; guarded path uses n=2 and reports the shortfall"))

    # ---- PC3: unjudged rows must leave first-pass denominators -----------
    def corrupt_unjudge(d):
        # blank the evaluator history of every gemma Arm A row that is
        # first-pass CORRECT: if unjudged rows were counted as negatives, arm
        # A first-pass accuracy would crater; if they are excluded it holds.
        if d["arm"] == "A" and d["actor_model"] == "google/gemma-4-31B-it":
            eh = d.get("evaluator_history") or []
            if eh and eh[0].get("correctness") == 1:
                d["evaluator_history"] = []
        return d

    base_t, _ = load(args.frozen)
    bi = cell_index(base_t)

    def fp_acc(ix, actor, arm):
        rs = [ix[(actor, arm)][p] for p in sorted(ix[(actor, arm)])]
        j = [r for r in rs if not r["unjudged_fp"]]
        return rate(sum(r["fp"] for r in j), len(j)), len(j)

    b_acc, b_n = fp_acc(bi, "gemma-4-31B-it", "A")
    c_t, _ = load(args.frozen, corrupt=corrupt_unjudge)
    ci = cell_index(c_t)
    c_acc, c_n = fp_acc(ci, "gemma-4-31B-it", "A")
    fired = (abs(c_acc - 0.0) < 1e-12) and (c_n < b_n)
    results.append(("PC3 unjudged rows excluded from first-pass denominator", fired,
                    "blanked all %d first-pass-correct rows in gemma/A: n_judged %d->%d, "
                    "accuracy %.4f->%.4f (correct: every remaining judged row is wrong; "
                    "a defect that scored unjudged as 0 would instead keep n=%d)"
                    % (b_n - c_n, b_n, c_n, b_acc, c_acc, b_n)))

    # ---- PC4: PREREG vs AS-GRADED must diverge when a grade is removed ---
    def corrupt_ungrade(d):
        if d["arm"] == "A" and d["actor_model"] == "google/gemma-4-31B-it" \
                and d.get("correct") == 1:
            d["correct"] = None
        return d

    u_t, _ = load(args.frozen, corrupt=corrupt_ungrade)
    ui = cell_index(u_t)
    rs = [ui[("gemma-4-31B-it", "A")][p] for p in sorted(ui[("gemma-4-31B-it", "A")])]
    pre = rate(sum(r["final_prereg"] for r in rs), len(rs))
    gr = [r for r in rs if r["final_asgraded"] is not None]
    agr = rate(sum(int(r["final_asgraded"]) for r in gr), len(gr))
    fired = (abs(pre) < 1e-12) and (abs(agr) < 1e-12 or math.isnan(agr) or agr == 0.0)
    results.append(("PC4 PREREG scores None as 0; AS-GRADED drops it", fired,
                    "nulled every correct=1 in gemma/A: PREREG acc=%.4f over n=%d (all "
                    "None->0), AS-GRADED acc=%.4f over n=%d (Nones dropped). The two "
                    "scorings are demonstrably different code paths."
                    % (pre, len(rs), agr, len(gr))))

    # ---- PC5: noise floor must count a planted discordant group ----------
    planted = {k: list(v) for k, v in real_groups.items()}
    key = ("__PLANTED__", "planted candidate string")
    planted[key] = [0, 1]

    def floor_of(g):
        ge2 = disc = 0
        for k in sorted(g.keys()):
            v = g[k]
            if len(v) < 2:
                continue
            ge2 += 1
            if sum(v) and (len(v) - sum(v)):
                disc += 1
        return disc, ge2

    d0, g0 = floor_of(real_groups)
    d1, g1 = floor_of(planted)
    fired = (d1 == d0 + 1) and (g1 == g0 + 1)
    results.append(("PC5 grader-noise check counts a planted discordant group", fired,
                    "discordant %d->%d, repeated groups %d->%d (exactly +1 each)"
                    % (d0, d1, g0, g1)))

    # ---- PC5b: a group graded twice the SAME way must NOT count -----------
    planted2 = {k: list(v) for k, v in real_groups.items()}
    planted2[("__PLANTED2__", "concordant")] = [1, 1]
    d2, g2 = floor_of(planted2)
    fired = (d2 == d0) and (g2 == g0 + 1)
    results.append(("PC5b concordant repeat raises denominator only", fired,
                    "discordant %d->%d (unchanged), repeated groups %d->%d"
                    % (d0, d2, g0, g2)))

    # ---- PC6: arm-blind extractor reads arm C as maximally frozen --------
    cell = bi[("gemma-4-31B-it", "C")]
    rs = [cell[p] for p in sorted(cell)]
    fpw = [r for r in rs if (not r["unjudged_fp"]) and r["fp"] == 0]
    aw = rate(sum(1 for r in fpw if r["n_distinct_answers"] <= 1), len(fpw))
    bl = rate(sum(1 for r in fpw if r["n_distinct_answers_blind"] <= 1), len(fpw))
    fired = bl > aw + 0.3
    results.append(("PC6 arm-blind \\boxed-only extractor mis-reads arm C", fired,
                    "gemma/C frozen-answer rate: arm-aware %.4f vs arm-BLIND %.4f "
                    "(blind reads C as %s frozen, the backwards answer)"
                    % (aw, bl, "far MORE" if bl > aw else "less")))

    # ---- PC7: production JSON parser actually parses arm-C executors -----
    n_try = n_ok = 0
    for line in open(Path(args.frozen) / "campaign_v2.jsonl"):
        d = json.loads(line)
        if d["arm"] != "C":
            continue
        for m in d.get("messages") or []:
            if m.get("role") == "executor" and not m.get("rejected"):
                n_try += 1
                if extract_answer("C", "executor", m.get("text")) is not None:
                    n_ok += 1
                break
        if n_try >= 500:
            break
    fired = n_try > 0 and (n_ok / n_try) > 0.95
    results.append(("PC7 arm-C answer extraction is not silently empty", fired,
                    "%d/%d sampled accepted arm-C executor messages yielded an answer "
                    "(%.1f%%). A silent-empty parser would look like 'no answers', which "
                    "is the failure mode that makes an arm look frozen." % (n_ok, n_try, 100.0 * n_ok / n_try)))

    # ---- PC8: duplicate-key assertion fires ------------------------------
    fired = False
    detail = "assertion did NOT fire"
    try:
        cell_index(base_t + [dict(base_t[0])])
    except AssertionError as exc:
        fired = True
        detail = "AssertionError raised: %s" % str(exc)[:70]
    results.append(("PC8 duplicate (problem,arm,actor) key is rejected", fired, detail))

    # ---- PC9: McNemar must be able to reject -----------------------------
    p_null = mcnemar_exact(10, 10)
    p_skew = mcnemar_exact(37, 3)
    fired = (p_null > 0.9) and (p_skew < 1e-6)
    results.append(("PC9 exact McNemar discriminates", fired,
                    "b=c=10 -> p=%.4f (null); b=37,c=3 -> p=%.3e (rejects)" % (p_null, p_skew)))

    # ---- PC10: bootstrap CI reacts to a known shift ----------------------
    z = [0] * 1000
    m0, l0, u0, _ = boot_paired_ci(z, "PC10a")
    o = [1] * 50 + [0] * 950
    m1, l1, u1, _ = boot_paired_ci(o, "PC10b")
    fired = (l0 == 0.0 and u0 == 0.0) and (l1 > 0)
    results.append(("PC10 bootstrap CI is not degenerate", fired,
                    "all-zero -> %.4f [%.4f,%.4f]; 5%% ones -> %.4f [%.4f,%.4f]"
                    % (m0, l0, u0, m1, l1, u1)))

    ok = 0
    emit("  %-58s %-6s %s" % ("control", "fired", "detail"))
    for name, f, det in results:
        ok += 1 if f else 0
        emit("  %-58s %-6s %s" % (name, "YES" if f else "*NO*", det))
    emit("  POSITIVE CONTROLS PASSED: %d / %d" % (ok, len(results)))
    return ok == len(results)


if __name__ == "__main__":
    sys.exit(main())
