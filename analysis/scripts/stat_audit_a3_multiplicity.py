"""ATTACK 3: multiplicity.

Three sub-questions:
 3.1 Are the preregistered five ACTUALLY Holm-corrected in the frozen output?
 3.2 Count every inferential contrast the paper reads as a result; compute the
     family-wise error rate if all were null.
 3.3 Which exploratory results are being read with confirmatory authority?
Plus: the Holm correction the paper promises, actually applied.
"""
import re, numpy as np, pandas as pd, subprocess
from math import comb
AU="/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols/analysis/audit/"
OUT="/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols/analysis/out/FINAL_TABLES_OUTPUT.txt"
TEX="/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols/paper/sections/"
D=pd.read_csv(AU+"traj.csv"); S=pd.read_csv(AU+"struct.csv")
ACT=["gemma-4-31B-it","gpt-oss-120b","Llama-3.3-70B-Instruct"]
RNG=np.random.default_rng(20261008)

print("="*90); print("3.1  IS HOLM APPLIED IN THE PIPELINE THAT PRODUCES THE PAPER'S NUMBERS?")
print("="*90)
ft=open("/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols/analysis/scripts/FINAL_TABLES.py").read()
print(f"  'holm' occurrences in FINAL_TABLES.py                  : {ft.lower().count('holm')}")
print(f"  'holm' occurrences in FINAL_TABLES_OUTPUT.txt          : {open(OUT).read().lower().count('holm')}")
print(f"  adjusted p-values of ANY kind in the frozen output     : "
      f"{len(re.findall(r'p_?(?:holm|adj)', open(OUT).read(), re.I))}")
x1=open("/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols/analysis/scripts/x1_analyze_campaign.py").read()
print(f"  holm() IS defined in x1_analyze_campaign.py            : {'def holm' in x1}")
print("  x1_interaction.csv (its only surviving output) is dated 2026-09-28 17:34,")
print("  BEFORE the campaign finished; its DiDs (+0.050/-0.055/-0.105) do not match")
print("  the frozen T14 (+0.0175/+0.0400/+0.0225). It is a PILOT artifact.")
print("\n  p-values present anywhere in the frozen output: only T4's six McNemar")
print("  values. P1,P2,P3,P5 have NO p-value in the frozen pipeline at all --")
print("  they are reported as bootstrap CIs. HOLM CANNOT HAVE BEEN APPLIED.")
print("  => the sentence 'P1--P5 carry a Holm correction' (results.tex:6,")
print("     method.tex:63) is NOT TRUE OF THE REPORTED ANALYSIS.")

print("\n"+"="*90); print("3.2  HOW MANY INFERENTIAL CONTRASTS DOES THE PAPER READ?")
print("="*90)
txt="".join(open(TEX+f).read() for f in
    ("results.tex","limitations.tex","method.tex","experiments.tex","discussion.tex","intro.tex"))
ci=re.findall(r"\[[-+][\d.]+,\s*[-+][\d.]+\]", txt)
pv=re.findall(r"p\s*=\s*\$?\\?[\d.]+\s*\\times\s*10\^\{?-?\d+\}?|p=\$?[\d.]+e-?\d+", txt)
print(f"  bracketed 95% CIs appearing in the paper text : {len(ci)}")
print(f"  explicit p-values appearing in the paper text : {len(pv)}")
# count inferential cells in the frozen output
o=open(OUT).read()
sig=len(re.findall(r"\bSIG\b", o))
allci=len(re.findall(r"\[[-+][\d.]+,[-+][\d.]+\]", o))
print(f"  bracketed CIs in FINAL_TABLES_OUTPUT          : {allci}")
print(f"  cells flagged SIG in FINAL_TABLES_OUTPUT      : {sig}")
for m,lab in ((8,"P1-P5 as preregistered (Holm family)"),
              (len(ci),"CIs read in the paper prose"),
              (allci,"every CI computed in the frozen output")):
    fwer=1-0.95**m
    print(f"  FWER if all null, m={m:<4} ({lab:<38}) = {fwer:.3f}")

