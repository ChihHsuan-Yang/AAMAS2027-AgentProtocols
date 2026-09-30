"""ATTACK 1: the recovery denominator. Can a selection story produce
gemma-4's 37 vs 3 (p=2e-08) with NO true recovery effect?

Structure of the attack:
 1.1 Is the MARGINAL recovery contrast identified? Exact arithmetic decomposition.
 1.2 Is the PAIRED set a valid principal stratum? What breaks it?
 1.3 Selection story S1: arm-independent repair probability -> symmetry theorem.
 1.4 Selection story S2: differential error DEPTH in the paired set.
 1.5 Selection story S3: recovery is a grader flip, not a repair (format/noise).
 1.6 Selection story S4: differential number of grader draws.
"""
import pandas as pd, numpy as np, json, glob, re, collections
from math import comb
AU="/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols/analysis/audit/"
D=pd.read_csv(AU+"traj.csv"); S=pd.read_csv(AU+"struct.csv")
ACT=["gemma-4-31B-it","gpt-oss-120b","Llama-3.3-70B-Instruct"]

print("="*90)
print("1.1  IS THE MARGINAL RECOVERY CONTRAST IDENTIFIED BY ARITHMETIC?")
print("="*90)
print("  final = fp + (1-fp)*recovery   exactly, when recovery is defined on the")
print("  graded first-pass-wrong set and ungraded score 0. So:")
print("     d_final = d_fp*(1-rec_A) + (1-fp_B)*d_rec")
print("  If d_fp == 0 the recovery contrast is a REPARAMETERISATION of the ITT,")
print("  which is NOT post-treatment conditioned. If d_fp != 0 it is not pinned.")
print(f"\n{'actor':<24}{'d_fp':>9}{'d_rec':>9}{'(1-fpB)*d_rec':>15}{'d_final(obs)':>14}{'resid':>9}{'verdict':>34}")
for a in ACT:
    A=D[(D.actor==a)&(D.arm=="A")]; B=D[(D.actor==a)&(D.arm=="B")]
    Ag=A[A.graded==1]; Bg=B[B.graded==1]
    fpA,fpB=Ag.fp.mean(),Bg.fp.mean()
    rA=Ag[Ag.fp==0].fin_prereg.mean(); rB=Bg[Bg.fp==0].fin_prereg.mean()
    dfin=B.fin_prereg.mean()-A.fin_prereg.mean()
    pred=(fpB-fpA)*(1-rA)+(1-fpB)*(rB-rA)
    v = "IDENTIFIED (=ITT reparam)" if abs(fpB-fpA)<0.002 else "NOT pinned by the ITT"
    print(f"{a:<24}{fpB-fpA:>+9.4f}{rB-rA:>+9.4f}{(1-fpB)*(rB-rA):>+15.4f}"
          f"{dfin:>+14.4f}{dfin-pred:>+9.4f}{v:>34}")

print("\n"+"="*90)
print("1.2  IS THE PAIRED SET A VALID PRINCIPAL STRATUM?")
print("="*90)
print("  Conditioning on {fp_A=0 AND fp_B=0} is a JOINT event on potential")
print("  outcomes under both arms -> a principal stratum (Frangakis&Rubin 2002).")
print("  Contrasts within a principal stratum ARE causally interpretable.")
print("  This holds ONLY if fp is deterministic given (problem, arm).")
print("  Check: is fp deterministic? Cp re-runs Arm C; determinism.json says")
print("  temp-0 decoding on this endpoint is NOT bitwise deterministic.")
det=json.load(open("/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols/experiments/infra/determinism.json"))
for d in det:
    print(f"    {d['model']:<24} reps={d['n_ok']} identical={d['identical']} distinct={d['distinct_hashes']}")
# empirical stochasticity of fp: C vs Cp are the same arm config on 400 problems
print("\n  EMPIRICAL fp stability, Arm C vs Arm Cp (same enforcement, differing only")
print("  in context control) -- an upper bound on pure re-run fp noise:")
for a in ("gemma-4-31B-it","gpt-oss-120b"):
    C=S[(S.actor==a)&(S.arm=="C")&(S.n_eval>0)].drop_duplicates("problem_uid").set_index("problem_uid")
    P=S[(S.actor==a)&(S.arm=="Cp")&(S.n_eval>0)].drop_duplicates("problem_uid").set_index("problem_uid")
    cm=sorted(set(C.index)&set(P.index))
    dis=sum(1 for p in cm if C.fp[p]!=P.fp[p])
    print(f"    {a:<24} n={len(cm)}  fp discordant={dis} ({dis/len(cm):.3f})")

print("\n"+"="*90)
print("1.3  SELECTION STORY S1 -- arm-independent repair probability")
print("="*90)
print("  Model: problem p has latent repair prob pi(p) NOT depending on arm.")
print("  Within the paired stratum both arms draw Bernoulli(pi(p)) independently.")
print("  Then E[Aonly] = E[Bonly] = sum pi(1-pi): the discordance is EXCHANGEABLE.")
print("  McNemar is exactly the test of that exchangeability. Simulate the")
print("  most favourable version of S1 (pi fitted to the OBSERVED pooled rate)")
print("  and ask how often it yields |Aonly-Bonly| >= 34.")
rng=np.random.default_rng(7)
a="gemma-4-31B-it"
A=S[(S.actor==a)&(S.arm=="A")].drop_duplicates("problem_uid").set_index("problem_uid")
B=S[(S.actor==a)&(S.arm=="B")].drop_duplicates("problem_uid").set_index("problem_uid")
Af=set(A[(A.graded==1)&(A.fp==0)].index); Bf=set(B[(B.graded==1)&(B.fp==0)].index)
both=sorted(Af&Bf); n=len(both)
nrecA=sum(1 for p in both if A.fin[p]==1); nrecB=sum(1 for p in both if B.fin[p]==1)
pooled=(nrecA+nrecB)/(2*n)
obs=abs(nrecA-nrecB)
print(f"  paired n={n}  recA={nrecA} recB={nrecB} pooled pi={pooled:.4f} observed |diff|={obs}")
# most favourable S1: maximal heterogeneity in pi (pi in {0,1} mixture) MINIMISES
# discordance; homogeneous pi MAXIMISES it. Use homogeneous = worst case for us.
hits=0; N=200000
for _ in range(N):
    x=rng.random(n)<pooled; y=rng.random(n)<pooled
    if abs(x.sum()-y.sum())>=obs: hits+=1
print(f"  S1 (homogeneous pi, the variance-MAXIMISING member of S1): "
      f"P(|diff|>={obs}) = {hits/N:.2e} over {N} sims")
print("  => S1 cannot produce the result. Any selection story must make repair")
print("     probability ARM-DEPENDENT, which is the effect itself.")
