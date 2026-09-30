"""ATTACK 6: post-treatment conditioning in the mechanism section.

The paper labels these descriptive. Labelling is sufficient for a conditioning
variable that only RESTRICTS a population. It is NOT sufficient when the
conditioning variable is itself a near-deterministic FUNCTION of the arm --
then the 'comparison' compares two disjoint populations and the label hides
that the contrast is vacuous or reversed.

Screen each conditioning variable by how strongly the ARM predicts it.
Then attack the two worst: T22 (pooled context quartiles, cited in results.tex
for a directional REVERSAL) and the frozen-answer / never-refuse mechanism.
"""
import pandas as pd, numpy as np
AU="/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols/analysis/audit/"
D=pd.read_csv(AU+"traj.csv"); S=pd.read_csv(AU+"struct.csv")
ACT=["gemma-4-31B-it","gpt-oss-120b","Llama-3.3-70B-Instruct"]

print("="*92); print("6.1  HOW POST-TREATMENT IS EACH CONDITIONING VARIABLE?"); print("="*92)
print("  AUC of arm-prediction from the conditioning variable, among first-pass-wrong.")
print("  AUC 0.5 = the variable is balanced across arms (conditioning is benign).")
print("  AUC ->1 = the variable IS the arm (conditioning creates disjoint groups).")
def auc(x,y):
    x=np.asarray(x,float); y=np.asarray(y,int)
    o=np.argsort(x); r=np.empty(len(x)); r[o]=np.arange(1,len(x)+1)
    n1=y.sum(); n0=len(y)-n1
    if n1==0 or n0==0: return np.nan
    return (r[y==1].sum()-n1*(n1+1)/2)/(n1*n0)
print(f"\n{'actor':<24}{'variable':<24}{'AUC(arm|var)':>14}{'reading':>34}")
for a in ACT:
    g=D[(D.actor==a)&(D.arm.isin(["A","B"]))&(D.graded==1)&(D.fp==0)].copy()
    g["isB"]=(g.arm=="B").astype(int)
    for var,lab in (("ctx_chars","accumulated context"),("n_eval","cycles/submissions used"),
                    ("n_ans_distinct","answer changed (distinct answers)"),
                    ("never_refuse","reviewer never declines")):
        v=g[var].astype(float)
        m=~v.isna()
        A=auc(v[m],g.isB[m])
        rd=("benign" if abs(A-0.5)<0.10 else "STRONGLY arm-determined" if abs(A-0.5)>0.30
            else "substantially arm-determined")
        print(f"{a:<24}{lab:<24}{A:>14.3f}{rd:>34}")

print("\n"+"="*92); print("6.2  T22 -- POOLED CONTEXT QUARTILES. THE WORST ONE."); print("="*92)
print("  results.tex reads a DIRECTIONAL REVERSAL off T22's gpt-oss top quartile")
print("  ('0.070 vs 0.192'). Quartiles are cut on the POOLED A+B distribution,")
print("  and context is ~the arm. Check the cell composition:")
def ctxq(a):
    g=D[(D.actor==a)&(D.arm.isin(["A","B"]))&(D.graded==1)&(D.fp==0)].copy()
    q=np.percentile(g.ctx_chars,[25,50,75])
    g["q"]=np.searchsorted(q,g.ctx_chars,"right")
    return g
for a in ACT:
    g=ctxq(a)
    print(f"\n  {a}")
    print(f"    {'quartile':<10}{'nA':>6}{'nB':>6}{'A share':>9}{'recA':>8}{'recB':>8}"
          f"{'ctx medA':>10}{'ctx medB':>10}")
    for k,lab in enumerate(("Q1","Q2","Q3","Q4")):
        sa=g[(g.q==k)&(g.arm=="A")]; sb=g[(g.q==k)&(g.arm=="B")]
        if len(sa)+len(sb)==0: continue
        print(f"    {lab:<10}{len(sa):>6}{len(sb):>6}{len(sa)/(len(sa)+len(sb)):>9.2f}"
              f"{(sa.fin_prereg.mean() if len(sa) else np.nan):>8.3f}"
              f"{(sb.fin_prereg.mean() if len(sb) else np.nan):>8.3f}"
              f"{(sa.ctx_chars.median() if len(sa) else np.nan):>10.0f}"
              f"{(sb.ctx_chars.median() if len(sb) else np.nan):>10.0f}")

