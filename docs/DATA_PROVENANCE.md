# Data provenance: construction, eligibility, validity, and where the data lives

Hand-written, unlike the generated files in `docs/`, because these are
*decisions* rather than measurements. Every rule below names the code that
implements it, the guard that tests it, and the artifact where its effect is
visible — so none of it has to be reverse-engineered from the runner.

Back to [the project README](../README.md) ·
[artifact map](PAPER_ARTIFACT_MAP.md) ·
[trace availability](TRACE_AVAILABILITY.md) ·
[invalid and superseded](INVALID_AND_SUPERSEDED.md)

---

## Where the data is, and what is canonical

| artifact | unit | count | location | status |
|---|---|---|---|---|
| Omni-MATH campaign | trajectory | **11,600** over 1,600 distinct problems | `experiments/results/FROZEN/` (local, gitignored) + HF `raw/` | **CANONICAL** — every main-paper number |
| SciBench campaign | trajectory | **2,296** over the complete 574-problem matched slice | `experiments/results/xdomain/FROZEN_SCIBENCH/` + HF `raw/` | **CANONICAL** — the cross-domain claim |
| adjudication | trajectory (3 repetitions each) | **171 trajectories, 513 verdict rows** | `adjudication/` — **in git** | CANONICAL for the collapse second opinion; outcome-blind, **not** condition-blind |
| single-agent comparator | trajectory | external corpus | outside this repo, local only | **DIAGNOSTIC** — a directional guard only; its two actor arms came from different source commits |
| grader noise floor | evaluator call group | 2,790 groups | derived, `[T6]` | CALIBRATION |
| `campaign_v1`, `smoke_v1` | — | — | `experiments/results/{main,smoke}/` | **QUARANTINED** — see [INVALID_AND_SUPERSEDED.md](INVALID_AND_SUPERSEDED.md) |

**Hugging Face.** `AgentsSci/AAMAS2027-Roles`, **v1.1.0**, **PRIVATE**.
8 parquet tables (5 Omni-MATH, 3 SciBench), 4 raw JSONL traces, prompts,
configs, manifests, checksums. Last verified **2026-10-02** by cold
download: `shasum -c CHECKSUMS.txt` 52/52 OK, private confirmed three ways
(authenticated API `private=True`; anonymous fetch of both `README.md` and
`data/trajectories.parquet` → 401; positive control `openai/gsm8k` → 200).

**Withheld, and why.** Problem text and gold answers are not redistributed
— only `problem_uid`, which joins to the public benchmark. Omni-MATH-2 is
Apache-2.0 and SciBench is MIT (© 2023 Xiaoxuan Wang); the artifact is
mixed-licence and declares both. The repository must stay private through
double-blind review: a public dataset matching the paper's numbers is a
deanonymization path even with no pointer from the paper.
`scripts/preflight_public.py` **fails by design** until institution-naming
rows are sanitized after acceptance. Do not weaken it to make it pass.

Field-by-field availability, measured from the rows rather than asserted:
[TRACE_AVAILABILITY.md](TRACE_AVAILABILITY.md).

---

## What a unit of analysis is

| term | definition | where it lives |
|---|---|---|
| **problem** | one benchmark item, identified by `problem_uid`. Problem text and gold answer are **not** redistributed; the uid joins to the public benchmark | `experiments/manifest_*.json` |
| **trajectory** | one complete run of one protocol on one problem by one actor: the atomic row | one JSONL line |
| **cell** | (actor × condition), the unit a denominator is quoted over | `MANIFEST.json` → `cell_census` |
| **deliberation cycle** | one Planner→Executor→Reviewer pass. Budget is 6 per trajectory **by construction, in every condition** | `budget.max_outer_rounds × inner_rounds` on each row |
| **submission** | a cycle ending in Reviewer approval, which fires the evaluator | `evaluator_history` entries |
| **revision** | a cycle that changes the held answer without submitting | derived; `[T16]` in the canonical output |

Pairing is **always by `problem_uid`**: every condition ran the same problems,
so every contrast in this paper is paired. A number quoted over a different
population than the one it is compared against is the error this project has
made most often, which is why every table names its population in the header
rather than in a footnote.

## The two denominators, and why they are not interchangeable

| population | definition | used for |
|---|---|---|
| **marginal** | every trajectory in the cell; each condition on its own denominator | descriptive rates |
| **paired** | only problems first-pass wrong under **both** conditions compared; one shared denominator | **every reported $p$-value** |

