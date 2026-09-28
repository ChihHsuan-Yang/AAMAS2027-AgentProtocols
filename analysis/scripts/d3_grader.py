"""D3: Build an answer grader and CALIBRATE it against the recorded labels.

Discipline: never trust a fresh grader. Grade each trajectory's own
`final_answer` and check agreement with the recorded `final_correct`.
Only use the grader on benchmarks where that agreement is high.
"""
import os, re
import pandas as pd, pyarrow.parquet as pq

REL = "/Users/bellayang/Documents/note/projects/IEEE-BigData-SciAgentTrace/analysis/hf_cache/release"
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/results"
pd.set_option("display.width", 250)

BOX = re.compile(r"\\boxed\{(.*)\}", re.S)
def unbox(s):
    if not isinstance(s, str): return None
    x = s.strip()
    for _ in range(4):
        m = BOX.search(x)
        if not m: break
        x = m.group(1).strip()
    return x

def norm(s):
    x = unbox(s)
    if x is None: return None
    x = x.replace("\\text{", "").replace("\\mathrm{", "")
    x = re.sub(r"[\\${}\s\(\)\[\].,;:]", "", x)
    return x.upper() or None

def mcq_set(s):
    """For MCQ: reduce to the set of option letters."""
    x = norm(s)
    if not x: return None
    letters = sorted(set(re.findall(r"[A-E]", x)))
    # only treat as MCQ answer if it is *only* letters
    if letters and re.fullmatch(r"[A-E]+", x):
        return "".join(letters)
    return None

def grade_mcq(pred, gold):
    a, b = mcq_set(pred), mcq_set(gold)
    if a is None or b is None: return None
    return int(a == b)

prob = pq.read_table(REL + "/data/problems/part-00000.parquet",
                     columns=["problem_uid", "benchmark_id", "question_type",
                              "answer", "answer_text"]).to_pandas()
traj = pq.read_table(REL + "/data/trajectories/part-00000.parquet",
                     columns=["trajectory_uid", "problem_uid", "benchmark_id",
                              "protocol_id", "actor_model_id", "final_answer",
                              "final_correct", "first_pass_correct"]).to_pandas()

g = traj.merge(prob[["problem_uid", "question_type", "answer", "answer_text"]],
               on="problem_uid", how="left")
g["gold"] = g.answer.fillna(g.answer_text)
g["my_grade"] = [grade_mcq(p, q) for p, q in zip(g.final_answer, g.gold)]

print("=== GRADER CALIBRATION vs recorded final_correct ===")
cal = (g.dropna(subset=["my_grade"])
         .assign(agree=lambda d: (d.my_grade == d.final_correct.astype(int)).astype(int))
         .groupby("benchmark_id")
         .agg(n_gradable=("agree", "size"), agreement=("agree", "mean")))
cal["n_total"] = g.groupby("benchmark_id").size()
cal["coverage"] = cal.n_gradable / cal.n_total
print(cal.round(4).to_string())

print("\n=== by benchmark x protocol (agreement) ===")
gg = g.dropna(subset=["my_grade"]).copy()
gg["agree"] = (gg.my_grade == gg.final_correct.astype(int)).astype(int)
print(pd.crosstab(gg.benchmark_id, gg.protocol_id, values=gg.agree, aggfunc="mean").round(4).to_string())
print(pd.crosstab(gg.benchmark_id, gg.protocol_id).to_string())
g.to_parquet(OUT + "/d3_graded_finals.parquet", index=False)
