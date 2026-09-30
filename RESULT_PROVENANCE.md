# Result provenance — AAMAS 2027

Every number in the manuscript must be traceable to a run, a script, and a
commit. **Rewritten 2026-09-30 against the frozen snapshot.**

> ## The whole of this file, in one line
>
> **Final numeric truth = `experiments/results/FROZEN/` + `analysis/scripts/FINAL_TABLES.py`.**
>
> Nothing else is a provenance. A number that cannot be produced by running
> that script against that directory does not go in the paper.

This file used to carry a "headline numbers and their source" table — a
hand-maintained list of figures copied out of intermediate analyses. **That
table has been deleted, not updated.** Every number in it was computed on a
pre-freeze cut and at least four of them supported claims that are now on the
dead list (`CLAIM_STATUS.md` §FALSIFIED). Maintaining a second copy of the
numbers is the defect, not the staleness: a number typed into a second file
stops tracking the first. The current values live in
`analysis/out/FINAL_TABLES_OUTPUT.txt` and are regenerated, never transcribed.

---

## The frozen snapshot

```
experiments/results/FROZEN/
  MANIFEST.json      frozen_at 2026-09-30T10:09:30.201557   total_rows 11600
  campaign_v2.jsonl  9,600 rows  227,526,687 B  sha256 e4e53cb117d91129991ce2fe87e336e1…
  actor3.jsonl       1,200 rows   46,037,025 B  sha256 fa22a446d5314bb67b1c6a6444b511ee…
  armCp.jsonl          800 rows   23,627,781 B  sha256 038e08aec4d4aee166106a6325309dfe…
```

Freeze commit `74ab7da`. **All three hashes, row counts and byte counts
verified 2026-09-30.** The three files are byte-identical to their copies in
`experiments/results/main/` (verified). They are **not in git** — see
`PROJECT_PATHS.md`.

Cells: gemma-4 A/B/C 1600 each + Cp 400; gpt-oss A/B/C 1600 each + Cp 400;
Llama-3.3 A/B/C 400 each. 11 cells, 11,600 rows.

## Runs

| run id | file | cells | status |
|---|---|---|---|
| `main-n1600-v2` | `campaign_v2.jsonl` | gpt-oss-120b & gemma-4-31B × arms A/B/C, Omni-MATH | **complete, 9,600/9,600** |
| `armCp-n400` | `armCp.jsonl` | both reference actors × arm C′, n=400 | **complete, 800/800** |
| `actor3-n400` | `actor3.jsonl` | Llama-3.3-70B × A/B/C, n=400 | **complete, 1,200/1,200** |
| `main-n1600` (v1) | `campaign_v1_TRUNCATION_BUG.jsonl` | — | **QUARANTINED**, never pooled (D8) |
| smoke v1 | `smoke_v1_prefix_PREFIX_BUG.jsonl` | — | **QUARANTINED** (pre-fix validators) |
| smoke v3 | `smoke_v3.jsonl` | 78 trajectories | the launch-gate run; 15/15 gates pass |

Backend: **`sophia_vllm` for every trajectory** — verified, no cell straddles
backends. Launch commands for all three runs are in `README.md` §7 of the
cold-start handoff, reconstructed from the run logs.

## config_version audit — pooling is valid, verified not assumed

Two hashes appear: `e3afa39849c1b980` (arms A/B/C, both reference actors) and
`231b8c4fe205d04b` (arm C′, and all Llama-3.3 cells).

- The reference actors' A/B/C cells are **entirely** `e3afa398`; Llama-3.3 is **entirely** `231b8c4f`. Zero `(actor, arm, problem, role)` keys appear under both, so **no within-actor A/B/C comparison mixes versions**.
- The one cross-version comparison is **C′ vs C**. The hashed files were diffed between the two launch commits (`60fc60d` → `8420b8d`): the change is **purely additive** — new `CP_*` templates plus the VISIBILITY correction. **No `C_*` prompt and no `MAX_*` knob changed.** Both ran under MAX_TOKENS 8192, MAX_ACTOR_CALLS 30, MAX_EVALUATOR_CALLS 6, MAX_REGENERATIONS 3. C′ vs C is therefore a valid comparison.

T24 confirms **one distinct budget** across all 11,600 rows:
`{max_actor_calls 30, max_evaluator_calls 6, max_regenerations 3,
max_transport_retries 4, max_outer_rounds 3, inner_rounds 2, temperature 0.0,
max_tokens 8192}`.

## Scripts → results

