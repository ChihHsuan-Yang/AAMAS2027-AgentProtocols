"""FINAL — every headline number, from the FROZEN snapshot only.

Reads experiments/results/FROZEN/ exclusively. Nothing else may source a
manuscript number. Run after any edit and diff the output.

Scoring conventions, both reported, per PREREGISTRATION.md:
  PREREG  : trajectories that never produced a graded answer are scored 0
            ("failing to parse are counted as incorrect, not dropped").
            THIS IS PRIMARY.
  ASGRADED: those trajectories are dropped. SENSITIVITY ONLY -- it carries
            8-17% one-sided attrition in Arm C (see FINDING-24).
"""
import json, glob, re, collections, hashlib, os
import numpy as np

FROZEN = "/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols/experiments/results/FROZEN"
RNG = np.random.default_rng(20261008)
ACTORS = ["gemma-4-31B-it", "gpt-oss-120b", "Llama-3.3-70B-Instruct"]
BOX = re.compile(r"\\boxed\s*\{")

def load():
    rows = []
    for f in sorted(glob.glob(FROZEN + "/*.jsonl")):
        for l in open(f):
            try: rows.append(json.loads(l))
            except Exception: pass
    return rows

rows = load()
def actor(r): return r["actor_model"].split("/")[-1]
def ev(r):    return r.get("evaluator_history") or []
def graded(r):return bool(ev(r)) and r.get("correct") is not None
def fp(r):    return int(ev(r)[0].get("correctness") or 0) if ev(r) else None
def fin_prereg(r):   return int(r.get("correct") or 0)          # ungraded -> 0
def fin_asgraded(r): return r.get("correct")                     # may be None

def boot(x, n=4000):
    x = np.asarray(x, float)
    if len(x) < 5: return (np.nan, np.nan)
    return tuple(np.percentile([RNG.choice(x, len(x)).mean() for _ in range(n)], [2.5, 97.5]))

def paired(a, armx, army, scorer):
    X = {r["problem_uid"]: scorer(r) for r in rows if actor(r) == a and r["arm"] == armx}
    Y = {r["problem_uid"]: scorer(r) for r in rows if actor(r) == a and r["arm"] == army}
    cm = [p for p in set(X) & set(Y) if X[p] is not None and Y[p] is not None]
    if len(cm) < 30: return None
    d = np.array([Y[p] - X[p] for p in cm], float)
    lo, hi = boot(d)
    return d.mean(), lo, hi, len(cm)

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
def unanimous(r):
    f = first3(r)
    if len(f) != 3: return None
    a = []
    for m in f:
        b = boxed_all(m.get("text") or "")
        if not b: return None
        a.append(nrm(b[-1]))
    return len(set(a)) == 1

print("=" * 96)
print("FINAL TABLES — FROZEN SNAPSHOT")
man = json.load(open(FROZEN + "/MANIFEST.json"))
print(f"frozen_at {man['frozen_at']}   total_rows {man['total_rows']}")
for k, v in man["files"].items(): print(f"  {k:22s} {v['rows']:>6} rows  sha256 {v['sha256'][:16]}")
print("=" * 96)

# ---------------------------------------------------------------- T0 census
print("\n[T0] CELL CENSUS")
print(f"{'actor':<24}{'arm':<5}{'planned':>8}{'done':>7}{'graded':>8}{'ungraded':>10}"
      f"{'hardfail':>10}{'retries/traj':>13}{'evalcalls':>11}")
for a in ACTORS:
    for arm in ("A","B","C","Cp"):
        s = [r for r in rows if actor(r) == a and r["arm"] == arm]
        if not s: continue
        g = [r for r in s if graded(r)]
        hf = sum(1 for r in s if r.get("hard_failure"))
        rt = np.mean([r.get("retries") or 0 for r in s])
        ec = np.mean([len(ev(r)) for r in s])
        planned = 1600 if a != "Llama-3.3-70B-Instruct" else 400
        if arm == "Cp": planned = 400
        print(f"{a:<24}{arm:<5}{planned:>8}{len(s):>7}{len(g):>8}{len(s)-len(g):>10}"
              f"{hf:>10}{rt:>13.3f}{ec:>11.2f}")

# ---------------------------------------------------------------- T1 master
print("\n[T1] MASTER RESULTS  (PREREG scoring: ungraded = incorrect)")
print(f"{'actor':<24}{'arm':<5}{'n':>6}{'firstpass':>11}{'final':>9}"
      f"{'recovery':>10}{'n_fpw':>7}{'collapse':>10}{'unanim':>9}{'frozen_ans':>12}")
