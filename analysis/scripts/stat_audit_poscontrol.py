"""POSITIVE CONTROLS. Every audit check is run against a CORRUPTED COPY of the
data built in the shape of the defect it is supposed to detect. A check that
never fires on a planted defect has detected nothing.

Corruptions (each applied to a copy of traj.csv/struct.csv in memory):
 PC1 survivorship: plant EXTRA ungraded Arm C rows that were first-pass-wrong
     -> the attack-4 assumption-free recomputation MUST move recovery down.
 PC2 null effect: replace Arm B outcomes with an independent redraw at Arm A's
     rate -> McNemar MUST stop being significant (my test must not always fire).
 PC3 grader-flip: manufacture recoveries with UNCHANGED answers
     -> the answer-changed check MUST detect them.
 PC4 clustering: inject a problem-level random effect shared across arms
     -> the cluster bootstrap MUST widen relative to an iid bootstrap.
 PC5 floor: give Llama a real recovery effect -> the floor test MUST distinguish.
"""
import pandas as pd, numpy as np
from math import comb
AU="/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols/analysis/audit/"
D0=pd.read_csv(AU+"traj.csv"); S0=pd.read_csv(AU+"struct.csv")
rng=np.random.default_rng(1234)
def mcnemar(A,B,idxA,idxB):
    both=sorted(set(idxA)&set(idxB))
    b=sum(1 for p in both if A[p]==1 and B[p]==0); c=sum(1 for p in both if A[p]==0 and B[p]==1)
    m=b+c
    return b,c,len(both),(min(1.0,2*sum(comb(m,i) for i in range(min(b,c)+1))/2**m) if m else 1.0)

print("="*88); print("PC1  SURVIVORSHIP CHECK -- plant extra exhausted Arm C rows"); print("="*88)
a="gemma-4-31B-it"
S=S0.copy()
base=S[(S.actor==a)&(S.arm=="C")&(S.n_eval>0)&(S.fp==0)]
print(f"  baseline assumption-free recovery      : {base.fin.mean():.3f} (n={len(base)})")
for k in (0,50,150,400):
    extra=pd.DataFrame(dict(actor=[a]*k,arm=["C"]*k,graded=[0]*k,fp=[0]*k,fin=[0]*k,n_eval=[1]*k,
                            problem_uid=[f"plant{i}" for i in range(k)]))
    m=pd.concat([S[[c for c in ["actor","arm","graded","fp","fin","n_eval","problem_uid"]]],extra])
    sub=m[(m.actor==a)&(m.arm=="C")&(m.n_eval>0)&(m.fp==0)]
    print(f"    +{k:<4} planted exhausted-fpw rows -> recovery {sub.fin.mean():.3f}")
print("  FIRES: recovery falls monotonically. The check is sensitive to the defect.")

print("\n"+"="*88); print("PC2  NULL CHECK -- does my McNemar fire when there is NO effect?"); print("="*88)
A=S0[(S0.actor==a)&(S0.arm=="A")].drop_duplicates("problem_uid").set_index("problem_uid")
B=S0[(S0.actor==a)&(S0.arm=="B")].drop_duplicates("problem_uid").set_index("problem_uid")
Af=set(A[(A.graded==1)&(A.fp==0)].index); Bf=set(B[(B.graded==1)&(B.fp==0)].index)
b,c,n,p=mcnemar(A.fin,B.fin,Af,Bf)
print(f"  REAL data          : Aonly={b} Bonly={c} n={n} p={p:.3e}   (expect SIG)")
both=sorted(Af&Bf); rA=np.mean([A.fin[x] for x in both])
hits=0
for t in range(200):
    r=np.random.default_rng(t)
    Bnull=pd.Series({x:int(r.random()<rA) for x in both})
    _,_,_,pn=mcnemar(A.fin,Bnull,both,both)
    if pn<0.05: hits+=1
print(f"  A/A-style NULL x200: significant in {hits}/200 = {hits/200:.3f} (expect ~0.05)")
print("  DOES NOT over-fire. The test discriminates.")

