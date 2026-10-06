#!/usr/bin/env python3
"""bf_numbers -- every Arm Bf number in the manuscript, generated from data.

WHAT ARM Bf IS
  Arm B (role-free) never received the evaluator's FAIL verdict or repair
  hint: its prompt template has no ${advice} slot. Arm Bf is Arm B with that
  one defect removed. The same "Evaluator feedback: FAIL ... Repair hint: ..."
  string that Arm A receives is shown to every agent for one cycle, and the
  Arm B prompt is otherwise byte-identical. Design and reading rules are in
  experiments/BF_CONTROL.md, committed before any Bf data existed. Bf was run
  AFTER the frozen snapshot, on the same endpoint, problems and budget. It is a
  post hoc control and is never pooled into a frozen cell.

INPUTS (gitignored data; every sha256 is printed and exported)
  frozen   experiments/results/hf_frozen/raw/{campaign_v2,actor3,scibench_AB}.jsonl
           checked against the MANIFEST.json files committed to git
  Bf       experiments/results/bf/bf_{omnimath,scibench}_*.jsonl
  bridge   experiments/results/bf/bridgeA_omnimath_gemma4_n400.jsonl
           Arm A re-run on 400 frozen problems. This is an endpoint-drift
           check only and is never pooled.
  gold     the problems parquet that runner.py reads (AAMAS_PROBLEMS_PARQUET).
           Used only for the hint-leak check [B10].

OUTPUTS
  analysis/out/BF_TABLES_OUTPUT.txt   this script's stdout
  analysis/out/FIGDATA_BF.json        everything a figure or table may draw

DEFINITIONS are copied verbatim from analysis/scripts/FINAL_TABLES.py. That
module reads a fixed path on another machine at import time, so it cannot be
imported. The positive control [B1] recomputes every frozen cell from the
same files and asserts that it equals analysis/out/FIGDATA.json. If it does
not, the definitions or the inputs differ and nothing below is valid.

Usage (repo root):  python3 analysis/scripts/bf_numbers.py
"""
import argparse
import collections
import glob
import hashlib
import json
import math
import os
import re
import sys
from math import comb

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SEED = 20261008                      # same seed as FINAL_TABLES.py
RNG = np.random.default_rng(SEED)
ACTORS = ["gemma-4-31B-it", "gpt-oss-120b", "Llama-3.3-70B-Instruct"]
ARMS = ("A", "B", "Bf", "C")
DOMAINS = ("omni", "scibench")
DOMAIN_NAME = {"omni": "Omni-MATH", "scibench": "SciBench"}
DOMAIN_OF_BENCH = {"omnimath2": "omni", "scibench": "scibench"}
FROZEN_FILES = {                     # file -> (domain, manifest committed to git)
    "campaign_v2.jsonl": ("omni", "experiments/results/FROZEN/MANIFEST.json"),
    "actor3.jsonl": ("omni", "experiments/results/FROZEN/MANIFEST.json"),
    "scibench_AB.jsonl": ("scibench", "experiments/results/xdomain/FROZEN_SCIBENCH/MANIFEST.json"),
}
INFRA = ("model_unavailable", "runtime_error")
BOX = re.compile(r"\\boxed\s*\{")
PAIRS = (("A", "B"), ("A", "Bf"), ("B", "Bf"), ("C", "Bf"))


# =============================================================================
# Definitions copied from FINAL_TABLES.py (do not edit one without the other)
# =============================================================================
def actor(r): return r["actor_model"].split("/")[-1]
def ev(r):    return r.get("evaluator_history") or []
def graded(r): return bool(ev(r)) and r.get("correct") is not None
def fp(r):    return int(ev(r)[0].get("correctness") or 0) if ev(r) else None
def judged(r): return bool(ev(r))
def is_fpw(r): return judged(r) and fp(r) == 0
def fin_prereg(r): return int(r.get("correct") or 0)          # ungraded -> 0


def boxed_all(t):
    o = []
    for m in BOX.finditer(t or ""):
        i, dd = m.end() - 1, 0
        for j in range(i, min(len(t), i + 4000)):
            if t[j] == "{": dd += 1
            elif t[j] == "}":
                dd -= 1
                if dd == 0: o.append(t[i+1:j]); break
    return o


def jans(t):
    o = [m.group(1) for m in re.finditer(r'"answer"\s*:\s*"((?:[^"\\]|\\.)*)"', t or "")]
    o += [m.group(1) for m in re.finditer(r'"answer"\s*:\s*(-?[0-9][0-9.eE+/-]*)', t or "")]
    return o


def nrm(s):
    if s is None: return None
    s = re.sub(r"\s+", "", str(s)).strip("$").strip(); return s or None


def first3(r):
    return [m for m in (r.get("messages") or []) if m.get("role") in ("planner","executor","reviewer")][:3]


def ansseq(r):
    seq, arm = [], r.get("arm")
    for m in (r.get("messages") or []):
        if m.get("role") not in ("planner","executor","reviewer"): continue
        t = m.get("text") or ""
        for b in boxed_all(t) + (jans(t) if arm in ("C","Cp") else []):
            x = nrm(b)
            if x and (not seq or seq[-1] != x): seq.append(x)
    return seq


def routes(r):
    return [m.get("route") for m in (r.get("messages") or [])
            if m.get("role") == "reviewer" and m.get("route")]


def func_collapse(r):
    f = first3(r)
    if len(f) != 3: return None
    return all(BOX.search(m.get("text") or "") for m in f)


def mcnemar(b, c):
    """Two-sided exact McNemar on discordant counts (FINAL_TABLES T4)."""
    m = b + c
    return min(1.0, 2 * sum(comb(m, i) for i in range(min(b, c) + 1)) / 2 ** m) if m else 1.0