| script | produces | reads |
|---|---|---|
| **`analysis/scripts/FINAL_TABLES.py`** | **T0–T28 — every manuscript number** | **`FROZEN/` only** (+2 labelled external sources) |
| `analysis/scripts/mk_figstyle.py` + `mk_fig1_dissociation.py` | Figure 1, three variants | `analysis/out/FIGDATA.json` (written by T28 from `FROZEN/`) |
| `adjudication/analyze.py` | the blinded-adjudication result (T23's source) | `adjudication/VERDICTS.jsonl` + `KEY.jsonl` |
| `scripts/verify_paper_numbers.py` | independent cross-check | `experiments/results/main/` (the live tree) |
| `scripts/smoke_gates.py` | the 15 launch gates | a smoke JSONL |
| `experiments/make_manifest.py` | deterministic problem manifests | the sibling release parquet |
| `experiments/runner.py` + `schemas.py` + `prompts.py` | all trajectories | the live endpoint |
| `analysis/scripts/stat_audit_*.py` (18) | the adversarial audit behind `STATISTICAL_AUDIT.md`, incl. the **corrected** Arm C recovery | `FROZEN/` |
| `analysis/scripts/{d,r,x}*.py` (~40) | **exploratory history — NOT provenance** | older cuts, `main/` |

The `{d,r,x}` scripts are the audit trail. Their printed numbers may predate a
correction, and several implement metric definitions that were later replaced.
Read them to understand how a conclusion was reached; never to source a
current number.

## Two tables that read outside the frozen snapshot

Both label themselves in their own output. Wherever either is used, that
provenance must travel with it.

| table | source | verified 2026-09-30 |
|---|---|---|
| **T17** budget-matched single-agent control (claim A9) | `…/IEEE-BigData-SciAgentTrace/analysis/hf_cache/release/data/trajectories/part-00000.parquet`, `protocol_id='single_agent'`, benchmark omnimath2, joined by `problem_uid`. 9,195 source rows, file sha256 `d56dc5bdab0134fd…` | path exists, 3.7 MB |
| **T23** blinded adjudication (claim A1) | `adjudication/VERDICTS.jsonl` sha `a6d18adabbd3f547…`, `KEY.jsonl` sha `94fa8ee76b532948…`, `RUBRIC_v1.md` sha `4f624de5b1073940…`, `ITEMS_blinded.jsonl` sha `997d0185133a1205…` | all four hashes **verified** |

If the sibling project moves, T17 prints `UNAVAILABLE: <error>` and everything
else still runs.

## Problem manifests

Deterministic: `omnimath2` rows from the released parquet, filtered to rows
with both `problem_text` and `answer`, sorted by `problem_uid`, seeded sample
(seed `20261008`), sorted again. Every arm and actor sees **the same problems**.

| manifest | n | recorded sha256 | verified 2026-09-30 |
|---|---|---|---|
| `experiments/manifest_omnimath2_n1600.json` | 1600 | `39cdeeecffc383a7…` | **recomputes exactly** |
| `experiments/manifest_omnimath2_n400.json` | 400 | `94955e7f65332258…` | **recomputes exactly** |
| `experiments/manifest_omnimath2_n25.json` | 25 | `04009d74a21bc13a…` | **recomputes exactly** |

## Two scoring conventions, both reported

Per `PREREGISTRATION.md`:

- **PREREG (primary)** — trajectories that never produced a graded answer are scored 0: *"failing to parse are counted as incorrect, not dropped."*
- **AS-GRADED (sensitivity only)** — those trajectories are dropped. Carries **8–17% one-sided attrition in Arm C**.

**They disagree in sign for Arm C** (gemma-4 C−A: −0.0225 prereg vs +0.0190
as-graded). Quoting as-graded as the headline would reproduce the
pre-declared NOT-SUBMIT pattern — see `notes/FINDING-24-P4-NOTSUBMIT-CHECK.md`.
Both must appear, with attrition disclosed, because a reader who re-derives
either needs to find the other.

## One frozen-output column is superseded and still prints

`STATISTICAL_AUDIT.md` (2026-09-30) reproduced T1/T2/T4/T7 **exactly** and
found no arithmetic error, but two reported quantities are wrong as
*constructed*:

| column | problem | where the correct value lives |
|---|---|---|
| **T1 Arm C `recovery`** | Denominator `graded(r) and fp==0` dropped 173 trajectories with a first *incorrect* verdict that then died in regeneration. All 173 have `fp==0` structurally, so they belong in the denominator by the paper's own definition and score 0 under prereg scoring. | **FIXED in commit `ba28977`.** T1 now prints **0.314 / 0.395 / 0.139**; the pre-fix 0.412/0.461/0.150 is stale wherever it still appears. Two of three paired A-vs-C p-values were lost. |
| **T27 noise-floor ratio** ("3.9x clears") | Dividing an effect size by a grader-disagreement rate is not a valid operation, and the noise largely cancels in a paired contrast. | **STILL PRINTS — do not quote it.** Propagate the per-call rate into the bootstrap: `analysis/scripts/stat_audit_a5_noisefloor.py`. Verdicts unchanged. |

Arms A and B recovery moved by ≤ 0.002 and are unaffected; the gemma-4
headline survived six separate attacks.

Also open from the audit: **the methods assert a Holm correction that the code
never applies** (`holm` appears 0 times in `FINAL_TABLES.py` and 0 times in its
output). Applying it changes no verdict — so the fix is to run it, not to
reword it.

## Known limits carried into the paper

- **Temperature 0 is not deterministic on this endpoint** (3 distinct outputs from 3 identical requests). No per-trajectory claim is made — and the frozen data therefore cannot be regenerated by re-running.
- **The retry loop is oracle-gated** (the evaluator sees gold). "Recovery" means recovery *with* an oracle signal. T25: **0 cells recover before the first oracle verdict**, all nine.
- **Grader noise floor 0.0086** group-level, range 0.0020–0.0086 across estimators (T6). Do **not** quote a ratio against it. Propagating the per-call disagreement rate into the bootstrap gives gemma-4 [−0.0488,−0.0175] SIG, gpt-oss null, Llama null.
- **F18 scoring defect**: the recorded grade is the grade of the last *submitted* answer, not the answer the team last *held*. 409 mismatched among first-pass-wrong, **54 demonstrably under-credited**; positive control 0 of 10,734 (T19). It penalises the revising arms, i.e. it works *against* the headline.
- **F13 logging defect**: gpt-oss's Arm B planner is uninstrumented (2.85 visible ch/s vs 195 in its own Arm A) (T9, T26). Bounds both the duplication claim and any collapse-*mode* reading.
- **Llama-3.3 accuracy is 0.307** vs ~0.80 for the other two: reported as a third collapse profile, **never** used for a collapse-vs-role-value relationship. Its null recovery is a **genuine null, not a floor** — Arm C moves it (0.096 vs 0.009, p=3.8e-06).
- **The evaluator is also an actor** (`openai/gpt-oss-120b`). R-10 evaluator independence remains **UNTESTED**.
- **One benchmark, one domain** (omnimath2, math).

---

## Sample definitions and denominators (audited 2026-09-30)

Full audit: `analysis/out/SAMPLING_AUDIT.md`
Reproducible by: `python3 analysis/scripts/audit_sampling.py`
Figure: `figures/audit_sampling_representativeness.png`

### OmniMath2 — 4,181 available, 1,600 run

| | |
|---|---|
| full matched pool | **4,181** |
| scientific run | **1,600** (38.3%) |
| seed | **20270101** |
| drawn by | `runner.load_problems(n=1600, seed=20270101)` |
| manifest | `experiments/manifest_omnimath2_n1600.json` |

**Uniform random sample of the whole pool.** Not tier-specific, not
difficulty-stratified, not purposive. Verified: all 1,600 distinct problems
in the frozen campaign match the seed-20270101 draw exactly, 1600/1600.

**Representativeness — the sample is not distinguishable from the pool:**

| test | result |
|---|---|
| difficulty_score, two-sample KS | **D=0.0251, p=0.449** |
| subset (competition source), chi-square | **chi2=58.3, dof=46, p=0.106** |
| mean difficulty_score | 4.9444 full vs 4.9524 selected (+0.008) |
| median / quartiles | identical (4 / 5 / 6) |

`difficulty_tier` and `question_type` are **entirely null** for this
benchmark (0/4,181), so no tier table exists; `difficulty_score` (27 distinct
values, 100% populated) is the difficulty axis.

### SciBench — 692 upstream, 580 released, 574 matched, **all 574 run**

| | |
|---|---|
| upstream published benchmark | 692 |
| present in the SciAgentTrace release | 580 |
| carrying the `text_only` slice | **574** |
| **run in this campaign** | **574 x 2 actors x 2 arms = 2,296** |

**`574 matched` is NOT `574 total benchmark`.** No sub-sampling was applied:
the entire matched slice was run.

- **692 -> 580**: **not recoverable from this release.** Excluded rows are
  absent from the table and carry no reason code. An earlier draft of this
  audit asserted a reason; that was an inference presented as a measurement
  and was removed. Tracked as P2; it affects no denominator the paper reports.
- **580 -> 574**: six rows carry only the `full` slice, not `text_only`,
  listed individually in the audit. They are a **disjoint set** from the six
  `conflicting_source_id_disambiguated` rows — two independent subtractions,
  not the same six counted twice.
