"""R4: Build a stratified validation subset for MANUAL annotation.

Bella's instruction 5: do not build the paper on an unvalidated measure.
Sample ~240 messages stratified across role x actor x domain x correctness,
write them to a readable file, and record which automated labels each received
so agreement can be computed after annotation.
"""
import os
import numpy as np, pandas as pd, pyarrow.parquet as pq

REL = "/Users/bellayang/Documents/note/projects/IEEE-BigData-SciAgentTrace/analysis/hf_cache/release"
OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/results"
NOTES = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/../notes"

A = pd.read_parquet(OUT + "/r3_fidelity_messages.parquet")
traj = pq.read_table(REL + "/data/trajectories/part-00000.parquet",
                     columns=["trajectory_uid", "benchmark_id", "actor_model_id",
                              "final_correct"]).to_pandas()
A = A.merge(traj, on="trajectory_uid", how="left")
A = A[A.n_chars > 50]                      # skip degenerate stubs for annotation

rng = np.random.default_rng(7)
strata = ["sender", "actor_model_id", "benchmark_id", "final_correct"]
picks = []
for k, g in A.groupby(strata):
    n = min(len(g), 4)
    picks.append(g.sample(n, random_state=int(rng.integers(1e6))))
S = pd.concat(picks).sample(frac=1, random_state=0).reset_index(drop=True)
S = S.head(240)
print(f"validation sample: {len(S)} messages")
print(S.groupby(["sender", "actor_model_id"]).size().to_string())
print("\nby benchmark:"); print(S.benchmark_id.value_counts().to_string())
print("by correctness:"); print(S.final_correct.value_counts().to_string())

cols = ["trajectory_uid", "sequence_index", "sender", "stage", "actor_model_id",
        "benchmark_id", "final_correct", "n_chars", "eval_eq_density",
        "P1_abstains_compute", "P2_abstains_answer", "P3_decomposes", "P4_declares_form",
        "E1_computes", "E2_uses_plan", "E3_commits_answer",
        "R1_routes", "R2_diagnoses", "R3_targeted_fix", "R4_not_resolving", "content"]
S[cols].to_parquet(OUT + "/r4_validation_sample.parquet", index=False)

# human-readable annotation sheet
with open(NOTES + "/VALIDATION_SHEET.md", "w") as fh:
    fh.write("# Manual validation sheet — PER role fidelity\n\n")
    fh.write("240 messages, stratified by role x actor x benchmark x correctness.\n")
    fh.write("For each: does the message honour the named contract clause? y/n/unclear.\n\n")
    for i, r in S.head(240).iterrows():
        fh.write(f"\n---\n## [{i}] {r.sender} | {r.actor_model_id} | {r.benchmark_id} "
                 f"| final_correct={r.final_correct} | stage={r.stage}\n")
        auto = {c: r[c] for c in cols[9:20] if pd.notna(r[c])}
        fh.write(f"AUTO: {auto}\n\n```\n{str(r.content)[:1800]}\n```\n")
print(f"\nwrote annotation sheet to notes/VALIDATION_SHEET.md")
