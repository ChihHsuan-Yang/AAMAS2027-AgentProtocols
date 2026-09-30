"""Audit step 0: reproduce FINAL_TABLES headline numbers from my own extract.
If I cannot reproduce them, every later attack is suspect."""
import pandas as pd, numpy as np
from math import comb
D = pd.read_csv("/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols/analysis/audit/traj.csv")
ACT = ["gemma-4-31B-it","gpt-oss-120b","Llama-3.3-70B-Instruct"]
RNG = np.random.default_rng(20261008)

def boot(x,n=20000):
    x=np.asarray(x,float)
    if len(x)<5: return (np.nan,np.nan)
    return tuple(np.percentile([RNG.choice(x,len(x)).mean() for _ in range(n)],[2.5,97.5]))

print("=== T1 repro: firstpass / final / recovery ===")
for a in ACT:
    for arm in ("A","B","C","Cp"):
        s = D[(D.actor==a)&(D.arm==arm)]
        if not len(s): continue
        g = s[s.graded==1]
        fpw = g[g.fp==0]
        print(f"{a:<24}{arm:<4} n={len(s):<5} fp={g.fp.mean():.3f} fin={s.fin_prereg.mean():.3f} "
              f"rec={fpw.fin_prereg.mean():.3f} n_fpw={len(fpw)}")

print("\n=== T2 repro: paired contrasts PREREG ===")
for x,y in (("A","B"),("A","C")):
    for a in ACT:
        X = D[(D.actor==a)&(D.arm==x)].set_index("problem_uid").fin_prereg
        Y = D[(D.actor==a)&(D.arm==y)].set_index("problem_uid").fin_prereg
        cm = sorted(set(X.index)&set(Y.index))
        d = (Y[cm].values - X[cm].values).astype(float)
        lo,hi = boot(d)
        print(f"  {y}-{x} {a:<24}{d.mean():+.4f} [{lo:+.4f},{hi:+.4f}] n={len(cm)}")

print("\n=== T4 repro: paired recovery McNemar ===")
for a in ACT:
    for x,y in (("A","B"),("A","C")):
        P = D[(D.actor==a)&(D.arm==x)&(D.graded==1)].set_index("problem_uid")
        Q = D[(D.actor==a)&(D.arm==y)&(D.graded==1)].set_index("problem_uid")
        both = sorted(p for p in set(P.index)&set(Q.index) if P.fp[p]==0 and Q.fp[p]==0)
        if len(both)<20: continue
        b = sum(1 for p in both if P.fin_prereg[p]==1 and Q.fin_prereg[p]==0)
        c = sum(1 for p in both if P.fin_prereg[p]==0 and Q.fin_prereg[p]==1)
        m=b+c
        pv = min(1.0, 2*sum(comb(m,i) for i in range(min(b,c)+1))/2**m) if m else 1.0
        print(f"  {a:<24}{x}v{y} n={len(both):<5} {x}only={b:<4} {y}only={c:<4} p={pv:.2e}")

print("\n=== T7 repro: attrition ===")
for a in ACT:
    for arm in ("A","B","C","Cp"):
        s = D[(D.actor==a)&(D.arm==arm)]
        if not len(s): continue
        print(f"  {a:<24}{arm:<4} attrition={1-s.graded.mean():.3f} exhausted={s.exhausted.mean():.3f}")
