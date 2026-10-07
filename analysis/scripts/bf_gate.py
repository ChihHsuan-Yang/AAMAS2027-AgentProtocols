#!/usr/bin/env python3
"""Where do the role-structured team's revising cycles come from?

Reviewer question (mock review round 2): is the role-structured team's low
resubmission rate the one explicit prompt clause ("after a FAIL the Reviewer
MUST NOT output [Agree]"), or the role contract at large?  The clause binds
only the cycle that RECEIVES a FAIL; every later cycle the Reviewer is free to
approve.  This script splits every first-pass-wrong trajectory's cycles into

  pre      cycles before the first submission (the first approval)
  fail     cycles that received a FAIL (the clause applies in arm A)
             -> declined / approved (approved = a clause violation in A)
  free     later cycles that did not receive a FAIL
             -> declined / approved

and reports, per cell, how many trajectories never resubmit although cycles
remained in which the clause did not apply.  Arms A, Bf and C; B for
reference.  Same inputs and row rules as bf_numbers.py (frozen files pinned
by their manifests, Bf files from experiments/results/bf, infrastructure rows
dropped or superseded exactly as there).  Positive control: n_fpw, cycles and
submissions per cell must equal BF_TABLES_OUTPUT.txt [B7].

Outputs analysis/out/BF_GATE_OUTPUT.txt and analysis/out/FIGDATA_GATE.json.
"""
import argparse
import collections
import glob
import hashlib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ACTORS = ["gemma-4-31B-it", "gpt-oss-120b", "Llama-3.3-70B-Instruct"]
DOMAIN_OF_BENCH = {"omnimath2": "omni", "scibench": "scibench"}
DOMAIN_NAME = {"omni": "Omni-MATH", "scibench": "SciBench"}
FROZEN_FILES = {
    "campaign_v2.jsonl": "experiments/results/FROZEN/MANIFEST.json",
    "actor3.jsonl": "experiments/results/FROZEN/MANIFEST.json",
    "scibench_AB.jsonl": "experiments/results/xdomain/FROZEN_SCIBENCH/MANIFEST.json",
}
INFRA = ("model_unavailable", "runtime_error")
BUDGET_CYCLES = 6


def actor(r): return r["actor_model"].split("/")[-1]
def ev(r): return r.get("evaluator_history") or []
def nrm(s):
    if s is None: return None
    s = re.sub(r"\s+", "", str(s)).strip("$").strip(); return s or None
GOLD = {}    # problem_uid -> normalized gold answer (filled in main from the problems parquet)


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def rows(p):
    with open(p) as fh:
        for line in fh:
            if line.strip():
                try:
                    yield json.loads(line)
                except Exception:
                    pass


def routes(r):
    return [m.get("route") for m in (r.get("messages") or [])
            if m.get("role") == "reviewer" and m.get("route")]


def feat(r):
    e = ev(r)
    fpw = bool(e) and int(e[0].get("correctness") or 0) == 0
    if not fpw:
        return None
    rt = routes(r)
    verdicts = [int(x.get("correctness") or 0) for x in e]
    first = next((i for i, x in enumerate(rt) if x == "agree"), None)
    c = collections.Counter()
    fail_cycle = False          # does THIS cycle receive a FAIL from the previous one?
    for i, x in enumerate(rt):
        ag = (x == "agree")
        if first is None or i < first:
            c["pre_decl" if not ag else "pre_agree"] += 1
        elif i == first:
            c["first_sub"] += 1
        elif fail_cycle:
            c["fail_agree" if ag else "fail_decl"] += 1
        else:
            c["free_agree" if ag else "free_decl"] += 1
        # an approval that did not end the trajectory produced a FAIL (or a
        # no-answer FAIL) that the next cycle receives
        fail_cycle = ag
    left = (BUDGET_CYCLES - (first + 1)) if first is not None else 0
    # scoring defect (FINAL_TABLES T19, bf_numbers): the runner grades the last
    # SUBMITTED answer but records the last HELD one; 'uc' = held answer equals the
    # gold string while the trajectory is graded 0 (same rule as bf_numbers.py)
    g = GOLD.get(r["problem_uid"])
    held = nrm(r.get("final_answer"))
    last_sub = nrm((e[-1] or {}).get("candidate")) if e else None
    uc = bool(held is not None and last_sub is not None and held != last_sub
              and g is not None and held == g and int(r.get("correct") or 0) == 0)
    return dict(uid=r["problem_uid"], stop=r.get("stopping_condition"), verdicts=verdicts, uc=uc,
                approvals=sum(1 for x in rt if x == "agree"),
                cycles=len(rt), subs=len(verdicts), first=(first + 1) if first is not None else None,
                left=left, resub=len(verdicts) >= 2, rec=1 in verdicts, c=c)


