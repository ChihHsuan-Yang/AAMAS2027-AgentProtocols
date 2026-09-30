"""Audit extract 2: structure of the deliberation, needed to test whether
'first pass' denotes the same pipeline position in every arm, and to model
the recovery process."""
import json, glob, re, csv

FROZEN = "/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols/experiments/results/FROZEN"
OUT    = "/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols/analysis/audit/struct.csv"
BOX = re.compile(r"\\boxed\s*\{")

def boxed_all(t):
    o=[]
    for m in BOX.finditer(t or ""):
        i,dd=m.end()-1,0
        for j in range(i,min(len(t),i+4000)):
            if t[j]=="{": dd+=1
            elif t[j]=="}":
                dd-=1
                if dd==0: o.append(t[i+1:j]); break
    return o
def nrm(s):
    if s is None: return None
    s=re.sub(r"\s+","",str(s)).strip("$").strip(); return s or None

FIELDS=["problem_uid","arm","actor","graded","fp","fin","n_eval","inner_used",
        "msgs_before_first_eval","first_eval_outer","first_eval_inner",
        "n_distinct_submitted","submitted_seq_len","ev_verdicts",
        "n_regen_events","n_regen_failed","exhausted","n_role_msgs",
        "ctx_before_first_eval","last_eval_correct","any_eval_correct",
        "first_cand","last_cand","held"]
w=csv.writer(open(OUT,"w",newline="")); w.writerow(FIELDS)
for f in sorted(glob.glob(FROZEN+"/*.jsonl")):
    for line in open(f):
        try: r=json.loads(line)
        except Exception: continue
        arm=r["arm"]; act=r["actor_model"].split("/")[-1]
        evh=r.get("evaluator_history") or []
        msgs=[m for m in (r.get("messages") or []) if m.get("role") in ("planner","executor","reviewer")]
        # position of the first evaluator call: count role messages whose
        # timestamp precedes the first evaluator entry's timestamp when present,
        # else fall back to outer/inner of the first eval record.
        fe = evh[0] if evh else {}
        fo, fi = fe.get("outer_round"), fe.get("inner_round")
        nb = ""
        ts = fe.get("timestamp")
        if ts:
            nb = sum(1 for m in msgs if (m.get("timestamp") or "") < ts)
        cb = ""
        if ts:
            cb = sum(len(m.get("text") or "") for m in msgs if (m.get("timestamp") or "") < ts)
        cands=[nrm(e.get("candidate")) for e in evh]
        verd="".join(str(int(e.get("correctness") or 0)) for e in evh)
        regs=r.get("regeneration_events") or []
        nrf=sum(1 for e in regs if not (e.get("validation_result") or {}).get("ok",True))
        hf=r.get("hard_failure") or ""
        w.writerow([r["problem_uid"],arm,act,int(bool(evh) and r.get("correct") is not None),
                    (int(evh[0].get("correctness") or 0) if evh else ""),
                    int(r.get("correct") or 0), len(evh), r.get("inner_used") or 0,
                    nb, fo, fi, len(set(c for c in cands if c)), len(cands), verd,
                    len(regs), nrf, int(hf.startswith("regeneration_exhausted")),
                    len(msgs), cb,
                    (int(evh[-1].get("correctness") or 0) if evh else ""),
                    (int(any(e.get("correctness") for e in evh)) if evh else ""),
                    (cands[0] if cands else ""), (cands[-1] if cands else ""),
                    nrm(r.get("final_answer"))])
print("done ->",OUT)
