"""ATTACK 5: the noise-floor comparison.

The paper compares an EFFECT SIZE (B-A = 0.0338, a difference of two accuracy
means) against a DISAGREEMENT RATE (0.0086, P(two identical prompts get
contradictory verdicts)). Are these commensurable? Build the right operation.
"""
import pandas as pd, numpy as np, json, glob, re, collections
AU="/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols/analysis/audit/"
D=pd.read_csv(AU+"traj.csv")
ACT=["gemma-4-31B-it","gpt-oss-120b","Llama-3.3-70B-Instruct"]

print("="*92); print("5.1  ARE THE TWO QUANTITIES COMMENSURABLE?"); print("="*92)
print("  effect        : E[Y_B] - E[Y_A], a difference of means, units = accuracy")
print("  'noise floor' : P(a graded string receives contradictory verdicts),")
print("                  units = probability of an INTERNAL INCONSISTENCY event")
print("  These have the same UNITS only by coincidence. A 0.86% disagreement")
print("  rate does NOT imply a 0.0086 uncertainty on a difference of means:")
print("   (a) grader noise is LARGELY COMMON to both arms -- the same grader")
print("       grades both, so it CANCELS in a paired difference;")
print("   (b) the residual is a VARIANCE contribution, not a BIAS floor, and it")
print("       shrinks as 1/sqrt(n) while the 'floor' is stated as a constant;")
print("   (c) the operation 'effect / disagreement rate = 3.9x' has no")
print("       inferential interpretation at all -- it is a ratio of a mean")
print("       difference to a probability.")

print("\n"+"="*92); print("5.2  THE DEFENSIBLE OPERATION: propagate grader noise into the CI"); print("="*92)
print("  Model: each graded trajectory's recorded outcome is flipped with prob q")
print("  INDEPENDENTLY per grading event (the per-call rate, the least favourable")
print("  to us: 0.0072). Re-run the paired contrast under that corruption and see")
print("  how much the interval widens and whether significance survives.")
rng=np.random.default_rng(31)
def wide(a):
    s=D[D.actor==a].drop_duplicates(["problem_uid","arm"])
    return s.pivot(index="problem_uid",columns="arm",values="fin_prereg")
print(f"\n{'actor':<24}{'obs B-A':>9}{'clean CI':>22}{'noise-propagated CI':>26}{'sig?':>7}")
for a in ACT:
    W=wide(a)[["A","B"]].dropna()
    ya=W["A"].values.astype(float); yb=W["B"].values.astype(float)
    n=len(ya); obs=(yb-ya).mean()
    r=np.random.default_rng(3)
    clean=np.percentile([(yb-ya)[r.choice(n,n)].mean() for _ in range(8000)],[2.5,97.5])
    out=[]
    for _ in range(8000):
        k=r.choice(n,n)
        fa=ya[k].copy(); fb=yb[k].copy()
        ma=r.random(n)<0.0072; mb=r.random(n)<0.0072
        fa[ma]=1-fa[ma]; fb[mb]=1-fb[mb]
        out.append((fb-fa).mean())
    nz=np.percentile(out,[2.5,97.5])
    sig="SIG" if not (nz[0]<0<nz[1]) else "null"
    print(f"{a:<24}{obs:>+9.4f}  [{clean[0]:+.4f},{clean[1]:+.4f}]      "
          f"[{nz[0]:+.4f},{nz[1]:+.4f}]{sig:>9}")
print("\n  => Under the DEFENSIBLE operation gemma stays significant, gpt-oss")
print("     becomes null, Llama stays null. Same three verdicts as the ratio")
print("     framing delivers -- but by a coherent route.")

print("\n"+"="*92); print("5.3  IS THE 'FLOOR' EVEN A BIAS? does grader noise cancel?"); print("="*92)
print("  The grader is the SAME model, temperature 0, on both arms. If its")
print("  errors were identical functions of the candidate string, they cancel")
print("  exactly in a paired contrast. They do not cancel only to the extent")
print("  the two arms SUBMIT DIFFERENT STRINGS. Measure that overlap:")
S=pd.read_csv(AU+"struct.csv")
for a in ACT:
    A=S[(S.actor==a)&(S.arm=="A")&(S.graded==1)].drop_duplicates("problem_uid").set_index("problem_uid")
    B=S[(S.actor==a)&(S.arm=="B")&(S.graded==1)].drop_duplicates("problem_uid").set_index("problem_uid")
    cm=sorted(set(A.index)&set(B.index))
    same=sum(1 for p in cm if str(A.last_cand[p])==str(B.last_cand[p]))
    print(f"  {a:<24} final graded string IDENTICAL across arms on {same}/{len(cm)} = {same/len(cm):.3f}")
print("  On identical strings the grader's verdict (and its noise) is shared, so")
print("  those rows contribute ZERO to the contrast AND zero noise. The floor")
print("  applies only to the discordant-string minority, making the stated")
print("  0.0086 a LOOSE OVER-estimate of noise on the contrast, not a floor.")

print("\n"+"="*92); print("5.4  WHAT THE T6 ESTIMATOR ACTUALLY MEASURES"); print("="*92)
print("  T6 groups by (problem_uid, normalised candidate) and asks whether the")
print("  verdicts within a group disagree. That conflates two things:")
print("   - real grader nondeterminism (same prompt, different verdict);")
print("   - PROMPT differences: the same candidate string graded in different")
print("     contexts / at different cycles is NOT an identical prompt.")
print("  Check: within disagreeing groups, were the evaluator prompts identical?")
FROZEN="/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols/experiments/results/FROZEN"
def nrm(s):
    if s is None: return None
    s=re.sub(r"\s+","",str(s)).strip("$").strip(); return s or None
grp=collections.defaultdict(list)
for f in sorted(glob.glob(FROZEN+"/*.jsonl")):
    for l in open(f):
        try: r=json.loads(l)
        except Exception: continue
        for e in (r.get("evaluator_history") or []):
            c,k=e.get("candidate"),e.get("correctness")
            if c is None or k is None: continue
            grp[(r["problem_uid"],nrm(c))].append((int(k),e.get("prompt_sha256_12"),
                                                   tuple(sorted(e.keys()))))
multi={k:v for k,v in grp.items() if len(v)>=2}
disc={k:v for k,v in multi.items() if len({x[0] for x in v})>1}
print(f"  groups with >=2 gradings: {len(multi)};  disagreeing: {len(disc)}"
      f" = {len(disc)/len(multi):.4f}  (matches T6's 0.0086)")
haveph=sum(1 for v in multi.values() if all(x[1] for x in v))
print(f"  groups where every grading records a prompt hash: {haveph}")
if haveph:
    sameph_multi=sum(1 for v in multi.values() if all(x[1] for x in v) and len({x[1] for x in v})==1)
    sameph_disc=sum(1 for v in disc.values() if all(x[1] for x in v) and len({x[1] for x in v})==1)
    print(f"    of those, IDENTICAL prompt hash: {sameph_multi}")
    print(f"    disagreeing AND identical prompt: {sameph_disc}")
    if sameph_multi:
        print(f"    TRUE same-prompt disagreement rate = {sameph_disc}/{sameph_multi}"
              f" = {sameph_disc/sameph_multi:.4f}")
else:
    print("    evaluator_history entries carry NO prompt hash -> the claim")
    print("    'identical evaluator prompts' in T6/results.tex/limitations.tex")
    print("    is NOT VERIFIABLE from the frozen snapshot.")
    k0=list(multi.keys())[0]
    print(f"    evaluator_history keys available: {multi[k0][0][2]}")
