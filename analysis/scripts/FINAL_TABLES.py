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

def boot(x, n=20000):
    x = np.asarray(x, float)
    if len(x) < 5: return (np.nan, np.nan)
    return tuple(np.percentile([RNG.choice(x, len(x)).mean() for _ in range(n)], [2.5, 97.5]))

def paired(a, armx, army, scorer):
    X = {r["problem_uid"]: scorer(r) for r in rows if actor(r) == a and r["arm"] == armx}
    Y = {r["problem_uid"]: scorer(r) for r in rows if actor(r) == a and r["arm"] == army}
    cm = sorted(p for p in set(X) & set(Y) if X[p] is not None and Y[p] is not None)
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
    cm = sorted(set(FA) & set(FB))
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
        both = sorted(p for p in set(P)&set(Q) if P[p][0]==0 and Q[p][0]==0)
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
NOISE_FLOOR = len(disc)/len(multi)
NOISE_FLOOR_N = (len(disc), len(multi))
print(f"  group-level (conservative) : {len(disc)}/{len(multi)} = {NOISE_FLOOR:.4f}")
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

# =====================================================================================
# ADDITIONS (2026-09-30) — every remaining manuscript literal, from the frozen snapshot.
# Added per the writing brief: "If a number you need is not in FINAL_TABLES.py output,
# ADD a section to that script to compute it from the frozen snapshot."
# =====================================================================================

EVAL_EQ = re.compile(r"=\s*[-+]?\d+(?:\.\d+)?")   # frozen definition, from x2/x3
NUMTOK  = re.compile(r"[0-9]+(?:\.[0-9]+)?")

def role_msgs(r, role):
    return [m for m in (r.get("messages") or []) if m.get("role") == role]

def has_answer(m, arm):
    t = m.get("text") or ""
    return bool(boxed_all(t)) or (arm in ("C","Cp") and bool(jans(t)))

# ---------------------------------------------------------------- T8 role decomposition
print("\n[T8] FUNCTIONAL COLLAPSE DECOMPOSED BY ROLE (first pipeline pass)")
print(f"{'actor':<24}{'arm':<5}{'n':>6}{'planner':>10}{'executor':>10}{'reviewer':>10}{'all3':>8}")
for a in ACTORS:
    for arm in ("A","B","C","Cp"):
        s = [r for r in rows if actor(r) == a and r["arm"] == arm]
        if not s: continue
        pr, ex, rv, al = [], [], [], []
        for r in s:
            f = first3(r)
            if len(f) != 3: continue
            d = {m["role"]: m for m in f}
            if set(d) != {"planner","executor","reviewer"}: continue
            pr.append(has_answer(d["planner"], arm)); ex.append(has_answer(d["executor"], arm))
            rv.append(has_answer(d["reviewer"], arm)); al.append(pr[-1] and ex[-1] and rv[-1])
        if not pr: continue
        print(f"{a:<24}{arm:<5}{len(pr):>6}{np.mean(pr):>10.3f}{np.mean(ex):>10.3f}"
              f"{np.mean(rv):>10.3f}{np.mean(al):>8.3f}")

# ---------------------------------------------------------------- T9 planner shape
print("\n[T9] ARM B PLANNER SHAPE (the F22 instrument check)")
print(f"{'actor':<24}{'arm':<5}{'n':>6}{'med chars':>11}{'med lat_s':>11}{'med ch/s':>10}"
      f"{'frac<500ch':>12}{'reasfallbk':>12}")
for a in ACTORS:
    for arm in ("A","B"):
        ms = [m for r in rows if actor(r)==a and r["arm"]==arm for m in role_msgs(r,"planner")]
        if not ms: continue
        ch  = np.array([len(m.get("text") or "") for m in ms], float)
        lat = np.array([m.get("latency_s") or np.nan for m in ms], float)
        ok  = ~np.isnan(lat) & (lat > 0)
        chs = ch[ok] / lat[ok]
        rf  = np.mean([bool(m.get("used_reasoning_fallback")) for m in ms])
        print(f"{a:<24}{arm:<5}{len(ms):>6}{np.median(ch):>11.0f}{np.median(lat[ok]):>11.1f}"
              f"{np.median(chs):>10.2f}{np.mean(ch < 500):>12.3f}{rf:>12.3f}")
