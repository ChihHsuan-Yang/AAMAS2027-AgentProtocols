# Beyond Division of Labor: How Roles Shape Feedback and Recovery in Multi-Agent Systems

**Preprint · October 2026**

[![Project page](https://img.shields.io/badge/Project-Page-1f6f8b)](https://chihhsuan-yang.github.io/AAMAS2027-AgentProtocols/)
[![Paper](https://img.shields.io/badge/Paper-PDF-333333)](https://chihhsuan-yang.github.io/AAMAS2027-AgentProtocols/paper.pdf)
[![Supplement](https://img.shields.io/badge/Supplement-PDF-333333)](https://chihhsuan-yang.github.io/AAMAS2027-AgentProtocols/supplement.pdf)
[![HF dataset](https://img.shields.io/badge/%F0%9F%A4%97%20Dataset-AAMAS2027--Roles-ffcc4d)](https://huggingface.co/datasets/AgentsSci/AAMAS2027-Roles) **[TODO: dataset is private]**
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)

Chih-Hsuan Yang¹\*, Xinyang Li²\*, Rajeev Thakur¹, Feng Yan²
¹ Argonne National Laboratory, Lemont, IL, USA  ·  ² University of Houston, Houston, TX, USA
\* Equal contribution

---

Multi-agent LLM systems assign roles such as Planner, Executor and Reviewer,
and the role diagram is usually read as the mechanism: roles divide the work,
so roles make the team better. We test that reading by **deleting every role
instruction** while holding the agents, topology, call budget and evaluator
fixed. Roles do divide the work: without them, every agent asserts its own
final answer and the division of labor collapses. Yet the team's first answer
is no worse. What roles change is **who decides when the team asks for
feedback**. The role-structured Reviewer withholds approval, so the team
submits less often, receives fewer corrective verdicts, and recovers from a
failed first answer less often. Force it to submit every cycle and the gap
closes.

![Figure 2 of the paper. (A) First-pass accuracy is about equal with and without roles. (B) Recovery after a failed first answer is highest for the role-free team with feedback in all five actor–benchmark cells. (C) For gemma-4 on Omni-MATH, the role-structured team spends most of its six-cycle budget on internal cycles that never submit; forcing a submission every cycle reverses this.](docs/assets/fig1_main.png)

## Key finding

On Omni-MATH with gemma-4-31B-it, the role-free team with feedback recovers
**0.609** of its failed first answers against **0.222** for the
role-structured team. Of the 236 problems both teams first answer wrongly,
**89 are recovered only without roles and 4 only with them** (exact McNemar
*p* = 6.2×10⁻²²), and final accuracy rises from **0.846 to 0.921**. The
role-free team recovers more in **all five** actor–benchmark cells.

The gap comes from the submission gate. Per failed trajectory, the
role-structured team submits **1.27** times against **3.20**, and 84 of its
316 failed trajectories never submit at all. Keeping the role prompts byte for
byte but forcing a submission every cycle lifts gemma-4's recovery from
**0.198 to 0.613** on 400 problems, matching the role-free team's 0.549 on
the same problems. Matched on the number of evaluator verdicts (post hoc),
the difference vanishes: pooled **+0.009**, 95% CI [−0.014, +0.033].

Roles govern decision rights and information flow, not only work allocation.
Evaluating a multi-agent organization means measuring its decision policy and
feedback access, not just role fidelity.

## Conditions

All conditions share three agents and one evaluator, the order
Planner → Executor → Reviewer, a grid of six deliberation cycles
(3 outer × 2 inner), a budget of 30 actor and 6 evaluator calls, temperature 0,
`max_tokens` 8192, one pinned vLLM server, and `gpt-oss-120b` as the
evaluator. A PASS ends the trajectory; a FAIL returns a verdict and a repair
hint.

| Condition | Prompts | Where FAIL feedback enters | Who approves submission | Code |
|---|---|---|---|:--:|
| **Role-structured** (RS) | Planner, Executor and Reviewer prompts | each role's advice slot | Reviewer | `A` |
| **Role-free, with feedback** (RF) — *main comparison* | one byte-identical generic prompt for all three agents | `[Evaluator]` entry after the shared history | third agent (`[Agree]`) | `Bf` |
| **Role-free, feedback withheld** (RF⁻) — *diagnostic* | same generic prompt | nowhere | third agent (`[Agree]`) | `B` |
| **Structurally enforced** | typed JSON contracts; the Planner schema has no answer field | each role's advice slot | Reviewer (`accept` promotes the Executor's answer) | `C` |
| **Context-restored enforced** | as enforced, plus the shared history | each role's advice slot | Reviewer | `Cp` |
| **Forced submission** — *exploratory* | RS prompts, byte for byte | each role's advice slot | none: submitted every cycle | `Afs` |

The paper uses the names; code and raw data use the codes.

![Figure 1 of the paper: one deliberation cycle and where the FAIL feedback enters in each condition.](docs/assets/fig_pipeline.png)

**Actors:** `google/gemma-4-31B-it`, `openai/gpt-oss-120b`,
`meta-llama/Llama-3.3-70B-Instruct`. One model plays all three agents.
**Benchmarks:** Omni-MATH (1,600 problems sampled from 4,181; 400 for
Llama-3.3) and the complete 574-problem text-only free-response slice of
SciBench.

## Scope

| Cell | gemma-4 | gpt-oss | Llama-3.3 |
|---|:--:|:--:|:--:|
| Omni-MATH: RS, RF, RF⁻, enforced | 1,600 | 1,600 | 400 |
| Omni-MATH: context-restored enforced | 400 | 400 | — |
| Omni-MATH: forced submission | 400 | — | — |
| SciBench: RS, RF, RF⁻ | 574 | 574 | — |

The RS-versus-RF contrast was pre-registered as secondary; the
pre-registered primary endpoint is null and is reported in the supplement.
The evaluator, `gpt-oss-120b`, is also one of the actors. Each cell is one
realized run at temperature 0. The two gemma-4 RF cells were run twice, and
gemma-4's RS cell was re-run on 400 problems as a drift check; both are in
the supplement.

## Reproducing the paper

| Level | What it does | Command | Time | Needs |
|---|---|---|---|---|
| **A** | regenerate Table 2, the post-freeze supplement tables and every figure from the committed intermediate files | `make smoke`, `make figures` | ~1 min | CPU; nothing to download |
| **B** | re-derive every intermediate from the released trajectories and diff it against the committed record; regenerate every table | `make data numbers tables` | minutes | CPU; ~500 MB download |
| **C** | re-run inference | see below | hours | an OpenAI-compatible vLLM endpoint; does **not** reproduce the frozen numbers bit for bit |

Every analysis script is deterministic: bootstraps are seeded (`20261008`)
and every *p*-value is an exact McNemar test, so each `make` target ends in a
`git diff --exit-code` against the committed files and fails on any
difference. Level C is not deterministic: temperature-0 decoding on a shared
server is not bit-reproducible, which is why the sha256-manifested
trajectories are the record.

### Setup

```bash
git clone https://github.com/ChihHsuan-Yang/AAMAS2027-AgentProtocols.git
cd AAMAS2027-AgentProtocols
make setup                      # .venv with the pinned environment (Python 3.13)
```

Use `make setup PYTHON=/path/to/python3.13` if `python3` is another version.
Every other target runs inside `.venv`; nothing needs activating.

Figures are set in **Libertinus Sans**. `make figures` downloads it once
from the [Libertinus release](https://github.com/alerque/libertinus/releases)
into `.fonts/`; no TeX installation is needed. Run without the font, the
generators fall back to DejaVu Sans, which is wider: labels clip and
`mk_fig_pipeline.py` stops with `table too wide`.

### Level A: regenerate the paper's results (no download)

```bash
make smoke      # offline tests of the RF and forced-submission prompts (no model calls),
                # then Table 2 and Tables S3-S6 from analysis/out/; fails on any byte difference
make figures    # Figures 1, 2 and S1-S4 into paper/figures/
```

Tables regenerate byte for byte. Figures render pixel-identical to the
committed PDFs (checked at 200 dpi); their PDF bytes differ between runs, so
compare them by rendering, not with `git diff`.

### Level B: re-derive every number from the trajectories

```bash
make data       # download both datasets, find every pinned file by sha256, link it in place
make numbers    # FINAL_TABLES.py, bf_numbers.py (both RF runs), bf_gate.py -> analysis/out/
make tables     # every table, including Table 1 and the frozen-snapshot supplement tables
```

`make data` downloads two Hugging Face datasets: the trajectories
(`AgentsSci/AAMAS2027-Roles`) and the problem set with gold answers
(`AgentsSci/IEEE2026_BigData_MAS-4-Science-Matching`, `data/problems/` and
`data/trajectories/`). [`scripts/place_data.py`](scripts/place_data.py) then
locates each of the 14 trajectory files by the sha256 recorded in the
committed manifests, whatever its name or folder in the download, and links
it where the analysis reads it. It exits non-zero if anything is missing.
Data already on disk can be placed with
`python3 scripts/place_data.py --source <dir>`.

**[TODO: `AgentsSci/AAMAS2027-Roles` is private, and v1.1.0 lacks the ten
post-freeze files pinned by `experiments/results/bf/MANIFEST_BF.json` and
`experiments/results/bf/chain2/MANIFEST.json`. Upload them as v1.2.0 and
make the dataset public.]**

### Main results → command

| Paper item | Result | Generator | Target |
|---|---|---|---|
| Figure 1 | one cycle; feedback route per condition | `mk_fig_pipeline.py` | `make figures` |
| Table 1 | functional collapse per actor | `mk_tables.py` | `make tables` |
| Figure 2 | first pass, recovery, budget use | `mk_fig1_bf.py` | `make figures` |
| Table 2 | RS vs RF in all five cells | `mk_table_main.py` | `make smoke` |

Every supplement table and figure, with its input and data source, is in
[`docs/reproduction/paper_artifact_matrix.md`](docs/reproduction/paper_artifact_matrix.md).

Spot-check the first row of Table 2:

| gemma-4, Omni-MATH | RS | RF |
|---|:--:|:--:|
| recovery | 0.222 | 0.609 |
| recovered only by (paired, *n* = 236) | 4 | 89 |
| final accuracy | 0.846 | 0.921 |
| submissions per failed trajectory | 1.27 | 3.20 |

### Level C: re-run inference

```bash
python3 experiments/runner.py --dry-run --n 2 --arms A,B,Bf,C \
    --out /tmp/dry.jsonl                                          # stub model, zero API calls
bash experiments/run_bf.sh experiments/results/bf                 # post-freeze campaign (RF, RS re-run)
```

`run_bf.sh` takes the actor (`ACTOR`, `TAG`), problem count (`N_OMNI`) and
concurrency (`CONC`) from the environment, and requires
`AAMAS_PROBLEMS_PARQUET` and `AAMAS_AUTH_SCRIPT_DIR` even with `DRY=1`.
The design of the post-freeze RF condition, written before its data existed,
is [`experiments/BF_CONTROL.md`](experiments/BF_CONTROL.md).
The runners call the OpenAI-compatible vLLM gateway used for the paper
(`BASE_URL` in `experiments/runner.py` and `runner_xdomain.py`) with a bearer
token from the helper in `AAMAS_AUTH_SCRIPT_DIR`. To run against your own
server, point `BASE_URL` at it and supply a token helper. Every trajectory
records a `config_version` hash of the prompts, schemas and run constants,
`BASE_URL` included: the code in this repository reproduces the hashes
recorded for the forced-submission run (`1a5f4fe24f242c80`) and the SciBench
RF runs (`d311904cee36c21b`), and a changed endpoint yields a new hash, so
new runs are never pooled with the released ones by accident.

Problem manifests are deterministic and hash-verified
(`experiments/manifest_omnimath2_n1600.json`, `…_n400.json`). Each trajectory
is written as one fsync'd JSONL line; re-running the same command resumes and
skips completed `(problem_uid, arm, actor_model)` triples.

## What is released

- **Every trajectory** behind the paper: 11,600 frozen Omni-MATH and 2,296
  frozen SciBench trajectories, with role messages, evaluator calls and
  enforcement events, sha256-manifested. In 18 rows the `error` field held a
  response page returned by the inference gateway; the public files replace
  it with a fixed marker ([`scripts/redact_release.py`](scripts/redact_release.py)).
  No analysis reads that text, so every number is unchanged, and each
  manifest records the hash of the original file under `redacted_from_sha256`.
  **[TODO: plus the 4,748 post-freeze RF trajectories, the RF second run, the
  RS re-run and the forced-submission run.]**
- **Prompts, schemas and run configurations** for every condition, including
  the domain-adapted SciBench prompts.
- **The collapse adjudication**: frozen rubric, sample, and verdicts
  ([`adjudication/`](adjudication/)).
- **The analysis code** that computes every number, the intermediate files it
  writes (`analysis/out/`), and the generators for every table and figure.
- **The LaTeX source** of the preprint, with every table and figure as generated.

## What is not released

- **SciBench problem text and answers.** Trajectory rows carry `problem_uid`,
  which joins to the public SciBench release. (The Omni-MATH-2 sample's text
  and reference answers are in the problem manifests; see [`NOTICE`](NOTICE).)
- **Token counts and cost.** They were never recorded; every budget in the
  paper is in calls and cycles.
- **Model weights.** All three actors are third-party open-weight models.
- **Repeated stochastic runs.** One realized trajectory per problem and cell,
  except the two gemma-4 RF cells.

## Repository layout

```
experiments/    runner, prompts, schemas, problem manifests, offline tests,
                and the sha256 manifests that pin every trajectory file
analysis/       FINAL_TABLES.py, bf_numbers.py, bf_gate.py, the table and
                figure generators, and their committed outputs in out/
adjudication/   collapse adjudication: rubric, sample, verdicts
paper/          LaTeX source of the preprint, generated tables and figures
scripts/        place_data.py: locate and link the downloaded data
docs/           artifact matrix and README figures
```

## Documentation

- [Paper artifact matrix](docs/reproduction/paper_artifact_matrix.md): every table and figure → generator → data
- [RF control design](experiments/BF_CONTROL.md): the post-freeze condition, written before its data existed
- [Table provenance](paper/tables/README.md): input, denominator and caveats of every generated table

## Citation

```bibtex
@misc{yang2026beyond,
    title = "Beyond Division of Labor: How Roles Shape Feedback and Recovery in Multi-Agent Systems",
    author = "Yang, Chih-Hsuan  and
      Li, Xinyang  and
      Thakur, Rajeev  and
      Yan, Feng",
    year = "2026",
    note = "Preprint"
}
```

## Acknowledgments

This research used resources of the Argonne Leadership Computing Facility, a
U.S. Department of Energy (DOE) Office of Science user facility at Argonne
National Laboratory (ANL) operated under Contract No. DE-AC02-06CH11357. The
work was also supported under the same contract by the DOE Office of Science's
Advanced Scientific Computing Research Program and by Laboratory Directed
Research and Development (LDRD) funding from ANL, provided by the Director,
DOE Office of Science. The work of the University of Houston coauthors was
supported in part by the National Science Foundation under grants
CAREER-2305491 and CNS-2504762.

We thank the authors of Omni-MATH and SciBench, whose benchmarks this study
measures against.

## License

Code and documentation in this repository are released under the [MIT License](LICENSE).
Released trajectories are our own measurements; upstream benchmark content
remains under its original terms, described in [`NOTICE`](NOTICE).

## Contact

Chih-Hsuan (Bella) Yang — bellayang@anl.gov
