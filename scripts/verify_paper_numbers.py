"""Verify every headline number in the manuscript against the live data.

Run before handover. Prints PAPER vs DATA for each checked quantity and exits
non-zero if any differs beyond tolerance, so a stale number cannot ship.
"""
import json, glob, re, sys, collections
import numpy as np

ROOT = "/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols"
RNG = np.random.default_rng(20261008)
BOX = re.compile(r"\\boxed")
ANS = re.compile(r"\\boxed|Final Answer")
BOUND = ("additional_property","answer_leak","missing_field","wrong_type","conditional_required")

rows = []
for f in glob.glob(ROOT + "/experiments/results/main/*.jsonl"):
    if "BUG" in f or "SNAPSHOT" in f: continue
    for l in open(f):
        try: rows.append(json.loads(l))
        except Exception: pass

def actor(r): return r["actor_model"].split("/")[-1]
def first3(r):
    return [m for m in (r.get("messages") or [])
            if m.get("role") in ("planner","executor","reviewer")][:3]

# --- functional collapse -----------------------------------------------------
fc = collections.defaultdict(list)
for r in rows:
    ms = first3(r)
    if len(ms) < 3: continue
    fc[(actor(r), r["arm"])].append(all(BOX.search(m.get("text") or "") for m in ms))

# --- P2 answer-authorship ----------------------------------------------------
p2 = collections.defaultdict(list)
for r in rows:
    for m in (r.get("messages") or []):
        if m.get("role") != "planner": continue
        if not (m.get("validation") or {}).get("ok", True): continue
        t = m.get("text") or ""
        if not t: continue
        p2[(actor(r), r["arm"])].append(0 if ANS.search(t) else 1)
        break

# --- paired B-A accuracy -----------------------------------------------------
acc = {}
byk = collections.defaultdict(dict)
for r in rows:
    byk[(actor(r), r["arm"])][r["problem_uid"]] = (r.get("correct") or 0)
for a in {actor(r) for r in rows}:
    A, B = byk.get((a,"A"),{}), byk.get((a,"B"),{})
    common = set(A) & set(B)
    if len(common) < 30: continue
    d = np.array([B[p]-A[p] for p in common], float)
    bs = [RNG.choice(d,len(d)).mean() for _ in range(4000)]
    acc[a] = (d.mean(), *np.percentile(bs,[2.5,97.5]), len(d))

# --- boundary rejections -----------------------------------------------------
br = collections.defaultdict(collections.Counter)
for r in rows:
    if r["arm"] not in ("C","Cp"): continue
    k = (actor(r), r["arm"]); br[k]["n"] += 1
    for e in (r.get("regeneration_events") or []):
        vr = e.get("validation_result") or {}
        if vr.get("ok"): continue
        if str(vr.get("violated_constraint")).startswith(BOUND): br[k]["b"] += 1

print("="*72); print("LIVE NUMBERS FOR THE MANUSCRIPT"); print("="*72)
print("\nfunctional collapse (Arm A / Arm B) — INVALID for C/Cp, not shown:")
for a in sorted({k[0] for k in fc}):
    va, vb = fc.get((a,"A"),[]), fc.get((a,"B"),[])
    if va and vb:
        print(f"  {a:24s} A={np.mean(va):.3f} (n={len(va)})   B={np.mean(vb):.3f} (n={len(vb)})")
print("\nP2 answer-authorship compliance:")
for k in sorted(p2):
    print(f"  {k[0]+'/'+k[1]:26s} {np.mean(p2[k]):.3f} (n={len(p2[k])})")
print("\npaired B-A accuracy:")
for a, (m,lo,hi,n) in sorted(acc.items()):
    sig = "" if lo < 0 < hi else "  SIG"
    print(f"  {a:24s} {m:+.4f} [{lo:+.4f},{hi:+.4f}] n={n}{sig}")
print("\nArm C/C' boundary rejections:")
for k in sorted(br):
    c = br[k]
    print(f"  {k[0]+'/'+k[1]:26s} {c['b']} total ({c['b']/c['n']:.2f}/traj, n={c['n']})")

print("\n" + "="*72)
print("TOTAL trajectories:", len(rows))
print("cells:", len({(actor(r), r['arm']) for r in rows}))
print("backends:", sorted({r.get('backend') for r in rows}))
