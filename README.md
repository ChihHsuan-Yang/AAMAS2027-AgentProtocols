# When Is Multi-Agent Organization Load-Bearing?

AAMAS 2027 submission (GAAI track). **Abstract Oct 1, full paper Oct 8 AoE.**
8 pages main text + unlimited references, double-blind, LaTeX mandatory.

**Bella submits manually.** An agent's job ends at a submission-ready package —
see `SUBMISSION_CHECKLIST.md`, section *"Bella — manual submission actions"*.

> **New agent with no prior context?** Read this file top to bottom, then go to
> **[Cold-Start Handoff for the Next Agent](#cold-start-handoff-for-the-next-agent)**
> at the bottom. Everything you need is in those two places.

---

## Project Goal

Multi-agent LLM systems are specified as role diagrams — Planner → Executor →
Reviewer — and those diagrams are routinely read as *mechanism*: the roles are
assumed to be doing the work the picture says they do. This project asks a
falsifiable version of that assumption: **when is the organization actually
load-bearing?** Load-bearing is defined operationally as *removing or altering
the role structure causes a reproducible performance degradation under matched
compute and information budgets.* Holding the actor models, the call budget,
the context-visibility policy, the verifier and the grading fixed, we delete
the role instructions (Arm B) and separately make the division of labor
structurally unrepresentable (Arm C), and measure what breaks.

## Current Story

**Plain language.** Give three copies of the same model the roles "planner,"
"executor," and "reviewer," and they divide up the work. Take the role labels
away and they stop dividing it — all three just solve the whole problem
themselves and agree with each other. Surprisingly, this costs nothing on the
first attempt: the team gets the same fraction of problems right the first
time, and one model actually gets *better*. The damage shows up only after the
team gets an answer wrong. A team with roles will argue with itself, change its
answer, and sometimes fix the mistake. A team without roles locks onto its
first answer, rubber-stamps it for the rest of its budget, and almost never
recovers. So the roles are not what produce the answer — they are what let the
team abandon a wrong one.

**Technical.** Removing role instructions destroys the functional division of
labor in all three actors (blinded adjudication: 0.964 "no division of labor"
in Arm B vs 0.000 in Arm A). First-pass accuracy is unchanged or improves,
which is our control condition and is consistent with prior role-ablation work.
The cost is localized to *recovery* conditional on a wrong first pass, and only
one actor shows it cleanly (gemma-4 0.222 → 0.051, McNemar p=2e-08); Llama-3.3
does not replicate it, and that is a genuine null rather than a floor — its
recovery channel is demonstrably movable by Arm C. It is not
premature stopping: every arm holds the same six deliberation cycles by
construction, and the role-free arm receives *more* evaluator feedback, having
converted nearly every cycle into a resubmission instead of a revision. The
proximate mechanism is failure to produce a distinct second candidate —
frozen-answer rate 0.288 → 0.845 — which is Liang's Degeneration-of-Thought
arriving in a setting where multi-agency was the prescribed cure. Architectural
enforcement (Arm C) restores the organization, and restores recovery in
Llama-3.3 (p=3.8e-06) — the other two actors move in the same direction but
are not resolvable against Arm C's 8–17% attrition. It does not improve final
accuracy in any actor.

One sentence, from `APPROVED_CLAIMS.md`:

> Role structure is not load-bearing for generating the first answer, but it
> can be load-bearing for repairing an initially wrong one.

## Current Headline Results

All numbers from `analysis/out/FINAL_TABLES_OUTPUT.txt`, frozen
`2026-09-30T10:09:30`, 11,600 trajectories. Table ids (T*) index that file.

| | gemma-4-31B-it | gpt-oss-120b | Llama-3.3-70B |
|---|---|---|---|
| **functional collapse**, Arm A → B (T8) | 0.000 → 0.976 | 0.120 → 0.846 | 0.000 → 0.872 |
| **adjudicated** "no division of labor", A / B / C (T23) | 0.000 / 0.857 / 0.188 | 0.000 / 1.000 / 0.143 | 0.000 / 1.000 / 0.071 |
| **first pass**, A → B (T3) | 0.802 → 0.802 (+0.000) | 0.713 → 0.763 (**+0.050**) | 0.308 → 0.316 (+0.008) |
| **recovery**, A → B (T3) | **0.222 → 0.051** | 0.324 → 0.247 | 0.014 → 0.015 (a genuine null, **not** a floor) |
| paired recovery McNemar, A vs B (T4) | **p=1.95e-08** | p=0.208 (**n.s.**) | p=0.375 (**n.s.**) |
| paired recovery A vs C (post-correction) | p=0.298 (**n.s.**) | p=0.105 (**n.s.**) | **p=3.81e-06** |
| **final accuracy** B−A, prereg (T2) | −0.0338 [−0.0488,−0.0187] | +0.0163 [+0.0000,+0.0331] | +0.0025 [−0.0325,+0.0375] |
| **final accuracy** C−A, prereg (T2) | −0.0225 [−0.0387,−0.0063] | −0.0050 (null) | +0.0175 (null) |
| **recovery** Arm C (T1, post-`ba28977`) | 0.314 | 0.395 | 0.139 |
| Arm C attrition (T7) | 0.080 | 0.099 | 0.170 |
| frozen-answer rate, A / B / C (T1) | 0.288 / 0.845 / 0.122 | 0.052 / 0.202 / 0.069 | 0.749 / 0.805 / 0.064 |
| vs its budget-matched single agent, A / B (T17) | −0.0225 / −0.0563 | +0.0131 / +0.0294 | — |

Two figures that carry the argument: every arm uses the **same 6 cycles**
(T5) — gemma-4 first-pass-wrong spends 5.52 cycles / 1.54 submissions / 3.98
revising in Arm A, against 5.83 / 5.80 / **0.03** in Arm B. And the grader
noise floor is **0.0086** (T6): propagating the per-call disagreement rate into
the bootstrap leaves gemma-4's B−A significant ([−0.0488,−0.0175]) and gpt-oss
and Llama null.

> **The two Arm C recovery rows above are post-correction.**
> `STATISTICAL_AUDIT.md` (2026-09-30) found a fatal denominator bug — the Arm C
> recovery denominator dropped 173 trajectories that received a first incorrect
> verdict and then died in regeneration. **Fixed in commit `ba28977`; T1 now
> prints the corrected 0.314/0.395/0.139** (the pre-fix values were
> 0.412/0.461/0.150, and any artifact still showing those is stale). Arms A and
> B moved by ≤ 0.002. Two of three paired A-vs-C p-values were lost.
>
> **T27 is still wrong and still prints.** Its "|B−A| ÷ floor = 3.9x clears"
> line divides an effect size by a grader-disagreement rate, which is not a
> valid operation, and the noise largely cancels in a paired contrast
> (SERIOUS-4). **Do not quote any T27 ratio.** Propagate the per-call rate into
> the bootstrap instead — `analysis/scripts/stat_audit_a5_noisefloor.py`; the
> three verdicts are unchanged.

**Do not quote a number from anywhere else.** See Source-of-Truth Policy.

## Claim Status

Full detail, with evidence and finding note per claim, in **`CLAIM_STATUS.md`**.
The authority is **`APPROVED_CLAIMS.md`** (Master Agent owns it).

**SUPPORTED** (A1–A4, A6–A10): roles → division of labor destroyed in all three
actors; first-pass parity (our control, not our novelty); the recovery cost,
gemma-4 clean / gpt-oss weaker / Llama a genuine null; not premature stopping;
enforcement restores organization, and recovery **for Llama-3.3 only**;
enforcement does not improve accuracy and is brittle; the noise floor; the
two-directional single-agent control; and the preregistered primary (P4) is
**null**.

**An adversarial statistical audit ran on 2026-09-30** —
`STATISTICAL_AUDIT.md`. It independently reproduced T1/T2/T4/T7 exactly, found
**no arithmetic error anywhere in the headline pipeline**, and attacked the
gemma-4 headline six ways without breaking it. It did find one FATAL and five
SERIOUS issues of *what was computed*: the Arm C recovery denominator (now
corrected), a Holm correction the methods assert but the code never applies, a
"floor effect" the paper's own Arm C falsifies, T22's pooled quartiles acting
as arm indicators, an invalid effect÷noise ratio, and two underpowered P4 DiDs.
**Read it before writing prose.** Its required changes are reflected in
`APPROVED_CLAIMS.md` and `CLAIM_STATUS.md`; several are still open in
`paper/`.

**EXPLORATORY**: the lock-in mechanism (A5 — post-treatment, descriptive,
never causal); context contamination; the duplication-vs-null measure; the
C′−C context control; the Reviewer's unexercised critique function.

**FALSIFIED — DO NOT RESURRECT** (15 claims). The prominent ones:

| dead claim | note |
|---|---|
| "the model whose organization collapses most loses least" — the ordering **reverses** under the functional measure | **F22** |
| "gemma-4 shows no first-pass collapse" — byte-metric artifact; adjudged 0.857 | **F13** |
| "hard enforcement universally improves accuracy" — survivorship, 8–17% one-sided attrition | **F24** |
| "Arm B gets 2.5× more repair opportunity" — wrong unit; the budget is identical | **F17** |
| "per-opportunity, Arm B recovers better" — matched on a post-treatment variable | **F17** |
| "roles prevent premature stopping" — refuted **by construction** | **F17** |
| "no accuracy claim is resolvable above scorer noise" — wrong grading key | **F21** |
| "gpt-oss's Arm B planner rubber-stamps" — it is **uninstrumented**, 2.85 ch/s | **F22** |
| preregistered actor × enforcement interaction on accuracy — P4 null | prereg |
| monotone unanimity → recovery damage across actors | freeze |
| "Arm C recovery is highest of any arm, above Arm A in all three actors (p ≤ 1.6e-3)" — denominator dropped 173 rows; 2 of 3 p-values lost | **audit FATAL-1** |
| Llama-3.3's null recovery is a "floor effect" — Arm C moves it (p=3.8e-06), so the channel exists | **audit SERIOUS-2** |

A dead claim gets reintroduced by being re-derived from an old note, not by
being invented. **Old notes under `notes/` contain numbers from earlier cuts
and several of the claims above.** They are kept readable deliberately — a
retraction that deletes its evidence kills the repair it prescribes — but no
number ships from them.

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
| **adjudicator** | Opus 5 (`claude-opus-5`), blinded, rubric frozen before first judgement |
| **benchmark** | `omnimath2` (Omni-MATH), sampled from the released problem parquet |
| **domain** | `math` only. **One domain — the runner pins omnimath2.** No two-domain claim. |
| **backend** | `sophia_vllm` for **every** trajectory; no cell straddles backends (verified) |
| **sample sizes** | gemma-4 and gpt-oss: 1,600 problems × arms A/B/C, plus 400 × C′. Llama-3.3: 400 × A/B/C, **no C′ cell**. **11,600 trajectories, 83,320 role messages, 17,486 evaluator gradings, 1,600 distinct problems** (T24). |

Llama-3.3 is much weaker on this benchmark (Arm A 0.307 vs ~0.80). Report its
contrasts as same-direction evidence; **never as a matched third point.**

## Frozen Results

```
experiments/results/FROZEN/
  MANIFEST.json      922 B    [IN GIT]
  campaign_v2.jsonl  227.5 MB  9,600 rows  sha256 e4e53cb117d91129…  [NOT in git]
  actor3.jsonl        46.0 MB  1,200 rows  sha256 fa22a446d5314bb6…  [NOT in git]
  armCp.jsonl         23.6 MB    800 rows  sha256 038e08aec4d4aee1…  [NOT in git]
```

Frozen at `2026-09-30T10:09:30`. 11,600 rows, 11 cells. Freeze commit
`74ab7da`. **All three hashes verified 2026-09-30.**

Verify them yourself — 3 seconds:

```bash
cd experiments/results/FROZEN && python3 -c "
import json,hashlib
m=json.load(open('MANIFEST.json'))
for f,v in m['files'].items():
    h=hashlib.sha256(open(f,'rb').read()).hexdigest()
    print(f, 'OK' if h==v['sha256'] else 'MISMATCH')"
```

> ### ⚠️ The frozen data is not in git and has no backup
>
> `.gitignore:14` excludes `experiments/results/**/*.jsonl`. A fresh
> `git clone` gets `MANIFEST.json` and **zero rows**. These 297 MB exist in
> exactly one place: this laptop (plus a byte-identical copy in
> `experiments/results/main/`, same disk). They cannot be regenerated —
> temperature 0 is **not** deterministic on this endpoint, so a re-run produces
> different trajectories and different numbers.
>
> **Copy them off this machine. This is the single highest-risk fact in the
> project.**

Two headline tables read files **outside** the frozen snapshot, and say so in
their own output: **T17** (single-agent control) reads the historical released
trace corpus; **T23** (blinded adjudication) reads `adjudication/`. Wherever
either is used, its provenance must be stated.

## Analysis — how to regenerate every table

**One command produces every table in the paper.**

```bash
python3 analysis/scripts/FINAL_TABLES.py > analysis/out/FINAL_TABLES_OUTPUT.txt
```

~16 s. Deterministic (`np.random.default_rng(20261008)`) — re-running
reproduces the committed output byte-for-byte. **Verified 2026-09-30: exit 0,
output identical to the committed file.**

It reads `experiments/results/FROZEN/` exclusively and emits T0–T28:

| | |
|---|---|
| T0 cell census · T1 master results · T2 paired contrasts (both scorings) | T3 first-pass vs recovery · T4 McNemar transitions · T5 mechanism |
| T6 grader noise floor · T7 enforcement cost · T8 collapse by role | T9 Arm B planner shape · T10 duplication vs null · T11 authorship |
| T12 equation density · T13 oracle retry gain · T14 P4 interaction | T15 C′−C · T16 unanimity · T17 single-agent control *(external)* |
| T18 byte duplication · T19 F18 scoring defect · T20 marker sensitivity | T21 token-set sizes · T22 contamination quartiles · T23 adjudication *(external)* |
| T24 scale · T25 pre-oracle recovery · T26 F13 logging defect | T27 noise-floor margins · T28 figure data export |

Two scoring conventions are reported throughout, per `PREREGISTRATION.md`:
**PREREG** (ungraded → scored 0; *primary*) and **AS-GRADED** (ungraded
dropped; *sensitivity only* — it carries 8–17% one-sided attrition in Arm C,
see F24). They disagree in sign for Arm C. Never quote as-graded as the
headline.

Blinded adjudication (T23's source), reproducible from a clone:

```bash
python3 adjudication/analyze.py     # ~1 s, exit 0 verified
```

Re-running `adjudicate.py` issues **new judge calls** and would produce a
different verdict file. Use the committed `VERDICTS.jsonl`.

Independent cross-check against the live (non-frozen) tree:

```bash
python3 scripts/verify_paper_numbers.py    # ~25 s, exit 0 verified
```

The ~40 scripts under `analysis/scripts/{d,r,x}*.py` are the **exploratory
history**. Most read `experiments/results/main/` or older cuts; their printed
numbers may predate a correction. Read them for the audit trail, never for a
current number.

## Figures

Figure generation was rebuilt on 2026-09-30 to source the **frozen snapshot**
rather than the live tree. Two steps:

```bash
python3 analysis/scripts/FINAL_TABLES.py          # T28 writes analysis/out/FIGDATA.json
python3 analysis/scripts/mk_fig1_dissociation.py  # reads FIGDATA.json, writes 3 variants
```

**Verified 2026-09-30: exit 0.** It emits three alternative designs of the same
figure, all from the same numbers — `fig1_v1_grouped` (1 column),
`fig1_v2_slopes` (1 column), `fig1_v3_dumbbell` (2 columns), each as `.pdf` and
`.png` in `figures/`. Shared style and the `figdata()` accessor live in
`analysis/scripts/mk_figstyle.py`. The script prints its provenance line
(frozen timestamp, n, the three sha prefixes) on every run, and derives the
floor-effect annotation and the attrition span from the data rather than
asserting them.

Claims visualised: **A2** (first-pass parity), **A3** (recovery cost —
gemma-4 clean, gpt-oss weaker, Llama a floor), **A6** (Arm C restores
recovery), **A7** (Arm C attrition 8–17%). Nothing else.

> **`figures/` and the figure scripts are owned by the figures/paper worker.
> Coordinate before touching either.**
>
> `figures/fig1_dissociation.{pdf,png}` is the **superseded** figure from the
> previous generation. It plots **byte-identity collapse**, which
> `APPROVED_CLAIMS.md` classes as a **LOWER BOUND ONLY** (precision 1.000,
> **recall 0.262**) and whose scope reading is dead claim **F22** — its
> gemma-4 Arm B collapse reads 0.000 against the approved functional 0.976 —
> and it read `results/main/` rather than `FROZEN/`. Do not revive it, and do
> not caption a byte-identity number as "organizational collapse".

No figure is currently `\includegraphics`-ed into `paper/main.tex`; which
variant ships is an open P1 decision.

## Paper

```
paper/main.tex          preamble, abstract, CCS, IFAAMAS copyright block
paper/sections/*.tex    10 sections
paper/refs.bib          24 entries, each verified (paper_support/BIB-AUDIT-*.txt)
paper/aamas.cls         the OFFICIAL IFAAMAS class — must NOT be modified
```

**`paper/` is owned by the paper worker. Do not edit it.**

Build (verified 2026-09-30, from clean — exit 0, 9 pages):

```bash
cd paper
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
pdfinfo main.pdf | grep Pages
```

> **`latexmk -pdf main.tex` fails from a clean tree** (exit 12): with no
> `.aux` present it schedules `bibtex` first and dies on "I found no
> \citation commands." Use the four-command sequence above, or run `latexmk`
> only after one `pdflatex` pass has created `main.aux`.

**Page status: 9 pages against an 8-page main-text limit** (references
unlimited). Over budget. AAMAS: *"Excessive use of typesetting tricks to make
everything fit into 8 pages is not admissible"* — cut content, not leading.

**Overleaf** is where Bella submits from. Clone:
`/tmp/aamas_ol` ← `git.overleaf.com/6abae70ebd16e2dc9cdecee6`. Credential is in
that clone's `origin` URL and in Bella's account, **nowhere in this repo**.
It is a `/tmp` path and will not survive a reboot; re-clone from Overleaf.
**It is stale** — HEAD `128771e`, 12 files, missing the class file and the
subsequent section rewrites. `paper/` in this repo is the working copy;
Overleaf must be synced from it before submission.

Class provenance, including the exact fetch command (the server returns a
401 KB HTML "404" without a browser User-Agent and a same-site Referer):
`paper_support/aamas_official/PROVENANCE.md`. **The class and the submission
rules are the AAMAS-2026 ones**; 2027 had not published its kit. The copyright
block is the 2026 block with the year advanced — see `CAMERA_READY_CHECKLIST.md`
§2, where "Paphos, Cyprus" is flagged as the field most likely to ship wrong.

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

## Current TODO

Full board with owners and validation criteria: **`TODO.md`**.

**P0 — submission-threatening**
- Page budget: **9 → 8 pages** by cutting content.
- Sync `paper/` → Overleaf; the clone is stale and in `/tmp`.
- **Back up `experiments/results/FROZEN/` off this laptop.** Irreplaceable, unbacked, not in git.
- Push the 16 local commits; `origin/main` is behind.
- Re-run the anonymity audit **after** the final trim (it is not a one-time check).
- Bella-only, cannot be agent-verified: OpenReview profiles (API 403s on every call), reciprocal-reviewer requirement, author-list lock.

- **Act on `STATISTICAL_AUDIT.md`.** FATAL-1 is **DONE** (`ba28977` — T1's Arm C recovery regenerated on the corrected denominator); the corresponding `results.tex` §R5 edit is still open. SERIOUS-1: actually run the Holm correction the methods claim — `holm` appears zero times in `FINAL_TABLES.py`, and a reviewer verifies that with one grep. SERIOUS-2/3/4/5: the corresponding edits in `results.tex`, `method.tex` and `limitations.tex`.

**P1 — strengthening**
- Decide which Figure 1 variant ships (`fig1_v1_grouped` / `v2_slopes` / `v3_dumbbell`) and `\includegraphics` it — none is in `main.tex` yet. All three are frozen-snapshot-sourced via `FIGDATA.json`.
- R-10 evaluator independence: gpt-oss grades itself. **UNTESTED.** The identical-prompt control rules out bias on the answer string only and does not upgrade this.
- Confirm `results.tex` §p4null uses **prereg** scoring, with the as-graded row as a disclosed sensitivity and attrition beside it (F24 §6).
- Record in `SUBMISSION_CHECKLIST.md` that the pre-declared NOT-SUBMIT condition was evaluated against final data and **not met**, with the derivation (F24).

**P2**
- Reviewer-annotation work (R4/N-14) — decided: **narrow the claim** rather than annotate further.
- Supplementary material: decide after the page budget. Anything cited must ship *in the submission zip*, never behind a link.

## Reproducibility

**Environment** (what the frozen results were produced under):

| | |
|---|---|
| Python | 3.9.6 (macOS system python3, Darwin 24.6.0 arm64) |
| numpy 2.0.2 · pandas 2.3.3 · pyarrow 21.0.0 · matplotlib 3.9.4 · requests 2.32.5 | |
| LaTeX | TinyTeX / TeX Live 2026, `pdflatex` + `bibtex`; `pdftotext`/`pdfinfo` from poppler |

No `requirements.txt` or lockfile exists. The analysis needs only numpy (+
pandas/pyarrow for T17 and the figure script); the runner adds `requests`.

**Endpoint and authentication.** ALCF Sophia vLLM,
`https://inference-api.alcf.anl.gov/resource_server/sophia/vllm/v1`. **There is
no HPC job and no cluster filesystem in this project** — everything ran as an
HTTP client from the laptop. Auth is a Globus bearer token obtained by
`/Users/bellayang/work/agent-e/mas-eval/inference_auth_token.py`, which caches
under `~/.globus/app/.../tokens.json`. **Paths only — no credential appears in
this repo, and the runner holds the token in memory and scrubs it from every
error string** (smoke gate 12 checks trajectory rows for bearer/JWT material).
Re-auth is interactive: it needs a browser and a human. A 401 triggers exactly
one token refresh per retry slot.

**Regenerate everything derived** (all four verified 2026-09-30):

```bash
python3 analysis/scripts/FINAL_TABLES.py > analysis/out/FINAL_TABLES_OUTPUT.txt  # ~16 s
python3 adjudication/analyze.py                                                  # ~1 s
python3 scripts/verify_paper_numbers.py                                          # ~25 s
python3 scripts/smoke_gates.py experiments/results/smoke/smoke_v3.jsonl          # ~1 s, 15/15 pass
```

**Re-run the campaign from scratch** (needs a live token; ~8 h at concurrency
24; **will not reproduce the frozen numbers** — temperature 0 is not
deterministic here):

```bash
python3 experiments/runner.py --dry-run --n 2 --arms A,B,C   # zero API calls, verified exit 0
python3 experiments/make_manifest.py 1600                    # needs the sibling parquet
python3 experiments/runner.py --n 1600 --arms A,B,C \
    --actors "openai/gpt-oss-120b,google/gemma-4-31B-it" \
    --out experiments/results/main/campaign_v2.jsonl --run-id main-n1600-v2 --concurrency 24
```

Manifests are deterministic and hash-verified (n=1600 `39cdeeecffc383a7`,
n=400 `94955e7f65332258`, n=25 `04009d74a21bc13a` — all **verified
2026-09-30**). `make_manifest.py` reads a parquet in the sibling
`IEEE-BigData-SciAgentTrace` project (see `PROJECT_PATHS.md`) and fails without
it.

**Resume is automatic.** Writes are one fsync'd JSONL line per completed
trajectory; on restart the runner reads the output file and skips every
completed `(problem_uid, arm, actor_model)`. Re-run the identical command.
Trajectories recorded `model_unavailable` are **not** treated as complete and
are retried.

## AI Assistance

AAMAS 2027 permits AI-assisted research but **requires disclosure, including
the prompt**, when AI is used in hypothesis creation, methodology creation, or
experimental design. The running record — maintained from day one, not
reconstructed at submission — is **`AI_ASSISTANCE_LOG.md`**, with full prompt
text archived under `notes/prompts/`.

Summary: Claude Opus 5 (`claude-opus-5[1m]`) via Claude Code, autonomous
analysis under Bella's direction with approval gates on any new campaign. Opus
5 was also used **as a measurement instrument** (the blinded adjudicator) —
disclosed as model adjudication, never as human annotation or ground truth.
The log records 8 self-caught errors and 4 retracted claims.

## Source-of-Truth Policy

Each kind of artifact has exactly one authority. When two copies disagree, the
authority wins and the other copy is the bug.

| kind | authority |
|---|---|
| **code and workflow** | **GitHub** — `github.com/ChihHsuan-Yang/AAMAS2027-AgentProtocols`, branch `main` |
| **manuscript** | **Overleaf** — project `6abae70ebd16e2dc9cdecee6`. Bella submits from there. |
| **large structured data** | **the frozen store** — `experiments/results/FROZEN/`, hashed in `MANIFEST.json`; HuggingFace after acceptance only (see `CAMERA_READY_CHECKLIST.md` §3 — publishing early de-anonymizes the submission) |
| **claims** | **`APPROVED_CLAIMS.md`** — Master Agent is sole authority |
| **paths** | **`PROJECT_PATHS.md`** |

> ### Final numeric truth = `experiments/results/FROZEN/` + `analysis/scripts/FINAL_TABLES.py`
>
> Every number in the paper comes from running that script against that
> directory. **No manually maintained duplicate numbers anywhere.**

What this forbids, concretely:

- **No hand-typed number** in a README, note, slide, or commit message that is not also derivable by re-running `FINAL_TABLES.py`. A number typed into a second file stops tracking the first.
- **No headline number from any other script.** The ~40 exploratory scripts read older cuts and pre-correction definitions.
- **No number from `notes/`.** Those files are the audit trail. Several contain figures from earlier cuts (n≈9,030) and claims now on the dead list.
- **A retracted number stays visible and marked**, never deleted — deleting it kills the repair the retraction prescribes.
- **T17 and T23 read outside the frozen snapshot** and label themselves so. Carry that provenance wherever they are used.

Everything else in this repo — `analysis/out/`, `analysis/results/`,
`figures/`, `paper/main.pdf`, `tables/` (empty) — is **derived** and may be
deleted and regenerated.

---
---

# Cold-Start Handoff for the Next Agent

*Self-contained. Assumes no access to any prior conversation. Written
2026-09-30; every path and command below was checked or executed on that date.*

## 1. What are we publishing?

An AAMAS 2027 GAAI-track paper, **"When Is Multi-Agent Organization
Load-Bearing?"** — 8 pages + references, double-blind, abstract due Oct 1 AoE,
full paper Oct 8 AoE. **Bella submits by hand.** Your job ends at a
submission-ready package.

It is a controlled ablation, not a dataset paper and not a systems paper. Three
LLM actors run a Planner→Executor→Reviewer pipeline on 1,600 Omni-MATH
problems under four conditions, with compute and information budgets held
fixed. 11,600 trajectories.

## 2. What is the current story?

Roles are not load-bearing for producing the first answer; they are
load-bearing for repairing a wrong one. Remove the role instructions and the
division of labor is destroyed in all three actors, first-pass accuracy is
unchanged or better, and *recovery after a wrong first answer* collapses.
Longer versions in **Current Story** above. The one-sentence version lives in
`APPROVED_CLAIMS.md` and that file, not this one, is the authority.

## 3. What has been falsified?

**15 claims. Do not resurrect any of them.** They are listed with evidence in
`CLAIM_STATUS.md` §FALSIFIED and (the canonical 11) in `APPROVED_CLAIMS.md`
§DEAD. Each with its finding note:

| dead claim | note file |
|---|---|
| "the model whose organization collapses most loses least" | `notes/FINDING-22-TWO-COLLAPSE-MODES.md` |
| "gemma-4 shows no first-pass organization collapse" | `notes/FINDING-13-hidden-reasoning-CONFOUND.md` |
| "hard enforcement universally improves accuracy" | `notes/FINDING-24-P4-NOTSUBMIT-CHECK.md` |
| "Arm B gets 2.5× more repair opportunity" | `notes/FINDING-17-LOCKIN-CORRECTED.md` |
| "per-opportunity, Arm B recovers better" | `notes/FINDING-17-LOCKIN-CORRECTED.md` |
| "roles prevent premature stopping" | `notes/FINDING-17-LOCKIN-CORRECTED.md` |
| "no accuracy claim is resolvable above scorer noise" | `notes/FINDING-21-SCORER-NOISE.md` |
| "gpt-oss's Arm B planner rubber-stamps" (it is uninstrumented) | `notes/FINDING-22-TWO-COLLAPSE-MODES.md` |
| "gpt-oss self-favours as a grader" | `notes/FINDING-21-SCORER-NOISE.md` |
| noise floor 0.0395 / 0.0023 / 0.0014 / 0.0092 (settled: **0.0086**) | `notes/FINDING-23-NOISE-FLOOR-SETTLED.md` |
| preregistered actor × enforcement interaction on accuracy (P4 null) | `PREREGISTRATION.md`, `notes/FINDING-24-P4-NOTSUBMIT-CHECK.md` |
| monotone unanimity → recovery damage across actors | `APPROVED_CLAIMS.md` §DEAD |
| "Huang et al. showed LLMs cannot self-correct even with oracle feedback" | `notes/FINDING-19-POSITIONING-AFTER-AUDIT.md` |
| "Arm C recovery highest of any arm, above Arm A in all three actors" | `STATISTICAL_AUDIT.md` FATAL-1 |
| Llama-3.3's null recovery is a "floor effect" | `STATISTICAL_AUDIT.md` SERIOUS-2 |

Eleven of these were killed by the project's own follow-up measurement or by
the adversarial statistical audit. The failure mode is not inventing them — it
is re-deriving one from an old note, or reaching for one because it makes a
paragraph flow better.

## 4. What is frozen?

- **The data.** `experiments/results/FROZEN/` — 3 JSONL, 11,600 rows, sha256 per file in `MANIFEST.json`, frozen `2026-09-30T10:09:30`, commit `74ab7da`. **Verified 2026-09-30.**
- **The numbers.** `analysis/out/FINAL_TABLES_OUTPUT.txt`, regenerable exactly.
- **The claims.** `APPROVED_CLAIMS.md`, frozen 2026-09-30, Master Agent is sole authority.
- **The preregistration.** `PREREGISTRATION.md`, committed before confirmatory results; three dated amendments. Primary tests may not be redefined.
- **The adjudication rubric.** `adjudication/RUBRIC_v1.md`, sha `4f624de5b1073940`, frozen before the first judgement.
- **The metrics** P1a / E2v2 (`notes/VALIDATION-FINAL.md`) — must not change post-hoc.

## 5. What is still active?

- **Closing out `STATISTICAL_AUDIT.md`** — FATAL-1 is fixed in the tables (`ba28977`); five SERIOUS findings remain open, in `paper/` and in `FINAL_TABLES.py` (T27's invalid ratio, the unapplied Holm correction).
- The manuscript (page budget 9 → 8; Overleaf sync). **Owned by the paper worker.**
- Figures — whether Fig 1 ships and on what measure. **Owned by the figures worker.**
- This documentation set.
- Bella-only admin: OpenReview, reciprocal reviewer, author list.

**No campaign is running.** Nothing is in flight on any endpoint. The data is
complete and frozen; there is nothing to babysit and no job to poll.

## 6. Where is everything?

Full map with authority labels: **`PROJECT_PATHS.md`**. Absolute paths:

```
project root   /Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols
frozen data    …/experiments/results/FROZEN/          <- NOT IN GIT, NO BACKUP
raw + logs     …/experiments/results/main/            <- byte-identical copy
final tables   …/analysis/out/FINAL_TABLES_OUTPUT.txt
table script   …/analysis/scripts/FINAL_TABLES.py
adjudication   …/adjudication/
figures        …/figures/                             <- other worker owns
paper          …/paper/                               <- other worker owns
claims         …/APPROVED_CLAIMS.md                   <- Master owns
notes          …/notes/FINDING-*.md                   <- audit trail, stale numbers
overleaf       /tmp/aamas_ol  (git.overleaf.com/6abae70ebd16e2dc9cdecee6)
auth helper    /Users/bellayang/work/agent-e/mas-eval/inference_auth_token.py
external data  /Users/bellayang/Documents/note/projects/IEEE-BigData-SciAgentTrace/
               analysis/hf_cache/release/data/{problems,trajectories}/part-00000.parquet
github         https://github.com/ChihHsuan-Yang/AAMAS2027-AgentProtocols
```

**Files you must not edit**: `paper/`, `figures/`, `APPROVED_CLAIMS.md`,
`analysis/scripts/FINAL_TABLES.py`. Other workers own them.

## 7. HPC, endpoints, launch, resume, logs, auth

**There is no HPC in this project.** No PBS, no `qsub`, no cluster filesystem,
no `/lus/eagle` path, no code staged on a login node. Everything ran from the
laptop as an HTTPS client.

| | |
|---|---|
| **endpoint** | `https://inference-api.alcf.anl.gov/resource_server/sophia/vllm/v1` (ALCF Sophia vLLM inference gateway) |
| **backend tag** | `sophia_vllm` on every one of the 11,600 rows; no cell straddles backends |
| **concurrency** | **24 global.** The measured ladder (`experiments/infra/throughput_ledger.md`) is clean to 25 for both reference actors: gpt-oss 189 req/min, gemma-4 143 req/min, 0% errors, 3–10% transient 429 retries. Untested above 25. |
| **auth** | Globus bearer token via `/Users/bellayang/work/agent-e/mas-eval/inference_auth_token.py`, cached at `~/.globus/app/<client>/<app>/tokens.json`. **Interactive re-auth needs a browser and a human.** Never written to disk or logs by this project. |

**The three runs, with their real launch commands** (reconstructed from the run
logs; `run_id` and `config_version` are recorded in each log's first line):

```bash
# campaign_v2 — 9,600 rows, run_id main-n1600-v2, config_version e3afa39849c1b980
python3 experiments/runner.py --n 1600 --arms A,B,C \
    --actors "openai/gpt-oss-120b,google/gemma-4-31B-it" \
    --out experiments/results/main/campaign_v2.jsonl \
    --run-id main-n1600-v2 --concurrency 24

# actor3 — 1,200 rows, run_id actor3-n400, config_version 231b8c4fe205d04b
python3 experiments/runner.py --n 400 --arms A,B,C \
    --actors "meta-llama/Llama-3.3-70B-Instruct" \
    --out experiments/results/main/actor3.jsonl \
    --run-id actor3-n400 --concurrency 24

# armCp — 800 rows, run_id armCp-n400, config_version 231b8c4fe205d04b
python3 experiments/runner.py --n 400 --arms Cp \
    --actors "openai/gpt-oss-120b,google/gemma-4-31B-it" \
    --out experiments/results/main/armCp.jsonl \
    --run-id armCp-n400 --concurrency 24
```

Runs were launched detached via `nohup` (smoke gate 15). **Logs**:
`experiments/results/main/{campaign_v2,actor3,armCp}.log`.

**How to resume:** re-run the identical command. One fsync'd line per completed
trajectory; on restart the runner skips every completed
`(problem_uid, arm, actor_model)` and prints `already complete (skipped): N`.
`model_unavailable` rows are not treated as complete and are retried, so a
backend outage is not baked into the dataset.

**Two `config_version` hashes exist and pooling was verified, not assumed**:
`e3afa398…` (A/B/C, the two reference actors) and `231b8c4f…` (C′ and all
Llama cells). No `(actor, arm, problem, role)` key appears under both, so no
within-actor A/B/C comparison mixes versions. The one cross-version comparison
is C′ vs C, and the diff between launch commits is purely additive — new `CP_*`
templates plus a visibility correction; no `C_*` prompt and no `MAX_*` knob
changed. See `RESULT_PROVENANCE.md`.

## 8. Exact regeneration commands

All executed 2026-09-30 with the exit status shown.

```bash
cd /Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols

# frozen-data integrity  — exit 0, 3/3 hashes OK
cd experiments/results/FROZEN && python3 -c "
import json,hashlib,os
m=json.load(open('MANIFEST.json'))
for f,v in m['files'].items():
    h=hashlib.sha256(open(f,'rb').read()).hexdigest(); n=sum(1 for _ in open(f))
    print(f,'OK' if (h==v['sha256'] and n==v['rows']) else 'MISMATCH')"; cd -

# FINAL TABLES — the authority.        exit 0, ~16 s, byte-identical to committed
python3 analysis/scripts/FINAL_TABLES.py > analysis/out/FINAL_TABLES_OUTPUT.txt

# statistics: blinded adjudication     exit 0, ~1 s
python3 adjudication/analyze.py

# number verification (live tree)      exit 0, ~25 s
python3 scripts/verify_paper_numbers.py

# launch gates                         exit 0, 15/15 pass
python3 scripts/smoke_gates.py experiments/results/smoke/smoke_v3.jsonl

# manifest integrity                   exit 0, 3/3 match
python3 -c "
import json,hashlib
for n in (1600,400,25):
    p=f'experiments/manifest_omnimath2_n{n}.json'; m=json.load(open(p)); s=m.pop('manifest_sha256')
    print(p,'OK' if hashlib.sha256(json.dumps(m,sort_keys=True).encode()).hexdigest()==s else 'MISMATCH')"

# figures — needs FIGDATA.json from the FINAL_TABLES run above.  exit 0.
# figures/ is owned by another worker; coordinate before regenerating.
python3 analysis/scripts/mk_fig1_dissociation.py   # -> fig1_v{1,2,3}_* .pdf/.png

# PDF build                            exit 0, 9 pages  (latexmk alone FAILS from clean)
cd paper && pdflatex -interaction=nonstopmode main.tex && bibtex main \
  && pdflatex -interaction=nonstopmode main.tex && pdflatex -interaction=nonstopmode main.tex \
  && pdfinfo main.pdf | grep Pages; cd -

# anonymity audit — on the RENDERED PDF, never the source
pdftotext paper/main.pdf /tmp/anon.txt
for t in AgentsSci ChihHsuan github.com huggingface Argonne ALCF Sophia bellayang; do
  printf '%s: %s\n' "$t" "$(grep -ci "$t" /tmp/anon.txt)"; done
pdfinfo paper/main.pdf | grep -Ei 'Author|Creator|Producer'
```

**Anonymity audit result 2026-09-30: all eight counts 0.** Author surnames
(Yang ×7, Jiang ×4, Zheng ×5, Thakur ×3, Vishwanath ×2, Chih-Hsuan ×3) appear
**only in bibliography entries [10], [19], [20]** — the three third-person
self-citations. That is the required blinding form, not a leak. PDF metadata
carries no Author field; Creator/Producer are toolchain strings.

## 9. How to continue after an interruption

1. **Orient.** `git -C <root> status` and `git log --oneline -10`. At handoff other workers had uncommitted changes in flight (`paper/sections/*.tex`, the rebuilt figure scripts, a statistical-audit script set, `hf_artifact/`). **`origin/main` was 16 commits behind local** — check before treating GitHub as current.
2. **Verify the data is still there and intact.** Run the frozen-data integrity command in §8. If `experiments/results/FROZEN/` is missing or a hash mismatches, **stop and tell Bella** — the numbers cannot be regenerated and there is no backup.
3. **Reproduce the numbers.** Run `FINAL_TABLES.py`, diff against the committed output. If it differs, something changed under you; find out what before doing anything else.
4. **Re-read the authority, not your memory.** `APPROVED_CLAIMS.md`, then `CLAIM_STATUS.md`. Do not restate a claim from recall — scope (which actors) is part of every claim here, and several claims are true for one actor and false for another.
5. **Check ownership before editing.** `paper/`, `figures/`, `APPROVED_CLAIMS.md`, `analysis/scripts/FINAL_TABLES.py` belong to other workers.
6. **Pick up P0** from §Current TODO / `TODO.md`.
7. **Nothing is running.** No campaign, no job, no endpoint work in flight. If you think you need a new campaign: Bella's approval is required for any new HPC/inference generation, and it is 8 days to the deadline with the data already frozen.

## 10. Six things that will bite you

1. **The frozen JSONL is not in git.** Clone ≠ reproducible. 297 MB, one machine, no backup.
2. **`latexmk -pdf main.tex` fails from a clean tree.** Use the four-command pdflatex/bibtex sequence.
3. **`figures/fig1_dissociation.*` is the superseded figure** — byte-identity collapse, a lower-bound metric whose scope reading is dead claim F22, read from `main/` not `FROZEN/`. The current script writes `fig1_v{1,2,3}_*` from `FIGDATA.json`. Do not revive the old one.
4. **Two scoring conventions disagree in sign for Arm C.** PREREG is primary; AS-GRADED is sensitivity only and carries 8–17% one-sided survivorship. Quoting the as-graded numbers as the headline would reproduce the pre-declared NOT-SUBMIT pattern (F24).
5. **T27 still prints an invalid statistic.** Its "effect ÷ noise floor = 3.9x clears" line is not a valid operation and is on the dead list, but `FINAL_TABLES.py` still emits it. (T1's Arm C recovery *was* the same kind of problem and **has** been fixed, in `ba28977` — so do not assume the reverse.)
6. **Old notes contain dead claims and stale numbers by design.** `notes/` is the audit trail. Retracted figures are kept visible on purpose. Source nothing from them.
