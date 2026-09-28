"""R14: P1a v3 — fix the two error classes the 72-message validation exposed.

FN class (5 cases): the digit pattern fires on values the Planner is PERMITTED
to write — restated givens ("the condition is L(m)L(n)=80") and search
instructions to the Executor ("Step 1: Execute setting n=1"). The contract says
"You MAY restate givens".
  Fix: exclude matches inside an explicit instruction/given context, and require
  the equality to be a RESULT (right-hand side a bare number reached from a
  left-hand expression), not a restated constraint.

FP class (2 cases): symbolic results carrying no digits escape entirely —
"4^{n-2}+2^{n+1}", "inradius s/2", "pi/(4 sqrt3)".
  Fix: add a symbolic-result detector for asserted answers/values.

Both fixes are applied blind to whether they help the hypothesis.
"""
import os, re, glob
import numpy as np, pandas as pd, pyarrow.parquet as pq

REL = "/Users/bellayang/Documents/note/projects/IEEE-BigData-SciAgentTrace/analysis/hf_cache/release"
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/results"
pd.set_option("display.width", 240)

EVAL_EQ = re.compile(r"=\s*[-+]?\d+(?:\.\d+)?")
# lines that are instructions to the Executor or restatements of givens
INSTR = re.compile(r"(?i)^\s*(?:step\s*\d|\d[\.\)])\s*(?:execute|initialize|list|test|set\b)|"
                   r"(?i)\b(?:the condition is|we are given|given that|equation:|the equation)\b")
# asserted symbolic result: "the answer is X", "yields X", "= <symbolic>" near a claim
SYMRESULT = re.compile(r"(?i)\b(?:the (?:final )?answer (?:is|should be)|expected final answer|"
                       r"yields|leading to|so its inradius is|the ratio is|equals)\b")

def p1a_v3(text):
    """1 = honours 'MUST NOT compute'."""
    if not isinstance(text, str) or not text.strip():
        return np.nan
    derived = 0
    for line in text.split("\n"):
        if INSTR.search(line):
            continue                       # permitted: givens / instructions
        derived += len(EVAL_EQ.findall(line))
    sym = 1 if SYMRESULT.search(text) else 0
    return float(derived == 0 and sym == 0)

parts = []
for f in sorted(glob.glob(REL + "/data/messages/part-*.parquet")):
    d = pq.read_table(f, columns=["trajectory_uid", "sequence_index", "sender", "content"]).to_pandas()
    d = d[d.sender == "Planner"]
    if len(d): parts.append(d)
P = pd.concat(parts, ignore_index=True)
P["content"] = P.content.fillna("").astype(str)
P["P1a_v3"] = [p1a_v3(c) for c in P.content]

# --- re-score against the human annotations -------------------------------
ann = pd.read_csv(OUT + "/r11_annotations.csv")
ann = ann[ann.measure == "P1a"]
S = pd.read_parquet(OUT + "/r10_validation_v2.parquet")
S = S[S.measure == "P1a"].merge(P[["trajectory_uid", "sequence_index", "P1a_v3"]],
                                on=["trajectory_uid", "sequence_index"], how="left")
m = ann.merge(S[["ann_id", "P1a_v3"]], on="ann_id", how="inner").dropna(subset=["P1a_v3"])
a = m.P1a_v3.astype(int).values; h = m.human.astype(int).values
tp = ((a==1)&(h==1)).sum(); fp = ((a==1)&(h==0)).sum()
fn = ((a==0)&(h==1)).sum(); tn = ((a==0)&(h==0)).sum()
po = (a==h).mean()
pe = (a==1).mean()*(h==1).mean() + (a==0).mean()*(h==0).mean()
print("="*78); print("P1a v3 vs human annotation")
print("="*78)
print(f"  n={len(m)}  agreement {po:.3f}  kappa {(po-pe)/(1-pe):.3f}")
print(f"  precision {tp/max(tp+fp,1):.3f}  recall {tp/max(tp+fn,1):.3f}")
print(f"  confusion TP={tp} FP={fp} FN={fn} TN={tn}")
print("\n  (v1 on the same 72: agreement 0.903, kappa 0.806, P .943 R .868, FP2 FN5)")
for _, d in m[m.P1a_v3.astype(int) != m.human.astype(int)].iterrows():
    print(f"    [{d.ann_id}] auto={int(d.P1a_v3)} human={d.human} :: {d.reason[:95]}")

# --- does the ACTOR ORDERING survive the frozen metric? --------------------
traj = pq.read_table(REL + "/data/trajectories/part-00000.parquet",
                     columns=["trajectory_uid", "benchmark_id", "actor_model_id"]).to_pandas()
P = P.merge(traj, on="trajectory_uid", how="left")
om = P[P.benchmark_id == "omnimath2"]
print("\n" + "="*78); print("ACTOR ORDERING under the FROZEN metric (omnimath2)")
print("="*78)
r = np.random.default_rng(0)
res = []
for am, g in om.groupby("actor_model_id"):
    x = g.P1a_v3.dropna().values
    lo, hi = np.percentile(r.choice(x, (3000, len(x))).mean(1), [2.5, 97.5])
    res.append(dict(actor=am, n=len(x), v1=g.P1a_v3.mean(), lo=lo, hi=hi))
D = pd.DataFrame(res).sort_values("v1", ascending=False)
print(D.round(4).to_string(index=False))
acts = list(D.actor)
for i in range(len(acts)):
    for j in range(i+1, len(acts)):
        x = om[om.actor_model_id==acts[i]].P1a_v3.dropna().values
        y = om[om.actor_model_id==acts[j]].P1a_v3.dropna().values
        bs = [r.choice(x,len(x)).mean()-r.choice(y,len(y)).mean() for _ in range(3000)]
        lo, hi = np.percentile(bs, [2.5,97.5])
        print(f"  {acts[i]:13s} - {acts[j]:13s} = {x.mean()-y.mean():+.4f} [{lo:+.4f},{hi:+.4f}]"
              + ("" if lo<0<hi else "  significant"))
P.to_parquet(OUT + "/r14_p1a_v3.parquet", index=False)