sub = [m for r in rows if actor(r)=="gpt-oss-120b" and r["arm"]=="B"
       for m in role_msgs(r,"planner") if len(m.get("text") or "") < 100]
print(f"  gpt-oss Arm B planner messages <100 visible chars: n={len(sub)}, "
      f"used_reasoning_fallback true in {sum(bool(m.get('used_reasoning_fallback')) for m in sub)}")

# ---------------------------------------------------------------- T10 duplication vs null
print("\n[T10] PLANNER-EXECUTOR NUMERIC-TOKEN OVERLAP vs A SHUFFLED NULL (first pass)")
print(f"{'actor':<24}{'arm':<5}{'n':>6}{'real J':>9}{'null J':>9}{'excess':>9}")
EXC = {}
for a in ACTORS:
    for arm in ("A","B"):
        P, E = [], []
        for r in rows:
            if actor(r) != a or r["arm"] != arm: continue
            f = first3(r); d = {m["role"]: m for m in f}
            if "planner" not in d or "executor" not in d: continue
            p = set(NUMTOK.findall(d["planner"].get("text") or ""))
            e = set(NUMTOK.findall(d["executor"].get("text") or ""))
            if not p or not e: continue
            P.append(p); E.append(e)
        if len(P) < 30: continue
        J = lambda x, y: len(x & y) / len(x | y)
        real = np.mean([J(P[i], E[i]) for i in range(len(P))])
        idx = RNG.permutation(len(P))
        idx = np.where(idx == np.arange(len(P)), (idx + 1) % len(P), idx)
        null = np.mean([J(P[i], E[idx[i]]) for i in range(len(P))])
        EXC[(a, arm)] = real - null
        print(f"{a:<24}{arm:<5}{len(P):>6}{real:>9.3f}{null:>9.3f}{real-null:>+9.3f}")
print("  excess-over-null B-A:  " + "  ".join(
    f"{a.split('-')[0]}={EXC[(a,'B')]-EXC[(a,'A')]:+.3f}" for a in ACTORS if (a,"B") in EXC and (a,"A") in EXC))

# ---------------------------------------------------------------- T11 manipulation check
print("\n[T11] ARM C MANIPULATION CHECK — answer authorship, TWO definitions")
print("  authored  = planner emits a schema answer field / a boxed answer as its OWN output")
print("  anymarker = planner text contains any answer marker at all, incl. inside plan prose")
print(f"{'actor':<24}{'arm':<5}{'msgs':>6}{'authored-free':>15}{'anymarker-free':>16}"
      f"{'boundaryRej':>13}{'perTraj':>9}")
BOUND = ("answer_leak:", "missing_field:", "additional_property:")
for a in ACTORS:
    for arm in ("A","B","C","Cp"):
        s_ = [r for r in rows if actor(r)==a and r["arm"]==arm]
        if not s_: continue
        au, am, br = [], [], 0
        for r in s_:
            for m in role_msgs(r, "planner"):
                t = m.get("text") or ""
                # In C/Cp the planner schema HAS no answer field, so "authored" can only
                # be a JSON answer key; a \boxed inside a plan string is not authorship.
                au.append(not (jans(t) if arm in ("C","Cp") else boxed_all(t)))
                am.append(not (boxed_all(t) or (jans(t) if arm in ("C","Cp") else [])))
            for e in r.get("regeneration_events") or []:
                vr = e.get("validation_result") or {}
                vc = str(vr.get("violated_constraint") or "")
                if not vr.get("ok", True) and vc.startswith(BOUND): br += 1
        if not au: continue
        print(f"{a:<24}{arm:<5}{len(au):>6}{np.mean(au):>15.3f}{np.mean(am):>16.3f}"
              f"{br:>13}{br/len(s_):>9.2f}")