T1 = {}
for a in ACTORS:
    for arm in ("A","B","C","Cp"):
        s = [r for r in rows if actor(r) == a and r["arm"] == arm]
        if not s: continue
        g = [r for r in s if graded(r)]
        f1 = np.mean([fp(r) for r in g]) if g else np.nan
        fin = np.mean([fin_prereg(r) for r in s])
        fpw = [r for r in g if fp(r) == 0]
        rec = np.mean([fin_prereg(r) for r in fpw]) if fpw else np.nan
        fc = [func_collapse(r) for r in s]; fc = [x for x in fc if x is not None]
        un = [unanimous(r) for r in s];     un = [x for x in un if x is not None]
        fr = [len(set(ansseq(r))) <= 1 for r in fpw]
        T1[(a,arm)] = dict(n=len(s), fp=f1, fin=fin, rec=rec, nfpw=len(fpw))
        cs = f"{np.mean(fc):.3f}" if fc and arm in ("A","B") else "n/a"
        print(f"{a:<24}{arm:<5}{len(s):>6}{f1:>11.3f}{fin:>9.3f}{rec:>10.3f}{len(fpw):>7}"
              f"{cs:>10}{(np.mean(un) if un else np.nan):>9.3f}"
              f"{(np.mean(fr) if fr else np.nan):>12.3f}")

# ---------------------------------------------------------------- T2 contrasts
print("\n[T2] PAIRED CONTRASTS, BOTH SCORINGS")
for label, scorer in (("PREREG (primary)", fin_prereg), ("AS-GRADED (sensitivity)", fin_asgraded)):
    print(f"\n  --- {label} ---")
    for x, y in (("A","B"), ("A","C")):
        print(f"    {y}-{x}:")
        for a in ACTORS:
            r_ = paired(a, x, y, scorer)
            if not r_: continue
            m, lo, hi, n = r_
            sig = "SIG" if not (lo < 0 < hi) else ""
            print(f"      {a:<24}{m:+.4f} [{lo:+.4f},{hi:+.4f}] n={n:<6}{sig}")

# ---------------------------------------------------------------- T3 firstpass/recovery
print("\n[T3] FIRST-PASS vs RECOVERY DECOMPOSITION  (the central claim)")
print(f"{'actor':<24}{'fpA':>7}{'fpB':>7}{'B-A fp':>9}{'  CI':<20}"
      f"{'recA':>7}{'recB':>7}{'B-A rec':>9}{'  CI':<20}{'nA':>6}{'nB':>6}")
for a in ACTORS:
    gA = [r for r in rows if actor(r)==a and r["arm"]=="A" and graded(r)]
    gB = [r for r in rows if actor(r)==a and r["arm"]=="B" and graded(r)]
    if not gA or not gB: continue
    FA = {r["problem_uid"]: fp(r) for r in gA}; FB = {r["problem_uid"]: fp(r) for r in gB}
    cm = set(FA) & set(FB)
    d = np.array([FB[p]-FA[p] for p in cm], float); lo,hi = boot(d)
    wA = [r for r in gA if fp(r)==0]; wB = [r for r in gB if fp(r)==0]
    rA = [fin_prereg(r) for r in wA]; rB = [fin_prereg(r) for r in wB]
    dr = np.mean(rB)-np.mean(rA)
    bs = [RNG.choice(rB,len(rB)).mean()-RNG.choice(rA,len(rA)).mean() for _ in range(4000)]
    rlo,rhi = np.percentile(bs,[2.5,97.5])
    print(f"{a:<24}{np.mean([FA[p] for p in cm]):>7.3f}{np.mean([FB[p] for p in cm]):>7.3f}"
          f"{d.mean():>+9.4f}  [{lo:+.4f},{hi:+.4f}]"
          f"{np.mean(rA):>7.3f}{np.mean(rB):>7.3f}{dr:>+9.4f}  [{rlo:+.4f},{rhi:+.4f}]"
          f"{len(rA):>6}{len(rB):>6}")

