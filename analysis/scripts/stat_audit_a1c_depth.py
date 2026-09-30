"""ATTACK 1c: the LAST plausible selection story for gemma-4's 37 vs 3.

S2 (differential error depth): the paired stratum {fp_A=0 AND fp_B=0} is
selected on BOTH arms failing. If Arm A fails first-pass only on HARD problems
while Arm B fails on hard AND easy ones, then conditioning on 'both wrong'
could enrich Arm A's side with problems that are easy-but-unlucky, which repair
readily, while Arm B's side... -- but note BOTH arms are evaluated on the SAME
problems in the stratum. So S2 must be reformulated:

  S2': within the SAME problem, the two arms' first-pass errors differ in
  DEPTH. Arm A's wrong answer is 'nearly right' (repairable), Arm B's is
  catastrophically wrong (unrepairable). Then A recovers more with NO
  difference in repair ABILITY -- purely a difference in what was there to
  repair. That WOULD be a real alternative explanation.

Test it: within the 237 paired problems, is the Arm A first answer closer to
gold / different from Arm B's at all? Also test the strongest version: are
the two arms' FIRST WRONG ANSWERS even different?
"""
import pandas as pd, numpy as np, re
AU="/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols/analysis/audit/"
S=pd.read_csv(AU+"struct.csv")
import pyarrow.parquet as pq
PQ=("/Users/bellayang/Documents/note/projects/IEEE-BigData-SciAgentTrace/"
    "analysis/hf_cache/release/data/problems/part-00000.parquet")
df=pq.read_table(PQ).to_pandas(); df=df[df.benchmark_id=="omnimath2"]
def nrm(s):
    if s is None: return None
    s=re.sub(r"\s+","",str(s)).strip("$").strip(); return s or None
GOLD={str(k):nrm(v) for k,v in zip(df.problem_uid.astype(str),df.answer.astype(str))}

a="gemma-4-31B-it"
A=S[(S.actor==a)&(S.arm=="A")].drop_duplicates("problem_uid").set_index("problem_uid")
B=S[(S.actor==a)&(S.arm=="B")].drop_duplicates("problem_uid").set_index("problem_uid")
Af=set(A[(A.graded==1)&(A.fp==0)].index); Bf=set(B[(B.graded==1)&(B.fp==0)].index)
both=sorted(Af&Bf)
print("="*92); print(f"1c.  S2' -- DIFFERENTIAL ERROR DEPTH within the {len(both)} paired problems")
print("="*92)
same=sum(1 for p in both if str(A.first_cand[p])==str(B.first_cand[p]))
print(f"  paired problems where BOTH ARMS' FIRST WRONG ANSWER IS THE SAME STRING:"
      f" {same}/{len(both)} = {same/len(both):.3f}")
print("  On those rows there is NOTHING for an error-depth story to differ on:")
print("  the thing to be repaired is byte-identical. Restrict to them.")
sub=[p for p in both if str(A.first_cand[p])==str(B.first_cand[p])]
from math import comb
b=sum(1 for p in sub if A.fin[p]==1 and B.fin[p]==0); c=sum(1 for p in sub if A.fin[p]==0 and B.fin[p]==1)
m=b+c; pv=min(1.0,2*sum(comb(m,i) for i in range(min(b,c)+1))/2**m) if m else 1.0
print(f"\n  *** IDENTICAL-STARTING-ERROR SUBSET ***")
print(f"  n={len(sub)}  Aonly={b}  Bonly={c}  recA={sum(1 for p in sub if A.fin[p]==1)/len(sub):.3f}"
      f"  recB={sum(1 for p in sub if B.fin[p]==1)/len(sub):.3f}  McNemar p={pv:.3e}")
print("  Both arms start from the SAME wrong answer on the SAME problem.")
print("  S2' (error depth) is held EXACTLY constant by construction.")
print("  If the effect survives here, error depth cannot explain it.")

print("\n  the complement (different starting errors), for contrast:")
sub2=[p for p in both if str(A.first_cand[p])!=str(B.first_cand[p])]
b2=sum(1 for p in sub2 if A.fin[p]==1 and B.fin[p]==0); c2=sum(1 for p in sub2 if A.fin[p]==0 and B.fin[p]==1)
m2=b2+c2; pv2=min(1.0,2*sum(comb(m2,i) for i in range(min(b2,c2)+1))/2**m2) if m2 else 1.0
print(f"  n={len(sub2)}  Aonly={b2}  Bonly={c2}  McNemar p={pv2:.3e}")

print("\n"+"="*92); print("1c.2  SAME TEST FOR THE OTHER TWO ACTORS"); print("="*92)
for a2 in ("gpt-oss-120b","Llama-3.3-70B-Instruct"):
    A2=S[(S.actor==a2)&(S.arm=="A")].drop_duplicates("problem_uid").set_index("problem_uid")
    B2=S[(S.actor==a2)&(S.arm=="B")].drop_duplicates("problem_uid").set_index("problem_uid")
    Af2=set(A2[(A2.graded==1)&(A2.fp==0)].index); Bf2=set(B2[(B2.graded==1)&(B2.fp==0)].index)
    bo=sorted(Af2&Bf2)
    su=[p for p in bo if str(A2.first_cand[p])==str(B2.first_cand[p])]
    if len(su)<20:
        print(f"  {a2:<24} identical-start subset n={len(su)} -- too small"); continue
    bb=sum(1 for p in su if A2.fin[p]==1 and B2.fin[p]==0); cc=sum(1 for p in su if A2.fin[p]==0 and B2.fin[p]==1)
    mm=bb+cc; p2=min(1.0,2*sum(comb(mm,i) for i in range(min(bb,cc)+1))/2**mm) if mm else 1.0
    print(f"  {a2:<24} n={len(su)}/{len(bo)}  Aonly={bb} Bonly={cc}"
          f"  recA={sum(1 for p in su if A2.fin[p]==1)/len(su):.3f}"
          f"  recB={sum(1 for p in su if B2.fin[p]==1)/len(su):.3f}  p={p2:.3e}")

print("\n"+"="*92); print("1c.3  THE ONE REMAINING DEGREE OF FREEDOM"); print("="*92)
print("  Even on identical starting errors, Arm A and Arm B differ in the")
print("  NUMBER OF GRADER DRAWS (1.54 vs 5.80). A recovery requires at least")
print("  one more draw. Does Arm A recover DESPITE fewer draws?")
for lab,ps,T in (("A-only",[p for p in sub if A.fin[p]==1 and B.fin[p]==0],A),
                 ("B-only",[p for p in sub if A.fin[p]==0 and B.fin[p]==1],B)):
    if not ps: print(f"    {lab}: n=0"); continue
    print(f"    {lab}: n={len(ps)} mean draws={np.mean([T.n_eval[p] for p in ps]):.2f}"
          f"  answer changed {sum(1 for p in ps if str(T.first_cand[p])!=str(T.last_cand[p]))}/{len(ps)}")
print("  Arm A recovers MORE with FEWER draws: the confound runs AGAINST the result.")