# ---------------------------------------------------------------- T12 planner eq density
print("\n[T12] PLANNER EVALUATED-EQUATION DENSITY (per 1,000 chars) + binary P1a-style rate")
print(f"{'actor':<24}{'arm':<5}{'n':>6}{'density':>10}{'binary abstain':>16}{'med chars':>11}")
for a in ACTORS:
    for arm in ("A","B","C","Cp"):
        ms = [m for r in rows if actor(r)==a and r["arm"]==arm for m in role_msgs(r,"planner")]
        if not ms: continue
        tot_eq = sum(len(EVAL_EQ.findall(m.get("text") or "")) for m in ms)
        tot_ch = sum(len(m.get("text") or "") for m in ms)
        binr = np.mean([len(EVAL_EQ.findall(m.get("text") or "")) == 0 for m in ms])
        print(f"{a:<24}{arm:<5}{len(ms):>6}{1000*tot_eq/max(tot_ch,1):>10.2f}{binr:>16.3f}"
              f"{np.median([len(m.get('text') or '') for m in ms]):>11.0f}")

# ---------------------------------------------------------------- T13 oracle-loop value
print("\n[T13] WHAT THE ORACLE RETRY LOOP BUYS (first pass -> final, paired, PREREG scoring)")
print(f"{'actor':<24}{'arm':<5}{'n':>6}{'firstpass':>11}{'final':>9}{'gain':>9}{'  CI':<22}")
for a in ACTORS:
    for arm in ("A","B","C"):
        g = [r for r in rows if actor(r)==a and r["arm"]==arm and graded(r)]
        if len(g) < 30: continue
        d = np.array([fin_prereg(r) - fp(r) for r in g], float)
        lo, hi = boot(d)
        print(f"{a:<24}{arm:<5}{len(g):>6}{np.mean([fp(r) for r in g]):>11.3f}"
              f"{np.mean([fin_prereg(r) for r in g]):>9.3f}{d.mean():>+9.4f}  [{lo:+.4f},{hi:+.4f}]")

# ---------------------------------------------------------------- T14 P4 interaction
print("\n[T14] P4 — ACTOR x INTERVENTION INTERACTION ON ACCURACY (C-A), PREREG scoring")
def ca_vec(a):
    X = {r["problem_uid"]: fin_prereg(r) for r in rows if actor(r)==a and r["arm"]=="A"}
    Y = {r["problem_uid"]: fin_prereg(r) for r in rows if actor(r)==a and r["arm"]=="C"}
    cm = sorted(set(X) & set(Y))
    return np.array([Y[p] - X[p] for p in cm], float)
for i in range(len(ACTORS)):
    for j in range(i+1, len(ACTORS)):
        u, v = ca_vec(ACTORS[i]), ca_vec(ACTORS[j])
        if len(u) < 30 or len(v) < 30: continue
        dd = v.mean() - u.mean()
        bs = [RNG.choice(v, len(v)).mean() - RNG.choice(u, len(u)).mean() for _ in range(4000)]
        lo, hi = np.percentile(bs, [2.5, 97.5])
        print(f"  {ACTORS[j]:<24} minus {ACTORS[i]:<24} {dd:+.4f} [{lo:+.4f},{hi:+.4f}]"
              f"{'  SIG' if not (lo<0<hi) else '  null'}")

# ---------------------------------------------------------------- T15 Cp - C
print("\n[T15] C' MINUS C (context control at fixed enforcement), both scorings")
for label, scorer in (("PREREG", fin_prereg), ("AS-GRADED", fin_asgraded)):
    for a in ACTORS:
        r_ = paired(a, "C", "Cp", scorer)
        if not r_: continue
        m, lo, hi, n = r_
        print(f"  {label:<10}{a:<24}{m:+.4f} [{lo:+.4f},{hi:+.4f}] n={n}"
              f"{'  SIG' if not (lo<0<hi) else ''}")