def boot(x, n=20000):                # FINAL_TABLES.boot
    x = np.asarray(x, float)
    if len(x) < 5: return (float("nan"), float("nan"))
    return tuple(float(v) for v in
                 np.percentile([RNG.choice(x, len(x)).mean() for _ in range(n)], [2.5, 97.5]))


def mean_ci(v, n=4000):              # FINAL_TABLES._mean_ci
    v = np.asarray(v, float)
    if len(v) == 0: return (float("nan"),) * 3
    if len(v) < 5: return (float(v.mean()), float("nan"), float("nan"))
    b = np.percentile([RNG.choice(v, len(v)).mean() for _ in range(n)], [2.5, 97.5])
    return float(v.mean()), float(b[0]), float(b[1])


# The repair hint exactly as runner.parse_evaluator extracts it.
def evaluator_hint(text):
    if not text: return ""
    h = re.search(r"Response\s*[:=]\s*(.*)", text, re.DOTALL)
    return (h.group(1).strip() if h else text.strip())[:1500]


# =============================================================================
# One compact feature record per trajectory, so 10k+ trajectories fit in memory
# =============================================================================
def features(r, gold):
    e = ev(r)
    msgs = r.get("messages") or []
    g = nrm(gold.get(r["problem_uid"])) if gold else None
    gold_ok = g is not None and len(g) >= 2      # 1-character golds match by accident
    fails = [x for x in e if int(x.get("correctness") or 0) == 0]
    leaks = sum(1 for x in fails if gold_ok and g in (nrm(evaluator_hint(x.get("raw"))) or ""))
    # FINAL_TABLES T19: the runner grades the last SUBMITTED answer but records
    # the last HELD one (final_answer); count disagreements and the ones where
    # the held answer equals the gold string while the grade is 0.
    held = nrm(r.get("final_answer"))
    last_sub = nrm((e[-1] or {}).get("candidate")) if e else None
    mism = held is not None and last_sub is not None and held != last_sub
    undercredit = bool(mism and g is not None and held == g and fin_prereg(r) == 0)
    return dict(
        uid=r["problem_uid"], arm=r.get("arm"), actor=actor(r),
        stop=r.get("stopping_condition"), cfg=r.get("config_version"),
        budget=json.dumps(r.get("budget") or {}, sort_keys=True),
        judged=judged(r), fp=fp(r), graded=graded(r), fin=fin_prereg(r),
        verdicts=[int(x.get("correctness") or 0) for x in e],
        inner_used=int(r.get("inner_used") or 0),
        actor_calls=int(r.get("actor_calls") or 0),
        evaluator_calls=int(r.get("evaluator_calls") or 0),
        routes=routes(r), frozen=len(set(ansseq(r))) <= 1, collapse=func_collapse(r),
        cand1=nrm(e[0].get("candidate")) if e else None,
        fb_msgs=sum(1 for m in msgs if m.get("evaluator_feedback_in_prompt")),
        actor_msgs=sum(1 for m in msgs if m.get("role") in ("planner", "executor", "reviewer")),
        n_fail=len(fails), gold_ok=gold_ok, n_leak=leaks,
        mismatch=mism, undercredit=undercredit,
    )


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_rows(path):
    bad = 0
    with open(path) as fh:
        for line in fh:
            if not line.strip(): continue
            try:
                yield json.loads(line)
            except Exception:
                bad += 1
    if bad:
        print("  WARNING {}: {} unparseable line(s) skipped".format(os.path.basename(path), bad))


def load_gold(parquet):
    if not parquet or not os.path.exists(parquet):
        return None, "parquet not found: {}".format(parquet)
    try:
        import pyarrow.parquet as pq  # noqa: PLC0415
        t = pq.read_table(parquet, columns=["problem_uid", "answer"]).to_pydict()
    except ImportError:
        try:
            import pandas as pd  # noqa: PLC0415
            df = pd.read_parquet(parquet, columns=["problem_uid", "answer"])
            t = {"problem_uid": list(df["problem_uid"]), "answer": list(df["answer"])}
        except Exception as exc:  # noqa: BLE001
            return None, "cannot read parquet ({})".format(type(exc).__name__)
    return ({str(u): (None if a is None else str(a)) for u, a in zip(t["problem_uid"], t["answer"])},
            "sha256 {}".format(sha256(parquet)[:16]))


# =============================================================================
# Statistics over feature records (dict uid -> feature)
# =============================================================================
def cell_stats(C):
    s = list(C.values())
    j = [f for f in s if f["judged"]]
    fpw = [f for f in s if f["judged"] and f["fp"] == 0]
    fpr = [f for f in s if f["judged"] and f["fp"] == 1]
    unj = [f for f in s if not f["judged"]]
    held = sum(f["fin"] for f in fpr)
    rec = sum(f["fin"] for f in fpw)
    fpm, fplo, fphi = mean_ci([f["fp"] for f in j])
    rcm, rclo, rchi = mean_ci([f["fin"] for f in fpw])
    fnm, fnlo, fnhi = mean_ci([f["fin"] for f in s])
    if j:
        assert abs((1 - fpm) * len(j) - len(fpw)) < 1e-6, "first-pass identity violated"
    fc = [f["collapse"] for f in s if f["collapse"] is not None]
    d = dict(n=len(s), n_judged=len(j), n_unjudged=len(unj),
             n_graded=sum(1 for f in s if f["graded"]), n_fpw=len(fpw),
             firstpass=fpm, firstpass_lo=fplo, firstpass_hi=fphi,
             recovery=rcm, recovery_lo=rclo, recovery_hi=rchi,
             final_prereg=fnm, final_lo=fnlo, final_hi=fnhi,
             collapse=float(np.mean(fc)) if fc else float("nan"),
             decomp=dict(held=held, lost=len(fpr) - held, recovered=rec,
                         unrecovered=len(fpw) - rec, unjudged=len(unj)))
    if len(fpw) >= 20:               # FINAL_TABLES T5 / T28 mechanism columns
        cy = np.array([f["inner_used"] for f in fpw], float)
        su = np.array([len(f["verdicts"]) for f in fpw], float)
        rr = [f["routes"] for f in fpw]
        d["cycles"] = float(cy.mean())
        d["submissions"] = float(su.mean())
        d["revising"] = float((cy - su).mean())
        d["actor_calls"] = float(np.mean([f["actor_calls"] for f in fpw]))
        d["evaluator_calls"] = float(np.mean([f["evaluator_calls"] for f in fpw]))
        t1 = [v[0] == "agree" for v in rr if v]
        d["acc_t1"] = float(np.mean(t1)) if t1 else float("nan")
        d["neverrefuse"] = float(np.mean([not any(z != "agree" for z in v) for v in rr]))
        d["frozen_ans"] = float(np.mean([f["frozen"] for f in fpw]))
    return d