BOX = re.compile(r"\\boxed\s*\{")
CLEAN = collections.defaultdict(lambda: [0, 0, 0, 0])   # (actor, arm) -> [n, collapse, n_clean, collapse_clean]


def first3(r):
    return [m for m in (r.get("messages") or []) if m.get("role") in ("planner", "executor", "reviewer")][:3]


def defect_check(r):
    """FINAL_TABLES T26 definition: a message is affected if visible characters per
    second of latency < 10; a first pass is clean if none of its three messages is."""
    f = first3(r)
    if len(f) != 3:
        return
    col = all(BOX.search(m.get("text") or "") for m in f)
    low = any((m.get("latency_s") or 0) > 0 and len(m.get("text") or "") / m["latency_s"] < 10 for m in f)
    c = CLEAN[(actor(r), r.get("arm"))]
    c[0] += 1; c[1] += col
    if not low:
        c[2] += 1; c[3] += col


BRIDGE_ALL = collections.defaultdict(set)     # actor -> problem uids in the bridge re-run


def load(a):
    cells = collections.defaultdict(dict)       # (dom, actor, arm) -> uid -> feat
    for name, manp in FROZEN_FILES.items():
        p = os.path.join(a.frozen_dir, name)
        want = (json.load(open(os.path.join(ROOT, manp))).get("files", {}).get(name) or {}).get("sha256")
        got = sha256(p)
        assert got == want, ("frozen manifest mismatch", name)
        print("frozen {:<20} sha256 {} manifest OK".format(name, got[:16]))
        for r in rows(p):
            dom = DOMAIN_OF_BENCH[r["benchmark_id"]] if r.get("benchmark_id") in DOMAIN_OF_BENCH else (
                "scibench" if name.startswith("scibench") else "omni")
            if name == "campaign_v2.jsonl" and r.get("arm") in ("A", "B"):
                defect_check(r)
            f = feat(r)
            key = (dom, actor(r), r.get("arm"))
            cells[key].setdefault("_all", 0)
            if f:
                cells[key][f["uid"]] = f
    for p in sorted(glob.glob(os.path.join(a.bf_dir, "bridgeA_*.jsonl"))):
        name = os.path.basename(p)
        print("bridge {:<34} sha256 {}".format(name, sha256(p)[:16]))
        for r in rows(p):
            if r.get("arm") != "A" or r.get("stopping_condition") == "model_unavailable":
                continue
            f = feat(r)
            if f:
                cells[("omni", actor(r), "Abridge")][f["uid"]] = f
            BRIDGE_ALL[(actor(r))].add(r["problem_uid"])
    for p in sorted(glob.glob(os.path.join(a.bf_dir, "bf_*.jsonl"))):
        name = os.path.basename(p)
        if name.endswith(".infra_failed.jsonl"):
            continue
        print("Bf     {:<34} sha256 {}".format(name, sha256(p)[:16]))
        store = collections.defaultdict(dict)
        for r in rows(p):
            if r.get("arm") != "Bf":
                continue
            if r.get("stopping_condition") == "model_unavailable":
                continue
            dom = DOMAIN_OF_BENCH[r["benchmark_id"]]
            key = (dom, actor(r), "Bf")
            prev = store[key].get(r["problem_uid"])
            if prev is not None and r.get("stopping_condition") in INFRA:
                continue
            store[key][r["problem_uid"]] = r
        for key, d in store.items():
            for uid, r in d.items():
                f = feat(r)
                if f:
                    cells[key][uid] = f
    return cells


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frozen-dir", default=os.environ.get(
        "AAMAS_FROZEN_DIR", os.path.join(ROOT, "experiments/results/hf_frozen/raw")))
    ap.add_argument("--bf-dir", default=os.path.join(ROOT, "experiments/results/bf"))
    ap.add_argument("--out-dir", default=os.path.join(ROOT, "analysis/out"))
    ap.add_argument("--parquet", default=os.environ.get(
        "AAMAS_PROBLEMS_PARQUET",
        os.path.join(ROOT, "analysis/hf_cache/release/data/problems/part-00000.parquet")))
    a = ap.parse_args()
    if os.path.exists(a.parquet):
        try:
            import pyarrow.parquet as pq
            t = pq.read_table(a.parquet, columns=["problem_uid", "answer"]).to_pydict()
        except Exception:
            import pandas as pd
            t = pd.read_parquet(a.parquet, columns=["problem_uid", "answer"]).to_dict("list")
        for u, g in zip(t["problem_uid"], t["answer"]):
            GOLD[str(u)] = nrm(g)
    out = open(os.path.join(a.out_dir, "BF_GATE_OUTPUT.txt"), "w")

    def P(*s):
        line = " ".join(str(x) for x in s)
        print(line)
        out.write(line + "\n")

    cells = load(a)
    FIG = {}
    P("=" * 100)
    P("BF_GATE -- first-pass-wrong trajectories; generated by analysis/scripts/bf_gate.py")
    P("cycle = one Reviewer (third-agent) turn; a 'submission' is an approval; budget 6 cycles")
    P("fail  = a cycle that receives a FAIL (arm A: the clause forbids approval in it)")
    P("free  = a later cycle that does not receive a FAIL (no clause applies in any arm)")
    P("=" * 100)
    hdr = ("{:<9} {:<23}{:<4}{:>6}{:>7}{:>7} | {:>6}{:>7}{:>8} | {:>7}{:>7}{:>9} | {:>6}{:>7}{:>7}"
           .format("domain", "actor", "arm", "n_fpw", "cycles", "subs",
                   "pre", "first", "f_decl", "f_agree", "fr_decl", "fr_agree",
                   "noRes", "left>=2", "share"))
    P(hdr)
    for dom in ("omni", "scibench"):
        for act in ACTORS:
            for arm in ("A", "Bf", "C", "B"):
                C = {k: v for k, v in cells.get((dom, act, arm), {}).items() if k != "_all"}
                if not C:
                    continue
                n = len(C)
                tot = collections.Counter()
                for f in C.values():
                    tot.update(f["c"])
                cyc = sum(f["cycles"] for f in C.values()) / n
                subs = sum(f["subs"] for f in C.values()) / n
                nores = [f for f in C.values() if not f["resub"] and not f["rec"]]
                nores_left2 = [f for f in nores if f["left"] >= 2]
                # at least one free cycle exists after the clause cycle
                P("{:<9} {:<23}{:<4}{:>6}{:>7.2f}{:>7.2f} | {:>6.2f}{:>7.2f}{:>8.2f} | {:>7.2f}{:>7.2f}{:>9.2f}"
                  " | {:>6}{:>7}{:>7.3f}".format(
                      DOMAIN_NAME[dom], act, arm, n, cyc, subs,
                      tot["pre_decl"] / n, tot["first_sub"] / n, tot["fail_decl"] / n,
                      tot["fail_agree"] / n, tot["free_decl"] / n, tot["free_agree"] / n,
                      len(nores), len(nores_left2), len(nores_left2) / n))
                fd, fa, rd, ra = tot["fail_decl"], tot["fail_agree"], tot["free_decl"], tot["free_agree"]
                decl_after = fd + rd
                appr = sum(f["approvals"] for f in C.values()) / n
                FIG["{}|{}|{}".format(dom, act, arm)] = dict(
                    n_fpw=n, cycles=cyc, submissions=subs, approvals=appr,
                    declines=(tot["pre_decl"] + tot["fail_decl"] + tot["free_decl"]) / n,
                    pre_decl=tot["pre_decl"] / n, fail_decl=fd / n, fail_agree=fa / n,
                    free_decl=rd / n, free_agree=ra / n,
                    fail_cycles=fd + fa, fail_agree_rate=(fa / (fd + fa) if fd + fa else None),
                    free_cycles=rd + ra, free_agree_rate=(ra / (rd + ra) if rd + ra else None),
                    declines_after_first=decl_after,
                    declines_total=tot["pre_decl"] + decl_after,
                    share_declines_pre=(tot["pre_decl"] / (tot["pre_decl"] + decl_after)
                                        if tot["pre_decl"] + decl_after else None),
                    share_declines_fail=(fd / (tot["pre_decl"] + decl_after)
                                         if tot["pre_decl"] + decl_after else None),
                    share_declines_free=(rd / (tot["pre_decl"] + decl_after)
                                         if tot["pre_decl"] + decl_after else None),
                    share_declines_in_free=(rd / decl_after if decl_after else None),
                    first_sub_hist={str(k): v for k, v in collections.Counter(f["first"] for f in C.values()).items()},
                    never_resubmitted=len(nores), never_resubmitted_with_free_cycle=len(nores_left2))
    P("")
    P("columns: pre = declines before the first submission; first = the first submission;")
    P("  f_decl/f_agree = declines/approvals in cycles that received a FAIL;")
    P("  fr_decl/fr_agree = declines/approvals in later cycles that did not receive one (per trajectory);")
    P("  noRes = first-pass-wrong trajectories never submitted again; left>=2 = of those, with at")
    P("  least two cycles left after the first submission (so at least one cycle the clause does not cover)")
    P("")
    P("Approval rates by cycle type (pooled over trajectories):")
    for k, v in FIG.items():
        dom, act, arm = k.split("|")
        P("  {:<9} {:<23}{:<4} fail-cycle approval {:>5}/{:<5} = {}   free-cycle approval {:>5}/{:<5} = {}"
          "   share of post-submission declines in free cycles {}".format(
              DOMAIN_NAME[dom], act, arm,
              round(v["fail_agree"] * v["n_fpw"]), v["fail_cycles"],
              "{:.3f}".format(v["fail_agree_rate"]) if v["fail_agree_rate"] is not None else "-",
              round(v["free_agree"] * v["n_fpw"]), v["free_cycles"],
              "{:.3f}".format(v["free_agree_rate"]) if v["free_agree_rate"] is not None else "-",
              "{:.3f}".format(v["share_declines_in_free"]) if v["share_declines_in_free"] is not None else "-"))
    P("")
    P("Where the declining cycles fall (share of all declining cycles of first-pass-wrong trajectories):")
    P("  before the first submission / in a cycle that received a FAIL (arm A: the clause) / free")
    for k, v in FIG.items():
        dom, act, arm = k.split("|")
        if v["declines_total"]:
            P("  {:<9} {:<23}{:<4} declines {:>5}   pre {:.3f}   fail {:.3f}   free {:.3f}".format(
                DOMAIN_NAME[dom], act, arm, v["declines_total"], v["share_declines_pre"],
                v["share_declines_fail"], v["share_declines_free"]))
    P("")
    P("First-submission cycle (count of first-pass-wrong trajectories by cycle 1..6):")
    for k, v in FIG.items():
        dom, act, arm = k.split("|")
        h = v["first_sub_hist"]
        P("  {:<9} {:<23}{:<4} ".format(DOMAIN_NAME[dom], act, arm) +
          "  ".join("{}:{}".format(i, h.get(str(i), 0)) for i in range(1, 7)) + "  never:{}".format(h.get("None", 0)))
    P("")
    P("Approvals (true submissions) and declines per first-pass-wrong trajectory, cycles with a")
    P("Reviewer turn only; 'verdicts' (bf_numbers [B7] 'submits') also counts the one grading at the")
    P("end of the budget of a trajectory that never submitted:")
    for k, v in FIG.items():
        if "|" not in k or k.count("|") != 2:
            continue
        dom, act, arm = k.split("|")
        P("  {:<9} {:<23}{:<4} approvals {:.2f}   declines {:.2f}   verdicts {:.2f}".format(
            DOMAIN_NAME[dom], act, arm, v["approvals"], v["declines"], v["submissions"]))
    P("")
    P("[G3] VERDICT-MATCHED PAIRED RECOVERY: problems first-pass wrong under both A and Bf; the Bf")
    P("     trajectory is truncated at the number of evaluator verdicts the A trajectory received on")
    P("     the same problem (so both receive the same number of gold-informed verdicts and hints)")
    from math import comb
    def mcn(b, c):
        m = b + c
        return 1.0 if m == 0 else min(1.0, 2 * sum(comb(m, i) for i in range(min(b, c) + 1)) / 2 ** m)
    for dom in ("omni", "scibench"):
        for act in ACTORS:
            A = {k: v for k, v in cells.get((dom, act, "A"), {}).items() if k != "_all"}
            F = {k: v for k, v in cells.get((dom, act, "Bf"), {}).items() if k != "_all"}
            if not A or not F:
                continue
            both = sorted(set(A) & set(F))
            a_only = f_only = both_rec = 0
            ks = []
            for u in both:
                kA = len(A[u]["verdicts"])
                ks.append(kA)
                ra = 1 in A[u]["verdicts"]
                rf = 1 in F[u]["verdicts"][:kA]
                a_only += ra and not rf
                f_only += rf and not ra
                both_rec += ra and rf
            n = len(both)
            pv = mcn(a_only, f_only)
            P("  {:<9} {:<23} n={:<4} mean A verdicts {:.2f}  A-only {:<3} Bf(truncated)-only {:<3} both {:<3}"
              "  rec_A {:.3f}  rec_Bf_trunc {:.3f}  p={:.2g}".format(
                  DOMAIN_NAME[dom], act, n, sum(ks) / n, a_only, f_only, both_rec,
                  (a_only + both_rec) / n, (f_only + both_rec) / n, pv))
            FIG["verdict_matched|{}|{}".format(dom, act)] = dict(
                n=n, mean_verdicts_A=sum(ks) / n, a_only=a_only, bf_only=f_only, both=both_rec,
                rec_A=(a_only + both_rec) / n, rec_Bf_trunc=(f_only + both_rec) / n, p=pv)
    P("")
    P("[G4] VERDICT-MATCHED CONTRAST: uncertainty, pooled estimate, symmetric matching, same window")
    P("     diff = rec_A - rec_Bf_truncated (positive favours roles); 95% paired bootstrap over problems,")
    P("     20,000 draws, RNG seeded per cell; pooled = all five cells stratified by cell; TOST at +-0.05")
    P("     uses the 90% interval. Symmetric: both trajectories cut at min(verdicts A, verdicts Bf).")
    import random, zlib
    def boot(pairs, draws=20000, key=""):
        rng = random.Random(20261008 ^ zlib.crc32(key.encode()))
        n = len(pairs)
        d = [x - y for x, y in pairs]
        est = sum(d) / n
        stats = []
        for _ in range(draws):
            stats.append(sum(d[rng.randrange(n)] for _ in range(n)) / n)
        stats.sort()
        q = lambda f: stats[int(f * (draws - 1))]
        return est, q(0.025), q(0.975), q(0.05), q(0.95)
    def boot_strat(groups, draws=20000, key="pooled"):
        rng = random.Random(20261008 ^ zlib.crc32(key.encode()))
        N = sum(len(g) for g in groups)
        est = sum(x - y for g in groups for x, y in g) / N
        stats = []
        for _ in range(draws):
            tot = 0
            for g in groups:
                m = len(g)
                for _ in range(m):
                    x, y = g[rng.randrange(m)]
                    tot += x - y
            stats.append(tot / N)
        stats.sort()
        q = lambda f: stats[int(f * (draws - 1))]
        return est, q(0.025), q(0.975), q(0.05), q(0.95)
    groups = []
    for dom in ("omni", "scibench"):
        for act in ACTORS:
            A = {k: v for k, v in cells.get((dom, act, "A"), {}).items() if k != "_all"}
            F = {k: v for k, v in cells.get((dom, act, "Bf"), {}).items() if k != "_all"}
            if not A or not F:
                continue
            both = sorted(set(A) & set(F))
            pairs, sym = [], []
            for u in both:
                kA, kF = len(A[u]["verdicts"]), len(F[u]["verdicts"])
                pairs.append((int(1 in A[u]["verdicts"]), int(1 in F[u]["verdicts"][:kA])))
                k = min(kA, kF)
                sym.append((int(1 in A[u]["verdicts"][:k]), int(1 in F[u]["verdicts"][:k])))
            groups.append(pairs)
            key = "{}|{}".format(dom, act)
            e, lo, hi, lo90, hi90 = boot(pairs, key=key)
            es, los, his, _, _ = boot(sym, key=key + "|sym")
            P("  {:<9} {:<23} n={:<4} diff {:+.3f} [{:+.3f},{:+.3f}]  90% [{:+.3f},{:+.3f}]   symmetric {:+.3f} [{:+.3f},{:+.3f}]"
              "  events A {} Bf {}".format(DOMAIN_NAME[dom], act, len(pairs), e, lo, hi, lo90, hi90,
                                          es, los, his, sum(x for x, _ in pairs), sum(y for _, y in pairs)))
            FIG["verdict_matched|{}".format(key)].update(dict(
                diff=e, ci95=[lo, hi], ci90=[lo90, hi90], sym_diff=es, sym_ci95=[los, his],
                events_A=sum(x for x, _ in pairs), events_Bf=sum(y for _, y in pairs)))
    e, lo, hi, lo90, hi90 = boot_strat(groups)
    tost = (lo90 > -0.05) and (hi90 < 0.05)
    P("  pooled (5 cells, n={})  diff {:+.4f} [{:+.4f},{:+.4f}]  90% [{:+.4f},{:+.4f}]  equivalent within +-0.05: {}".format(
        sum(len(g) for g in groups), e, lo, hi, lo90, hi90, "YES" if tost else "NO"))
    FIG["verdict_matched_pooled"] = dict(n=sum(len(g) for g in groups), diff=e, ci95=[lo, hi],
                                         ci90=[lo90, hi90], tost_margin=0.05, equivalent=tost)
    # same window: the bridge re-run of A (run after the freeze, like Bf) against Bf on its problems
    for act in ACTORS:
        AB = {k: v for k, v in cells.get(("omni", act, "Abridge"), {}).items() if k != "_all"}
        F = {k: v for k, v in cells.get(("omni", act, "Bf"), {}).items() if k != "_all"}
        if not AB or not F:
            continue
        both = sorted(set(AB) & set(F))
        pairs = [(int(1 in AB[u]["verdicts"]), int(1 in F[u]["verdicts"][:len(AB[u]["verdicts"])])) for u in both]
        unmatched = [(int(1 in AB[u]["verdicts"]), int(1 in F[u]["verdicts"])) for u in both]
        a_only = sum(1 for x, y in pairs if x and not y); f_only = sum(1 for x, y in pairs if y and not x)
        ua = sum(1 for x, y in unmatched if x and not y); uf = sum(1 for x, y in unmatched if y and not x)
        e, lo, hi, _, _ = boot(pairs, key="bridge|" + act)
        P("  same window (re-run of A after the freeze, {} problems both first-pass wrong of {} re-run): "
          "unmatched A-only {} Bf-only {} p={:.2g};  verdict-matched A-only {} Bf-only {} p={:.2g}, diff {:+.3f} [{:+.3f},{:+.3f}]".format(
              len(both), len(BRIDGE_ALL[act]), ua, uf, mcn(ua, uf), a_only, f_only, mcn(a_only, f_only), e, lo, hi))
        FIG["verdict_matched_bridge|omni|{}".format(act)] = dict(
            n=len(both), unmatched_a_only=ua, unmatched_bf_only=uf, unmatched_p=mcn(ua, uf),
            a_only=a_only, bf_only=f_only, p=mcn(a_only, f_only), diff=e, ci95=[lo, hi])
    # ------------------------------------------------------------------ G6
    P("")
    P("[G6] VERDICT-MATCHED CONTRAST: ROBUSTNESS (mock review round 3)")
    P("     forced ties = paired problems where A received one verdict (it never submitted, or submitted")
    P("     once and stopped): Bf truncated to one verdict cannot recover either, so the pair is 0-0 by")
    P("     construction. informative = A received >= 2 verdicts. symmetric = both cut at min(verdicts).")
    P("     recoded = scoring defect recoded: an A trajectory whose held answer equals the gold string")
    P("     counts as recovered; a Bf one only if it was not truncated (its verdicts <= A's).")
    P("     diff = A - Bf (positive favours roles); 95% and 90% paired bootstrap (numpy, 20,000 draws,")
    P("     seeded), pooled stratified by cell; TOST at +-0.05 on the 90% interval. gold strings: {} problems".format(len(GOLD)))
    import numpy as np
    def nboot(groups, draws=20000, seed=20261008):
        rng = np.random.default_rng(seed)
        N = sum(len(g) for g in groups)
        if N == 0:
            return None
        tot = np.zeros(draws)
        for g in groups:
            d = np.array([x - y for x, y in g], dtype=float)
            if len(d) == 0:
                continue
            idx = rng.integers(0, len(d), size=(draws, len(d)))
            tot += d[idx].sum(axis=1)
        st = np.sort(tot / N)
        est = sum(x - y for g in groups for x, y in g) / N
        q = lambda f: float(st[int(f * (draws - 1))])
        return est, q(0.025), q(0.975), q(0.05), q(0.95), N
    VAR = ("main", "informative", "symmetric", "symmetric_informative", "recoded", "recoded_informative")
    G6 = {v: {} for v in VAR}
    for dom in ("omni", "scibench"):
        for act in ACTORS:
            A = {k: v for k, v in cells.get((dom, act, "A"), {}).items() if k != "_all"}
            F = {k: v for k, v in cells.get((dom, act, "Bf"), {}).items() if k != "_all"}
            if not A or not F:
                continue
            both = sorted(set(A) & set(F))
            ties = never = ucA = ucF = 0
            pv = {v: [] for v in VAR}
            for u in both:
                kA, kF = len(A[u]["verdicts"]), len(F[u]["verdicts"])
                ra = int(1 in A[u]["verdicts"])
                rf = int(1 in F[u]["verdicts"][:kA])
                k = min(kA, kF)
                sa, sf = int(1 in A[u]["verdicts"][:k]), int(1 in F[u]["verdicts"][:k])
                rra = int(ra or A[u]["uc"])
                rrf = int(rf or (F[u]["uc"] and kF <= kA))
                ucA += A[u]["uc"]; ucF += F[u]["uc"]
                inf = kA >= 2
                ties += (kA <= 1)
                never += (A[u]["approvals"] == 0)
                pv["main"].append((ra, rf)); pv["symmetric"].append((sa, sf)); pv["recoded"].append((rra, rrf))
                if inf:
                    pv["informative"].append((ra, rf)); pv["symmetric_informative"].append((sa, sf))
                    pv["recoded_informative"].append((rra, rrf))
            key = "{}|{}".format(dom, act)
            P("  {:<9} {:<23} paired n={:<4} forced ties {:<4} ({:.0%})  of which A never submitted {:<4}"
              "  informative n={:<4}  held-answer recodes A {} Bf {}".format(
                  DOMAIN_NAME[dom], act, len(both), ties, ties / len(both), never,
                  len(pv["informative"]), ucA, ucF))
            for v in VAR:
                G6[v][key] = pv[v]
                r = nboot([pv[v]], seed=20261008 ^ (zlib.crc32((key + v).encode()) & 0xffff))
                if r is None:
                    continue
                e, lo, hi, l9, h9, n = r
                P("      {:<22} n={:<4} A {:<3} Bf {:<3} diff {:+.3f} [{:+.3f},{:+.3f}]  90% [{:+.3f},{:+.3f}]".format(
                    v, n, sum(x for x, _ in pv[v]), sum(y for _, y in pv[v]), e, lo, hi, l9, h9))
                FIG["verdict_robust|{}|{}".format(v, key)] = dict(
                    n=n, events_A=sum(x for x, _ in pv[v]), events_Bf=sum(y for _, y in pv[v]),
                    diff=e, ci95=[lo, hi], ci90=[l9, h9])
            FIG["verdict_robust_ties|{}".format(key)] = dict(n=len(both), forced_ties=ties, never_submitted=never,
                                                            informative=len(pv["informative"]), recodes_A=ucA, recodes_Bf=ucF)
    P("  pooled (stratified by cell):")
    for v in VAR:
        for label, keys in (("all five cells", list(G6[v])),
                            ("without Llama-3.3", [k for k in G6[v] if not k.endswith("Llama-3.3-70B-Instruct")])):
            r = nboot([G6[v][k] for k in keys], seed=20261008 ^ (zlib.crc32((v + label).encode()) & 0xffff))
            e, lo, hi, l9, h9, n = r
            eq = (l9 > -0.05) and (h9 < 0.05)
            P("    {:<22} {:<18} n={:<4} diff {:+.4f} [{:+.4f},{:+.4f}]  90% [{:+.4f},{:+.4f}]  equivalent within +-0.05: {}".format(
                v, label, n, e, lo, hi, l9, h9, "YES" if eq else "NO"))
            FIG["verdict_robust_pooled|{}|{}".format(v, "all" if label.startswith("all") else "noLlama")] = dict(
                n=n, diff=e, ci95=[lo, hi], ci90=[l9, h9], equivalent=eq)
    # per-verdict hazard: P(verdict k+1 is PASS | verdicts 1..k all FAIL and a (k+1)th verdict exists)
    P("  per-verdict hazard on the paired problems (both first-pass wrong): PASS at verdict k+1 given")
    P("  k FAILs and a (k+1)th verdict; A vs Bf, pooled over the five cells and for gemma-4 Omni-MATH")
    for scope in ("pooled", "omni|gemma-4-31B-it"):
        for kk in (1, 2, 3, 4, 5):
            num = {"A": 0, "Bf": 0}; den = {"A": 0, "Bf": 0}
            for dom in ("omni", "scibench"):
                for act in ACTORS:
                    key = "{}|{}".format(dom, act)
                    if scope != "pooled" and key != scope:
                        continue
                    A = {k: v for k, v in cells.get((dom, act, "A"), {}).items() if k != "_all"}
                    F = {k: v for k, v in cells.get((dom, act, "Bf"), {}).items() if k != "_all"}
                    for u in set(A) & set(F):
                        for arm, D in (("A", A), ("Bf", F)):
                            vv = D[u]["verdicts"]
                            if len(vv) >= kk + 1 and all(x == 0 for x in vv[:kk]):
                                den[arm] += 1; num[arm] += vv[kk]
            if den["A"] == 0 and den["Bf"] == 0:
                continue
            P("    {:<22} verdict {}: A {:>3}/{:<4} = {}   Bf {:>3}/{:<4} = {}".format(
                scope, kk + 1, num["A"], den["A"], "{:.3f}".format(num["A"] / den["A"]) if den["A"] else "-",
                num["Bf"], den["Bf"], "{:.3f}".format(num["Bf"] / den["Bf"]) if den["Bf"] else "-"))
            FIG["verdict_hazard|{}|{}".format(scope, kk + 1)] = dict(
                A=[num["A"], den["A"]], Bf=[num["Bf"], den["Bf"]])
    # ------------------------------------------------------------------ G5
    # Forced submission (arm Afs), per actor, on the 400 Omni-MATH problems of the
    # post-freeze bridge re-run. gemma-4 keeps its original FIG keys ("afs|...",
    # "afs_paired|..."); every other actor's keys carry its file tag
    # ("afs_llama33|...", "afs_llama33_paired|...").
    AFS_CELLS = [  # actor, file tag, frozen file holding its arm-A cell
        ("gemma-4-31B-it", "gemma4", "campaign_v2.jsonl"),
        ("Llama-3.3-70B-Instruct", "llama33", "actor3.jsonl"),
    ]
    for act_name, tag, frozen_name in AFS_CELLS:
        afs_path = os.path.join(a.bf_dir, "afs_omnimath_{}_n400.jsonl".format(tag))
        if tag == "gemma4":
            afs_path = os.environ.get("AAMAS_AFS_FILE") or afs_path
        if not os.path.exists(afs_path):
            continue
        pfx = "afs" if tag == "gemma4" else "afs_" + tag
        P("")
        P("[G5] FORCED SUBMISSION (arm Afs: role-structured prompts, the pipeline submits every cycle)")
        P("     {}, Omni-MATH, the 400 problems of the bridge re-run; Afs file {} sha256 {}".format(
            act_name, os.path.basename(afs_path), sha256(afs_path)[:16]))

        def outcomes(path, arm, keep=None, act_name=act_name):
            out = {}
            if not os.path.exists(path):
                return out
            for r in rows(path):
                if r.get("arm") != arm or r.get("stopping_condition") == "model_unavailable":
                    continue
                if not str(r.get("actor_model", "")).endswith(act_name):
                    continue
                u = r["problem_uid"]
                if keep is not None and u not in keep:
                    continue
                prev = out.get(u)
                if prev is not None and r.get("stopping_condition") in INFRA:
                    continue
                e = ev(r)
                rt = routes(r)
                out[u] = dict(fp=(int(e[0].get("correctness") or 0) if e else None),
                              fin=int(r.get("correct") or 0),
                              verdicts=[int(x.get("correctness") or 0) for x in e],
                              approvals=sum(1 for x in rt if x == "agree"),
                              cycles=len(rt), infra=r.get("stopping_condition") in INFRA)
            return out
        X = outcomes(afs_path, "Afs")
        keep = set(X)
        BA = outcomes(os.path.join(a.bf_dir, "bridgeA_omnimath_{}_n400.jsonl".format(tag)), "A", keep)
        BF = outcomes(os.path.join(a.bf_dir, "bf_omnimath_{}.jsonl".format(tag)), "Bf", keep)
        FA = outcomes(os.path.join(a.frozen_dir, frozen_name), "A", keep)

        def summ(name, D):
            n = len(D); judged = [d for d in D.values() if d["fp"] is not None]
            fpw = [d for d in judged if d["fp"] == 0]
            rec = sum(1 for d in fpw if 1 in d["verdicts"])
            appr = sum(d["approvals"] for d in fpw) / len(fpw) if fpw else float("nan")
            ver = sum(len(d["verdicts"]) for d in fpw) / len(fpw) if fpw else float("nan")
            never = sum(1 for d in fpw if d["approvals"] == 0)
            P("  {:<34} n={:<4} infra {:<3} first pass {:.3f}  recovery {:>3}/{:<3} = {:.3f}  final {:.3f}"
              "  approvals {:.2f}  verdicts {:.2f}  never submits {}".format(
                  name, n, sum(1 for d in D.values() if d["infra"]),
                  sum(1 for d in judged if d["fp"] == 1) / len(judged) if judged else float("nan"),
                  rec, len(fpw), rec / len(fpw) if fpw else float("nan"),
                  sum(d["fin"] for d in D.values()) / n if n else float("nan"), appr, ver, never))
            FIG[pfx + "|" + name] = dict(n=n, n_fpw=len(fpw), recovered=rec,
                                         firstpass=(sum(1 for d in judged if d["fp"] == 1) / len(judged)
                                                    if judged else None),
                                         recovery=(rec / len(fpw) if fpw else None),
                                         final=(sum(d["fin"] for d in D.values()) / n if n else None),
                                         approvals=appr, verdicts=ver, never_submits=never)
        summ("Afs (forced submission)", X)
        if BA:
            summ("A re-run after the freeze (bridge)", BA)
        summ("A frozen", FA)
        summ("Bf (role-free with feedback)", BF)

        def paired(name, Y, Z, key):
            both = sorted(set(Y) & set(Z))
            if key == "rec":
                both = [u for u in both if Y[u]["fp"] == 0 and Z[u]["fp"] == 0]
                f = lambda d: int(1 in d["verdicts"])
            else:
                f = lambda d: d["fin"]
            y_only = sum(1 for u in both if f(Y[u]) and not f(Z[u]))
            z_only = sum(1 for u in both if f(Z[u]) and not f(Y[u]))
            P("  paired {:<6} {:<44} n={:<4} first-only {:<3} second-only {:<3} p={:.2g}".format(
                key, name, len(both), y_only, z_only, mcn(y_only, z_only)))
            FIG["{}_paired|{}|{}".format(pfx, key, name)] = dict(n=len(both), first_only=y_only,
                                                                 second_only=z_only, p=mcn(y_only, z_only))
        for key in ("rec", "final"):
            if BA:
                paired("Afs vs A re-run (bridge)", X, BA, key)
            paired("Afs vs A frozen", X, FA, key)
            paired("Afs vs Bf", X, BF, key)
            if BA:
                paired("A re-run (bridge) vs Bf", BA, BF, key)
    P("")
    P("[G2] LOGGING-DEFECT CHECK (Omni-MATH frozen campaign): functional collapse on all first")
    P("     passes and on clean ones (no message under 10 visible characters per second, T26)")
    for (act, arm), (n, col, nc, colc) in sorted(CLEAN.items()):
        P("  {:<23}{:<3} all {:>5} collapse {:.3f}   clean {:>5} collapse {}".format(
            act, arm, n, col / n, nc, "{:.3f}".format(colc / nc) if nc else "-"))
        FIG["defect_check|{}|{}".format(act, arm)] = dict(n=n, collapse=col / n, n_clean=nc,
                                                          collapse_clean=(colc / nc if nc else None))
    json.dump(FIG, open(os.path.join(a.out_dir, "FIGDATA_GATE.json"), "w"), indent=1, sort_keys=True)
    P("")
    P("wrote FIGDATA_GATE.json")


if __name__ == "__main__":
    main()