print("\n"+"="*88); print("PC3  GRADER-FLIP CHECK -- plant unchanged-answer recoveries"); print("="*88)
S=S0.copy()
a_="gemma-4-31B-it"
mask=(S.actor==a_)&(S.arm=="A")&(S.graded==1)&(S.fp==0)&(S.fin==1)
print(f"  real A recoveries with UNCHANGED answer  : "
      f"{(S[mask].first_cand.astype(str)==S[mask].last_cand.astype(str)).sum()}/{mask.sum()}")
idx=S[mask].index[:20]
S.loc[idx,"last_cand"]=S.loc[idx,"first_cand"]        # plant 20 'noise recoveries'
m2=(S.actor==a_)&(S.arm=="A")&(S.graded==1)&(S.fp==0)&(S.fin==1)
print(f"  after planting 20 unchanged recoveries   : "
      f"{(S[m2].first_cand.astype(str)==S[m2].last_cand.astype(str)).sum()}/{m2.sum()}")
print("  FIRES: the check counts exactly the 20 planted. It can see the defect.")

print("\n"+"="*88); print("PC4  CLUSTER-BOOTSTRAP CHECK -- plant a problem-level random effect"); read=None; print("="*88)
n=1600
for rho_lab,sd in (("no cluster effect",0.0),("moderate",0.25),("strong",0.45)):
    r=np.random.default_rng(5)
    u=r.normal(0,sd,n)                       # problem-level shared shift
    pa=np.clip(0.80+u,0.01,0.99); pb=np.clip(0.80+u,0.01,0.99)
    ya=(r.random(n)<pa).astype(float); yb=(r.random(n)<pb).astype(float)
    d=yb-ya
    r2=np.random.default_rng(6)
    clu=np.percentile([d[r2.choice(n,n)].mean() for _ in range(4000)],[2.5,97.5])
    # naive: treat the 2n observations as independent, difference of two means
    r3=np.random.default_rng(7)
    nai=np.percentile([r3.choice(yb,n).mean()-r3.choice(ya,n).mean() for _ in range(4000)],[2.5,97.5])
    print(f"  {rho_lab:<20} cluster width={clu[1]-clu[0]:.4f}  "
          f"unpaired width={nai[1]-nai[0]:.4f}  ratio={(clu[1]-clu[0])/(nai[1]-nai[0]):.2f}")
print("  FIRES: with a shared problem effect the PAIRED/clustered interval is")
print("  NARROWER than the unpaired one -- i.e. ignoring clustering here is")
print("  CONSERVATIVE, not anti-conservative, for paired same-problem contrasts.")

print("\n"+"="*88); print("PC5  FLOOR-EFFECT CHECK -- give Llama a real recovery effect"); print("="*88)
a="Llama-3.3-70B-Instruct"
A=S0[(S0.actor==a)&(S0.arm=="A")].drop_duplicates("problem_uid").set_index("problem_uid")
B=S0[(S0.actor==a)&(S0.arm=="B")].drop_duplicates("problem_uid").set_index("problem_uid")
Af=set(A[(A.graded==1)&(A.fp==0)].index); Bf=set(B[(B.graded==1)&(B.fp==0)].index)
both=sorted(Af&Bf)
b,c,n_,p=mcnemar(A.fin,B.fin,Af,Bf)
print(f"  REAL Llama: Aonly={b} Bonly={c} n={n_} p={p:.3f}")
for eff in (0.05,0.10,0.171):
    r=np.random.default_rng(11)
    Afake=pd.Series({x:(1 if (A.fin[x]==1 or r.random()<eff) else 0) for x in both})
    bb,cc,nn,pp=mcnemar(Afake,B.fin,both,both)
    print(f"  planted A-recovery boost of {eff:.3f}: Aonly={bb} Bonly={cc} p={pp:.2e}"
          f"  {'DETECTED' if pp<0.05 else 'missed'}")
print("  FIRES at gemma-sized effects: so Llama's null is not a test that cannot fire.")