Significance is exact McNemar on discordant pairs — seed-free. An earlier
version of this project read significance off a bootstrap CI bound, which
was seed-dependent: the same contrast read SIG in 62% of seeds. That defect
appeared at four separate sites and is recorded in `STATISTICAL_AUDIT.md`.

## Eligibility, validity, and what is never silently zero

| rule | decided | implementation | guard |
|---|---|---|---|
| **A trajectory that fails to parse counts as INCORRECT, not dropped** | pre-registered, before any data | `analysis/scripts/FINAL_TABLES.py` `fin_prereg()` | the enforced condition's attrition table, `[T7]` |
| **The recovery denominator is a recorded *first* evaluator verdict of incorrect** — including trajectories that later died in regeneration | corrected after audit | `is_fpw()` | asserted: `(1 − firstpass) × n_judged == n_fpw` |
| **`judged()` ≠ `graded()`** — a trajectory can receive a verdict and never be graded | — | both defined in `FINAL_TABLES.py` | the distinction is why the enforced rates do not compose into its accuracy column |
| **A regenerated emission is the one analysed**; the rejected one is logged with its reason | pre-registered | `experiments/runner.py` | `regeneration_events[].violated_constraint` |
| **No condition is dropped after seeing results.** A failed manipulation check is reported as the result | pre-registered | — | `\Pone` failed and is reported as a failure |
| **An absent value is never scored as zero** | standing rule | — | the two places this was violated are in `STATISTICAL_AUDIT.md`, both repaired |

The pre-registration is `PREREGISTRATION.md`; it was frozen before any
intervention data existed, and `paper/tables/prereg_endpoints.tex` reports
what became of every endpoint, including the primary one, which is **null**.

## How each condition is constructed

All conditions share topology, call budget, decoding (temperature 0,
identical `max_tokens`), retry budget, verifier, verifier prompt, stopping
rule and grading. Only what each agent is told it is, or what its interface
permits, varies.

| condition | construction | code |
|---|---|---|
| **role-structured** (`A`) | role prompts as ordinarily written | `build_messages()`, `arm == "A"` |
| **role-free** (`B`) | identical topology; all three agents get one generic prompt; role names retained for routing only | `arm == "B"` |
| **structurally enforced** (`C`) | specialization enforced by schema: the Planner has **no answer field**, the Executor receives the parsed plan object rather than raw text, the Reviewer can only promote the Executor's answer by reference | `experiments/schemas.py`, `validate_planner/executor/reviewer` |
| **context-restored enforcement** (`Cp`) | `C` with shared history restored, to separate enforcement from context loss | `cp = (arm == "Cp")` |

Matching `Cp` to the baseline exactly would require feeding raw prose back
in, which dissolves the constraint that defines the condition. It is
therefore a **partial** control and the paper says so.

## The one asymmetry we do not smooth

The evaluator fires on Reviewer approval, so a team that submits more
*consumes* more oracle verdicts even under an identical cap. The role-free
team draws 1.95 / 1.85 / 3.82 evaluator calls per trajectory against the
role-structured team's 1.11 / 1.35 / 1.03.

**This runs against our result** and is reported in the Intervention section
for that reason: a ground-truth verdict is the only external information in
the loop, and the condition we find worse receives more of it in every
actor.

## Known instrumentation defects, and their direction

Each is disclosed in the paper rather than silently repaired. Direction
matters: a defect that flatters the claim and one that works against it
require different treatment.

| defect | direction | handling |
|---|---|---|
| **F13** — visible text truncated relative to hidden reasoning, one actor, one condition | affects a *behavioral* measure, not an outcome | that actor's planner-behavior claim withdrawn |
| **F18** — `correct` grades the last answer *submitted*; `final_answer` records the last answer *held* | **against us**: repairing it *widens* every recovery gap | pre-registered scoring kept as primary; the repair reported |
| **recovery denominator** excluded trajectories that died in regeneration | **for us**: inflated the enforced condition | repaired; two of three paired p-values did not survive |
| **adjudication condition leak** | would flatter the collapse claim | the paper does **not** call the adjudication blinded, and the collapse claim rests on mechanical measures |

## Why the frozen snapshot cannot be regenerated

Temperature 0 is **not** bit-deterministic on this endpoint. A re-run would
produce different rows, so the snapshot is irreplaceable rather than
reproducible, and its sha256 manifest is the only thing that makes a
reported number checkable. Denominators do not change after a freeze; a
changed denominator is a *re-freeze* with a new manifest and a recorded
reason, never a silent edit.
