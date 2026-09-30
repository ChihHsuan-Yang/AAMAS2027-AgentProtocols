"""ATTACK 4: Arm C attrition / survivorship in the RECOVERY denominator.

Claim A6 says Arm C recovery 0.412/0.461/0.150 is "highest of any arm, above
Arm A in all three actors". That is computed on GRADED trajectories only.
Arm C drops 8.0/9.9/17.0% to regeneration_exhausted. Bound the bias.
"""
import pandas as pd, numpy as np
from math import comb
D = pd.read_csv("/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols/analysis/audit/traj.csv")
S = pd.read_csv("/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols/analysis/audit/struct.csv")
ACT = ["gemma-4-31B-it","gpt-oss-120b","Llama-3.3-70B-Instruct"]

print("=== 4.1 WHAT IS IN THE UNGRADED SET? ===")
print(f"{'actor':<24}{'arm':<4}{'ungraded':>9}{'has>=1 eval':>12}{'fp=0 of those':>15}{'fp=1':>6}{'0 eval':>8}")
for a in ACT:
    for arm in ("A","B","C","Cp"):
        s = S[(S.actor==a)&(S.arm==arm)&(S.graded==0)]
        if not len(s): continue
        he = s[s.n_eval>0]
        fp0 = (he.fp==0).sum(); fp1 = (he.fp==1).sum()
        print(f"{a:<24}{arm:<4}{len(s):>9}{len(he):>12}{fp0:>15}{fp1:>6}{(s.n_eval==0).sum():>8}")

print("\n=== 4.2 WORST-CASE BOUND on Arm C recovery (marginal) ===")
print("  worst case: every ungraded Arm C trajectory was first-pass-wrong and scores 0")
print("  (PREREG scoring already scores them 0; this puts them in the DENOMINATOR too)")
print(f"{'actor':<24}{'recC_as-is':>12}{'nfpw':>6}{'nrec':>6}{'ungr':>6}"
      f"{'recC_worst':>12}{'recA':>8}{'verdict':>28}")
for a in ACT:
    C = D[(D.actor==a)&(D.arm=="C")]
    g = C[C.graded==1]; fpw = g[g.fp==0]
    nrec = int(fpw.fin_prereg.sum()); n = len(fpw)
    ung = int((C.graded==0).sum())
    A = D[(D.actor==a)&(D.arm=="A")]; Ag = A[A.graded==1]; Afpw = Ag[Ag.fp==0]
    recA = Afpw.fin_prereg.mean()
    worst = nrec/(n+ung)
    v = "STILL above A" if worst > recA else "*** FLIPS: below Arm A ***"
    print(f"{a:<24}{nrec/n:>12.3f}{n:>6}{nrec:>6}{ung:>6}{worst:>12.3f}{recA:>8.3f}{v:>28}")

print("\n=== 4.3 PLAUSIBLE-CASE BOUND ===")
print("  ungraded trajectories imputed as first-pass-wrong at the rate OBSERVED")
print("  among graded Arm C rows, and recovering at Arm A's rate (a generous")
print("  'they are ordinary trajectories' assumption), then at 0 (pessimistic).")
for a in ACT:
    C = D[(D.actor==a)&(D.arm=="C")]
    g = C[C.graded==1]; fpw = g[g.fp==0]
    nrec = int(fpw.fin_prereg.sum()); n = len(fpw)
    ung = int((C.graded==0).sum())
    fpw_rate = len(fpw)/len(g)
    A = D[(D.actor==a)&(D.arm=="A")]; Ag=A[A.graded==1]; recA=Ag[Ag.fp==0].fin_prereg.mean()
    add_n = ung*fpw_rate
    print(f"  {a:<24} fpw_rate={fpw_rate:.3f} added_fpw={add_n:.0f}"
          f"  rec@0={nrec/(n+add_n):.3f}  rec@recA={(nrec+add_n*recA)/(n+add_n):.3f}"
          f"  (recA={recA:.3f})")

print("\n=== 4.4 PAIRED A-vs-C McNemar UNDER WORST CASE ===")
print("  Prereg-consistent: include ungraded C rows in the paired fpw stratum,")
print("  scored 0, whenever the A-side of that problem was first-pass-wrong.")
for a in ACT:
    A = D[(D.actor==a)&(D.arm=="A")].set_index("problem_uid")
    C = D[(D.actor==a)&(D.arm=="C")].set_index("problem_uid")
    Ag = A[A.graded==1]; Afpw = set(Ag[Ag.fp==0].index)
    Cg = C[C.graded==1]; Cfpw = set(Cg[Cg.fp==0].index)
    Cung = set(C[C.graded==0].index)
    for label, cset in (("as-published (graded C only)", Cfpw),
                        ("worst-case (+ungraded C as fpw, score 0)", Cfpw | Cung)):
        both = sorted(Afpw & cset)
        b = sum(1 for p in both if A.fin_prereg[p]==1 and C.fin_prereg[p]==0)   # A only
        c = sum(1 for p in both if A.fin_prereg[p]==0 and C.fin_prereg[p]==1)   # C only
        m=b+c
        pv = min(1.0, 2*sum(comb(m,i) for i in range(min(b,c)+1))/2**m) if m else 1.0
        rA = sum(1 for p in both if A.fin_prereg[p]==1)/len(both)
        rC = sum(1 for p in both if C.fin_prereg[p]==1)/len(both)
        print(f"  {a:<24}{label:<42} n={len(both):<5} Aonly={b:<4} Conly={c:<4}"
              f" recA={rA:.3f} recC={rC:.3f} p={pv:.2e}")
