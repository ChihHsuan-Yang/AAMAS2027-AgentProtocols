"""ATTACK 2: bootstrap clustering unit.

FINAL_TABLES bootstraps the PAIRED DIFFERENCE vector within one (actor, contrast).
Each element is one problem. Question: is that the right unit, given each problem
appears in 3 arms x 3 actors?

Key distinction:
 - For a SINGLE paired contrast, resampling the difference vector by problem
   ALREADY clusters by problem: both arms of a problem move together.
 - The clustering is NOT right for (i) contrasts that resample two arms
   INDEPENDENTLY (T3 recovery, T14 DiD use RNG.choice on each arm separately),
   and (ii) any statement combining actors.
Recompute with a proper problem-level cluster bootstrap.
"""
import pandas as pd, numpy as np
AU="/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols/analysis/audit/"
D=pd.read_csv(AU+"traj.csv")
ACT=["gemma-4-31B-it","gpt-oss-120b","Llama-3.3-70B-Instruct"]
RNG=np.random.default_rng(20261008)
NB=20000

def wide(a, scorer="fin_prereg"):
    s=D[D.actor==a].drop_duplicates(["problem_uid","arm"])
    return s.pivot(index="problem_uid",columns="arm",values=scorer)

print("="*92)
print("2.1  PAIRED ACCURACY CONTRASTS: published (paired-vector) vs cluster bootstrap")
print("="*92)
print("  These should agree EXACTLY in structure -- resampling a paired difference")
print("  vector IS a problem-level cluster bootstrap for a single actor+contrast.")
print(f"{'actor':<24}{'contrast':<6}{'est':>9}{'published-style CI':>26}{'cluster CI':>26}{'same?':>7}")
for a in ACT:
    W=wide(a)
    for x,y in (("A","B"),("A","C")):
        sub=W[[x,y]].dropna()
        d=(sub[y]-sub[x]).values.astype(float)
        r1=np.random.default_rng(20261008)
        b1=np.percentile([r1.choice(d,len(d)).mean() for _ in range(NB)],[2.5,97.5])
        # explicit cluster bootstrap: resample problem IDs, carry both arms
        idx=np.arange(len(sub)); r2=np.random.default_rng(99)
        b2=np.percentile([d[r2.choice(idx,len(idx))].mean() for _ in range(NB)],[2.5,97.5])
        same = (abs(b1[0]-b2[0])<0.003 and abs(b1[1]-b2[1])<0.003)
        print(f"{a:<24}{y+'-'+x:<6}{d.mean():>+9.4f}  [{b1[0]:+.4f},{b1[1]:+.4f}]      "
              f"[{b2[0]:+.4f},{b2[1]:+.4f}]{str(same):>9}")

print("\n"+"="*92)
print("2.2  THE REAL PROBLEM: T3's RECOVERY CI resamples the two arms INDEPENDENTLY")
print("="*92)
print("  FINAL_TABLES T3:  RNG.choice(rB,len(rB)).mean() - RNG.choice(rA,len(rA)).mean()")
print("  rA and rB are DIFFERENT problem sets (A's fpw vs B's fpw), overlapping on")
print("  the paired stratum. Independent resampling ignores that overlap -> the CI")
print("  is WRONG in width. Direction of the error depends on the correlation.")
print(f"{'actor':<24}{'d_rec':>9}{'published (independent)':>26}{'cluster-by-problem':>24}{'width ratio':>13}")
for a in ACT:
    Ag=D[(D.actor==a)&(D.arm=="A")&(D.graded==1)]
    Bg=D[(D.actor==a)&(D.arm=="B")&(D.graded==1)]
    rA=Ag[Ag.fp==0].set_index("problem_uid").fin_prereg
    rB=Bg[Bg.fp==0].set_index("problem_uid").fin_prereg
    d=rB.mean()-rA.mean()
    r1=np.random.default_rng(20261008)
    bs=[r1.choice(rA.values,len(rA)).mean() for _ in range(4000)]
    bsB=[r1.choice(rB.values,len(rB)).mean() for _ in range(4000)]
    lo1,hi1=np.percentile(np.array(bsB)-np.array(bs),[2.5,97.5])
    # cluster: resample the UNION of problems; within a draw take whichever arms
    # that problem contributes to. This preserves the A/B overlap correlation.
    uni=np.array(sorted(set(rA.index)|set(rB.index)))
    inA=np.isin(uni,rA.index); inB=np.isin(uni,rB.index)
    vA=np.array([rA.get(p,np.nan) for p in uni],float)
    vB=np.array([rB.get(p,np.nan) for p in uni],float)
    r2=np.random.default_rng(99); out=[]
    for _ in range(4000):
        k=r2.choice(len(uni),len(uni))
        a_=vA[k][inA[k]]; b_=vB[k][inB[k]]
        if len(a_)<5 or len(b_)<5: continue
        out.append(b_.mean()-a_.mean())
    lo2,hi2=np.percentile(out,[2.5,97.5])
    print(f"{a:<24}{d:>+9.4f}  [{lo1:+.4f},{hi1:+.4f}]      [{lo2:+.4f},{hi2:+.4f}]"
          f"{(hi2-lo2)/(hi1-lo1):>13.2f}")

print("\n"+"="*92)
print("2.3  T14 (P4, the PREREGISTERED PRIMARY) resamples two ACTORS independently")
print("="*92)
print("  ca_vec(actor_i) and ca_vec(actor_j) are over the SAME problems (Llama 400,")
print("  others 1600). Independent resampling breaks the pairing ACROSS actors.")
print("  A DiD across actors on shared problems is itself paired and should be")
print("  clustered on problem.")
def cavec(a):
    W=wide(a)[["A","C"]].dropna()
    return (W["C"]-W["A"])
print(f"{'pair':<52}{'DiD':>9}{'published (indep)':>22}{'clustered':>22}{'changes?':>10}")
for i in range(3):
    for j in range(i+1,3):
        u,v=cavec(ACT[i]),cavec(ACT[j])
        dd=v.mean()-u.mean()
        r1=np.random.default_rng(20261008)
        b=[r1.choice(v.values,len(v)).mean()-r1.choice(u.values,len(u)).mean() for _ in range(4000)]
        lo1,hi1=np.percentile(b,[2.5,97.5])
        cm=sorted(set(u.index)&set(v.index))
        du=u[cm].values.astype(float); dv=v[cm].values.astype(float)
        diff=dv-du
        r2=np.random.default_rng(99)
        b2=[diff[r2.choice(len(diff),len(diff))].mean() for _ in range(4000)]
        lo2,hi2=np.percentile(b2,[2.5,97.5])
        s1 = not (lo1<0<hi1); s2 = not (lo2<0<hi2)
        ch = "*** YES ***" if s1!=s2 else "no"
        print(f"{ACT[j]+' - '+ACT[i]:<52}{diff.mean():>+9.4f}  [{lo1:+.4f},{hi1:+.4f}]  "
              f"[{lo2:+.4f},{hi2:+.4f}]{ch:>12}  (n_shared={len(cm)})")
