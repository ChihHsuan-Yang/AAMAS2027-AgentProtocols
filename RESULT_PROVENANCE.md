# Result provenance — AAMAS 2027

Every number in the manuscript must be traceable to a run, a script, and a
commit. This file is the index. **If a number is not here, it does not go in
the paper.**

## Runs

| run id | file | cells | status |
|---|---|---|---|
| `main-n1600-v2` | `experiments/results/main/campaign_v2.jsonl` | gpt-oss-120b & gemma-4-31B × arms A/B/C, Omni-MATH | in flight (7,700+/9,600) |
| `armCp-n400` | `experiments/results/main/armCp.jsonl` | both actors × arm C′, n=400 | **complete (800)** |
| `actor3-n400` | `experiments/results/main/actor3.jsonl` | Llama-3.3-70B × A/B/C | in flight (~150/1,200) |
| `main-n1600` (v1) | `campaign_v1_TRUNCATION_BUG.jsonl` | — | **QUARANTINED**, never pooled (D8) |
| smoke v1/v2 | `smoke_v1_prefix_PREFIX_BUG.jsonl` | — | **QUARANTINED** (pre-fix validators) |

Backend: **`sophia_vllm` for every trajectory** — verified, no cell straddles
backends (closes the backend-straddle TODO).

## config_version audit — POOLING IS VALID, verified not assumed

Two hashes appear: `e3afa39849c1b980` (arms A/B/C, both reference actors) and
`231b8c4fe205d04b` (arm C′, and all Llama-3.3 cells).

- The reference actors' A/B/C cells are **entirely** `e3afa398`; Llama-3.3 is
  **entirely** `231b8c4f`. Zero (actor, arm, problem, role) keys appear under
  both, so **no within-actor A/B/C comparison mixes versions**.
- The one cross-version comparison is **C′ vs C**. I diffed the hashed files
  between the two launch commits (`60fc60d` → `8420b8d`): the change is
  **purely additive** — new `CP_*` templates plus the VISIBILITY correction.
  **No `C_*` prompt and no `MAX_*` knob changed.** Both ran under
  MAX_TOKENS 8192, MAX_ACTOR_CALLS 30, MAX_EVALUATOR_CALLS 6,
  MAX_REGENERATIONS 3. C′ vs C is therefore a valid comparison.

## Scripts → results

| script | produces |
|---|---|
| `experiments/make_manifest.py` | deterministic problem manifests (n=25/400/1600, sha recorded in each) |
| `experiments/runner.py` + `schemas.py` + `prompts.py` | all trajectories |
| `analysis/scripts/x1_analyze_campaign.py` | pre-registered P1-P5, Holm-corrected |
| `analysis/scripts/x2_campaign_tables.py` | manipulation check, attrition, enforcement, C′, collapse, paired contrasts |
| `analysis/scripts/mk_fig1_dissociation.py` | Figure 1 + the numbers behind it |
| `scripts/smoke_gates.py` | the 15 launch gates |

## Headline numbers and their source

| quantity | value | source |
|---|---|---|
| first-pass collapse, Arm B | gpt-oss **0.698**, gemma-4 **0.000** | mk_fig1 / audit round 2 |
| paired transition, gpt-oss diff→collapsed | n=879, **+0.0171 [+0.0023,+0.0319]** | F10 |
| gemma-4 diff→diff | n=1266, **−0.0292 [−0.0450,−0.0134]** | F10 |
| gpt-oss whole-arm B−A (**null**) | **+0.0078 [−0.0102,+0.0259]** | F10 risk-3 check |
| mechanism: gemma-4 recovery | **0.490 → 0.045** (first-pass 0.809→0.809) | F11 |
| single-agent guard | **+0.0248 [+0.0072,+0.0424]** | F10 §12 |
| Arm C answer-authorship | **1.000** every cell | x2 manipulation table |
| difficulty strata (diff→collapsed) | HARD +0.041 / MED +0.046 / EASY +0.002 | F10 risk-2 |

## Known limits carried into the paper
- temperature 0 is **not** deterministic on this endpoint (3 distinct outputs
  from 3 identical requests) — no per-trajectory claim is made.
- the retry loop is **oracle-gated** (the evaluator sees gold); "recovery"
  means recovery *with* an oracle signal.
- Llama-3.3 accuracy is 0.22-0.35, far below the other two: reported as a third
  collapse profile, **not** used for a collapse-vs-role-value relationship.