# ---------------------------------------------------------------- T16 unanimity / lock-in
print("\n[T16] UNANIMITY AND ANSWER MOVEMENT, first-pass-wrong")
print(f"{'actor':<24}{'arm':<5}{'n_fpw':>7}{'unanim':>9}{'recov|unan':>12}"
      f"{'moves|unan':>12}{'n_unan':>8}")
for a in ACTORS:
    for arm in ("A","B"):
        g = [r for r in rows if actor(r)==a and r["arm"]==arm and graded(r) and fp(r)==0]
        if len(g) < 20: continue
        un = [r for r in g if unanimous(r) is True]
        ua = [unanimous(r) for r in g]; ua = [x for x in ua if x is not None]
        rec = np.mean([fin_prereg(r) for r in un]) if un else np.nan
        mov = np.mean([len(set(ansseq(r))) > 1 for r in un]) if un else np.nan
        print(f"{a:<24}{arm:<5}{len(g):>7}{(np.mean(ua) if ua else np.nan):>9.3f}"
              f"{rec:>12.3f}{mov:>12.3f}{len(un):>8}")

# ---------------------------------------------------------------- T17 single-agent control
print("\n[T17] BUDGET-MATCHED SINGLE-AGENT CONTROL")
print("  *** NOT IN THE FROZEN SNAPSHOT.  Source: historical released trace corpus,")
print("      protocol_id='single_agent', benchmark omnimath2, joined by problem_uid. ***")
SA_PARQUET = ("/Users/bellayang/Documents/note/projects/IEEE-BigData-SciAgentTrace/"
              "analysis/hf_cache/release/data/trajectories/part-00000.parquet")
try:
    import pyarrow.parquet as pq
    sa = pq.read_table(SA_PARQUET).to_pandas()
    sa = sa[(sa.protocol_id == "single_agent") & (sa.benchmark_id == "omnimath2")]
    NAME = {"gemma_4_31b": "gemma-4-31B-it", "gpt_oss_120b": "gpt-oss-120b"}
    print(f"  source rows {len(sa)}  sha256(file)[:16] "
          f"{hashlib.sha256(open(SA_PARQUET,'rb').read()).hexdigest()[:16]}")
    print(f"\n  {'actor':<24}{'arm':<5}{'n':>6}{'arm acc':>9}{'SA acc':>9}{'arm-SA':>9}{'  CI':<22}")
    for key, a in NAME.items():
        s = sa[sa.actor_model_id == key]
        S = dict(zip(s.problem_uid, s.final_correct.astype(int)))
        for arm in ("A", "B"):
            X = {r["problem_uid"]: fin_prereg(r) for r in rows
                 if actor(r) == a and r["arm"] == arm}
            cm = sorted(set(X) & set(S))
            if len(cm) < 30: continue
            d = np.array([X[p] - S[p] for p in cm], float)
            lo, hi = boot(d)
            print(f"  {a:<24}{arm:<5}{len(cm):>6}{np.mean([X[p] for p in cm]):>9.4f}"
                  f"{np.mean([S[p] for p in cm]):>9.4f}{d.mean():>+9.4f}  [{lo:+.4f},{hi:+.4f}]"
                  f"{'  SIG' if not (lo<0<hi) else ''}")
    print(f"\n  {'actor':<24}{'arm/protocol':<16}{'evalcalls':>11}{'actorcalls':>12}")
    for key, a in NAME.items():
        s = sa[sa.actor_model_id == key]
        print(f"  {a:<24}{'single_agent':<16}{s.evaluator_calls.mean():>11.2f}"
              f"{s.model_calls.mean():>12.2f}")
        for arm in ("A", "B"):
            g = [r for r in rows if actor(r) == a and r["arm"] == arm]
            print(f"  {a:<24}{'our Arm '+arm:<16}{np.mean([len(ev(r)) for r in g]):>11.2f}"
                  f"{np.mean([r.get('actor_calls') or 0 for r in g]):>12.2f}")
except Exception as e:
    print(f"  UNAVAILABLE: {e}")

