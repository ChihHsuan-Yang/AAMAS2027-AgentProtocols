"""ATTACK 1b: the strongest selection story -- recovery is a GRADER FLIP,
not a repair.

S3: suppose no arm ever repairs anything. Arm A's 37 'recoveries' are the
grader re-grading an UNCHANGED answer differently (temp-0 nondeterminism,
T6 says 0.86% of graded strings get contradictory verdicts). If Arm A gets
more grader draws than Arm B, A accumulates more noise-recoveries.

Two decisive checks:
  (a) DIRECTION OF DRAWS. Who gets more grader draws among first-pass-wrong?
  (b) DID THE ANSWER CHANGE? A noise-recovery requires the SAME answer to be
      graded 0 then 1. A repair requires a DIFFERENT answer.
Also S4: a quantitative ceiling on how many recoveries noise can manufacture.
"""
import pandas as pd, numpy as np, json, glob, re, collections
from math import comb
AU="/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols/analysis/audit/"
S=pd.read_csv(AU+"struct.csv")
ACT=["gemma-4-31B-it","gpt-oss-120b","Llama-3.3-70B-Instruct"]

print("="*90); print("1b.(a) DIRECTION OF GRADER DRAWS among first-pass-wrong"); print("="*90)
print(f"{'actor':<24}{'arm':<4}{'n_fpw':>7}{'mean draws':>12}{'median':>8}{'total draws':>13}")
for a in ACT:
    for arm in ("A","B","C"):
        g=S[(S.actor==a)&(S.arm==arm)&(S.graded==1)&(S.fp==0)]
        if len(g)<20: continue
        print(f"{a:<24}{arm:<4}{len(g):>7}{g.n_eval.mean():>12.2f}{g.n_eval.median():>8.0f}{g.n_eval.sum():>13}")
print("  -> if Arm B gets MORE draws, the noise story predicts B recovers MORE.")
print("     The observed effect is B recovers LESS. The story has the WRONG SIGN.")

print("\n"+"="*90); print("1b.(b) DID THE ANSWER CHANGE? repair vs re-grade"); print("="*90)
print("  For each recovered first-pass-wrong trajectory, compare the FIRST graded")
print("  candidate with the LAST graded candidate (both normalised).")
print(f"{'actor':<24}{'arm':<4}{'n_recovered':>13}{'answer CHANGED':>16}{'answer SAME':>13}{'frac same':>11}")
for a in ACT:
    for arm in ("A","B","C"):
        g=S[(S.actor==a)&(S.arm==arm)&(S.graded==1)&(S.fp==0)&(S.fin==1)]
        if not len(g): continue
        same=(g.first_cand.astype(str)==g.last_cand.astype(str)).sum()
        print(f"{a:<24}{arm:<4}{len(g):>13}{len(g)-same:>16}{same:>13}{same/len(g):>11.3f}")

print("\n"+"="*90); print("1b.(c) THE 37 vs 3 DISCORDANT PAIRS, DISSECTED"); print("="*90)
a="gemma-4-31B-it"
A=S[(S.actor==a)&(S.arm=="A")].drop_duplicates("problem_uid").set_index("problem_uid")
B=S[(S.actor==a)&(S.arm=="B")].drop_duplicates("problem_uid").set_index("problem_uid")
Af=set(A[(A.graded==1)&(A.fp==0)].index); Bf=set(B[(B.graded==1)&(B.fp==0)].index)
both=sorted(Af&Bf)
Aonly=[p for p in both if A.fin[p]==1 and B.fin[p]==0]
Bonly=[p for p in both if A.fin[p]==0 and B.fin[p]==1]
for lab,ps,T in (("A-only (n=37)",Aonly,A),("B-only (n=3)",Bonly,B)):
    ch=sum(1 for p in ps if str(T.first_cand[p])!=str(T.last_cand[p]))
    dr=np.mean([T.n_eval[p] for p in ps])
    print(f"  {lab:<16} answer changed {ch}/{len(ps)}   mean grader draws {dr:.2f}")
print("  A noise-recovery REQUIRES answer-unchanged. Count of answer-unchanged")
print("  recoveries is the maximum the grader-flip story can explain.")

print("\n"+"="*90); print("1b.(d) QUANTITATIVE CEILING: how many recoveries CAN noise make?"); print("="*90)
print("  Noise-recovery requires: same answer graded 0 at draw 1 and 1 at draw k.")
print("  Per-call flip rate (T6 per-call in split group) = 0.0072; the")
print("  minority-verdict rate 0.0020 is the rate at which a DRAW dissents.")
for a in ACT:
    A_=S[(S.actor==a)&(S.arm=="A")&(S.graded==1)&(S.fp==0)]
    B_=S[(S.actor==a)&(S.arm=="B")&(S.graded==1)&(S.fp==0)]
    for lab,g in (("A",A_),("B",B_)):
        extra=(g.n_eval-1).clip(lower=0).sum()   # draws after the first
        for rate,rl in ((0.0072,"per-call .0072"),(0.0086,"group .0086")):
            exp=extra*rate
            obs=g.fin.sum()
            if lab=="A" and rl.startswith("per"):
                print(f"  {a:<24}{lab} extra_draws={extra:<6} exp_noise_rec@{rl}={exp:>6.1f}"
                      f"  observed_rec={obs:<5} noise_share={exp/max(obs,1):.1%}")
            elif rl.startswith("per"):
                print(f"  {a:<24}{lab} extra_draws={extra:<6} exp_noise_rec@{rl}={exp:>6.1f}"
                      f"  observed_rec={obs:<5} noise_share={exp/max(obs,1):.1%}")
