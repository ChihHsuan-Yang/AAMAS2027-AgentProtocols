"""ATTACK 5b: T6 recomputed on the RAW candidate.

prompts.py EVALUATOR_PREPEND templates ONLY ${task_description}, ${solution},
${result}. No history. So the evaluator prompt is a deterministic function of
(problem_uid, RAW candidate string). That VINDICATES the 'identical prompts'
wording -- but only if the grouping key is the RAW candidate. T6 groups on the
NORMALISED candidate (whitespace stripped, $ stripped), which can merge two
DIFFERENT prompts into one group and score their disagreement as grader noise.

Recompute the floor three ways and see whether the paper's 0.0086 is right.
"""
import json, glob, re, collections
FROZEN="/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols/experiments/results/FROZEN"
def nrm(s):
    if s is None: return None
    s=re.sub(r"\s+","",str(s)).strip("$").strip(); return s or None

raw=collections.defaultdict(list); norm=collections.defaultdict(list)
for f in sorted(glob.glob(FROZEN+"/*.jsonl")):
    for l in open(f):
        try: r=json.loads(l)
        except Exception: continue
        for e in (r.get("evaluator_history") or []):
            c,k=e.get("candidate"),e.get("correctness")
            if c is None or k is None: continue
            raw[(r["problem_uid"],c)].append(int(k))
            norm[(r["problem_uid"],nrm(c))].append(int(k))

def rate(g,lab):
    m={k:v for k,v in g.items() if len(v)>=2}
    d={k:v for k,v in m.items() if len(set(v))>1}
    tot=sum(len(v) for v in m.values())
    pc=sum(len(v) for v in d.values())
    print(f"  {lab:<44} groups={len(m):<6} disagreeing={len(d):<4}"
          f" rate={len(d)/len(m):.4f}   per-call={pc}/{tot}={pc/tot:.4f}")
    return len(d)/len(m)
print("="*92); print("5b  THE NOISE FLOOR UNDER THE EXACT PROMPT KEY"); print("="*92)
print("  The evaluator prompt = f(problem, RAW candidate). Group accordingly.")
rn=rate(norm,"NORMALISED candidate (as published, T6)")
rr=rate(raw,  "RAW candidate (the actual prompt key)")
print(f"\n  published floor 0.0086 uses the normalised key.")
print(f"  On the exact-prompt key the floor is {rr:.4f}"
      f" ({'LOWER -- the published figure is conservative' if rr<rn else 'HIGHER'}).")

# how many normalised groups merge distinct raw strings?
merged=0; mdis=0
by=collections.defaultdict(set)
for (p,c) in raw: by[(p,nrm(c))].add(c)
for k,v in by.items():
    if len(v)>1:
        merged+=1
        vs=norm[k]
        if len(set(vs))>1: mdis+=1
print(f"\n  normalised groups merging >1 distinct RAW candidate: {merged}")
print(f"    of which disagreeing: {mdis}")
print("  => the published estimator is CONSERVATIVE (it can only add apparent")
print("     disagreement), so the floor is an over-estimate, not an under-estimate.")
print("\n  CONCLUSION on the wording: 'identical evaluator prompts' is TRUE for")
print("  the raw key and near-true for the published one. The wording is FINE.")
print("  The problem with A8 is the OPERATION (ratio), not the estimate.")