print("\n" + "=" * 96)

# ---------------------------------------------------------------- T18 byte duplication
print("\n[T18] EXACT OUTPUT DUPLICATION (first pass) AND THE OBVIOUS ATTACKS ON IT")
print(f"{'actor':<24}{'arm':<5}{'n':>6}{'byte dup':>10}{'norm dup':>10}"
      f"{'dup w/ identical prompts':>26}")
TOTDUP = TOTSAME = 0
for a in ACTORS:
    for arm in ("A","B","C","Cp"):
        s_ = [r for r in rows if actor(r)==a and r["arm"]==arm]
        if not s_: continue
        dup, nd, samep = [], [], 0
        for r in s_:
            f = first3(r)
            if len(f) != 3: continue
            h = [m.get("response_sha256_12") for m in f]
            t = [re.sub(r"\s+", " ", (m.get("text") or "")).strip().lower() for m in f]
            d = len(set(h)) < 3
            dup.append(d); nd.append(len(set(t)) < 3)
            if d:
                TOTDUP += 1
                ph = [m.get("prompt_sha256_12") for m in f]
                # was the duplication produced by two agents receiving the SAME prompt?
                for i in range(3):
                    for j in range(i+1, 3):
                        if h[i] == h[j] and ph[i] == ph[j]: samep += 1; TOTSAME += 1; break
                    else: continue
                    break
        if not dup: continue
        print(f"{a:<24}{arm:<5}{len(dup):>6}{np.mean(dup):>10.3f}{np.mean(nd):>10.3f}{samep:>26}")
print(f"  pooled: {TOTDUP} duplicated first passes, {TOTSAME} of them from identical prompts")

# ---------------------------------------------------------------- T19 F18 scoring defect
print("\n[T19] F18 SCORING DEFECT: graded answer vs the answer the team last HELD")
print("  runner records correct = grade of the last SUBMITTED answer, while")
print("  final_answer = the answer the team last held. They can disagree.")
# GOLD MUST come from the parquet runner.py reads, because that is the string
# the evaluator was shown (load_problems builds ref from r["answer"]). An
# earlier version read a seeded manifest instead; it covers only the n=1600
# sample, so 247 of 432 mismatched rows silently resolved to gold=None and the
# under-credited count came out 28 instead of 57. A missing key is not a
# negative.
import pandas as _pd
_PQ = ("/Users/bellayang/Documents/note/projects/IEEE-BigData-SciAgentTrace/"
       "analysis/hf_cache/release/data/problems/part-00000.parquet")
_df = _pd.read_parquet(_PQ); _df = _df[_df["benchmark_id"] == "omnimath2"]
GOLD = dict(zip(_df["problem_uid"].astype(str), _df["answer"].astype(str)))
_missing = sum(1 for r in rows if r["problem_uid"] not in GOLD)
print(f"  gold from the parquet the grader read: {len(GOLD)} problems; "
      f"trajectories with no gold entry: {_missing}")
assert _missing == 0, "gold coverage incomplete -- counts below would be floors of a floor"
print(f"{'actor':<24}{'arm':<5}{'n_fpw':>7}{'mismatch rate':>15}{'held==gold & graded 0':>23}")
TOTMM = TOTUC = 0
for a in ACTORS:
    for arm in ("A","B","C"):
        g = [r for r in rows if actor(r)==a and r["arm"]==arm and graded(r) and fp(r)==0]
        if len(g) < 20: continue
        mm = uc = 0
        for r in g:
            last_sub = nrm((ev(r)[-1] or {}).get("candidate"))
            held = nrm(r.get("final_answer"))
            if held is None or last_sub is None or held == last_sub: continue
            mm += 1
            gold = nrm(GOLD.get(r["problem_uid"]))
            if gold is not None and held == gold and fin_prereg(r) == 0: uc += 1
        TOTMM += mm; TOTUC += uc
        print(f"{a:<24}{arm:<5}{len(g):>7}{mm/len(g):>15.3f}{uc:>23}")
