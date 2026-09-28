"""Deterministic matched-problem manifest. Every arm x actor sees THE SAME problems."""
import hashlib, json, os, sys
import pandas as pd, pyarrow.parquet as pq

REL = "/Users/bellayang/Documents/note/projects/IEEE-BigData-SciAgentTrace/analysis/hf_cache/release"
OUT = os.path.dirname(os.path.abspath(__file__))

def build(domain="omnimath2", n=400, seed=20261008):
    p = pq.read_table(REL + "/data/problems/part-00000.parquet").to_pandas()
    d = p[p.benchmark_id == domain].copy()
    # deterministic: sort by uid, then seeded sample, then sort again
    d = d.sort_values("problem_uid").reset_index(drop=True)
    d = d.sample(n=min(n, len(d)), random_state=seed).sort_values("problem_uid")
    rows = []
    for r in d.itertuples(index=False):
        gold = r.answer if isinstance(r.answer, str) and r.answer.strip() else r.answer_text
        rows.append(dict(problem_uid=r.problem_uid, benchmark_id=r.benchmark_id,
                         problem_text=r.problem_text, gold=gold,
                         question_type=getattr(r, "question_type", None)))
    man = dict(domain=domain, n=len(rows), seed=seed,
               source="AgentsSci/IEEE2026_BigData_MAS-4-Science-Matching",
               problems=rows)
    body = json.dumps(man, sort_keys=True).encode()
    man["manifest_sha256"] = hashlib.sha256(body).hexdigest()
    path = f"{OUT}/manifest_{domain}_n{len(rows)}.json"
    with open(path, "w") as f: json.dump(man, f, indent=1)
    print(f"{path}\n  n={len(rows)} sha256={man['manifest_sha256'][:16]}")
    return path

if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    build("omnimath2", n)
    build("omnimath2", 25)   # smoke
