"""D4: Was the silenced agent right?

Broadcast polls all 3 deliberators in parallel with identical context, then lets
ONLY argmax(confidence) speak. Every agent's candidate answer is recorded.
On MCQ benchmarks the grader is exact (calibrated in d3), so for each poll we
can score EVERY agent's candidate -- including the ones that were suppressed.

This makes the selection rule counterfactually evaluable at the turn level:
  - was the chosen speaker's answer right?
  - was any suppressed agent's answer right?
  - would majority vote have beaten argmax-confidence?
"""
import os, re
import pandas as pd, pyarrow.parquet as pq, numpy as np

REL = "/Users/bellayang/Documents/note/projects/IEEE-BigData-SciAgentTrace/analysis/hf_cache/release"
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/results"
pd.set_option("display.width", 250)

def mcq_set(s):
    if not isinstance(s, str): return None
    x = s
    for _ in range(4):
        m = re.search(r"\\boxed\{(.*)\}", x, re.S)
        if not m: break
        x = m.group(1).strip()
    x = re.sub(r"[\\${}\s\(\)\[\].,;:]", "", x).upper()
    if x and re.fullmatch(r"[A-E]+", x):
        return "".join(sorted(set(x)))
    return None

polls = pd.read_parquet(OUT + "/d2_polls.parquet")
prob = pq.read_table(REL + "/data/problems/part-00000.parquet",
                     columns=["problem_uid", "benchmark_id", "answer", "answer_text"]).to_pandas()
traj = pq.read_table(REL + "/data/trajectories/part-00000.parquet",
                     columns=["trajectory_uid", "actor_model_id", "final_correct",
                              "first_pass_correct", "benchmark_id"]).to_pandas()

p = polls.merge(prob, on="problem_uid", how="left").merge(
    traj[["trajectory_uid", "actor_model_id", "final_correct", "first_pass_correct"]],
    on="trajectory_uid", how="left")
p["gold_set"] = [mcq_set(a if isinstance(a, str) and a.strip() else b)
                 for a, b in zip(p.answer, p.answer_text)]
p["cand_set"] = [mcq_set(c) for c in p.candidate_raw]
p["correct"] = [None if (a is None or b is None) else int(a == b)
                for a, b in zip(p.cand_set, p.gold_set)]

mcq = p[p.benchmark_id.isin(["labbench", "jeebench", "mascqa"])].copy()
print("MCQ-benchmark poll rows:", len(mcq),
      "| with gradable candidate:", mcq.correct.notna().sum())

# ---------- Q1: is self-reported confidence informative? --------------------
q = mcq.dropna(subset=["correct"]).copy()
q["correct"] = q.correct.astype(int)
print("\n=== Q1: accuracy by self-reported confidence bucket (parsed polls only) ===")
q_ok = q[q.parse_succeeded == True]
buck = pd.cut(q_ok.score, [0, 60, 70, 80, 85, 90, 95, 100], include_lowest=True)
print(q_ok.groupby(buck, observed=True).correct.agg(["mean", "size"]).round(4).to_string())

# ---------- Q2: turn-level selection counterfactual --------------------------
print("\n=== Q2: per-turn selection counterfactual ===")
rows = []
for (tid, rnd, turn), g in q.groupby(["trajectory_uid", "round_index", "turn"]):
    if len(g) < 2: continue
    g = g.sort_values("score", ascending=False)
    chosen = g.iloc[0]
    others = g.iloc[1:]
    # majority vote over candidates present this turn
    vc = g.cand_set.value_counts()
    maj = vc.index[0] if len(vc) and vc.iloc[0] > 1 else None
    gold = g.gold_set.iloc[0]
    rows.append(dict(
        trajectory_uid=tid, benchmark_id=g.benchmark_id.iloc[0],
        actor=g.actor_model_id.iloc[0], round_index=rnd, turn=turn, n_agents=len(g),
        chosen_correct=int(chosen.correct), chosen_score=chosen.score,
        any_other_correct=int(others.correct.max()) if len(others) else 0,
        all_agree=int(g.cand_set.nunique() == 1),
        majority_correct=(int(maj == gold) if maj is not None else None),
        oracle_correct=int(g.correct.max()),
        n_distinct=g.cand_set.nunique(),
    ))
sel = pd.DataFrame(rows)
print("turns with >=2 gradable candidates:", len(sel))
print("\npooled:")
print(pd.Series(dict(
    argmax_confidence=sel.chosen_correct.mean(),
    majority_vote=sel.majority_correct.dropna().mean(),
    best_available_oracle=sel.oracle_correct.mean(),
    all_three_agree_rate=sel.all_agree.mean(),
    silenced_right_while_chosen_wrong=((sel.chosen_correct == 0) & (sel.any_other_correct == 1)).mean(),
    chosen_right_while_all_others_wrong=((sel.chosen_correct == 1) & (sel.any_other_correct == 0)).mean(),
)).round(4).to_string())

print("\nby benchmark:")
print(sel.groupby("benchmark_id").agg(
    n=("chosen_correct", "size"),
    argmax_conf=("chosen_correct", "mean"),
    majority=("majority_correct", "mean"),
    oracle=("oracle_correct", "mean"),
    agree_rate=("all_agree", "mean"),
    silenced_right_chosen_wrong=("chosen_correct", lambda s: np.nan),
).round(4).to_string())

sel["miss"] = ((sel.chosen_correct == 0) & (sel.any_other_correct == 1)).astype(int)
print("\n'a silenced agent was right, the speaker was wrong' rate by benchmark:")
print(sel.groupby("benchmark_id").miss.agg(["mean", "sum", "size"]).round(4).to_string())

print("\n=== Q3: conditional on DISAGREEMENT (n_distinct>1) ===")
dis = sel[sel.n_distinct > 1]
print("share of turns with disagreement:", round(len(dis) / len(sel), 4))
print(pd.Series(dict(
    argmax_confidence=dis.chosen_correct.mean(),
    majority_vote=dis.majority_correct.dropna().mean(),
    oracle=dis.oracle_correct.mean(),
    n=len(dis))).round(4).to_string())

print("\n=== Q4: does within-turn agreement predict correctness? ===")
print(sel.groupby("all_agree").agg(chosen_correct=("chosen_correct", "mean"),
                                   n=("chosen_correct", "size")).round(4).to_string())

sel.to_parquet(OUT + "/d4_turn_selection.parquet", index=False)
q.to_parquet(OUT + "/d4_graded_polls.parquet", index=False)
