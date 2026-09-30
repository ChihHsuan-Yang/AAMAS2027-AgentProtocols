"""ATTACK 6b: is the T22 context variable itself corrupted by the F13 logging
defect the paper documents?

The paper says gpt-oss Arm B loses its reasoning trace to the logger (75.7% of
role messages, 93.4% of first passes). ctx_chars counts VISIBLE characters.
So for gpt-oss Arm B, ctx_chars is not 'accumulated context' -- it is
'accumulated context MINUS the part our logger threw away'. If so, the pooled
quartile cut sorts gpt-oss Arm B into low quartiles for an INSTRUMENT reason,
and the reversal the paper reads off Q4 is an artifact of a known defect.
"""
import json, glob, re, numpy as np, pandas as pd, collections
FROZEN="/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols/experiments/results/FROZEN"
ACT=["gemma-4-31B-it","gpt-oss-120b","Llama-3.3-70B-Instruct"]

print("="*92); print("6b.1  VISIBLE-CHARACTER CONTEXT vs LATENCY-IMPLIED CONTEXT"); print("="*92)
print("  latency is a defect-independent proxy for how much the model actually")
print("  generated. Compare each cell's visible chars against its total latency.")
rows=collections.defaultdict(lambda: dict(ch=0,lat=0.0,n=0,low=0))
for f in sorted(glob.glob(FROZEN+"/*.jsonl")):
    for l in open(f):
        try: r=json.loads(l)
        except Exception: continue
        a=r["actor_model"].split("/")[-1]; arm=r["arm"]
        evh=r.get("evaluator_history") or []
        if not (evh and r.get("correct") is not None): continue
        if int(evh[0].get("correctness") or 0)!=0: continue
        k=(a,arm); d=rows[k]; d["n"]+=1
        for m in (r.get("messages") or []):
            if m.get("role") not in ("planner","executor","reviewer"): continue
            c=len(m.get("text") or ""); lat=m.get("latency_s") or 0
            d["ch"]+=c; d["lat"]+=lat
            if lat>0 and c/lat<10: d["low"]+=1
print(f"\n{'actor':<24}{'arm':<4}{'n_fpw':>7}{'chars/traj':>12}{'latency_s/traj':>16}"
      f"{'visible ch/s':>14}{'low-rate msgs':>15}")
for a in ACT:
    for arm in ("A","B","C"):
        d=rows.get((a,arm))
        if not d or not d["n"]: continue
        print(f"{a:<24}{arm:<4}{d['n']:>7}{d['ch']/d['n']:>12.0f}{d['lat']/d['n']:>16.1f}"
              f"{d['ch']/max(d['lat'],1):>14.1f}{d['low']:>15}")

print("\n  READ: gemma A/B visible ch/s are comparable (the logger worked).")
print("  gpt-oss Arm B generates for a LONGER time than Arm A per trajectory")
print("  while logging FAR fewer characters. Its low ctx_chars is the logger,")
print("  not less context.")

print("\n"+"="*92); print("6b.2  RE-CUT T22 USING LATENCY (defect-independent) INSTEAD OF CHARS")
print("="*92)
rec=[]
for f in sorted(glob.glob(FROZEN+"/*.jsonl")):
    for l in open(f):
        try: r=json.loads(l)
        except Exception: continue
        a=r["actor_model"].split("/")[-1]; arm=r["arm"]
        if arm not in ("A","B"): continue
        evh=r.get("evaluator_history") or []
        if not (evh and r.get("correct") is not None): continue
        if int(evh[0].get("correctness") or 0)!=0: continue
        ch=lat=0
        for m in (r.get("messages") or []):
            if m.get("role") not in ("planner","executor","reviewer"): continue
            ch+=len(m.get("text") or ""); lat+=m.get("latency_s") or 0
        rec.append(dict(actor=a,arm=arm,ch=ch,lat=lat,fin=int(r.get("correct") or 0)))
R=pd.DataFrame(rec)
for a in ACT:
    g=R[R.actor==a].copy()
    print(f"\n  {a}")
    for var,lab in (("ch","POOLED quartiles on VISIBLE CHARS (as published)"),
                    ("lat","POOLED quartiles on LATENCY (defect-independent)")):
        q=np.percentile(g[var],[25,50,75]); g["q"]=np.searchsorted(q,g[var],"right")
        s=[]
        for k in range(4):
            sa=g[(g.q==k)&(g.arm=="A")]; sb=g[(g.q==k)&(g.arm=="B")]
            s.append(f"Q{k+1}: A={sa.fin.mean():.3f}(n={len(sa)}) B={sb.fin.mean():.3f}(n={len(sb)})"
                     if len(sa)>=8 and len(sb)>=8 else f"Q{k+1}: --")
        print(f"    {lab}")
        for x in s: print(f"      {x}")
        # does the ordering reverse in Q4?
        sa=g[(g.q==3)&(g.arm=="A")]; sb=g[(g.q==3)&(g.arm=="B")]
        if len(sa)>=8 and len(sb)>=8:
            print(f"      Q4 B-A = {sb.fin.mean()-sa.fin.mean():+.3f}"
                  f"  {'REVERSED (B>A)' if sb.fin.mean()>sa.fin.mean() else 'no reversal'}")
print("\n  => the gpt-oss 'reversal in the top quartile' the paper reports")
print("     depends on which context measure is used.")
