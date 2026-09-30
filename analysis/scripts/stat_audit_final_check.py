"""FINAL CONSOLIDATION: re-derive every number I will put in the audit,
in one place, so each is traceable."""
import pandas as pd, numpy as np
from math import comb
AU="/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols/analysis/audit/"
D=pd.read_csv(AU+"traj.csv"); S=pd.read_csv(AU+"struct.csv")
ACT=["gemma-4-31B-it","gpt-oss-120b","Llama-3.3-70B-Instruct"]
def mc(b,c):
    m=b+c
    return min(1.0,2*sum(comb(m,i) for i in range(min(b,c)+1))/2**m) if m else 1.0

print("### F1  ARM C SURVIVORSHIP (the FATAL one) ###")
for a in ACT:
    sub=S[(S.actor==a)&(S.arm=="C")]
    pub=sub[(sub.graded==1)&(sub.fp==0)]
    af =sub[(sub.n_eval>0)&(sub.fp==0)]
    ung=sub[sub.graded==0]
    print(f"  {a:<24} published rec={pub.fin.mean():.3f} (n={len(pub)});"
          f" assumption-free={af.fin.mean():.3f} (n={len(af)});"
          f" ungraded={len(ung)} (with-eval {int((ung.n_eval>0).sum())},"
          f" never-submitted {int((ung.n_eval==0).sum())})")
print("  paired A-vs-C, published vs assumption-free:")
for a in ACT:
    A=S[(S.actor==a)&(S.arm=="A")].drop_duplicates("problem_uid").set_index("problem_uid")
    C=S[(S.actor==a)&(S.arm=="C")].drop_duplicates("problem_uid").set_index("problem_uid")
    for lab,ga,gc in (("pub",(A.graded==1),(C.graded==1)),("af",(A.n_eval>0),(C.n_eval>0))):
        Af=set(A[ga&(A.fp==0)].index); Cf=set(C[gc&(C.fp==0)].index)
        bo=sorted(Af&Cf)
        b=sum(1 for p in bo if A.fin[p]==1 and C.fin[p]==0)
        c=sum(1 for p in bo if A.fin[p]==0 and C.fin[p]==1)
        print(f"    {a:<24}{lab:<4} n={len(bo):<4} Aonly={b:<3} Conly={c:<3} p={mc(b,c):.2e}")

print("\n### F2  GEMMA HEADLINE, EVERY STRESS TEST ###")
a="gemma-4-31B-it"
A=S[(S.actor==a)&(S.arm=="A")].drop_duplicates("problem_uid").set_index("problem_uid")
B=S[(S.actor==a)&(S.arm=="B")].drop_duplicates("problem_uid").set_index("problem_uid")
Af=set(A[(A.graded==1)&(A.fp==0)].index); Bf=set(B[(B.graded==1)&(B.fp==0)].index)
bo=sorted(Af&Bf)
tests=[("as published", bo),
       ("identical starting error", [p for p in bo if str(A.first_cand[p])==str(B.first_cand[p])]),
       ("different starting error", [p for p in bo if str(A.first_cand[p])!=str(B.first_cand[p])]),
       ("A got <= B draws", [p for p in bo if A.n_eval[p]<=B.n_eval[p]]),
       ("equal draws", [p for p in bo if A.n_eval[p]==B.n_eval[p]])]
for lab,ps in tests:
    if len(ps)<10: print(f"  {lab:<28} n={len(ps)} too small"); continue
    b=sum(1 for p in ps if A.fin[p]==1 and B.fin[p]==0)
    c=sum(1 for p in ps if A.fin[p]==0 and B.fin[p]==1)
    print(f"  {lab:<28} n={len(ps):<4} Aonly={b:<3} Bonly={c:<3} p={mc(b,c):.2e}")

print("\n### F3  d_fp EXACTLY ZERO FOR GEMMA? ###")
for a in ACT:
    Ag=D[(D.actor==a)&(D.arm=="A")&(D.graded==1)]; Bg=D[(D.actor==a)&(D.arm=="B")&(D.graded==1)]
    print(f"  {a:<24} fpA={Ag.fp.mean():.6f} fpB={Bg.fp.mean():.6f} "
          f"n_fpwA={int((Ag.fp==0).sum())} n_fpwB={int((Bg.fp==0).sum())}"
          f"  d_fp={Bg.fp.mean()-Ag.fp.mean():+.6f}")
print("  gemma: 316 vs 316 -- the note says 'coincidentally equal'. Check pairing:")
Ai=set(D[(D.actor=='gemma-4-31B-it')&(D.arm=='A')&(D.graded==1)&(D.fp==0)].problem_uid)
Bi=set(D[(D.actor=='gemma-4-31B-it')&(D.arm=='B')&(D.graded==1)&(D.fp==0)].problem_uid)
print(f"    |A fpw|={len(Ai)} |B fpw|={len(Bi)} |intersection|={len(Ai&Bi)}"
      f" |symmetric difference|={len(Ai^Bi)}")
print("    => EQUAL SIZE but DIFFERENT SETS. 'Coincidentally equal' is right,")
print("       and the marginal contrast is still an exact ITT reparameterisation")
print("       because the MEANS are equal, which is what the algebra needs.")

print("\n### F4  LLAMA FLOOR ###")
a="Llama-3.3-70B-Instruct"
for arm in ("A","B","C"):
    g=S[(S.actor==a)&(S.arm==arm)&(S.graded==1)&(S.fp==0)]
    print(f"  Arm {arm} recovery={g.fin.mean():.4f} n={len(g)} n_recovered={int(g.fin.sum())}")
print("\n### F5  MDE SUMMARY ###")
def wide(a):
    s=D[D.actor==a].drop_duplicates(["problem_uid","arm"])
    return s.pivot(index="problem_uid",columns="arm",values="fin_prereg")
for i in range(3):
    for j in range(i+1,3):
        Wi=wide(ACT[i])[["A","C"]].dropna(); Wj=wide(ACT[j])[["A","C"]].dropna()
        cm=sorted(set(Wi.index)&set(Wj.index))
        d=((Wj["C"]-Wj["A"])[cm]-(Wi["C"]-Wi["A"])[cm]).values.astype(float)
        mde=(1.959964+0.8416212)*d.std(ddof=1)/np.sqrt(len(d))
        print(f"  {ACT[j][:14]:<16}-{ACT[i][:14]:<16} n={len(d):<5} obs={d.mean():+.4f} MDE80={mde:.4f}")
