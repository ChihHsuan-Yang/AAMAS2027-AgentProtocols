# From Feedback to Revision: When Multi-Agent Roles Become Load-Bearing

[Project Website](https://chihhsuan-yang.github.io/AAMAS2027-AgentProtocols/) | [Code](https://github.com/ChihHsuan-Yang/AAMAS2027-AgentProtocols) | [Dataset](https://huggingface.co/datasets/AgentsSci/AAMAS2027-Roles)

**Release resources (2026-10-31):** The website hosts *Beyond Division of Labor:
How Roles Shape Feedback and Recovery in Multi-Agent Systems*, its current
release PDF, and supplementary material. Website source is in [`website/`](website/).
The experiment notes below describe an earlier research snapshot; refer to the
release manuscript and dataset card for comparison definitions and data coverage.
In particular, the frozen role-free B condition withholds evaluator feedback;
it must not be confused with the later role-free-with-feedback comparison.


> **Roles do not primarily help a team produce its first answer. They help it
> turn an external "your answer is wrong" signal into a revision rather than a
> resubmission of the same candidate.**


AAMAS 2027 submission, GAAI track. 8 pages main text + unlimited references,
double-blind. **Bella submits manually** — an agent's job ends at a
submission-ready package.

## Main Story

Multi-agent LLM systems are specified as role diagrams — Planner, Executor,
Reviewer — and the diagram is read as a mechanism. We ask which **phase** of
the work that organization actually carries. Deleting every role instruction,
with topology, model, information, retry budget and evaluator held fixed,
destroys the intended division of labor but leaves first-pass solving intact.
The difference appears only *after* a team is told its answer is wrong: both
teams hold the same six deliberation cycles and the role-free team draws
**more** oracle verdicts, so it is neither stopped early nor given less
information. What differs is use — told they are wrong, one team revises and
the other resubmits. That behavioral split becomes a recovery split, and the
same dissociation reappears in a second, free-response science domain.

## Main Claims and Evidence

Three claims. Diagnostic findings are not contributions and are not listed
here; the full claim register, including a binding DEAD list of falsified
claims, is [`APPROVED_CLAIMS.md`](APPROVED_CLAIMS.md).

| # | Claim | Evidence | Where |
|---|---|---|---|
| **1** | Deleting role instructions destroys the intended division of labor but **leaves first-pass solving intact** — in all three actors | functional collapse 0.000–0.120 → 0.846–0.976; first pass unchanged for gemma-4, *improved* for gpt-oss | Figure 1A, `paper/tables/main_role_collapse.tex` (main paper) |
| **2** | The difference appears **after an external correctness signal**: role-structured teams revise, role-free teams resubmit — and that becomes a recovery difference | same 6 cycles by construction, role-free draws *more* oracle verdicts; 1.54 submit + 3.98 revise vs 5.80 + 0.03; recovery 0.222 → 0.051, exact McNemar p=2×10⁻⁸ | Figure 1B/1C, `paper/tables/main_recovery.tex` (supplement) |
| **3** | Both halves **replicate in a second, free-response domain** | SciBench, gemma-4: first pass 0.794 → 0.794, paired recovery 0.212 → 0.020 (n=99, p=6.6×10⁻⁵) | Figure 2, `paper/tables/scibench_replication.tex` (supplement) |

**Actor scope, stated once and not smoothed.** gemma-4 clean; gpt-oss
directional but the paired contrast does not resolve (p=0.208); Llama-3.3
does not show the effect — a genuine null specific to the role
manipulation, **not** a floor, since structural enforcement moves that same
actor's recovery to 0.139.

**Supporting, not headline.** Making the division of labor unavoidable at
the interface returns the same capacity in all three actors, at 8–17%
one-sided attrition that keeps it from reaching end-to-end accuracy.

**The pre-registered primary endpoint is null** and is reported as the
failure of the theory it was written to test. The contrast this paper is
organized around was pre-registered as **secondary and exploratory**, and is
labeled post-hoc in the manuscript.

**The mechanism.** On gemma-4, told its answer is wrong, the role-structured
team spends 5.52 cycles as **1.54 submissions + 3.98 revisions**; the
role-free team spends 5.83 as **5.80 submissions + 0.03 revisions**, leaving
its answer unchanged in **0.845** of first-pass-wrong trajectories against
**0.288**. Same budget, opposite use.

**The outcome.** Recovery falls **0.222 → 0.051**. Paired on problems wrong
under both conditions: **37 recovered only with roles against 3 only without**,
exact McNemar **p = 2×10⁻⁸**. Because gemma-4's first-pass rates are equal to
four decimals, this contrast is algebraically the **intent-to-treat effect**,
not a post-treatment conditional — the cleanest answer available to the
obvious objection.

**The replication.** SciBench, gemma-4: first pass **0.794 → 0.794**, paired
recovery **0.212 → 0.020** (n=99, 21 vs 2 discordant, p = 6.6×10⁻⁵).

**Actor scope, stated once.** gemma-4 clean; gpt-oss directional but the
paired contrast does not resolve (p = 0.208); Llama-3.3 does not show the
effect — a genuine null specific to the role manipulation, **not** a floor,
since structural enforcement moves that same actor's recovery to 0.139.

## Current Project Status

| Component | Status | Current state | Canonical path / link | Last verified |
|---|---|---|---|---|
| Project stage | **CURRENT** | submission-ready; gate-complete | `FINAL_FREEZE.json` | 2026-10-02 |
| Core experiments | **DONE** | 13,896 trajectories, two domains, frozen and sha256-manifested | [`docs/DATA_PROVENANCE.md`](docs/DATA_PROVENANCE.md) | 2026-10-02 |
| Active experiment | **NOT APPLICABLE** | nothing running; no job to poll, no endpoint in use | [`HANDOFF_CURRENT.md`](HANDOFF_CURRENT.md) | 2026-10-02 |
| Paper | **CURRENT** | 9 pp (main text ends p8); all gates pass | [`paper/`](paper/) | 2026-10-02 |
| Supplement | **CURRENT** | 11 pp, no page limit, anonymous | [`paper/supplement.tex`](paper/supplement.tex) | 2026-10-02 |
| Overleaf | **BLOCKED** | git access refused — Argonne Premium affiliation not yet linked. Remote is two rewrites stale. **Not a project risk**: a fresh clone of this repo rebuilds both PDFs to identical text | [`HANDOFF_CURRENT.md`](HANDOFF_CURRENT.md) | 2026-10-02 |
| Hugging Face | **CURRENT** | `AgentsSci/AAMAS2027-Roles` v1.1.0, **PRIVATE**; cold download 52/52 checksums OK | [`docs/DATA_PROVENANCE.md`](docs/DATA_PROVENANCE.md) | 2026-10-02 |
| Figures / tables | **CURRENT** | 2 figures, 7 tables, all generated; no orphans | [`docs/PAPER_ARTIFACT_MAP.md`](docs/PAPER_ARTIFACT_MAP.md) | 2026-10-02 |
| Agent TODOs | **1 open** | final blind mock review | [below](#agent-todo) | 2026-10-02 |
| Human TODOs | **5 open** | all OpenReview / submission authority | [below](#human-todo) | 2026-10-02 |

**Abstract registration (Oct 1 AoE) has passed.** Whether the paper may
still be submitted is a question only the venue can answer; nothing in this
repository can.

## Start Here — canonical navigation

| Resource | Purpose | Canonical path / link | Status |
|---|---|---|---|
| Paper package | manuscript source — the complete intended Overleaf project | [`paper/`](paper/), guide at [`paper/README.md`](paper/README.md) | **CURRENT** |
| Overleaf | external manuscript workspace | project id in [`paper/README.md`](paper/README.md) (private links section) | **BLOCKED** — access refused |
| Submission package | what Bella pastes into the form | [`SUBMISSION_PACKAGE.md`](SUBMISSION_PACKAGE.md), abstract in [`paper/ABSTRACT_SUBMIT.txt`](paper/ABSTRACT_SUBMIT.txt) | **CURRENT** |
| Hugging Face | canonical dataset release | `AgentsSci/AAMAS2027-Roles` v1.1.0 — **PRIVATE during review** | **CURRENT** |
| Results index | the only source of a number | [`analysis/out/FINAL_TABLES_OUTPUT.txt`](analysis/out/FINAL_TABLES_OUTPUT.txt), from [`analysis/scripts/FINAL_TABLES.py`](analysis/scripts/FINAL_TABLES.py) | **CURRENT** |
| Figure/table map | publication-artifact provenance | [`docs/PAPER_ARTIFACT_MAP.md`](docs/PAPER_ARTIFACT_MAP.md) | **CURRENT** (generated) |
| Data provenance | construction, eligibility, validity, where data lives | [`docs/DATA_PROVENANCE.md`](docs/DATA_PROVENANCE.md) | **CURRENT** |
| Reproduction guide | three levels, cheapest first | [`docs/REPRODUCIBILITY.md`](docs/REPRODUCIBILITY.md) | **CURRENT** |
| Trace availability | what each trace holds, and what it does not | [`docs/TRACE_AVAILABILITY.md`](docs/TRACE_AVAILABILITY.md) | **CURRENT** (measured) |
| Invalid / superseded | runs and numbers not to use | [`docs/INVALID_AND_SUPERSEDED.md`](docs/INVALID_AND_SUPERSEDED.md) | **CURRENT** |
| Current handoff | live execution state, local paths, resume | [`HANDOFF_CURRENT.md`](HANDOFF_CURRENT.md) | **CURRENT** |
| Authoritative TODO | remaining work with validation criteria | [`TODO.md`](TODO.md) | **CURRENT** |
| Claim register | what may be asserted; DEAD list is binding | [`APPROVED_CLAIMS.md`](APPROVED_CLAIMS.md) | **CURRENT** |
| Source-of-truth policy | which artifact is authoritative for what | [`SOURCE_OF_TRUTH.md`](SOURCE_OF_TRUTH.md) | **CURRENT** |

Machine-specific absolute paths, the Overleaf project id and the local
clone location live in [`HANDOFF_CURRENT.md`](HANDOFF_CURRENT.md) and
[`paper/README.md`](paper/README.md), not here. **No credential appears
anywhere in this repository.**

## Paper / Overleaf

| | |
|---|---|
| canonical source | [`paper/`](paper/) — 28 tracked files: `main.tex`, `supplement.tex`, 10 sections, `refs.bib`, `aamas.cls`, the bibliography style, 2 figures, 7 generated tables, and three READMEs |
| build | `pdflatex` → `bibtex` → `pdflatex` ×2, per document. `latexmk` alone fails from a clean tree — it schedules bibtex before any `.aux` exists |
| one-command gate | `python3 scripts/final_freeze.py` — both documents, every gate, writes `FINAL_FREEZE.json` |
| Overleaf state | **BLOCKED.** Git access refused pending an affiliation link. The remote is two rewrites stale: it carries the old title and the pre-narrative sections. **Do not read it as current, do not create a replacement project, do not change the remote.** |
| sync procedure | in [`HANDOFF_CURRENT.md`](HANDOFF_CURRENT.md) — dry-run end to end locally, including two traps that only running it exposes |

**Overleaf being unavailable is not a project risk.** Verified 2026-10-02: a fresh
`git clone` of this repository, building `paper/` and nothing else,
produces both PDFs with extracted text identical to the working copy.
Reproducibility snapshots — commit, text hashes, data digests — are
recorded in `FINAL_FREEZE.json` rather than pasted into this file.

## Data / Hugging Face

| | |
|---|---|
| repository | `AgentsSci/AAMAS2027-Roles` |
| version | **v1.1.0** |
| visibility | **PRIVATE** — verified three ways on 2026-10-02: authenticated API `private=True`; anonymous fetch of both the card and a data file → 401; positive control `openai/gsm8k` → 200 |
| contents | 8 parquet tables (5 Omni-MATH, 3 SciBench), 4 raw JSONL traces, prompts, configs, manifests, checksums |
| integrity | cold download, `shasum -c CHECKSUMS.txt` → **52/52 OK** |
| unit | **trajectory** — 11,600 Omni-MATH over 1,600 distinct problems; 2,296 SciBench over the complete 574-problem matched slice |

**Withheld deliberately:** no problem text and no gold answers, only
`problem_uid`, which joins to the public benchmark. **Never captured:**
per-call token counts and cost — so every budget claim in the paper is in
*calls* and *cycles*, never tokens. **Must stay private** through
double-blind review; `hf_artifact/scripts/preflight_public.py` fails by design until
institution-naming rows are sanitized after acceptance, and must not be
weakened to make it pass.

Full detail: [`docs/DATA_PROVENANCE.md`](docs/DATA_PROVENANCE.md).
Field-by-field, measured from the rows:
[`docs/TRACE_AVAILABILITY.md`](docs/TRACE_AVAILABILITY.md).

## Publication artifacts

| Item | Scientific role | Canonical output | Status | Full provenance |
|---|---|---|---|---|
| Figure 1 | roles do not buy the first answer; the gap opens after failure; same budget, opposite use | `paper/figures/fig1_v1_story.pdf` | **CANONICAL** | [map](docs/PAPER_ARTIFACT_MAP.md) |
| Figure 2 | the same dissociation in a second domain | `paper/figures/fig2_v2_xdomain.pdf` | **CANONICAL** | [map](docs/PAPER_ARTIFACT_MAP.md) |
| Table 1 | functional collapse per actor | `paper/tables/main_role_collapse.tex` | **CANONICAL** — main paper | [map](docs/PAPER_ARTIFACT_MAP.md) |
| 6 further tables | recovery, SciBench, enforcement, single-agent, pre-registered endpoints, context quartiles | `paper/tables/*.tex` | **CANONICAL** — supplement | [map](docs/PAPER_ARTIFACT_MAP.md) |

Every one is **generated**; no numeric literal is hand-maintained anywhere
in either document. The map is itself generated from the sources and
reports a gap if a figure is shipped but unreferenced, or a table generated
but inputted by nothing.

## Remaining Work

### Human TODO

Only work requiring authority no agent has.

| TODO | Owner | Status | Dependency / blocker | Artifact | Done when |
|---|---|---|---|---|---|
| OpenReview profiles, complete author list | Bella | **TODO** | account access | — | all authors have profiles and the list is locked |
| Submit the PDF (Oct 8 AoE) | Bella | **TODO** | submission authority | `paper/main.pdf` + `paper/supplement.pdf` | the venue acknowledges the submission |
| Confirm whether the missed abstract deadline bars submission | Bella | **TODO** | venue only | — | the venue has answered |
| Reciprocal-reviewer requirement for 2027 | Bella | **TODO** | venue only | — | checked against the 2027 CFP |
| Decide when data goes public | Bella | **TODO** | acceptance | `hf_artifact/` | decision recorded; `preflight_public.py` passes before any flip |

Agent-prepared, human-approved: the submission package, the abstract text
and the compliance gates are ready; the submission action itself is yours.

### Agent TODO

| TODO | Owner | Status | Dependency / blocker | Artifact | Done when |
|---|---|---|---|---|---|
| Final blind mock review of both PDFs | agent | **TODO** | none | `paper/main.pdf`, `paper/supplement.pdf` | a review exists in `notes/MOCK-REVIEW-3-*.md` and every actionable finding is either fixed or recorded with a reason not to fix |
| Push to Overleaf and verify the remote builds | agent | **BLOCKED** | Overleaf git access (Human TODO: affiliation link) | `HANDOFF_CURRENT.md` procedure | remote HEAD equals local, and a fresh clone's `pdftotext \| shasum` matches |
| Add a GitHub backlink to the HF data card | agent | **DEFERRED** | the card must stay anonymous while the repo is private; a repo URL on the card is a deanonymization path | `hf_artifact/README.md` | added **after** acceptance, with the public release |

Full board with per-item validation commands: [`TODO.md`](TODO.md).

## Reader-facing naming

The manuscript never uses internal condition codes. Raw data keeps them,
because renaming would break provenance against every manifest and script:

| raw code | manuscript |
|---|---|
| A | role-structured |
| B | role-free |
| C | structurally enforced |
| Cp | context-restored structural enforcement |

---

# Technical detail

Everything above is the durable entry point. What follows is the material a
collaborator needs that has no better home: the design, the actor scope, and
the novelty constraints. **Detailed provenance, reproduction, data
availability and superseded work each have one canonical home** in `docs/` —
they are not duplicated here.

> **This section uses internal condition codes (A/B/C/C′)** because they match
> the code and the data. The manuscript uses the semantic names mapped above.

## Experimental Design

Four arms. All run the **same pipeline code** in `experiments/runner.py`; only
the manipulated variable differs. Held identical and asserted in code: 3 actors
+ 1 evaluator, order Planner → Executor → Reviewer, 3 outer × 2 inner rounds
(**6 deliberation cycles**), context-visibility policy, 30 actor + 6 evaluator
call budget, 4 transport retries + 3 regenerations, stopping rule (reviewer
approval **and** evaluator PASS), temperature 0, max_tokens 8192, backend
`sophia_vllm`, and grading by the same evaluator LLM.

| arm | name | prompts | division of labor | who may author the answer |
|---|---|---|---|---|
| **A** | soft roles (control) | original PER prompts, byte-verbatim from the source config | rhetorical | anyone (measured, not prevented) |
| **B** | no roles | ONE identical generic prompt for all three agents | **none** — role names only route turns | anyone |
| **C** | hard enforcement | minimal declarative output contracts | **architectural** — JSON schemas + information routing | executor only, by construction |
| **C′** | enforcement + restored context | as C, plus `shared_history` restored | as C | as C |

The validate→regenerate loop exists in **every** arm; A and B use an
always-valid validator so attempt 0 always passes. Only C has a constraint that
can fail — that is the manipulation. C′ − C isolates the context change at
fixed enforcement, and is a **partial** control (Arm C also changes the output
schema).

Arm C enforcement: the Planner must emit
`{subproblems, strategy, dependencies, required_quantities}` with
`additionalProperties: false` and **no answer field**; `\boxed{}` or "Final
Answer" is rejected. The Executor receives **only the parsed plan object**,
never the planner's raw text. The Reviewer emits a verdict with no answer
field; `accept` promotes the executor's answer **verbatim, by reference**.
Details and the two deliberate validator subtleties: `experiments/README.md`.

## Actors and Domains

| | |
|---|---|
| **actors** | `google/gemma-4-31B-it`, `openai/gpt-oss-120b`, `meta-llama/Llama-3.3-70B-Instruct` |
| **evaluator / grader** | `openai/gpt-oss-120b` (**it also serves as one of the actors** — see caveat 10 in `CLAIM_STATUS.md`) |
| **adjudicator** | Opus 5 (`claude-opus-5`), rubric frozen before the first judgement. **Outcome-blind, NOT condition-blind** — do not describe it as blinded |
| **benchmarks** | `omnimath2` (Omni-MATH, competition mathematics) and `scibench` (free-response college chemistry and physics) |
| **domains** | **two.** Omni-MATH is the main campaign; SciBench is a separate frozen campaign run by `runner_xdomain.py`, covering arms A and B only, two actors |
| **backend** | `sophia_vllm` for **every** trajectory; no cell straddles backends (verified) |
| **sample sizes, Omni-MATH** | gemma-4 and gpt-oss: 1,600 problems × arms A/B/C, plus 400 × C′. Llama-3.3: 400 × A/B/C, **no C′ cell**. **11,600 trajectories, 83,320 role messages, 17,486 evaluator gradings, 1,600 distinct problems** (T24) |
| **sample sizes, SciBench** | gemma-4 and gpt-oss × arms A/B over the complete 574-problem matched slice. **2,296 trajectories**; every problem has exactly 4 cells |

Llama-3.3 is much weaker on this benchmark (Arm A 0.307 vs ~0.80). Report its
contrasts as same-direction evidence; **never as a matched third point.** It
was not run on SciBench.

**The evaluator is also one of the actors.** gpt-oss-120b grades every
trajectory, including its own. The identical-prompt control rules out bias
on the answer *string* only and does not resolve this; it is a stated
limitation, not a closed question.

## Prior Work / Overlap — what this paper is NOT

This group has public arXiv work on the **same corpus**. AAMAS prohibits
substantially similar concurrent submissions and thin-sliced contributions.
`OVERLAP_AUDIT.md` is the full audit; the short version:

- **NOT a dataset paper.** No claim on the corpus, its schema, or its scale. The corpus is an *instrument*. The central claim rests on **new experimental arms that do not exist in the release**.
- **NOT** a workload/serving characterization (that is the companion BigData paper's genre, and directions reducing to it were self-rejected).
- **NOT** about DHD — that is a third, already-public paper's core asset, explicitly out of scope.
- **No figure or table is shared** with the companion papers.
- The three group papers (`2609.27822`, `2608.14927`, `2607.15388`) are cited **in the third person** for blinding.

Novelty constraints are binding, not advisory. Five things this paper **may not
claim** — first-pass parity as ours; being first to show LLMs fail to revise
under feedback; discovering answer lock-in (it is Liang's
**Degeneration-of-Thought** — cite `liang2024divergent`, claim only the
*inversion*); premature consensus as a novel hypothesis; "diversity is the
active ingredient." And one sentence that must **never** be written: *"Huang et
al. showed LLMs cannot self-correct even with oracle feedback"* — false, their
oracle condition **improves** GSM8K 75.9 → 84.3. See `CLAIM_STATUS.md`
§MUST NOT CLAIM and **F19**.

Residual novelty risk, stated rather than papered over: no forward-citation
search was possible (Semantic Scholar rate-limited). A scoop published *citing*
Huang/Stechly/Liang would not have been found.


## Things that will bite you

1. **The frozen JSONL is not in git.** A clone alone is not reproducible — it
   gets `MANIFEST.json` and zero rows. The off-laptop copy is the private HF
   repo; the bytes were verified identical, not just the filenames.
2. **`latexmk -pdf main.tex` fails from a clean tree.** It schedules bibtex
   before any `.aux` exists. Use the explicit pdflatex/bibtex sequence.
3. **Two scoring conventions disagree in sign for the enforced condition.**
   PREREG is primary; AS-GRADED is sensitivity only and carries 8–17%
   one-sided survivorship. Quoting as-graded as the headline would reproduce
   the pre-declared NOT-SUBMIT pattern.
4. **`scripts/pagecheck.py` is the only valid page check**, and must be run
   without a pipe — `| tail` makes `$?` report tail's status. Two earlier
   versions passed a 10-page paper; both failure modes are in its docstring.
5. **`notes/` contains dead claims and stale numbers by design.** It is the
   audit trail and retracted figures are kept visible on purpose. Source
   nothing from it; see
   [`docs/INVALID_AND_SUPERSEDED.md`](docs/INVALID_AND_SUPERSEDED.md).
6. **After any change to `FINAL_TABLES.py`, re-derive `APPROVED_CLAIMS.md`
   too.** It has fallen behind the manuscript twice.

## AI assistance

Used substantially in hypothesis formation, experimental design, execution,
analysis and writing, under human direction and approval. The anonymous
reviewer-facing disclosure is
[`paper/AI_ASSISTANCE_DISCLOSURE.md`](paper/AI_ASSISTANCE_DISCLOSURE.md) and
is reproduced in full in the supplement. The internal log
([`AI_ASSISTANCE_LOG.md`](AI_ASSISTANCE_LOG.md)) stays internal — it carries
identifying content.

---

# Next Agent: Start Here

You need no prior conversation. In order:

1. **Read the story and claims above.** They are user-approved. Do not
   restructure, reprioritize or reinterpret them; if new evidence looks
   inconsistent with them, record the discrepancy and ask — do not rewrite.
2. **Check Current Project Status** above for what is current, blocked, or
   superseded.
3. **Read [`HANDOFF_CURRENT.md`](HANDOFF_CURRENT.md)** — live state, local
   paths, the exact blocker, the resume procedure, and what not to redo.
4. **Take the first non-blocked item in [Agent TODO](#agent-todo)** and
   continue autonomously. Do not wait for approval unless that item names a
   Human TODO as its dependency.
5. **Before changing any artifact**, read
   [`docs/PAPER_ARTIFACT_MAP.md`](docs/PAPER_ARTIFACT_MAP.md) (what generates
   what) and [`APPROVED_CLAIMS.md`](APPROVED_CLAIMS.md) (what may be
   asserted — the DEAD list is binding).
6. **Before trusting a number**, check it against
   [`analysis/out/FINAL_TABLES_OUTPUT.txt`](analysis/out/FINAL_TABLES_OUTPUT.txt),
   not against whichever document looks most recent.
7. **Before quoting a result**, check
   [`docs/INVALID_AND_SUPERSEDED.md`](docs/INVALID_AND_SUPERSEDED.md) — seven
   superseded values are printed there beside their replacements precisely so
   you can recognise a stale one.
8. **Run `python3 scripts/final_freeze.py` before and after** any change to
   `paper/`. It is the single command that answers whether the project is
   releasable, and it gates both documents.

**Nothing is running.** No campaign, no job, no endpoint in use. There is
nothing to babysit and no process to resume — only the work listed above.

**Do not** start a new experiment, upload data, or mutate an external
service because documentation says something is missing. Those need an
explicit instruction.
