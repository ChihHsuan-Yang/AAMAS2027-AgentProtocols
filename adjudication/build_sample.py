"""Build a BLINDED, stratified sample for frontier-model adjudication.

Blinding: the judge sees only "Agent 1/2/3" text. Actor, arm, collapse flag,
correctness, and difficulty are written to a SEPARATE key file that the judge
never receives. Item order is randomized under a recorded seed.
"""
import json, glob, os, random, hashlib

ROOT = "/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols"
OUT = ROOT + "/adjudication"
SEED = 20260929
PER_CELL = 14          # cells: actor(2) x arm(A,B,C) x collapse(0/1) where non-empty

def coll3(r):
    h = [m.get("response_sha256_12") for m in (r.get("messages") or [])
         if m.get("role") in ("planner","executor","reviewer") and m.get("response_sha256_12")][:3]
    return (len(set(h)) < len(h)) if len(h) >= 2 else None

rows = []
for f in glob.glob(ROOT + "/experiments/results/main/*.jsonl"):
    if "BUG" in f or "SNAPSHOT" in f: continue
    for l in open(f):
        try: rows.append(json.loads(l))
        except Exception: pass

# eligible: has >=3 role messages with text
elig = []
for r in rows:
    ms = [m for m in (r.get("messages") or [])
          if m.get("role") in ("planner","executor","reviewer") and (m.get("text") or "").strip()]
    if len(ms) < 3: continue
    c = coll3(r)
    if c is None: continue
    elig.append((r, ms[:3], c))
print(f"eligible trajectories: {len(elig)}")

buckets = {}
for r, ms, c in elig:
    actor = r["actor_model"].split("/")[-1]
    buckets.setdefault((actor, r["arm"], bool(c)), []).append((r, ms, c))
print("non-empty strata:", len(buckets))
for k in sorted(buckets): print(f"   {k}: {len(buckets[k])}")

rng = random.Random(SEED)
picked = []
for k in sorted(buckets):
    pool = buckets[k]; rng.shuffle(pool)
    picked += [(k, *p) for p in pool[:PER_CELL]]
rng.shuffle(picked)

items, key = [], []
for i, (k, r, ms, c) in enumerate(picked):
    tid = "T%04d" % i
    body = "\n\n".join(
        f"=== Agent {j+1} ===\n{(m.get('text') or '')[:4000]}" for j, m in enumerate(ms))
    items.append({"tid": tid, "transcript": body})
    key.append({"tid": tid, "actor": k[0], "arm": k[1], "auto_collapse": k[2],
                "problem_uid": r["problem_uid"], "correct": r.get("correct"),
                "run_id": r.get("run_id"), "config_version": r.get("config_version")})

with open(OUT + "/ITEMS_blinded.jsonl", "w") as f:
    for it in items: f.write(json.dumps(it) + "\n")
with open(OUT + "/KEY.jsonl", "w") as f:
    for k_ in key: f.write(json.dumps(k_) + "\n")

man = {"seed": SEED, "per_cell": PER_CELL, "n_items": len(items),
       "strata": {str(k): len(v) for k, v in buckets.items()},
       "items_sha256": hashlib.sha256(open(OUT+"/ITEMS_blinded.jsonl","rb").read()).hexdigest()}
json.dump(man, open(OUT + "/SAMPLING_MANIFEST.json", "w"), indent=1)
print(f"\nwrote {len(items)} blinded items; manifest sha {man['items_sha256'][:16]}")
