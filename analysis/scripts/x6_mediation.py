"""x6 — the unanimity -> acceptance -> revision -> recovery chain (Bella S8).

CORRECTS TWO ERRORS IN F16
--------------------------
E1. F16 said "Arm B gets MORE repair opportunity (2.5x more evaluator calls)".
    Wrong unit. Every arm runs the SAME cycle budget: MAX_OUTER_ROUNDS=3 x
    INNER_ROUNDS=2 = 6 deliberation cycles. The evaluator fires only when the
    Reviewer approves, so "evaluator calls" counts SUBMISSIONS, not chances.
    Arm B submits on ~90-99% of its cycles; Arm A on ~31-46%. Same chances,
    different spending.
E2. F16's matched-opportunity table matched on evaluator calls, i.e. on
    submissions -- a post-treatment variable that differs by arm by
    construction. The correct matching variable is CYCLES.

Matching on cycles is still conditioning on a post-treatment quantity, so
everything here is labelled descriptive/associational.
"""
import json, glob, re, collections
import numpy as np

ROOT = "/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols"
RNG = np.random.default_rng(20261008)
BOXED = re.compile(r"\\boxed\s*\{")

rows = []
for f in sorted(glob.glob(ROOT + "/experiments/results/main/*.jsonl")):
    if "BUG" in f or "SNAPSHOT" in f: continue
    for l in open(f):
        try: rows.append(json.loads(l))
        except Exception: pass

def actor(r): return r["actor_model"].split("/")[-1]
ACTORS = sorted({actor(r) for r in rows})
def evals(r): return r.get("evaluator_history") or []
def fp_wrong(r):
    e = evals(r); return bool(e) and int(e[0].get("correctness") or 0) == 0
def cycles(r): return int(r.get("inner_used") or 0)
def rec(r): return int(r.get("correct") or 0)

def norm(s):
    if s is None: return None
    s = re.sub(r"\s+", "", str(s)).strip("$").strip(); return s or None

def boxed_all(t):
    out = []
    for m in BOXED.finditer(t or ""):
        i, d = m.end() - 1, 0
        for j in range(i, min(len(t), i + 4000)):
            if t[j] == "{": d += 1
            elif t[j] == "}":
                d -= 1
                if d == 0: out.append(t[i+1:j]); break
    return out

def json_ans(t):
    o = [m.group(1) for m in re.finditer(r'"answer"\s*:\s*"((?:[^"\\]|\\.)*)"', t or "")]
    o += [m.group(1) for m in re.finditer(r'"answer"\s*:\s*(-?[0-9][0-9.eE+/-]*)', t or "")]
    return o

def ansseq(r):
    seq, arm = [], r.get("arm")
    for m in (r.get("messages") or []):
        if m.get("role") not in ("planner","executor","reviewer"): continue
        t = m.get("text") or ""
        for b in boxed_all(t) + (json_ans(t) if arm in ("C","Cp") else []):
            a = norm(b)
            if a and (not seq or seq[-1] != a): seq.append(a)
    return seq

def routes(r):
    return [m.get("route") for m in (r.get("messages") or [])
            if m.get("role") == "reviewer" and m.get("route")]

def boot(x, n=4000):
    x = np.asarray(x, float)
    if len(x) < 5: return (np.nan, np.nan)
    return tuple(np.percentile([RNG.choice(x,len(x)).mean() for _ in range(n)],[2.5,97.5]))

print("="*78); print("x6  MEDIATION CHAIN — corrected units"); print("="*78)

# ---- M0: the correction itself, stated as a table ----------------------
print("\n" + "-"*78)
print("M0  SAME BUDGET, DIFFERENT SPENDING  (first-pass-wrong trajectories)")
print("-"*78)
print(f"{'actor':<24}{'arm':<5}{'n':>6}{'cycles used':>13}{'submissions':>13}"
      f"{'revisions':>11}{'recovery':>10}")
for a in ACTORS:
    for arm in ("A","B","C"):
        s = [r for r in rows if actor(r)==a and r["arm"]==arm and fp_wrong(r)]
        if len(s) < 10: continue
        cy = np.array([cycles(r) for r in s], float)
        su = np.array([len(evals(r)) for r in s], float)
        rv = cy - su                     # cycles NOT spent on a submission
        print(f"{a:<24}{arm:<5}{len(s):>6}{cy.mean():>13.2f}{su.mean():>13.2f}"
              f"{rv.mean():>11.2f}{np.mean([rec(r) for r in s]):>10.3f}")

# ---- M1: does the reviewer refuse? -------------------------------------
print("\n" + "-"*78)
print("M1  STEP 1-2  unanimity -> the Reviewer stops refusing")
print("-"*78)
print(f"{'actor':<24}{'arm':<5}{'n':>6}{'P(agree turn1)':>16}{'P(never refuses)':>18}"
      f"{'refusals/traj':>15}")
