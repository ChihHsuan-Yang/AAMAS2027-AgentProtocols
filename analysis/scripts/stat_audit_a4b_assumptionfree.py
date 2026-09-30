"""ATTACK 4b: the ASSUMPTION-FREE version of the Arm C survivorship bound.

Key structural fact from 4.1: among ungraded rows that DID reach at least one
evaluator call, 100% have fp=0. None have fp=1. So those rows are not an
imputation problem at all -- their first-pass verdict is RECORDED. They are
first-pass-wrong trajectories that then failed to produce a gradeable final
answer. Under PREREG scoring they score 0. They belong in the recovery
denominator by the paper's own definition, and they were dropped.

That is a DEFINITIONAL INCONSISTENCY, not a modelling assumption:
  recovery = P(final correct | first evaluator verdict incorrect)
  these rows HAVE a first evaluator verdict, and it is incorrect,
  and their final is scored 0 under PREREG.
"""
import pandas as pd, numpy as np
from math import comb
D = pd.read_csv("/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols/analysis/audit/traj.csv")
S = pd.read_csv("/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols/analysis/audit/struct.csv")
ACT = ["gemma-4-31B-it","gpt-oss-120b","Llama-3.3-70B-Instruct"]

print("=== is fp=1 & ungraded structurally impossible? ===")
x = S[(S.graded==0)&(S.n_eval>0)]
print(f"  ungraded rows with >=1 eval: {len(x)}; of these fp==1: {(x.fp==1).sum()}; fp==0: {(x.fp==0).sum()}")
y = S[(S.graded==1)]
print(f"  graded rows: {len(y)}; those whose FIRST eval passed: {(y.fp==1).sum()}")
print("  => a passing first verdict terminates the loop and is always graded;")
print("     so ungraded-with-an-eval is a pure first-pass-WRONG subpopulation.")

print("\n=== 4b.1 ASSUMPTION-FREE recovery recomputation (PREREG scoring, all arms) ===")
print("  denominator = every graded-or-not trajectory whose FIRST evaluator")
print("  verdict exists and is incorrect. numerator = fin_prereg.")
print(f"{'actor':<24}{'arm':<4}{'rec_published':>14}{'n_pub':>7}{'rec_prereg':>12}{'n_prereg':>10}{'delta':>9}")
REC = {}
for a in ACT:
    for arm in ("A","B","C","Cp"):
        sub = S[(S.actor==a)&(S.arm==arm)]
        if not len(sub): continue
        pub = sub[(sub.graded==1)&(sub.fp==0)]
        allfpw = sub[(sub.n_eval>0)&(sub.fp==0)]
        rp = pub.fin.mean(); ra = allfpw.fin.mean()
        REC[(a,arm)] = (ra, len(allfpw))
        print(f"{a:<24}{arm:<4}{rp:>14.3f}{len(pub):>7}{ra:>12.3f}{len(allfpw):>10}{ra-rp:>+9.3f}")

print("\n=== 4b.2 does A6's ordering survive? 'Arm C highest of any arm' ===")
for a in ACT:
    vals = {arm: REC[(a,arm)][0] for arm in ("A","B","C") if (a,arm) in REC}
    best = max(vals, key=vals.get)
    print(f"  {a:<24}" + "  ".join(f"{k}={v:.3f}" for k,v in vals.items())
          + f"   highest={best}" + ("" if best=="C" else "  *** NOT C ***"))

print("\n=== 4b.3 PAIRED A-vs-C McNemar, assumption-free denominator ===")
print("  pairs = problems first-pass-wrong under BOTH arms, using the RECORDED")
print("  first verdict (graded or not). Ungraded rows score 0 per PREREG.")
for a in ACT:
    A = S[(S.actor==a)&(S.arm=="A")].drop_duplicates("problem_uid").set_index("problem_uid")
    C = S[(S.actor==a)&(S.arm=="C")].drop_duplicates("problem_uid").set_index("problem_uid")
    for label, useall in (("published (graded only)", False), ("assumption-free", True)):
        if useall:
            Af = set(A[(A.n_eval>0)&(A.fp==0)].index); Cf = set(C[(C.n_eval>0)&(C.fp==0)].index)
        else:
            Af = set(A[(A.graded==1)&(A.fp==0)].index); Cf = set(C[(C.graded==1)&(C.fp==0)].index)
        both = sorted(Af & Cf)
        b = sum(1 for p in both if A.fin[p]==1 and C.fin[p]==0)
        c = sum(1 for p in both if A.fin[p]==0 and C.fin[p]==1)
        m = b+c
        pv = min(1.0, 2*sum(comb(m,i) for i in range(min(b,c)+1))/2**m) if m else 1.0
        rA = sum(1 for p in both if A.fin[p]==1)/max(len(both),1)
        rC = sum(1 for p in both if C.fin[p]==1)/max(len(both),1)
        star = "" if pv>=0.05 else "  SIG"
        print(f"  {a:<24}{label:<26} n={len(both):<5} Aonly={b:<3} Conly={c:<3}"
              f" recA={rA:.3f} recC={rC:.3f} p={pv:.2e}{star}")

print("\n=== 4b.4 A6's stated paired p-values were 'p <= 1.6e-3'. Under 4b.3: ===")
print("  see above. Also check the 46/107/51 NEVER-SUBMITTED rows separately:")
for a in ACT:
    for arm in ("A","B","C"):
        sub = S[(S.actor==a)&(S.arm==arm)]
        ns = sub[(sub.n_eval==0)]
        if len(ns): print(f"  {a:<24}{arm:<3} never-submitted n={len(ns):<4}"
                          f" (first-pass status UNOBSERVABLE; excluded from 4b entirely)")
