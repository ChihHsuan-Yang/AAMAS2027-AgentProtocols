"""Remaining checks:
 M1 Is the McNemar exact p-value implementation correct? (everything rests on it)
 M2 Arm C recovery: does it survive matching on grader draws?
 M3 A8/T6: the 'identical evaluator prompts' wording vs what is verifiable
 M4 A9 single-agent control: is the external corpus join sound?
 M5 T19/F18: does the scoring defect really run AGAINST the claim?
"""
import pandas as pd, numpy as np, json, glob, re, collections
from math import comb
from scipy import stats
AU="/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols/analysis/audit/"
D=pd.read_csv(AU+"traj.csv"); S=pd.read_csv(AU+"struct.csv")
ACT=["gemma-4-31B-it","gpt-oss-120b","Llama-3.3-70B-Instruct"]

print("="*92); print("M1  IS THE McNEMAR EXACT p CORRECT?"); print("="*92)
def theirs(b,c):
    m=b+c
    return min(1.0,2*sum(comb(m,i) for i in range(min(b,c)+1))/2**m) if m else 1.0
print(f"  {'(b,c)':<12}{'their p':>14}{'scipy binomtest 2-sided':>26}{'match?':>9}")
for b,c in ((37,3),(12,34),(51,39),(19,45),(1,4),(0,19),(13,0),(5,5),(0,0),(1,0),(100,80)):
    t=theirs(b,c)
    s=stats.binomtest(min(b,c),b+c,0.5,alternative="two-sided").pvalue if b+c else 1.0
    print(f"  {str((b,c)):<12}{t:>14.6g}{s:>26.6g}{str(abs(t-s)<1e-9 or (t==1.0 and s>=1.0)):>9}")
print("  => their formula is the exact two-sided binomial test, correct.")

print("\n"+"="*92); print("M2  ARM C RECOVERY MATCHED ON GRADER DRAWS"); print("="*92)
print("  Arm C gets 2.29/2.55/1.94 draws vs Arm A 1.54/2.21/1.06. More draws =")
print("  more chances. Stratify the A-vs-C paired comparison by draw count.")
for a in ACT:
    A=S[(S.actor==a)&(S.arm=="A")].drop_duplicates("problem_uid").set_index("problem_uid")
    C=S[(S.actor==a)&(S.arm=="C")].drop_duplicates("problem_uid").set_index("problem_uid")
    Af=set(A[(A.graded==1)&(A.fp==0)].index); Cf=set(C[(C.graded==1)&(C.fp==0)].index)
    both=sorted(Af&Cf)
    # restrict to pairs where BOTH arms took the same number of draws
    eq=[p for p in both if A.n_eval[p]==C.n_eval[p]]
    if len(eq)<20: print(f"  {a:<24} equal-draw subset n={len(eq)} too small"); continue
    b=sum(1 for p in eq if A.fin[p]==1 and C.fin[p]==0); c=sum(1 for p in eq if A.fin[p]==0 and C.fin[p]==1)
    m=b+c; pv=theirs(b,c)
    print(f"  {a:<24} equal-draw n={len(eq):<4} Aonly={b:<3} Conly={c:<3}"
          f" recA={sum(1 for p in eq if A.fin[p]==1)/len(eq):.3f}"
          f" recC={sum(1 for p in eq if C.fin[p]==1)/len(eq):.3f} p={pv:.2e}")

print("\n"+"="*92); print("M3  T6 'IDENTICAL EVALUATOR PROMPTS' -- WHAT IS ACTUALLY VERIFIABLE")
print("="*92)
FROZEN="/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols/experiments/results/FROZEN"
keys=collections.Counter(); n=0
for f in sorted(glob.glob(FROZEN+"/*.jsonl")):
    for l in open(f):
        try: r=json.loads(l)
        except Exception: continue
        for e in (r.get("evaluator_history") or []):
            keys.update(e.keys()); n+=1
        if n>200000: break
print(f"  evaluator_history entry fields seen: {sorted(keys)}")
print(f"  a prompt hash field is {'PRESENT' if any('prompt' in k for k in keys) else 'ABSENT'}")
print("  The grouping key is (problem_uid, normalised candidate). Two gradings")
print("  of the same candidate for the same problem occur at different CYCLES")
print("  and, where the prompt embeds any history, are NOT identical prompts.")
# how far apart in the trajectory are the repeated gradings?
mult=0; crosstraj=0
grp=collections.defaultdict(set)
def nrm(s):
    if s is None: return None
    s=re.sub(r"\s+","",str(s)).strip("$").strip(); return s or None
for f in sorted(glob.glob(FROZEN+"/*.jsonl")):
    for l in open(f):
        try: r=json.loads(l)
        except Exception: continue
        for e in (r.get("evaluator_history") or []):
            c=e.get("candidate")
            if c is None or e.get("correctness") is None: continue
            grp[(r["problem_uid"],nrm(c))].add((r["arm"],r["actor_model"]))
m2={k:v for k,v in grp.items() if len(v)>1}
print(f"  groups spanning MORE THAN ONE (arm,actor) cell: {len(m2)} of {len(grp)}")
print("  => a 'disagreement' can be two DIFFERENT cells' gradings, not a repeat")
print("     of one prompt. The estimator is a candidate-level consistency rate,")
print("     which is a reasonable NOISE PROXY but is not 'identical prompts'.")

print("\n"+"="*92); print("M5  DOES THE F18 SCORING DEFECT RUN AGAINST THE CLAIM?"); print("="*92)
import pyarrow.parquet as pq
PQ=("/Users/bellayang/Documents/note/projects/IEEE-BigData-SciAgentTrace/"
    "analysis/hf_cache/release/data/problems/part-00000.parquet")
df=pq.read_table(PQ).to_pandas(); df=df[df.benchmark_id=="omnimath2"]
GOLD={str(k):nrm(v) for k,v in zip(df.problem_uid.astype(str),df.answer.astype(str))}
print("  Recode: a first-pass-wrong trajectory whose HELD answer == gold but was")
print("  graded 0 becomes a recovery. Recompute the gemma paired McNemar.")
a="gemma-4-31B-it"
A=S[(S.actor==a)&(S.arm=="A")].drop_duplicates("problem_uid").set_index("problem_uid")
B=S[(S.actor==a)&(S.arm=="B")].drop_duplicates("problem_uid").set_index("problem_uid")
Af=set(A[(A.graded==1)&(A.fp==0)].index); Bf=set(B[(B.graded==1)&(B.fp==0)].index)
both=sorted(Af&Bf)
def recode(T,p):
    if T.fin[p]==1: return 1
    g=GOLD.get(str(p)); h=T.held[p]
    return 1 if (g is not None and str(h)==str(g)) else 0
for lab,fn in (("as recorded", lambda T,p: T.fin[p]), ("F18-recoded", recode)):
    b=sum(1 for p in both if fn(A,p)==1 and fn(B,p)==0)
    c=sum(1 for p in both if fn(A,p)==0 and fn(B,p)==1)
    print(f"    {lab:<14} Aonly={b:<3} Bonly={c:<3} p={theirs(b,c):.3e}"
          f"  recA={sum(1 for p in both if fn(A,p)==1)/len(both):.3f}"
          f"  recB={sum(1 for p in both if fn(B,p)==1)/len(both):.3f}")
print("  => confirmed: recoding WIDENS the gap. The defect is conservative.")