for a in ACTORS:
    for arm in ("A","B","C"):
        s = [r for r in rows if actor(r)==a and r["arm"]==arm and fp_wrong(r)]
        if len(s) < 10: continue
        f1 = [routes(r)[0] for r in s if routes(r)]
        nev = [not any(x!="agree" for x in routes(r)) for r in s]
        nr = [sum(1 for x in routes(r) if x!="agree") for r in s]
        print(f"{a:<24}{arm:<5}{len(s):>6}{np.mean([x=='agree' for x in f1]):>16.3f}"
              f"{np.mean(nev):>18.3f}{np.mean(nr):>15.2f}")

# ---- M2: refusal -> answer change --------------------------------------
print("\n" + "-"*78)
print("M2  STEP 3  a refusal is what moves the answer")
print("    (pooled over arms WITHIN actor, so the arm is not doing the work)")
print("-"*78)
print(f"{'actor':<24}{'refusals':<10}{'n':>7}{'P(answer moves)':>18}{'recovery':>10}")
for a in ACTORS:
    s = [r for r in rows if actor(r)==a and r["arm"] in ("A","B") and fp_wrong(r)]
    for lo, hi, lab in ((0,0,"0"),(1,1,"1"),(2,99,"2+")):
        g = [r for r in s if lo <= sum(1 for x in routes(r) if x!="agree") <= hi]
        if len(g) < 10: continue
        mv = np.mean([len(set(ansseq(r))) > 1 for r in g])
        print(f"{a:<24}{lab:<10}{len(g):>7}{mv:>18.3f}"
              f"{np.mean([rec(r) for r in g]):>10.3f}")

# ---- M3: the S8.4 question, matched on CYCLES --------------------------
print("\n" + "-"*78)
print("M3  STEP 4 (Bella S8.4)  AT MATCHED CYCLES, does the role-free arm")
print("    still recover less?  This is the test F16 got wrong by matching")
print("    on evaluator calls instead.")
print("-"*78)
for a in ACTORS:
    out = []
    for k in range(2, 7):
        cv = {}
        for arm in ("A","B"):
            g = [rec(r) for r in rows if actor(r)==a and r["arm"]==arm
                 and fp_wrong(r) and cycles(r)==k]
            if len(g) >= 15: cv[arm] = (np.mean(g), len(g))
        if len(cv) == 2: out.append((k, cv))
    if out:
        print(f"\n  {a}")
        print(f"    {'cycles':<9}{'Arm A':<22}{'Arm B':<22}{'delta':>8}")
        for k, cv in out:
            (ma,na),(mb,nb) = cv["A"], cv["B"]
            print(f"    {k:<9}{ma:.3f} (n={na}){'':<{max(1,10-len(str(na)))}}"
                  f"{mb:.3f} (n={nb}){'':<{max(1,10-len(str(nb)))}}{mb-ma:>+8.3f}")

# ---- M4: and at matched cycles, does the answer still freeze? ----------
print("\n" + "-"*78)
print("M4  AT MATCHED CYCLES, is the answer frozen?")
print("    If yes, the deficit is revision, not opportunity.")
print("-"*78)
for a in ACTORS:
    out = []
    for k in range(2, 7):
        cv = {}
        for arm in ("A","B"):
            g = [r for r in rows if actor(r)==a and r["arm"]==arm
                 and fp_wrong(r) and cycles(r)==k]
            if len(g) >= 15:
                cv[arm] = (np.mean([len(set(ansseq(r))) <= 1 for r in g]), len(g))
        if len(cv) == 2: out.append((k, cv))
    if out:
        print(f"\n  {a}   P(never changes its answer)")
        print(f"    {'cycles':<9}{'Arm A':<22}{'Arm B':<22}")
        for k, cv in out:
            (ma,na),(mb,nb) = cv["A"], cv["B"]
            print(f"    {k:<9}{ma:.3f} (n={na}){'':<{max(1,10-len(str(na)))}}"
                  f"{mb:.3f} (n={nb})")

# ---- M5: headline contrast, fully matched ------------------------------
print("\n" + "-"*78)
print("M5  HEADLINE CONTRAST at the FULL 6-cycle spend (identical budget,")
print("    identical realized spend, first-pass wrong under both)")
print("-"*78)
print(f"{'actor':<24}{'arm':<5}{'n':>6}{'P(frozen)':>12}{'   95% CI':<18}"
      f"{'recovery':>10}")
for a in ACTORS:
    for arm in ("A","B","C"):
        g = [r for r in rows if actor(r)==a and r["arm"]==arm
             and fp_wrong(r) and cycles(r) >= 6]
        if len(g) < 15: continue
        fr = [len(set(ansseq(r))) <= 1 for r in g]
        lo, hi = boot(fr)
        print(f"{a:<24}{arm:<5}{len(g):>6}{np.mean(fr):>12.3f}"
              f"   [{lo:.3f},{hi:.3f}]{np.mean([rec(r) for r in g]):>10.3f}")
print("\n" + "="*78)