print(f"  totals over first-pass-wrong: {TOTMM} mismatched, {TOTUC} demonstrably under-credited")
# positive control: does exact-match-gold ever disagree with the grader on
# NON-mismatched rows?  If it does, the count above is not a clean floor.
pcn = pcd = 0
for r in rows:
    if not graded(r): continue
    last_sub = nrm((ev(r)[-1] or {}).get("candidate")); held = nrm(r.get("final_answer"))
    if held is None or last_sub is None or held != last_sub: continue
    gold = nrm(GOLD.get(r["problem_uid"]))
    if gold is None: continue
    pcn += 1
    if held == gold and fin_prereg(r) == 0: pcd += 1
print(f"  positive control on {pcn} non-mismatched graded rows: "
      f"exact-match-gold AND graded wrong = {pcd} ({pcd/max(pcn,1):.4f})")

# ---------------------------------------------------------------- T20 collapse sensitivity
print("\n[T20] FUNCTIONAL COLLAPSE UNDER THREE ANSWER-MARKER DEFINITIONS (first pass)")
STRICT = re.compile(r"\\boxed\s*\{")
MED    = re.compile(r"\\boxed\s*\{|(?:final|the)\s+answer\s*(?:is|:)", re.I)
LOOSE  = re.compile(r"\\boxed\s*\{|answer\s*(?:is|:)|therefore[, ]|hence[, ]|=\s*[-+]?\d", re.I)
print(f"{'actor':<24}{'arm':<5}{'n':>6}{'strict':>9}{'medium':>9}{'loose':>9}")
for a in ACTORS:
    for arm in ("A","B"):
        s_ = [r for r in rows if actor(r)==a and r["arm"]==arm]
        out = []
        for rx in (STRICT, MED, LOOSE):
            v = []
            for r in s_:
                f = first3(r)
                if len(f) != 3: continue
                v.append(all(rx.search(m.get("text") or "") for m in f))
            out.append(np.mean(v) if v else np.nan)
        print(f"{a:<24}{arm:<5}{len(s_):>6}{out[0]:>9.3f}{out[1]:>9.3f}{out[2]:>9.3f}")

print("\n" + "=" * 96)

# ---------------------------------------------------------------- T21 token-set sizes
print("\n[T21] WHY T10's gpt-oss ROW IS NOT INTERPRETABLE: numeric-token-set sizes")
print(f"{'actor':<24}{'arm':<5}{'med |planner|':>15}{'med |executor|':>16}")
for a in ACTORS:
    for arm in ("A","B"):
        P, E = [], []
        for r in rows:
            if actor(r) != a or r["arm"] != arm: continue
            d = {m["role"]: m for m in first3(r)}
            if "planner" not in d or "executor" not in d: continue
            P.append(len(set(NUMTOK.findall(d["planner"].get("text") or ""))))
            E.append(len(set(NUMTOK.findall(d["executor"].get("text") or ""))))
        if not P: continue
        print(f"{a:<24}{arm:<5}{np.median(P):>15.0f}{np.median(E):>16.0f}")
print("  A Jaccard over 1-2 token sets is not a duplication measure; gpt-oss Arm B")
print("  is excluded from the duplication claim for this reason (and per FINDING-22).")

# ---------------------------------------------------------------- T22 context confound
print("\n[T22] CONTEXT CONTAMINATION: recovery by POOLED context quartile, first-pass-wrong")
print(f"{'actor':<24}{'quartile':<10}{'Arm A':>18}{'Arm B':>18}")
def ctx(r):
    return sum(len(m.get("text") or "") for m in (r.get("messages") or [])
               if m.get("role") in ("planner","executor","reviewer"))
