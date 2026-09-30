"""ATTACK 7 (power / MDE for each DiD) + ATTACK 8 (Llama floor effect).

7: Is P4's null informative or underpowered? Compute the minimum detectable
   effect (80% power, two-sided .05) for each of the three DiDs, by simulation
   using the OBSERVED paired C-A difference vectors (so the variance is real).
8: 'Floor effect' vs 'genuine absence'. A floor effect asserts the RECOVERY
   CHANNEL DOES NOT EXIST for Llama, not merely that the arms tie. Test the
   discriminating prediction: if it is a floor, Llama should not recover under
   ANY manipulation. Arm C is exactly that test.
"""
import pandas as pd, numpy as np
from math import comb
AU="/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols/analysis/audit/"
D=pd.read_csv(AU+"traj.csv"); S=pd.read_csv(AU+"struct.csv")
ACT=["gemma-4-31B-it","gpt-oss-120b","Llama-3.3-70B-Instruct"]

def wide(a):
    s=D[D.actor==a].drop_duplicates(["problem_uid","arm"])
    return s.pivot(index="problem_uid",columns="arm",values="fin_prereg")

print("="*92); print("7.1  MDE FOR EACH P4 DiD  (80% power, two-sided .05, 2000 sims)"); print("="*92)
print("  Method: take the observed paired C-A difference vectors for the two")
print("  actors on shared problems; the DiD vector is their difference. Add a")
print("  constant shift tau and ask what tau is detected 80% of the time by the")
print("  same bootstrap CI rule the paper uses.")
print(f"\n{'pair':<48}{'n':>6}{'sd(DiD)':>9}{'observed':>10}{'MDE@80%':>10}{'verdict':>34}")
res={}
for i in range(3):
    for j in range(i+1,3):
        Wi=wide(ACT[i])[["A","C"]].dropna(); Wj=wide(ACT[j])[["A","C"]].dropna()
        cm=sorted(set(Wi.index)&set(Wj.index))
        d=((Wj["C"]-Wj["A"])[cm]-(Wi["C"]-Wi["A"])[cm]).values.astype(float)
        n=len(d); sd=d.std(ddof=1); obs=d.mean()
        # analytic MDE then verify by sim
        mde=(1.959964+0.8416212)*sd/np.sqrt(n)
        r=np.random.default_rng(42); hit=0; N=2000
        for _ in range(N):
            samp=r.choice(d-obs,n)+mde
            se=samp.std(ddof=1)/np.sqrt(n)
            if abs(samp.mean())-1.959964*se>0: hit+=1
        lab=f"{ACT[j][:14]} - {ACT[i][:14]}"
        res[lab]=(n,sd,obs,mde)
        v=("informative: MDE < half the observed main effect"
           if mde<0.017 else "UNDERPOWERED for effects this size")
        print(f"{lab:<48}{n:>6}{sd:>9.3f}{obs:>+10.4f}{mde:>10.4f}{v:>34}  (sim power {hit/N:.2f})")

print("\n  Reference scale: the LARGEST per-actor C-A main effect is |-0.0225|.")
print("  A true interaction can be no larger than the spread of the main effects,")
print("  which is +0.0175 to +0.0400 across pairs. Compare to the MDEs above.")
for lab,(n,sd,obs,mde) in res.items():
    print(f"    {lab:<40} MDE={mde:.4f}  vs largest plausible interaction ~0.040"
          f"  -> {'CAN detect' if mde<0.040 else 'CANNOT detect'}")

print("\n"+"="*92); print("7.2  WHAT WOULD P4 HAVE NEEDED?"); print("="*92)
for lab,(n,sd,obs,mde) in res.items():
    for target in (0.02,0.03):
        nn=((1.959964+0.8416212)*sd/target)**2
        print(f"  {lab:<40} to detect {target:.02f} at 80% needs n={nn:,.0f} paired problems"
              f" (have {n})")

print("\n"+"="*92); print("8.1  IS LLAMA'S 'FLOOR EFFECT' FAIR OR CONVENIENT?"); print("="*92)
print("  A FLOOR claim asserts: the recovery channel does not exist for this")
print("  actor, so no manipulation can move it. A GENUINE ABSENCE claim asserts:")
print("  the channel exists but roles do not affect it. These make OPPOSITE")
print("  predictions about Arm C. Arm C is an out-of-sample test of the excuse.")
a="Llama-3.3-70B-Instruct"
for arm in ("A","B","C"):
    g=S[(S.actor==a)&(S.arm==arm)&(S.graded==1)&(S.fp==0)]
    print(f"    Arm {arm}: recovery {g.fin.mean():.3f} (n={len(g)})")
A=S[(S.actor==a)&(S.arm=="A")].drop_duplicates("problem_uid").set_index("problem_uid")
C=S[(S.actor==a)&(S.arm=="C")].drop_duplicates("problem_uid").set_index("problem_uid")
Af=set(A[(A.graded==1)&(A.fp==0)].index); Cf=set(C[(C.graded==1)&(C.fp==0)].index)
both=sorted(Af&Cf)
b=sum(1 for p in both if A.fin[p]==1 and C.fin[p]==0); c=sum(1 for p in both if A.fin[p]==0 and C.fin[p]==1)
m=b+c; pv=min(1.0,2*sum(comb(m,i) for i in range(min(b,c)+1))/2**m)
print(f"  Llama A-vs-C paired: Aonly={b} Conly={c} n={len(both)} p={pv:.2e}")
print("  => Llama's recovery channel DOES exist and IS movable (0.015 -> 0.150).")
print("     So 'too weak a solver for the recovery channel to exist at all'")
print("     (results.tex) is FALSIFIED BY THE PAPER'S OWN ARM C.")

print("\n"+"="*92); print("8.2  POWER OF THE LLAMA A-vs-B TEST -- could it have seen the effect?"); print("="*92)
print("  From PC5: a planted gemma-sized A-recovery boost IS detected at Llama's n.")
print("  So the Llama A-vs-B null is NOT merely underpowered for a gemma-sized effect.")
print("  Minimum detectable A-only excess at Llama's discordance, 80% power:")
rng=np.random.default_rng(9)
base=np.mean([A.fin[p] for p in sorted(Af&set(S[(S.actor==a)&(S.arm=='B')].problem_uid))])
for eff in (0.02,0.03,0.04,0.05,0.07,0.10):
    hit=0; N=1000
    for t in range(N):
        r=np.random.default_rng(t)
        n=243
        ya=(r.random(n)<0.004+eff).astype(int); yb=(r.random(n)<0.016).astype(int)
        bb=int(((ya==1)&(yb==0)).sum()); cc=int(((ya==0)&(yb==1)).sum()); mm=bb+cc
        p=min(1.0,2*sum(comb(mm,i) for i in range(min(bb,cc)+1))/2**mm) if mm else 1.0
        if p<0.05: hit+=1
    print(f"    true A-recovery excess {eff:.02f}: power {hit/N:.2f}")
print("  => Llama A-vs-B has ~80% power at an excess of about 0.04-0.05;")
print("     the gemma effect is 0.171. The null IS informative against a")
print("     gemma-sized effect, and uninformative below ~0.04.")