def paired_final(X, Y):
    cm = sorted(set(X) & set(Y))
    d = np.array([Y[u]["fin"] - X[u]["fin"] for u in cm], float)
    lo, hi = boot(d)
    b, c = int((d == -1).sum()), int((d == 1).sum())
    return dict(n=len(cm), delta=float(d.mean()), lo=lo, hi=hi, x_only=b, y_only=c, p=mcnemar(b, c))


def paired_recovery(X, Y):
    both = sorted(u for u in set(X) & set(Y)
                  if X[u]["judged"] and Y[u]["judged"] and X[u]["fp"] == 0 and Y[u]["fp"] == 0)
    t = collections.Counter((X[u]["fin"], Y[u]["fin"]) for u in both)
    b, c = t[(1, 0)], t[(0, 1)]
    n = len(both)
    return dict(n=n, both_rec=t[(1, 1)], x_only=b, y_only=c, both_fail=t[(0, 0)],
                rec_x=(t[(1, 1)] + b) / n if n else float("nan"),
                rec_y=(t[(1, 1)] + c) / n if n else float("nan"), p=mcnemar(b, c))


def strata(X, Y):
    """Final-accuracy difference Y - X split by the first-pass outcome pair.
    Contributions are counts of problems and sum to n * (final_Y - final_X)."""
    cm = sorted(set(X) & set(Y))
    def k(f): return "U" if not f["judged"] else str(f["fp"])
    out = collections.OrderedDict()
    for key in ("11", "10", "01", "00", "1U", "U1", "0U", "U0", "UU"):
        us = [u for u in cm if k(X[u]) + k(Y[u]) == key]
        if not us: continue
        out[key] = dict(n=len(us), fin_x=sum(X[u]["fin"] for u in us),
                        fin_y=sum(Y[u]["fin"] for u in us),
                        contribution=sum(Y[u]["fin"] - X[u]["fin"] for u in us))
    tot = sum(v["contribution"] for v in out.values())
    assert tot == sum(Y[u]["fin"] for u in cm) - sum(X[u]["fin"] for u in cm)
    return dict(n=len(cm), total=tot, strata=out)


def verdict_curve(C, kmax=6):
    """Over first-pass-wrong trajectories: at which verdict did the first PASS come?"""
    fpw = [f for f in C.values() if f["judged"] and f["fp"] == 0]
    if not fpw: return None
    ks = [next((i + 1 for i, x in enumerate(f["verdicts"]) if x == 1), None) for f in fpw]
    reached = {k: sum(1 for f in fpw if len(f["verdicts"]) >= k) for k in range(1, kmax + 1)}
    passed = {k: sum(1 for x in ks if x == k) for k in range(1, kmax + 1)}
    cum = {k: sum(passed[i] for i in range(1, k + 1)) / len(fpw) for k in range(1, kmax + 1)}
    agree = sum(1 for f, x in zip(fpw, ks) if (x is not None) == bool(f["fin"]))
    extra = sum(len(f["verdicts"]) - 1 for f in fpw)    # verdicts after the first FAIL
    rec = sum(1 for x in ks if x is not None)
    return dict(n_fpw=len(fpw), reached=reached, passed=passed, cum=cum,
                extra_verdicts=extra, recovered=rec,
                recoveries_per_extra_verdict=(rec / extra if extra else float("nan")),
                hazard={k: (passed[k] / reached[k] if reached[k] else float("nan"))
                        for k in range(1, kmax + 1)},
                pass_verdict_equals_final=agree)


# =============================================================================
# Output helpers
# =============================================================================
class Tee:
    def __init__(self, path):
        self.f = open(path, "w")
        self.o = sys.stdout
    def write(self, s):
        self.o.write(s); self.f.write(s)
    def flush(self):
        self.o.flush(); self.f.flush()


def clean(x):
    if isinstance(x, dict): return {str(k): clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)): return [clean(v) for v in x]
    if isinstance(x, (np.floating, float)):
        return None if math.isnan(float(x)) else float(x)
    if isinstance(x, np.integer): return int(x)
    return x


def fr(a, b): return "{}/{} = {:.3f}".format(a, b, a / b) if b else "{}/0".format(a)
def ci(m, lo, hi): return "{:.3f} [{:.3f},{:.3f}]".format(m, lo, hi)


def head(t):
    print("\n" + t)
    print("-" * len(t))