for a in ACTORS:
    g = [r for r in rows if actor(r)==a and r["arm"] in ("A","B") and graded(r) and fp(r)==0]
    if len(g) < 40: continue
    q = np.percentile([ctx(r) for r in g], [25, 50, 75])
    for k, lab in enumerate(("Q1 (low)","Q2","Q3","Q4 (high)")):
        cells = []
        for arm in ("A","B"):
            s_ = [r for r in g if r["arm"]==arm and np.searchsorted(q, ctx(r), "right")==k]
            cells.append(f"{np.mean([fin_prereg(r) for r in s_]):.3f} (n={len(s_)})"
                         if len(s_) >= 8 else f"-- (n={len(s_)})")
        print(f"{a:<24}{lab:<10}{cells[0]:>18}{cells[1]:>18}")

# ---------------------------------------------------------------- T23 adjudication
print("\n[T23] BLINDED ADJUDICATION")
print("  *** NOT IN THE FROZEN SNAPSHOT. Source: adjudication/VERDICTS.jsonl + KEY.jsonl,")
print("      rubric frozen before the first judgement. ***")
ADJ = os.path.join(os.path.dirname(FROZEN), "..", "..", "adjudication")
ADJ = os.path.normpath(ADJ)
try:
    V = [json.loads(l) for l in open(ADJ + "/VERDICTS.jsonl")]
    KEY = {json.loads(l)["tid"]: json.loads(l) for l in open(ADJ + "/KEY.jsonl")}
    for f in ("VERDICTS.jsonl", "KEY.jsonl", "RUBRIC_v1.md"):
        print(f"  {f:18s} sha256 {hashlib.sha256(open(ADJ+'/'+f,'rb').read()).hexdigest()[:16]}")
    byi = collections.defaultdict(list)
    for v in V:
        if v.get("parsed"): byi[v["tid"]].append(v["parsed"])
    multi = {t: ps for t, ps in byi.items() if len(ps) >= 2}
    for q in ("Q1","Q2","Q5"):
        ag = sum(1 for ps in multi.values() if len({p[q] for p in ps}) == 1)
        print(f"  stability {q}: all-reps-agree {ag}/{len(multi)} = {ag/len(multi):.3f}")
    maj = {t: {q: collections.Counter(p[q] for p in ps).most_common(1)[0][0]
               for q in ("Q1","Q2","Q5")} for t, ps in byi.items()}
    print(f"\n  {'actor':<24}{'arm':<5}{'n':>5}{'no division of labour':>24}")
    cells = collections.defaultdict(list)
    for t, m in maj.items():
        if t in KEY: cells[(KEY[t]["actor"], KEY[t]["arm"])].append(m["Q5"] == "NO")
    for (act, arm) in sorted(cells):
        v = cells[(act, arm)]
        print(f"  {act:<24}{arm:<5}{len(v):>5}{np.mean(v):>24.3f}")
    tp = sum(1 for t, m in maj.items() if t in KEY and KEY[t]["auto_collapse"] and m["Q5"]=="NO")
    fp_ = sum(1 for t, m in maj.items() if t in KEY and KEY[t]["auto_collapse"] and m["Q5"]=="YES")
    fn = sum(1 for t, m in maj.items() if t in KEY and not KEY[t]["auto_collapse"] and m["Q5"]=="NO")
    print(f"\n  byte metric vs judge (pooled n={len(maj)}): TP={tp} FP={fp_} FN={fn}"
          f"  precision={tp/(tp+fp_):.3f}  recall={tp/(tp+fn):.3f}")
    nflag = collections.Counter(KEY[t]["actor"] for t in maj if t in KEY and KEY[t]["auto_collapse"])
    print(f"  flag firings per actor: {dict(nflag)}")
except Exception as e:
    print(f"  UNAVAILABLE: {e}")

print("\n" + "=" * 96)

# ---------------------------------------------------------------- T24 scale
print("\n[T24] SCALE (for the Campaign paragraph)")
nm = sum(1 for r in rows for m in (r.get("messages") or [])
         if m.get("role") in ("planner","executor","reviewer"))
