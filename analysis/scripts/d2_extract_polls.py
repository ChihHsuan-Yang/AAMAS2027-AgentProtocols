"""D2: Extract the broadcast confidence-poll panel.

Every discussion turn, ALL deliberators are polled in parallel (asyncio.gather)
with identical context. Each returns {score 1-100, reason, intent,
candidate_answer}. Only argmax(score) speaks publicly; the rest are silenced
(and, if score >= speak_threshold=65, kept as a private 'deferred' note).

This means the release records, for every turn, the answer each agent WOULD
have contributed -- the counterfactual content of suppressed messages.
"""
import os, glob, json, re
import pandas as pd, pyarrow.parquet as pq

REL = "/Users/bellayang/Documents/note/projects/IEEE-BigData-SciAgentTrace/analysis/hf_cache/release"
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/results"

BOX = re.compile(r"\\boxed\{(.*)\}", re.S)

def norm_answer(s):
    if not isinstance(s, str) or not s.strip():
        return None
    x = s.strip()
    for _ in range(3):                      # unwrap nested \boxed{\boxed{B}}
        m = BOX.search(x)
        if not m: break
        x = m.group(1).strip()
    x = re.sub(r"\s+", " ", x).strip().strip("$").strip()
    return x or None

rows = []
for f in sorted(glob.glob(REL + "/data/messages/part-*.parquet")):
    t = pq.read_table(f, columns=["trajectory_uid", "problem_uid", "sequence_index",
                                  "stage", "sender", "round_index", "content",
                                  "extra_json", "trace_visible"])
    d = t.to_pandas()
    d = d[d.stage.str.match(r"^poll_\d+$", na=False)]
    if len(d) == 0: continue
    for r in d.itertuples(index=False):
        try:
            j = json.loads(r.extra_json) if r.extra_json else {}
        except Exception:
            j = {}
        sc = re.search(r"^score=(\d+)", r.content or "")
        rows.append(dict(
            trajectory_uid=r.trajectory_uid, problem_uid=r.problem_uid,
            sequence_index=r.sequence_index, stage=r.stage,
            turn=int(r.stage.split("_")[1]), round_index=r.round_index,
            sender=r.sender,
            score=int(sc.group(1)) if sc else (j.get("score") if isinstance(j.get("score"), int) else None),
            candidate_raw=j.get("candidate_answer"),
            candidate=norm_answer(j.get("candidate_answer")),
            parse_succeeded=j.get("parse_succeeded"),
            trace_visible=r.trace_visible,
        ))
    print(f, len(rows))

p = pd.DataFrame(rows)
p.to_parquet(OUT + "/d2_polls.parquet", index=False)
print("\npoll rows:", len(p), "trajectories:", p.trajectory_uid.nunique())
print("score distribution:"); print(p.score.describe().round(2).to_string())
print("\nscore histogram:"); print(p.score.value_counts().sort_index().tail(20).to_string())
print("\nagents per (traj,turn):")
print(p.groupby(["trajectory_uid", "turn"]).size().value_counts().to_string())
print("\ncandidate present rate:", p.candidate.notna().mean().round(4))