# =============================================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frozen-dir", default=os.environ.get(
        "AAMAS_FROZEN_DIR", os.path.join(ROOT, "experiments/results/hf_frozen/raw")))
    ap.add_argument("--bf-dir", default=os.path.join(ROOT, "experiments/results/bf"))
    ap.add_argument("--parquet", default=os.environ.get(
        "AAMAS_PROBLEMS_PARQUET",
        os.path.join(ROOT, "analysis/hf_cache/release/data/problems/part-00000.parquet")))
    ap.add_argument("--figdata", default=os.path.join(ROOT, "analysis/out/FIGDATA.json"))
    ap.add_argument("--out-dir", default=os.path.join(ROOT, "analysis/out"))
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    sys.stdout = Tee(os.path.join(a.out_dir, "BF_TABLES_OUTPUT.txt"))

    print("=" * 96)
    print("BF_NUMBERS -- Arm Bf (role-free + evaluator feedback) against the frozen cells")
    print("generated by analysis/scripts/bf_numbers.py; RNG seed {}".format(SEED))
    print("=" * 96)
    FIG = {"provenance": {"generated_by": "analysis/scripts/bf_numbers.py", "seed": SEED,
                          "files": {}},
           "cells": {}, "paired_final": {}, "paired_recovery": {}, "strata": {},
           "verdict_curve": {}, "first_verdict_agreement": {}, "delivery": {},
           "bridge": {}, "hint_leak": {}, "status": {}}

    # ------------------------------------------------------------------ B0
    head("[B0] INPUTS")
    gold, gmsg = load_gold(a.parquet)
    print("gold answers (hint-leak check only): {}".format(gmsg))
    F = {d: collections.defaultdict(dict) for d in DOMAINS}     # F[dom][(actor, arm)][uid]
    frozen_ok = True
    for name, (dom, manp) in FROZEN_FILES.items():
        p = os.path.join(a.frozen_dir, name)
        if not os.path.exists(p):
            print("frozen {:<22} ABSENT (cells from it are skipped)".format(name))
            continue
        got = sha256(p)
        man = json.load(open(os.path.join(ROOT, manp)))
        want = (man.get("files", {}).get(name) or {}).get("sha256")
        ok = got == want
        frozen_ok &= ok
        n = 0
        for r in read_rows(p):
            n += 1
            f = features(r, gold)
            cell = F[dom][(f["actor"], f["arm"])]
            assert f["uid"] not in cell, ("duplicate frozen row", name, f["actor"], f["arm"], f["uid"])
            cell[f["uid"]] = f
        print("frozen {:<22} {} rows  sha256 {}  manifest {}".format(
            name, n, got[:16], "OK" if ok else "MISMATCH ({})".format((want or "none")[:16])))
        FIG["provenance"]["files"][name] = dict(sha256=got, rows=n, role="frozen", domain=dom,
                                                 manifest_ok=ok)
    assert frozen_ok, "a frozen file does not match its committed MANIFEST: STOP"

    man_bf = {}
    mp = os.path.join(a.bf_dir, "MANIFEST_BF.json")
    if os.path.exists(mp):
        man_bf = json.load(open(mp)).get("files", {})
    BF = {d: collections.defaultdict(dict) for d in DOMAINS}    # BF[dom][actor][uid]
    BRIDGE = collections.defaultdict(dict)                      # BRIDGE[actor][uid]
    health = collections.defaultdict(lambda: dict(stops=collections.Counter(), cfg=set(),
                                                  budget=set(), dropped_unavailable=0))
    for p in sorted(glob.glob(os.path.join(a.bf_dir, "bf_*.jsonl")) +
                    glob.glob(os.path.join(a.bf_dir, "bridgeA_*.jsonl"))):
        name = os.path.basename(p)
        is_bridge = name.startswith("bridgeA_")
        got = sha256(p)
        n = 0
        for r in read_rows(p):
            n += 1
            arm = r.get("arm")
            if (is_bridge and arm != "A") or (not is_bridge and arm != "Bf"):
                continue
            dom = DOMAIN_OF_BENCH.get(r.get("benchmark_id"))
            assert dom, ("unknown benchmark_id", name, r.get("benchmark_id"))
            f = features(r, gold)
            hk = (dom, f["actor"], "bridgeA" if is_bridge else "Bf")
            if f["stop"] == "model_unavailable":      # infrastructure, never an outcome
                health[hk]["dropped_unavailable"] += 1
                continue
            store = BRIDGE[f["actor"]] if is_bridge else BF[dom][f["actor"]]
            prev = store.get(f["uid"])
            if prev is not None:
                # a later good row supersedes an earlier runtime_error row
                assert prev["stop"] in INFRA or f["stop"] in INFRA, ("two outcome rows", name, f["uid"])
                if f["stop"] in INFRA: continue
            store[f["uid"]] = f
        mf =(man_bf.get(name) or {}).get("sha256")
        print("{:<6} {:<36} {} rows  sha256 {}  {}".format(
            "bridge" if is_bridge else "Bf", name, n, got[:16],
            "" if not mf else ("MANIFEST_BF OK" if mf == got else "MANIFEST_BF MISMATCH")))
        FIG["provenance"]["files"][name] = dict(sha256=got, rows=n,
                                                role="bridge" if is_bridge else "Bf",
                                                manifest_bf=(None if not mf else mf == got))
    for dom in DOMAINS:
        for act, C in BF[dom].items():
            h = health[(dom, act, "Bf")]
            for f in C.values():
                h["stops"][f["stop"]] += 1; h["cfg"].add(f["cfg"]); h["budget"].add(f["budget"])
    for act, C in BRIDGE.items():
        h = health[("omni", act, "bridgeA")]
        for f in C.values():
            h["stops"][f["stop"]] += 1; h["cfg"].add(f["cfg"]); h["budget"].add(f["budget"])

    # ------------------------------------------------------------------ B1
    head("[B1] POSITIVE CONTROL: frozen cells recomputed here == analysis/out/FIGDATA.json")
    if not os.path.exists(a.figdata):
        print("FIGDATA.json not found at {} -- positive control NOT run".format(a.figdata))
        FIG["status"]["positive_control"] = "not run"
    else:
        ref = json.load(open(a.figdata))
        checked = 0
        for act in ACTORS:
            for arm in ("A", "B", "C"):
                C = F["omni"].get((act, arm))
                key = "{}|{}".format(act, arm)
                if not C or key not in ref["cells"]: continue
                mine, theirs = cell_stats(C), ref["cells"][key]
                for fld in ("n", "n_fpw", "n_judged", "firstpass", "recovery", "final_prereg",
                            "cycles", "submissions", "revising", "neverrefuse", "frozen_ans"):
                    if fld in theirs:
                        assert abs(float(mine[fld]) - float(theirs[fld])) < 1e-12, (key, fld, mine[fld], theirs[fld])
                assert mine["decomp"]["recovered"] == theirs["decomp"]["recovered"], key
                checked += 1
                print("  Omni-MATH {:<30} OK  (recovery {} , first pass {:.4f})".format(
                    key, fr(mine["decomp"]["recovered"], mine["n_fpw"]), mine["firstpass"]))
        for act, v in sorted((ref.get("scibench") or {}).items()):
            A, B = F["scibench"].get((act, "A")), F["scibench"].get((act, "B"))
            if not A or not B: continue
            pr = paired_recovery(A, B)
            sa, sb = cell_stats(A), cell_stats(B)
            assert pr["n"] == v["n_paired"] and pr["x_only"] == v["discordant_A_only"] \
                and pr["y_only"] == v["discordant_B_only"], ("scibench paired", act)
            assert abs(sa["recovery"] - v["recovery_marginal_A"]) < 1e-12
            assert abs(sb["recovery"] - v["recovery_marginal_B"]) < 1e-12
            assert abs(sa["firstpass"] - v["firstpass_marginal_A"]) < 1e-12
            checked += 1
            print("  SciBench  {:<30} OK  (paired n={} A-only {} B-only {})".format(
                act, pr["n"], pr["x_only"], pr["y_only"]))
        print("  {} frozen cells reproduce FIGDATA.json exactly".format(checked))
        FIG["status"]["positive_control"] = "{} cells OK".format(checked)

    # Bf cells live beside the frozen cells from here on
    CELLS = {d: {} for d in DOMAINS}    # CELLS[dom][(actor, arm)] -> dict uid->feat
    for dom in DOMAINS:
        for (act, arm), C in F[dom].items():
            if arm in ARMS: CELLS[dom][(act, arm)] = C
        for act, C in BF[dom].items():
            CELLS[dom][(act, "Bf")] = C

    # ------------------------------------------------------------------ B2
    head("[B2] Bf RUN HEALTH AND COMPLETENESS")
    pending = []
    for dom in DOMAINS:
        for act in ACTORS:
            A = CELLS[dom].get((act, "A"))
            if not A: continue
            Bf = CELLS[dom].get((act, "Bf"))
            if not Bf:
                print("  {:<9} {:<24} Bf PENDING (no rows yet)".format(DOMAIN_NAME[dom], act))
                pending.append("{}|{}".format(dom, act))
                FIG["status"]["{}|{}".format(dom, act)] = "pending"
                continue
            h = health[(dom, act, "Bf")]
            same = set(Bf) == set(A)
            n_rt = h["stops"].get("runtime_error", 0)
            fbudget = {f["budget"] for f in A.values()}
            status = "complete" if same else "PARTIAL {}/{}".format(len(set(Bf) & set(A)), len(A))
            FIG["status"]["{}|{}".format(dom, act)] = status
            print("  {:<9} {:<24} Bf {}  rows={}  problems == frozen A: {}  runtime_error kept: {}"
                  "  model_unavailable dropped: {}".format(
                      DOMAIN_NAME[dom], act, status, len(Bf), same, n_rt, h["dropped_unavailable"]))
            print("            stopping: {}".format(dict(h["stops"].most_common())))
            print("            config_version: {}   budget identical to frozen A: {}".format(
                sorted(h["cfg"]), h["budget"] == fbudget))
            if set(Bf) - set(A):
                print("            ** {} Bf problems are not in frozen A: selection differs. STOP. **".format(
                    len(set(Bf) - set(A))))
                sys.exit(2)

    # restrict every comparison to problems present in all compared cells
    def cells_for(dom, act):
        return {arm: CELLS[dom][(act, arm)] for arm in ARMS if (act, arm) in CELLS[dom]}

    # ------------------------------------------------------------------ B3
    head("[B3] MASTER TABLE  (PREREG scoring: never graded = incorrect; CIs: bootstrap, 4000)")
    print("{:<9} {:<24}{:<4}{:>6}{:>22}{:>22}{:>30}{:>10}{:>9}".format(
        "domain", "actor", "arm", "n", "first pass", "final", "recovery (n_fpw)", "collapse", "frozen"))
    for dom in DOMAINS:
        for act in ACTORS:
            cs = cells_for(dom, act)
            if "Bf" not in cs: continue
            for arm in ARMS:
                if arm not in cs: continue
                d = cell_stats(cs[arm])
                d.update(domain=dom, actor=act, arm=arm)
                FIG["cells"]["{}|{}|{}".format(dom, act, arm)] = d
                print("{:<9} {:<24}{:<4}{:>6}{:>22}{:>22}{:>30}{:>10}{:>9}".format(
                    DOMAIN_NAME[dom], act, arm, d["n"],
                    ci(d["firstpass"], d["firstpass_lo"], d["firstpass_hi"]),
                    ci(d["final_prereg"], d["final_lo"], d["final_hi"]),
                    "{} ({}/{})".format(ci(d["recovery"], d["recovery_lo"], d["recovery_hi"]),
                                        d["decomp"]["recovered"], d["n_fpw"]),
                    "{:.3f}".format(d["collapse"]),
                    "{:.3f}".format(d["frozen_ans"]) if "frozen_ans" in d else "n/a"))
                if arm == "Bf":
                    assert d["decomp"]["lost"] == 0, "first-pass-correct then lost in Bf"

    # ------------------------------------------------------------------ B4
    head("[B4] PAIRED FINAL ACCURACY, all problems, no conditioning (delta = Y - X; exact McNemar)")
    for dom in DOMAINS:
        for act in ACTORS:
            cs = cells_for(dom, act)
            if "Bf" not in cs: continue
            for x, y in PAIRS:
                if x not in cs or y not in cs: continue
                r = paired_final(cs[x], cs[y])
                FIG["paired_final"]["{}|{}|{}-{}".format(dom, act, x, y)] = r
                print("  {:<9} {:<24}{:>3} vs {:<3} n={:<5} {}-only {:>4}  {}-only {:>4}  "
                      "delta {:+.4f} [{:+.4f},{:+.4f}]  p={:.3g}".format(
                          DOMAIN_NAME[dom], act, x, y, r["n"], x, r["x_only"], y, r["y_only"],
                          r["delta"], r["lo"], r["hi"], r["p"]))

    # ------------------------------------------------------------------ B5
    head("[B5] PAIRED RECOVERY: problems first-pass wrong under BOTH arms (FINAL_TABLES T4)")
    for dom in DOMAINS:
        for act in ACTORS:
            cs = cells_for(dom, act)
            if "Bf" not in cs: continue
            for x, y in PAIRS:
                if x not in cs or y not in cs: continue
                r = paired_recovery(cs[x], cs[y])
                FIG["paired_recovery"]["{}|{}|{}-{}".format(dom, act, x, y)] = r
                print("  {:<9} {:<24}{:>3} vs {:<3} n={:<4} both_rec={:<4} {}only={:<4} {}only={:<4}"
                      " both_fail={:<4} rec_{}={:.3f} rec_{}={:.3f} p={:.2e}".format(
                          DOMAIN_NAME[dom], act, x, y, r["n"], r["both_rec"], x, r["x_only"],
                          y, r["y_only"], r["both_fail"], x, r["rec_x"], y, r["rec_y"], r["p"]))

    # ------------------------------------------------------------------ B6
    head("[B6] STRATIFIED ACCOUNTING of the final-accuracy difference (problems; key = fp_X fp_Y)")
    print("  key 11 both first-pass right, 10/01 the swap strata, 00 both wrong, U never judged")
    for dom in DOMAINS:
        for act in ACTORS:
            cs = cells_for(dom, act)
            if "Bf" not in cs: continue
            for x, y in (("A", "B"), ("A", "Bf"), ("B", "Bf")):
                if x not in cs or y not in cs: continue
                r = strata(cs[x], cs[y])
                FIG["strata"]["{}|{}|{}-{}".format(dom, act, x, y)] = r
                parts = "  ".join("{}: n={} {:+d}".format(k, v["n"], v["contribution"])
                                  for k, v in r["strata"].items())
                print("  {:<9} {:<24}{}->{:<3} total {:+d}/{}   {}".format(
                    DOMAIN_NAME[dom], act, x, y, r["total"], r["n"], parts))

    # ------------------------------------------------------------------ B7
    head("[B7] MECHANISM, first-pass-wrong trajectories (FINAL_TABLES T5 columns)")
    print("{:<9} {:<24}{:<4}{:>7}{:>8}{:>9}{:>10}{:>8}{:>13}{:>8}{:>10}{:>12}{:>11}".format(
        "domain", "actor", "arm", "n_fpw", "cycles", "submits", "revising", "acc_t1",
        "neverrefuse", "frozen", "recovery", "actor_calls", "eval_calls"))
    for dom in DOMAINS:
        for act in ACTORS:
            for arm in ARMS:
                d = FIG["cells"].get("{}|{}|{}".format(dom, act, arm))
                if not d or "cycles" not in d: continue
                print("{:<9} {:<24}{:<4}{:>7}{:>8.2f}{:>9.2f}{:>10.2f}{:>8.3f}{:>13.3f}{:>8.3f}{:>10.3f}"
                      "{:>12.2f}{:>11.2f}".format(
                    DOMAIN_NAME[dom], act, arm, d["n_fpw"], d["cycles"], d["submissions"],
                    d["revising"], d["acc_t1"], d["neverrefuse"], d["frozen_ans"], d["recovery"],
                    d["actor_calls"], d["evaluator_calls"]))

    # ------------------------------------------------------------------ B8
    head("[B8] RECOVERY BY VERDICT: first-pass-wrong trajectories; verdict k = k-th evaluator call")
    print("  cum@k  = share recovered by the k-th verdict (cum@2 = with at most ONE round of feedback)")
    print("  pass@k = P(verdict k is PASS | the trajectory reached verdict k)")
    print("  per extra verdict = recoveries / evaluator verdicts spent after the first FAIL")
    for dom in DOMAINS:
        for act in ACTORS:
            for arm in ("A", "B", "Bf", "C"):
                C = CELLS[dom].get((act, arm))
                if not C or "{}|{}|{}".format(dom, act, arm) not in FIG["cells"]: continue
                v = verdict_curve(C)
                FIG["verdict_curve"]["{}|{}|{}".format(dom, act, arm)] = v
                print("  {:<9} {:<24}{:<3} n_fpw={:<4} cum@2 {:.3f}  cum@6 {:.3f}  reached 2nd {:<4}"
                      " pass@2 {}  pass@3 {}   (PASS verdict <=> final correct: {}/{})".format(
                          DOMAIN_NAME[dom], act, arm, v["n_fpw"], v["cum"][2], v["cum"][6],
                          v["reached"][2], fr(v["passed"][2], v["reached"][2]),
                          fr(v["passed"][3], v["reached"][3]),
                          v["pass_verdict_equals_final"], v["n_fpw"]))
                print("  {:<34}{:<3} extra verdicts {:<5} recoveries per extra verdict {:.3f}".format(
                    "", arm, v["extra_verdicts"], v["recoveries_per_extra_verdict"]))

    # ------------------------------------------------------------------ B9
    head("[B9] FEEDBACK DELIVERY in Bf, and Bf vs B before any feedback")
    for dom in DOMAINS:
        for act in ACTORS:
            Bf, B = CELLS[dom].get((act, "Bf")), CELLS[dom].get((act, "B"))
            if not Bf or not B: continue
            fpw = [f for f in Bf.values() if f["judged"] and f["fp"] == 0]
            got = sum(1 for f in fpw if f["fb_msgs"] > 0)
            last_only = sum(1 for f in fpw if f["fb_msgs"] == 0 and len(f["verdicts"]) == 1
                            and f["inner_used"] >= 6)
            cm = [u for u in set(Bf) & set(B) if Bf[u]["judged"] and B[u]["judged"]]
            same_fp = sum(1 for u in cm if Bf[u]["fp"] == B[u]["fp"])
            cc = [u for u in cm if Bf[u]["cand1"] and B[u]["cand1"]]
            same_c = sum(1 for u in cc if Bf[u]["cand1"] == B[u]["cand1"])
            FIG["delivery"]["{}|{}".format(dom, act)] = dict(
                n_fpw=len(fpw), fpw_with_feedback=got, fpw_without_feedback_fail_in_last_cycle=last_only,
                flagged_msgs=sum(f["fb_msgs"] for f in Bf.values()),
                actor_msgs=sum(f["actor_msgs"] for f in Bf.values()))
            FIG["first_verdict_agreement"]["{}|{}".format(dom, act)] = dict(
                n=len(cm), same_first_verdict=same_fp, n_cand=len(cc), same_first_candidate=same_c)
            print("  {:<9} {:<24} feedback reached an agent in {} first-pass-wrong Bf trajectories;"
                  " first verdict Bf == B on {}; first submitted answer identical on {}".format(
                      DOMAIN_NAME[dom], act, fr(got, len(fpw)), fr(same_fp, len(cm)), fr(same_c, len(cc))))

    # ------------------------------------------------------------------ B10
    head("[B10] ENDPOINT DRIFT: Arm A re-run today on frozen problems (never pooled)")
    for act, Y in sorted(BRIDGE.items()):
        X0 = CELLS["omni"].get((act, "A"))
        if not X0: continue
        cm = sorted(set(Y) & set(X0))
        X, Yc = {u: X0[u] for u in cm}, {u: Y[u] for u in cm}
        sx, sy = cell_stats(X), cell_stats(Yc)
        pf = paired_final(X, Yc)
        j = [u for u in cm if X[u]["judged"] and Yc[u]["judged"]]
        b = sum(1 for u in j if X[u]["fp"] == 1 and Yc[u]["fp"] == 0)
        c = sum(1 for u in j if X[u]["fp"] == 0 and Yc[u]["fp"] == 1)
        h = health[("omni", act, "bridgeA")]
        FIG["bridge"][act] = dict(n=len(cm), frozen=sx, today=sy, paired_final=pf,
                                  paired_firstpass=dict(n=len(j), frozen_only=b, today_only=c,
                                                        p=mcnemar(b, c)),
                                  budget_identical=h["budget"] == {f["budget"] for f in X.values()})
        print("  {} n={} (planned 400)".format(act, len(cm)))
        print("    {:<8}{:>22}{:>22}{:>28}{:>14}".format("", "first pass", "final", "recovery", "submits|fpw"))
        for lab, s in (("frozen", sx), ("today", sy)):
            print("    {:<8}{:>22}{:>22}{:>28}{:>14.2f}".format(
                lab, ci(s["firstpass"], s["firstpass_lo"], s["firstpass_hi"]),
                ci(s["final_prereg"], s["final_lo"], s["final_hi"]),
                "{} ({}/{})".format(ci(s["recovery"], s["recovery_lo"], s["recovery_hi"]),
                                    s["decomp"]["recovered"], s["n_fpw"]), s["submissions"]))
        print("    paired first pass: frozen-only {} today-only {} p={:.3g};  paired final: frozen-only {}"
              " today-only {} delta {:+.4f} p={:.3g}".format(b, c, mcnemar(b, c), pf["x_only"],
                                                              pf["y_only"], pf["delta"], pf["p"]))

    # ------------------------------------------------------------------ B11
    head("[B11] HINT LEAK: FAIL verdicts whose repair hint contains the gold answer verbatim")
    print("  (whitespace-insensitive substring; golds of 1 character excluded; gold = parquet `answer`)")
    if gold is None:
        print("  SKIPPED: {}".format(gmsg))
    else:
        for dom in DOMAINS:
            for act in ACTORS:
                if (act, "Bf") not in CELLS[dom]: continue
                for arm in ("A", "B", "Bf"):
                    C = CELLS[dom].get((act, arm))
                    if not C: continue
                    fs = [f for f in C.values() if f["gold_ok"]]
                    nf = sum(f["n_fail"] for f in fs)
                    nl = sum(f["n_leak"] for f in fs)
                    fpw = [f for f in fs if f["judged"] and f["fp"] == 0]
                    tl = sum(1 for f in fpw if f["n_leak"] > 0)
                    # recovery over ALL first-pass-wrong trajectories once every
                    # trajectory with a leaking hint is removed (robustness)
                    allw = [f for f in C.values() if f["judged"] and f["fp"] == 0]
                    clean_w = [f for f in allw if f["n_leak"] == 0]
                    rc = sum(f["fin"] for f in clean_w)
                    FIG["hint_leak"]["{}|{}|{}".format(dom, act, arm)] = dict(
                        problems_with_gold=len(fs), fail_verdicts=nf, leaking=nl,
                        fpw=len(fpw), fpw_with_leak=tl,
                        recovery_without_leaking=rc, n_fpw_without_leaking=len(clean_w))
                    print("  {:<9} {:<24}{:<3} problems {:<5} FAIL verdicts leaking {}   "
                          "first-pass-wrong trajectories with any leak {}   recovery without them {}".format(
                              DOMAIN_NAME[dom], act, arm, len(fs), fr(nl, nf), fr(tl, len(fpw)),
                              fr(rc, len(clean_w))))
        print("  Arm B's hints were generated but never shown to its agents (the defect Bf removes).")

    # ------------------------------------------------------------------ B13
    head("[B13] SCORING DEFECT (FINAL_TABLES T19): graded = last SUBMITTED, recorded = last HELD")
    print("  first-pass-wrong trajectories; 'under-credited' = held answer equals the gold string")
    print("  but the trajectory is graded 0. 'recovery if recoded' counts those as recovered.")
    FIG["scoring_defect"] = {}
    if gold is None:
        print("  SKIPPED: {}".format(gmsg))
    else:
        for dom in DOMAINS:
            for act in ACTORS:
                if (act, "Bf") not in CELLS[dom]: continue
                for arm in ARMS:
                    C = CELLS[dom].get((act, arm))
                    if not C: continue
                    fpw = [f for f in C.values() if f["judged"] and f["fp"] == 0]
                    mm = sum(1 for f in fpw if f["mismatch"])
                    uc = sum(1 for f in fpw if f["undercredit"])
                    rec = sum(f["fin"] for f in fpw)
                    FIG["scoring_defect"]["{}|{}|{}".format(dom, act, arm)] = dict(
                        n_fpw=len(fpw), mismatched=mm, undercredited=uc, recovered=rec,
                        recovery_if_recoded=(rec + uc) / len(fpw) if fpw else float("nan"))
                    print("  {:<9} {:<24}{:<3} n_fpw={:<4} mismatch {:.3f}  under-credited {:<3} "
                          "recovery {} -> if recoded {}".format(
                              DOMAIN_NAME[dom], act, arm, len(fpw), mm / max(len(fpw), 1), uc,
                              fr(rec, len(fpw)), fr(rec + uc, len(fpw))))

    # ------------------------------------------------------------------ B12
    head("[B12] HEADLINE NUMBERS (each traceable to a block above)")
    for dom in DOMAINS:
        for act in ACTORS:
            k = "{}|{}|".format(dom, act)
            if k + "Bf" not in FIG["cells"]: continue
            c = {arm: FIG["cells"].get(k + arm) for arm in ARMS}
            pr = FIG["paired_recovery"].get(k + "A-Bf")
            pb = FIG["paired_recovery"].get(k + "B-Bf")
            pf = FIG["paired_final"].get(k + "A-Bf")
            print("  {} / {}  [{}]".format(DOMAIN_NAME[dom], act, FIG["status"].get(dom + "|" + act)))
            print("    recovery  " + "   ".join(
                "{} {}".format(arm, fr(c[arm]["decomp"]["recovered"], c[arm]["n_fpw"]))
                for arm in ARMS if c[arm]))
            print("    final     " + "   ".join(
                "{} {:.3f}".format(arm, c[arm]["final_prereg"]) for arm in ARMS if c[arm]))
            print("    first pass" + "   ".join(
                " {} {:.3f}".format(arm, c[arm]["firstpass"]) for arm in ARMS if c[arm]))
            if pb:
                print("    feedback alone (B -> Bf, paired): n={} recovered only under B {}, only under Bf {},"
                      " p={:.2g}".format(pb["n"], pb["x_only"], pb["y_only"], pb["p"]))
            if pr:
                print("    roles given feedback (A vs Bf, paired): n={} only A {}, only Bf {}, p={:.2g}".format(
                    pr["n"], pr["x_only"], pr["y_only"], pr["p"]))
            if pf:
                print("    final accuracy A vs Bf (paired, all problems): {}-only {} vs {} -> delta {:+.3f}"
                      " [{:+.3f},{:+.3f}], p={:.2g}".format("A", pf["x_only"], pf["y_only"], pf["delta"],
                                                            pf["lo"], pf["hi"], pf["p"]))
    if pending:
        print("\n  PENDING Bf cells: {}".format(", ".join(pending)))

    out = os.path.join(a.out_dir, "FIGDATA_BF.json")
    with open(out, "w") as fh:
        json.dump(clean(FIG), fh, indent=1, sort_keys=True)
    print("\nwrote {}  sha256[:16] {}".format(os.path.relpath(out, ROOT), sha256(out)[:16]))
    print("=" * 96)
    return 0


if __name__ == "__main__":
    sys.exit(main())
