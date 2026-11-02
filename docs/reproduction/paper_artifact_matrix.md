# Paper artifact matrix

Every table and figure in the paper, the script that generates it, what it
reads, and the reproduction level that regenerates it.

- **Level A** regenerates from the intermediate files committed in
  `analysis/out/` (`make smoke`, `make figures`).
- **Level B** re-derives those intermediates from the trajectories
  (`make data numbers tables`).

All generators live in `analysis/scripts/`.

## Data

Every trajectory file is pinned by sha256 in a committed manifest.
`scripts/place_data.py` finds each one by hash and links it into place.

| Data | Rows | Pinned by | Linked to |
|---|---:|---|---|
| Omni-MATH frozen campaign: `campaign_v2`, `actor3`, `armCp` | 11,600 | `experiments/results/FROZEN/MANIFEST.json` | `FROZEN/`, `hf_frozen/raw/` |
| SciBench frozen campaign: `scibench_AB` | 2,296 | `experiments/results/xdomain/FROZEN_SCIBENCH/MANIFEST.json` | `xdomain/FROZEN_SCIBENCH/`, `hf_frozen/raw/` |
| RF (`Bf`) in five cells, gemma-4 RS re-run (`bridgeA`), forced submission (`afs`) | 5,548 | `experiments/results/bf/MANIFEST_BF.json` | `bf/` |
| Second RF run, gemma-4 (both domains) + RS bridge | 2,574 | `experiments/results/bf/chain2/MANIFEST.json` | `bf/chain2/` |
| Collapse adjudication | 171 judged | in git | `adjudication/` |
| Problem set with gold answers; single-agent comparator | — | `AgentsSci/IEEE2026_BigData_MAS-4-Science-Matching` | `analysis/hf_cache/release/` |

## Intermediate files

| File in `analysis/out/` | Written by | Reads |
|---|---|---|
| `FINAL_TABLES_OUTPUT.txt`, `FIGDATA.json` | `FINAL_TABLES.py` | frozen campaign (both domains), adjudication, problem set |
| `FIGDATA_BF.json`, `BF_TABLES_OUTPUT.txt` | `bf_numbers.py` | frozen campaign, first RF run, RS re-run, problem set |
| `FIGDATA_BF_chain2.json`, `BF_TABLES_OUTPUT_chain2.txt` | `bf_numbers.py --bf-dir experiments/results/bf/chain2 --suffix _chain2` | frozen campaign, second RF run, problem set |
| `FIGDATA_GATE.json`, `BF_GATE_OUTPUT.txt` | `bf_gate.py` | frozen campaign, first RF run, forced submission, problem set |

## Reading rules

- **Three bodies of data, never pooled.** The frozen campaign (RS `A`,
  RF⁻ `B`, enforced `C`/`Cp`, both domains) is one record. The first RF run
  (`Bf` in all five cells, with the gemma-4 RS re-run and the forced-submission
  run `Afs`) is the paper's main comparison. The second RF run (the two gemma-4
  `Bf` cells and their RS re-run) is a replicate and appears only in Table S3.
- **`B` is not `Bf`.** In the frozen campaign the role-free team never
  received the evaluator's feedback (`B`, RF⁻); the post-freeze control
  delivers it (`Bf`, RF). RS against RF⁻ (Table S2, Table S7) and RS against
  RF (Table 2) answer different questions.
- **Marginal rates and paired comparisons are different numbers.** A recovery
  rate is computed over each condition's own first-pass-wrong trajectories; a
  paired comparison (exact McNemar) uses only the problems that both
  conditions first answer wrongly, so its denominator is smaller.
- **Forced submission is one exploratory intervention**: gemma-4 on 400
  Omni-MATH problems (Figure 2C, Table S6). It is not part of the five-cell
  comparison.

## Main paper

| Item | Content | Generator | Reads | Level |
|---|---|---|---|:--:|
| Figure 1 | one deliberation cycle; where feedback enters per condition | `mk_fig_pipeline.py` | — | A |
| Table 1 | functional collapse per actor | `mk_tables.py` | `FINAL_TABLES_OUTPUT.txt` T1, T23; `FIGDATA_BF.json` | B |
| Figure 2 | first pass, recovery, budget use | `mk_fig1_bf.py` | `FIGDATA.json`, `FIGDATA_BF.json`, `FIGDATA_GATE.json` | A |
| Table 2 | RS vs RF in all five cells | `mk_table_main.py` | `FIGDATA_BF.json`, `FIGDATA_GATE.json` | A |

## Supplement

| Item | Content | Generator | Reads | Level |
|---|---|---|---|:--:|
| Table S1 | functional collapse, all three measures | `mk_tables.py` | T1, T18, T20, T23 | B |
| Figure S1 | per-role answer assertion | `mk_fig_supp.py` | see note below | A |
| Table S2 | first pass and recovery, RS vs RF⁻ | `mk_tables.py` | T1, T3, T4 | B |
| Table S3 | the two gemma-4 RF runs | `mk_bf_replication.py` | `FIGDATA_BF.json`, `FIGDATA_BF_chain2.json` | A |
| Table S4 | where the Reviewer declines | `mk_gate_table.py` | `FIGDATA_GATE.json`, `FIGDATA_BF.json` | A |
| Figure S2 | recovery against the number of evaluator verdicts received | `mk_fig_supp.py` | see note below | A |
| Figure S3 | two robustness checks: the verdict-matched difference (a) and the pre-registered interaction P4 (b) | `mk_fig_supp.py` | see note below | A |
| Table S5 | verdict-matched robustness | `mk_robust_table.py` | `FIGDATA_GATE.json` | A |
| Table S6 | forced submission | `mk_afs_table.py` | `FIGDATA_GATE.json` | A |
| Table S7 | SciBench replication | `mk_tables.py` | `xdom_analyze.py` on the SciBench trajectories | B |
| Figure S4 | structural enforcement | `mk_fig_supp.py` | see note below | A |
| Table S8 | structural enforcement | `mk_tables.py` | T1, T2, T7, T11 | B |
| Table S9 | pre-registered endpoints, Holm correction | `mk_tables.py` | T2, T14, T29; `stat_audit_a7_power.py` on `analysis/audit/` | B |
| Table S10 | recovery by context quartile | `mk_tables.py` | T22 | B |
| Table S11 | budget-matched single agent | `mk_tables.py` | T17 | B |

`T` numbers are section labels in `FINAL_TABLES_OUTPUT.txt`. `mk_fig_supp.py`
draws all four supplement figures from `FINAL_TABLES_OUTPUT.txt`,
`FIGDATA_BF.json`, `FIGDATA_GATE.json` and `paper/tables/prereg_endpoints.tex`.
