"""Adversarial audit: compact extract of the FROZEN snapshot.

Writes analysis/audit/traj.csv with one row per trajectory and only the fields
the audit needs. Definitions are COPIED from FINAL_TABLES.py so any discrepancy
between my numbers and theirs is a real discrepancy, not a definition drift.
"""
import json, glob, re, csv, sys

FROZEN = "/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols/experiments/results/FROZEN"
OUT    = "/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols/analysis/audit/traj.csv"
if len(sys.argv) > 2:
    FROZEN, OUT = sys.argv[1], sys.argv[2]

BOX = re.compile(r"\\boxed\s*\{")

def boxed_all(t):
    o = []
    for m in BOX.finditer(t or ""):
        i, dd = m.end() - 1, 0
        for j in range(i, min(len(t), i + 4000)):
            if t[j] == "{": dd += 1
            elif t[j] == "}":
                dd -= 1
                if dd == 0: o.append(t[i+1:j]); break
    return o

def jans(t):
    o = [m.group(1) for m in re.finditer(r'"answer"\s*:\s*"((?:[^"\\]|\\.)*)"', t or "")]
    o += [m.group(1) for m in re.finditer(r'"answer"\s*:\s*(-?[0-9][0-9.eE+/-]*)', t or "")]
    return o

def nrm(s):
    if s is None: return None
    s = re.sub(r"\s+", "", str(s)).strip("$").strip(); return s or None

FIELDS = ["problem_uid","arm","actor","graded","fp","fin_prereg","fin_asgraded",
          "hard_failure","exhausted","n_eval","inner_used","n_ans_distinct",
          "ctx_chars","n_role_msgs","route1","never_refuse","unanimous",
          "func_collapse","retries","actor_calls","wall_time_s","last_cand","held",
          "domain","benchmark_id","run_id"]

w = csv.writer(open(OUT,"w",newline=""))
w.writerow(FIELDS)
n = 0
for f in sorted(glob.glob(FROZEN + "/*.jsonl")):
    for line in open(f):
        try: r = json.loads(line)
        except Exception: continue
        n += 1
        arm = r["arm"]; act = r["actor_model"].split("/")[-1]
        evh = r.get("evaluator_history") or []
        graded = bool(evh) and r.get("correct") is not None
        fp = int(evh[0].get("correctness") or 0) if evh else ""
        msgs = [m for m in (r.get("messages") or []) if m.get("role") in ("planner","executor","reviewer")]
        seq = []
        for m in msgs:
            t = m.get("text") or ""
            for b in boxed_all(t) + (jans(t) if arm in ("C","Cp") else []):
                x = nrm(b)
                if x and (not seq or seq[-1] != x): seq.append(x)
        rts = [m.get("route") for m in msgs if m.get("role")=="reviewer" and m.get("route")]
        f3 = msgs[:3]
        fc = ""
        if len(f3)==3: fc = int(all(BOX.search(m.get("text") or "") for m in f3))
        un = ""
        if len(f3)==3:
            aa=[]; ok=True
            for m in f3:
                b = boxed_all(m.get("text") or "")
                if not b: ok=False; break
                aa.append(nrm(b[-1]))
            if ok: un = int(len(set(aa))==1)
        hf = r.get("hard_failure") or ""
        w.writerow([r["problem_uid"], arm, act, int(graded), fp,
                    int(r.get("correct") or 0),
                    "" if r.get("correct") is None else int(r.get("correct")),
                    hf, int(hf.startswith("regeneration_exhausted")),
                    len(evh), r.get("inner_used") or 0, len(set(seq)),
                    sum(len(m.get("text") or "") for m in msgs), len(msgs),
                    (rts[0] if rts else ""),
                    (int(not any(z!="agree" for z in rts)) if rts else ""),
                    un, fc, r.get("retries") or 0, r.get("actor_calls") or 0,
                    r.get("wall_time_s") or 0,
                    nrm((evh[-1] or {}).get("candidate")) if evh else "",
                    nrm(r.get("final_answer")),
                    r.get("domain"), r.get("benchmark_id"), r.get("run_id")])
print("rows", n, "->", OUT)
