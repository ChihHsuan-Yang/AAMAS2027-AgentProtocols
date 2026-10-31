"""Analyze blinded adjudication: the full reporting contract from RUBRIC_v1.

Reports agreement, precision, recall, confusion matrix, per-actor AND per-arm
breakdowns, judge stability across reps, and disagreement inspection.
Never a single aggregate number alone.
"""
import json, os, collections
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
V = [json.loads(l) for l in open(HERE + "/VERDICTS.jsonl")]
KEY = {json.loads(l)["tid"]: json.loads(l) for l in open(HERE + "/KEY.jsonl")}

by = collections.defaultdict(list)
for v in V:
    if v.get("parsed"): by[v["tid"]].append(v["parsed"])

# ---- judge stability -------------------------------------------------------
print("="*74); print("JUDGE STABILITY across independent reps"); print("="*74)
for q in ["Q1","Q2","Q3","Q4","Q5"]:
    multi = {t: ps for t, ps in by.items() if len(ps) >= 2}
    if not multi: continue
    agree = sum(1 for t, ps in multi.items() if len({p[q] for p in ps}) == 1)
    print(f"  {q}: all-reps-agree {agree}/{len(multi)} = {agree/len(multi):.3f}")

# majority label per item
maj = {}
for t, ps in by.items():
    maj[t] = {q: collections.Counter(p[q] for p in ps).most_common(1)[0][0]
              for q in ["Q1","Q2","Q3","Q4","Q5"]}
print(f"\nitems with >=1 verdict: {len(maj)}")

# ---- the validation: flag vs Q5 -------------------------------------------
def block(label, sel):
    rows = [(t, KEY[t], maj[t]) for t in maj if t in KEY and sel(KEY[t])]
    if len(rows) < 4: return
    tp = sum(1 for _,k,m in rows if k["auto_collapse"] and m["Q5"]=="NO")
    fp = sum(1 for _,k,m in rows if k["auto_collapse"] and m["Q5"]=="YES")
    fn = sum(1 for _,k,m in rows if not k["auto_collapse"] and m["Q5"]=="NO")
    tn = sum(1 for _,k,m in rows if not k["auto_collapse"] and m["Q5"]=="YES")
    n = len(rows); acc = (tp+tn)/n
    prec = tp/(tp+fp) if tp+fp else float("nan")
    rec  = tp/(tp+fn) if tp+fn else float("nan")
    po = acc
    pe = (((tp+fp)/n)*((tp+fn)/n) + ((fn+tn)/n)*((fp+tn)/n))
    kap = (po-pe)/(1-pe) if pe < 1 else float("nan")
    print(f"\n  {label}  n={n}")
    print(f"    confusion TP={tp} FP={fp} FN={fn} TN={tn}")
    print(f"    agreement {acc:.3f}  precision {prec:.3f}  recall {rec:.3f}  kappa {kap:.3f}")
    print(f"    judged NO-division-of-labour: {(tp+fn)/n:.3f}")

print("\n" + "="*74)
print("AUTOMATED FLAG vs ADJUDICATED Q5 (division of labour)")
print("="*74)
block("POOLED (confounded by arm — see rubric)", lambda k: True)
print("\n-- per ARM --")
for arm in ["A","B","C","Cp"]:
    block(f"arm {arm}", lambda k, a=arm: k["arm"] == a)
print("\n-- per ACTOR --")
for act in sorted({k["actor"] for k in KEY.values()}):
    block(f"{act}", lambda k, a=act: k["actor"] == a)
print("\n-- per ACTOR x ARM (the honest cells) --")
for act in sorted({k["actor"] for k in KEY.values()}):
    for arm in ["A","B"]:
        block(f"{act} / {arm}", lambda k, a=act, r=arm: k["actor"]==a and k["arm"]==r)

# ---- Q-by-Q rates ----------------------------------------------------------
print("\n" + "="*74); print("RUBRIC ITEM RATES per actor x arm"); print("="*74)
g = collections.defaultdict(lambda: collections.Counter())
for t, m in maj.items():
    k = KEY.get(t)
    if not k: continue
    c = g[(k["actor"], k["arm"])]; c["n"] += 1
    for q in ["Q1","Q2","Q3","Q4","Q5"]:
        c[q] += (m[q] == "YES")
print(f"{'actor/arm':30s} {'n':>4s} {'Q1sem':>6s} {'Q2fun':>6s} {'Q3new':>6s} {'Q4inf':>6s} {'Q5div':>6s}")
for k in sorted(g):
    c = g[k]; n = c["n"]
    print(f"  {k[0]+'/'+k[1]:28s} {n:>4d} " +
          " ".join(f"{c[q]/n:>6.3f}" for q in ["Q1","Q2","Q3","Q4","Q5"]))

# ---- disagreements ---------------------------------------------------------
print("\n" + "="*74); print("DISAGREEMENT CASES (flag says collapse, judge says division exists)")
print("="*74)
shown = 0
for t, m in maj.items():
    k = KEY.get(t)
    if k and k["auto_collapse"] and m["Q5"] == "YES" and shown < 5:
        print(f"  {t} {k['actor']}/{k['arm']}: {by[t][0].get('reason','')[:110]}")
        shown += 1
if shown == 0: print("  none")