nev = sum(len(ev(r)) for r in rows)
print(f"  trajectories            {len(rows)}")
print(f"  role messages           {nm}")
print(f"  evaluator gradings      {nev}")
print(f"  distinct problems       {len({r['problem_uid'] for r in rows})}")
for a in ACTORS:
    pa = {r['problem_uid'] for r in rows if actor(r)==a}
    per = {arm: len({r['problem_uid'] for r in rows if actor(r)==a and r['arm']==arm})
           for arm in ("A","B","C","Cp")}
    print(f"  {a:<24} problems={len(pa):<6} per-arm={per}")
print(f"  benchmarks              {sorted({r['benchmark_id'] for r in rows})}")
print(f"  domains                 {sorted({r['domain'] for r in rows})}")
print(f"  evaluator model         {sorted({r['evaluator_model'] for r in rows})}")
print(f"  backends                {sorted({r['backend'] for r in rows})}")
bud = rows[0].get("budget") or {}
print(f"  budget (row 0)          {bud}")
print(f"  distinct budgets        {len({json.dumps(r.get('budget'), sort_keys=True) for r in rows})}")

# ---------------------------------------------------------------- T25 pre-oracle recovery
print("\n[T25] IS ANY RECOVERY PRE-ORACLE? (answer changes before the first evaluator verdict)")
print(f"{'actor':<24}{'arm':<5}{'n_fpw':>7}{'recovered before 1st verdict':>30}")
for a in ACTORS:
    for arm in ("A","B","C"):
        g = [r for r in rows if actor(r)==a and r["arm"]==arm and graded(r) and fp(r)==0]
        if len(g) < 20: continue
        # the first evaluator verdict is by construction the first submission; a
        # "pre-oracle recovery" would be a trajectory graded correct with exactly
        # one evaluator call whose own verdict was wrong -- impossible by definition.
        pre = sum(1 for r in g if len(ev(r)) == 1 and fin_prereg(r) == 1)
        print(f"{a:<24}{arm:<5}{len(g):>7}{pre:>30}")

print("\n" + "=" * 96)

# ---------------------------------------------------------------- T26 logging defect
print("\n[T26] F13 LOGGING DEFECT: visible characters per second of latency")
print("  A message whose reasoning was discarded logs as SHORT but is SLOW.")
print(f"{'actor':<24}{'arm':<5}{'msgs':>7}{'low ch/s (<10)':>16}"
      f"{'flag true':>11}{'first passes w/ >=1 low':>25}")
for a in ACTORS:
    for arm in ("A","B"):
        s_ = [r for r in rows if actor(r)==a and r["arm"]==arm]
        ms, fpw = [], []
        for r in s_:
            low_any = False
            for m in (r.get("messages") or []):
                if m.get("role") not in ("planner","executor","reviewer"): continue
                lat = m.get("latency_s") or 0
                if lat <= 0: continue
                low = (len(m.get("text") or "") / lat) < 10
                ms.append((low, bool(m.get("used_reasoning_fallback"))))
            f = first3(r)
            for m in f:
                lat = m.get("latency_s") or 0
                if lat > 0 and (len(m.get("text") or "") / lat) < 10: low_any = True
            if len(f) == 3: fpw.append(low_any)
        if not ms: continue
        print(f"{a:<24}{arm:<5}{len(ms):>7}{np.mean([x[0] for x in ms]):>16.3f}"
              f"{np.mean([x[1] for x in ms]):>11.3f}{np.mean(fpw):>25.3f}")

print(f"\n[T27] NOISE-FLOOR MARGIN for each B-A accuracy contrast "
      f"(floor = T6 group-level {NOISE_FLOOR_N[0]}/{NOISE_FLOOR_N[1]})")
floor = NOISE_FLOOR   # T6 group-level; do NOT recompute from `multi` (reused in T23)
for a in ACTORS:
    r_ = paired(a, "A", "B", fin_prereg)
    if not r_: continue
    m, lo, hi, n = r_
    print(f"  {a:<24}|B-A|={abs(m):.4f}  floor={floor:.4f}  ratio={abs(m)/floor:.1f}x"
          f"  {'clears' if abs(m)/floor >= 2 and not (lo<0<hi) else 'NOT resolvable above noise'}")

print("\n" + "=" * 96)