# ---------------------------------------------------------------- T4 paired recovery
print("\n[T4] PAIRED RECOVERY TRANSITIONS (first-pass wrong under BOTH arms)")
from math import comb
for a in ACTORS:
    for x, y in (("A","B"), ("A","C")):
        P = {r["problem_uid"]:(fp(r), fin_prereg(r)) for r in rows
             if actor(r)==a and r["arm"]==x and graded(r)}
        Q = {r["problem_uid"]:(fp(r), fin_prereg(r)) for r in rows
             if actor(r)==a and r["arm"]==y and graded(r)}
        both = [p for p in set(P)&set(Q) if P[p][0]==0 and Q[p][0]==0]
        if len(both) < 20: continue
        t = collections.Counter((P[p][1], Q[p][1]) for p in both)
        b, c = t[(1,0)], t[(0,1)]; m = b+c
        pv = min(1.0, 2*sum(comb(m,i) for i in range(min(b,c)+1))/2**m) if m else 1.0
        print(f"  {a:<24}{x} vs {y}  n={len(both):<5} "
              f"both_rec={t[(1,1)]:<4} {x}only={b:<4} {y}only={c:<4} both_fail={t[(0,0)]:<5} "
              f"rec_{x}={(t[(1,1)]+b)/len(both):.3f} rec_{y}={(t[(1,1)]+c)/len(both):.3f} p={pv:.2e}")

# ---------------------------------------------------------------- T5 mechanism
print("\n[T5] MECHANISM: opportunity vs use")
print(f"{'actor':<24}{'arm':<5}{'n_fpw':>7}{'cycles':>8}{'submits':>9}{'revising':>10}"
      f"{'acc_t1':>8}{'neverrefuse':>13}{'frozen':>8}{'recovery':>10}")
for a in ACTORS:
    for arm in ("A","B","C"):
        g = [r for r in rows if actor(r)==a and r["arm"]==arm and graded(r) and fp(r)==0]
        if len(g) < 20: continue
        cy = np.array([r.get("inner_used") or 0 for r in g], float)
        su = np.array([len(ev(r)) for r in g], float)
        rr = [routes(r) for r in g]
        t1 = np.mean([v[0]=="agree" for v in rr if v])
        nv = np.mean([not any(z!="agree" for z in v) for v in rr])
        fz = np.mean([len(set(ansseq(r)))<=1 for r in g])
        print(f"{a:<24}{arm:<5}{len(g):>7}{cy.mean():>8.2f}{su.mean():>9.2f}"
              f"{(cy-su).mean():>10.2f}{t1:>8.3f}{nv:>13.3f}{fz:>8.3f}"
              f"{np.mean([fin_prereg(r) for r in g]):>10.3f}")

# ---------------------------------------------------------------- T6 noise floor
print("\n[T6] GRADER NOISE FLOOR (identical evaluator prompts, temp 0)")
grp = collections.defaultdict(list)
for r in rows:
    for e in ev(r):
        c, k = e.get("candidate"), e.get("correctness")
        if c is None or k is None: continue
        grp[(r["problem_uid"], nrm(c))].append(int(k))
multi = {k:v for k,v in grp.items() if len(v) >= 2}
disc  = {k:v for k,v in multi.items() if len(set(v)) > 1}
tot = sum(len(v) for v in multi.values())
mino = sum(len(v)-max(collections.Counter(v).values()) for v in multi.values())
print(f"  group-level (conservative) : {len(disc)}/{len(multi)} = {len(disc)/len(multi):.4f}")
print(f"  per-call in split group    : {sum(len(v) for v in disc.values())}/{tot} = {sum(len(v) for v in disc.values())/tot:.4f}")
print(f"  minority-verdict           : {mino}/{tot} = {mino/tot:.4f}")

# ---------------------------------------------------------------- T7 Arm C cost
print("\n[T7] ARM C ENFORCEMENT COST")
print(f"{'actor':<24}{'arm':<5}{'n':>6}{'rejects/traj':>14}{'exhausted':>11}"
      f"{'attrition':>11}{'actorcalls':>12}{'walltime_s':>12}")
for a in ACTORS:
    for arm in ("A","B","C","Cp"):
        s = [r for r in rows if actor(r)==a and r["arm"]==arm]
        if not s: continue
        rej = np.mean([sum(1 for e in (r.get("regeneration_events") or [])
                           if not (e.get("validation_result") or {}).get("ok", True)) for r in s])
        exh = np.mean([1 if (r.get("hard_failure") or "").startswith("regeneration_exhausted") else 0 for r in s])
        att = 1 - sum(1 for r in s if graded(r))/len(s)
        print(f"{a:<24}{arm:<5}{len(s):>6}{rej:>14.2f}{exh:>11.3f}{att:>11.3f}"
              f"{np.mean([r.get('actor_calls') or 0 for r in s]):>12.2f}"
              f"{np.mean([r.get('wall_time_s') or 0 for r in s]):>12.1f}")
print("\n" + "=" * 96)