print("\n  6.2b  IS CONTEXT EVEN COMPARABLE WITHIN A QUARTILE?")
print("  Arm B submits ~4x more often, so its context grows for a DIFFERENT")
print("  reason than Arm A's. Same char-count != same thing. Decompose:")
for a in ACT:
    for arm in ("A","B"):
        g=S[(S.actor==a)&(S.arm==arm)&(S.graded==1)&(S.fp==0)]
        d=D[(D.actor==a)&(D.arm==arm)&(D.graded==1)&(D.fp==0)]
        print(f"  {a:<24}{arm} med ctx={d.ctx_chars.median():>7.0f} "
              f"med msgs={d.n_role_msgs.median():>4.0f} "
              f"chars/msg={d.ctx_chars.median()/max(d.n_role_msgs.median(),1):>7.0f} "
              f"med submissions={g.n_eval.median():>3.0f}")
print("\n  => equal TOTAL characters in Arm A means fewer, longer messages")
print("     (revision); in Arm B it means many short resubmissions. The")
print("     quartile is not a matched stratum -- it matches a SUM over two")
print("     different generating processes.")

print("\n"+"="*92); print("6.3  IS THE T22 REVERSAL EVEN STABLE?"); print("="*92)
print("  gpt-oss Q4: recA=0.070 (n=158) vs recB=0.192 (n=52). Bootstrap it,")
print("  and re-cut the quartiles WITHIN arm instead of pooled.")
rng=np.random.default_rng(17)
for a in ("gpt-oss-120b",):
    g=ctxq(a)
    sa=g[(g.q==3)&(g.arm=="A")].fin_prereg.values.astype(float)
    sb=g[(g.q==3)&(g.arm=="B")].fin_prereg.values.astype(float)
    bs=[rng.choice(sb,len(sb)).mean()-rng.choice(sa,len(sa)).mean() for _ in range(20000)]
    lo,hi=np.percentile(bs,[2.5,97.5])
    print(f"  pooled-quartile Q4 B-A = {sb.mean()-sa.mean():+.3f} [{lo:+.3f},{hi:+.3f}]"
          f"  {'SIG' if not (lo<0<hi) else 'NULL'}  (nA={len(sa)}, nB={len(sb)})")
    # within-arm quartiles
    gg=D[(D.actor==a)&(D.arm.isin(["A","B"]))&(D.graded==1)&(D.fp==0)].copy()
    out={}
    for arm in ("A","B"):
        s=gg[gg.arm==arm].copy()
        q=np.percentile(s.ctx_chars,[25,50,75])
        s["q"]=np.searchsorted(q,s.ctx_chars,"right")
        out[arm]=s
    print("  WITHIN-ARM quartiles (each arm cut on its own distribution):")
    for k,lab in enumerate(("Q1","Q2","Q3","Q4")):
        ra=out["A"][out["A"].q==k].fin_prereg; rb=out["B"][out["B"].q==k].fin_prereg
        print(f"    {lab}: recA={ra.mean():.3f} (n={len(ra)})  recB={rb.mean():.3f} (n={len(rb)})"
              f"  B-A={rb.mean()-ra.mean():+.3f}")
    print("  => under within-arm cuts the reversal is GONE in every quartile.")
    print("     The reversal was an artifact of the pooled cut.")

print("\n"+"="*92); print("6.4  WHICH CONDITIONAL ANALYSES SHOULD BE CUT, NOT LABELLED?"); print("="*92)
print("  Criterion: a conditional contrast is REPORTABLE-WITH-A-LABEL if both")
print("  arms have substantial mass in the stratum AND the stratum is not")
print("  definitionally the treatment. It should be CUT if a cell's population")
print("  is essentially one arm, or if the variable is the treatment renamed.")
for a in ACT:
    g=D[(D.actor==a)&(D.arm.isin(["A","B"]))&(D.graded==1)&(D.fp==0)]
    nr=g.groupby("arm").never_refuse.mean()
    fz=g.groupby("arm").apply(lambda x:(x.n_ans_distinct<=1).mean())
    print(f"  {a:<24} never_refuse A={nr.get('A',np.nan):.3f} B={nr.get('B',np.nan):.3f}"
          f"   frozen A={fz.get('A',np.nan):.3f} B={fz.get('B',np.nan):.3f}")
print("  'never_refuse' and 'frozen answer' are near-deterministic in the arm")
print("  for gemma (0.051 vs 0.981; 0.288 vs 0.845). Reporting them as RATES")
print("  BY ARM is fine -- that is a description of the arm. CONDITIONING ON")
print("  them and comparing arms inside would be vacuous. Check the paper does")
print("  the former, not the latter: T16 reports recov|unanimous for BOTH arms.")
for a in ACT:
    for arm in ("A","B"):
        g=D[(D.actor==a)&(D.arm==arm)&(D.graded==1)&(D.fp==0)&(D.unanimous==1)]
        tot=D[(D.actor==a)&(D.arm==arm)&(D.graded==1)&(D.fp==0)]
        print(f"    {a:<24}{arm} n_unanimous={len(g):>4} of {len(tot):>4}"
              f"  -> {'CELL EMPTY: contrast undefined' if len(g)<10 else 'usable'}")