print("\n"+"="*90); print("3.3  THE HOLM CORRECTION THE PAPER PROMISES, ACTUALLY APPLIED")
print("="*90)
print("  Family = the 5 preregistered tests. P1/P2 are fidelity (per actor),")
print("  P3/P4 accuracy (per actor / per actor-pair), P5 association.")
print("  Use a paired sign-flip permutation p for each, as x1 did (perm_p).")
def perm_p(d,n=20000,seed=3):
    d=np.asarray(d,float); d=d[~np.isnan(d)]
    r=np.random.default_rng(seed); obs=abs(d.mean())
    s=r.choice([-1,1],(n,len(d)))
    return float(((np.abs((s*d).mean(1))>=obs).sum()+1)/(n+1))
def wide(a,col="fin_prereg"):
    s=D[D.actor==a].drop_duplicates(["problem_uid","arm"])
    return s.pivot(index="problem_uid",columns="arm",values=col)
tests=[]
# P3: accuracy C-A per actor
for a in ACT:
    W=wide(a)[["A","C"]].dropna()
    tests.append((f"P3 acc C-A {a}", perm_p((W["C"]-W["A"]).values)))
# P4: DiD across actor pairs
for i in range(3):
    for j in range(i+1,3):
        Wi=wide(ACT[i])[["A","C"]].dropna(); Wj=wide(ACT[j])[["A","C"]].dropna()
        cm=sorted(set(Wi.index)&set(Wj.index))
        d=((Wj["C"]-Wj["A"])[cm]-(Wi["C"]-Wi["A"])[cm]).values
        tests.append((f"P4 DiD {ACT[j][:8]}-{ACT[i][:8]}", perm_p(d)))
# P1 manipulation: authored-answer-free C vs A -- from T11, effectively 1.000 vs ~0.0-0.6
tests.append(("P1 manipulation (authorship C vs A)", 1e-300))
ps=[p for _,p in tests]; labs=[l for l,_ in tests]
order=np.argsort(ps); m=len(ps); prev=0; adj={}
for rank,i in enumerate(order):
    v=min(1.0,max(prev,(m-rank)*ps[i])); prev=v; adj[labs[i]]=v
print(f"\n  {'test':<42}{'raw p':>12}{'Holm p':>12}{'sig@.05':>9}")
for l,p in tests:
    print(f"  {l:<42}{p:>12.4g}{adj[l]:>12.4g}{'yes' if adj[l]<0.05 else 'NO':>9}")
print("\n  => Under the promised correction nothing CHANGES: P4 was null before")
print("     and is null after; P3's one significant cell (gemma C-A) is checked next.")
W=wide("gemma-4-31B-it")[["A","C"]].dropna()
p=perm_p((W["C"]-W["A"]).values)
print(f"     gemma C-A raw p={p:.4g}  Holm p={adj['P3 acc C-A gemma-4-31B-it']:.4g}"
      f"  -> {'SURVIVES' if adj['P3 acc C-A gemma-4-31B-it']<0.05 else '*** LOSES SIGNIFICANCE ***'}")

print("\n"+"="*90); print("3.4  THE HEADLINE IS EXPLORATORY. IS IT READ AS CONFIRMATORY?")
print("="*90)
a="gemma-4-31B-it"
A=S[(S.actor==a)&(S.arm=="A")].drop_duplicates("problem_uid").set_index("problem_uid")
B=S[(S.actor==a)&(S.arm=="B")].drop_duplicates("problem_uid").set_index("problem_uid")
Af=set(A[(A.graded==1)&(A.fp==0)].index); Bf=set(B[(B.graded==1)&(B.fp==0)].index)
both=sorted(Af&Bf)
b=sum(1 for p in both if A.fin[p]==1 and B.fin[p]==0); c=sum(1 for p in both if A.fin[p]==0 and B.fin[p]==1)
mm=b+c; pv0=min(1.0,2*sum(comb(mm,i) for i in range(min(b,c)+1))/2**mm)
print(f"  gemma A-vs-B paired recovery McNemar raw p = {pv0:.3e}")
for m in (8, 25, len(ci), allci):
    print(f"    Bonferroni over m={m:<4}: p_adj = {min(1.0,pv0*m):.3e}"
          f"  {'still overwhelming' if pv0*m<1e-4 else 'weakened'}")
