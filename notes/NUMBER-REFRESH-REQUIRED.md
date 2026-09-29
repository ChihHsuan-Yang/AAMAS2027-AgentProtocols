# Number refresh required before submission (2026-09-29)

The campaign is still writing (7,823/9,600 at time of writing). Several figures
in the manuscript were computed on earlier cuts and have drifted. **None of
them changes a conclusion**, but every one must be refreshed from the final
data before the PDF is handed over.

## Drift found so far (Master, verified against current JSONL)

| quantity | in paper | current data | conclusion changed? |
|---|---|---|---|
| P2 soft-role, gemma-4 | 0.982 | **0.993** | no |
| P2 soft-role, gpt-oss | 0.604 | **0.818** | no |
| count-matched collapse, gpt-oss B | 0.698 | 0.691-0.693 | no |
| C′−C, gemma-4 | +0.0179 | +0.0232 | no (both null) |
| C′−C, gpt-oss | −0.0115 | +0.0000 | no (both null) |
| P4 interaction | −0.0073 | −0.0065 | no (both null) |

The gpt-oss P2 drift (0.604 → 0.818) is the largest and is worth understanding
rather than just patching: early-completing trajectories over-represent the
short, fast ones where the planner answers immediately. As the slow tail lands,
soft-role answer-abstention rises. **The Arm C claim is unaffected — it is
1.000 in every cell at every cut**, which is the number the manipulation check
rests on.

## Confirmed exact at the current cut
- Arm C / C′ answer-authorship compliance: **1.000 in all 5 cells** (n=392-1,304)
- Planner emits an answer in Arm C: **0.000**, all three actors
- funcColl Arm B: gemma-4 **0.975**, gpt-oss **0.845**, Llama-3.3 **0.915**
- funcColl Arm A: gemma-4 0.000, gpt-oss 0.117, Llama-3.3 0.000

## Procedure before handover
1. Wait for campaign completion (or freeze at a stated n).
2. Re-run `analysis/scripts/x2_campaign_tables.py` and `mk_fig1_dissociation.py`.
3. Re-run `adjudication/analyze.py` on the completed verdict set.
4. Diff every numeric literal in `paper/sections/*.tex` against the refreshed
   outputs; update and record old→new in `RESULT_PROVENANCE.md`.
5. **State the final n in the paper** and freeze. No number ships from a cut
   that is not the reported n.
