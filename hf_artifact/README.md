---
license: apache-2.0
task_categories:
  - question-answering
language:
  - en
tags:
  - multi-agent
  - llm-agents
  - reasoning
  - agent-trajectories
  - self-correction
size_categories:
  - 10K<n<100K
configs:
  - config_name: trajectories
    data_files: data/trajectories.parquet
  - config_name: evaluator_calls
    data_files: data/evaluator_calls.parquet
  - config_name: role_messages
    data_files: data/role_messages.parquet
  - config_name: enforcement_events
    data_files: data/enforcement_events.parquet
  - config_name: adjudication
    data_files: data/adjudication.parquet
---

# Role structure in multi-agent LLM problem solving — trajectory dataset

<!-- ANONYMIZED FOR DOUBLE-BLIND REVIEW.
     Do NOT add author names, institution, funding, grant numbers, repository
     URLs, or a citation block until the paper is accepted.
     See RELEASE_PROCEDURE.md. -->

A controlled study of whether **role structure** in a multi-agent LLM pipeline
is load-bearing. 11,600 trajectories, 3 actor models, 4 conditions, 1,600
competition-math problems, with an external oracle grader in the loop.

This release ships **both layers**: the raw frozen traces as exact bytes, and a
normalized analysis-ready parquet layer derived from them.

**Anonymous during review.** Author, institution, and code repository are
withheld and will be added on acceptance.

## The finding, in one sentence

Role structure is not load-bearing for generating a first answer, but it can be
load-bearing for **repairing** an initially wrong one.

Removing roles leaves first-pass accuracy unchanged (and for one actor slightly
improves it) while degrading recovery from a wrong first answer — for the
clearest actor, 0.222 → 0.051. The mechanism is not premature stopping and not
less feedback: every arm holds the same 6 deliberation cycles by construction,
and the role-free arm receives *more* oracle feedback. It is failure to produce
a distinct second candidate. Hard enforcement restores organization and
un-freezes answers, but does **not** improve final accuracy, because it is
brittle (8–17% attrition).

The effect is **actor-dependent** and the cells where it does not replicate are
released intact.

## Design

| arm | condition |
|---|---|
| **A** | full role structure — distinct planner / executor / reviewer prompts |
| **B** | role structure removed — three agents, one generic prompt |
| **C** | hard enforcement — role-boundary violations rejected and regenerated |
| **C′** | context control at fixed enforcement (C with `shared_history` restored) |

| actor model | A | B | C | C′ |
|---|---|---|---|---|
| `google/gemma-4-31B-it` | 1,600 | 1,600 | 1,600 | 400 |
| `openai/gpt-oss-120b` | 1,600 | 1,600 | 1,600 | 400 |
| `meta-llama/Llama-3.3-70B-Instruct` | 400 | 400 | 400 | — |

Grader: `openai/gpt-oss-120b`, temperature 0 — **the same checkpoint as one of
the three actors**. Budget identical across arms (3 outer × 2 inner = 6 cycles),
temperature 0, `max_tokens` 8192. Corpus: 1,600 Omni-MATH-2 problems, one
domain (competition math).

`config/` holds the **exact** prompts, JSON schemas and every knob. The paper is
about role manipulation, so the data is not interpretable without them.

## Contents

| path | what |
|---|---|
| `raw/` | **the frozen traces, exact bytes** — `campaign_v2.jsonl` (9,600), `actor3.jsonl` (1,200), `armCp.jsonl` (800) + `MANIFEST.json` |
| `data/trajectories.parquet` | 11,600 rows — one per trajectory; the main results tables |
| `data/role_messages.parquet` | 83,320 rows — one per role message; collapse, duplication, frozen-answer analyses |
| `data/evaluator_calls.parquet` | 17,486 rows — one per oracle grading; the noise-floor analysis |
| `data/enforcement_events.parquet` | 29,796 rows — Arm C/C′ validation attempts, **3,489** rejections, regenerations |
| `data/adjudication.parquet` | 513 rows — 171 items × up to 3 reps of model adjudication |
| `config/` | all 22 prompts, 3 JSON schemas, budgets, visibility policy |
| `adjudication/` | the study's protocol, rubric, blinded items, key, verdicts |
| `manifests/`, `LICENSES/` | frozen-snapshot manifest, per-cell census, problem ids; per-source licensing |
| `SCHEMA.md` | every column, and the defects in full |
| `VERSION`, `CHECKSUMS.txt`, `MANIFEST.json` | integrity and provenance |

Total ~352 MB. Raw and derived layers are consistent by construction: the build
verifies the snapshot sha256 before deriving anything and refuses on mismatch.

## Quick start

```python
import pandas as pd
tr = pd.read_parquet("data/trajectories.parquet")

for arm in ["A", "B"]:
    s = tr[(tr.actor_model == "gemma-4-31B-it") & (tr.arm == arm)]
    g, w = s[s.graded], s[s.first_pass_wrong]
    print(arm,
          "first-pass %.3f" % g.first_pass_correct.mean(),
          "recovery %.3f"   % w.final_correct_prereg.mean(),
          "frozen %.3f"     % w.frozen_answer.mean())
# A first-pass 0.802 recovery 0.222 frozen 0.288
# B first-pass 0.802 recovery 0.051 frozen 0.845
```

## Which analyses are primary, exploratory, invalid, superseded

**Primary.** First-pass accuracy and recovery under `final_correct_prereg`
(ungraded = 0, the pre-registered outcome); the paired A-vs-B recovery contrast;
the *mechanical* organization measures (functional collapse, numeric-token
duplication over a shuffled null); Arm C attrition.

**Exploratory / secondary.** The model adjudication — an outcome-blind second
opinion, **not** ground truth and **not** condition-blind (see below).
Everything conditioned on first-pass-wrong is post-treatment: descriptive and
associational, never causal.

**Sensitivity only, never primary.** `final_correct_asgraded` drops ungraded
trajectories and so inherits Arm C's 8–17% **one-sided** attrition; it flips the
sign of the C−A contrast (prereg gemma-4 −0.0225 SIG-negative vs as-graded
+0.0190 SIG-positive). Quoting it as the headline would manufacture the opposite
conclusion out of survivorship.

**Invalid — do not compute.** Any text-length measure over `gpt-oss-120b` Arm B
(F13: you are measuring the logger). `f18_mismatch` as a filter or covariate in
an arm contrast (post-treatment by construction). Grouping the noise floor on
`final_answer_held` instead of `candidate_normalized` (inflates ~6×, and
measures F18 rather than the grader). Dividing an effect size by the noise floor
— "effect / floor" is **withdrawn**, it is not a valid operation.

**Superseded.** Earlier drafts of this work reported: a blinded-adjudication
confirmation of the arm contrast (the blinding leaks — see below); Arm C
recovery "highest of any arm in all three actors" (the recovery denominator
dropped trajectories that got a first verdict then died in regeneration;
corrected, two of three paired p-values are lost — 0.298 and 0.105 — and only
Llama-3.3 survives at p=3.8e-06); and a grader noise floor of 0.0086. None of
these should be reused.

---

# Known instrumentation defects

Five. A consumer who does not read this section will trip over them.

### F13 — visible text is truncated relative to hidden reasoning (gpt-oss, Arm B)

The runner logged `message.content` and fell back to `message.reasoning` **only
when content was empty**. A response with short content and a long hidden
reasoning trace was logged as the short content, and `used_reasoning_fallback`
stayed `False`, so the loss is undocumented.

Its Arm B planner logs a median **37 characters at 2.85 chars/sec**, against
**4,824 characters at 195.16 chars/sec** in its own Arm A. **75.7%** of that
cell's role messages fall below 10 chars/sec; the documented flag fired on
**0** of the 2,302 sub-100-character planner messages.

**Its planner output is *uninstrumented*, not absent.** The work was done and
the logger discarded it. Any text-based measure over this cell measures the
instrument. Detect with `chars_per_sec`; exclude the cell and say so.

A later commit fixed the logger. **It did not reach any released row** —
measured directly, the gpt-oss Arm B planner median is 37 chars before the fix
commit and 36 after, so the release is uniform. Note `config_version` does
**not** change across that fix and therefore cannot be used to detect this.

### F18 — `correct` grades the last SUBMITTED answer, `final_answer` is the last answer HELD

A team that revises after its final submission is graded on the answer it
abandoned. Mismatch rate among first-pass-wrong trajectories:

| actor | arm A | arm B | arm C |
|---|---|---|---|
| gemma-4 | 0.171 | 0.000 | 0.363 |
| gpt-oss | 0.164 | 0.066 | 0.258 |
| Llama-3.3 | 0.058 | 0.004 | 0.478 |

So the defect reaches **up to ~17% in Arm A** and considerably higher in Arm C.
Totals: 509 mismatched first-pass-wrong trajectories, **62 demonstrably
under-credited** (held answer exactly matches gold, graded 0). Positive control
on the 10,734 non-mismatched graded rows finds **0** such cases, so 62 is a
clean floor rather than a matching artifact.

**The defect is concentrated in the arms that revise**, i.e. it works *against*
the paper's headline — correcting it would widen the gap. Primary analysis stays
as recorded (it is the pre-registered outcome and the conservative direction).
`f18_mismatch` and `f18_under_credited` are for **bounding**, not correcting:
the rate is a function of revision behaviour, which is the treatment.

### Arm C attrition — 8.0 / 9.9 / 17.0%, and it is one-sided

Regeneration-exhaustion attrition is **0.080** (gemma-4), **0.099** (gpt-oss),
**0.170** (Llama-3.3), against 0.000–0.025 in Arms A/B.

**The recovery denominator must INCLUDE trajectories that got a first verdict
and then died in regeneration.** An earlier implementation used
`graded(r) and first_pass==0`, which silently dropped them — and *all* of them
are first-pass-wrong structurally, because a PASS on the first verdict ends the
loop. They meet the definition and score 0 under pre-registered scoring.

Three counts circulate; each is correct for its own scope — **quote the one
matching your sentence**: Arm C only **150**; Arm C + C′ **173**; all arms
**178** (A 1, B 4, C 150, C′ 23).

Correcting this moved recovery to gemma-4 0.314, gpt-oss 0.395, Llama 0.139, and
cost two of three paired A-vs-C p-values.

### Adjudication condition leak — outcome-blind, NOT condition-blind

`adjudication/PROTOCOL.md` records role names neutralized to `Agent-P/E/R` with
"residual leaks: 0". **True of the strings, false of the signal:** the tokens
were renamed, their *presence* was not equalized.

| arm | has an `Agent-P/E/R` token | none |
|---|---|---|
| A | **42** | 0 |
| B | **3** | 53 |
| C | 0 | 44 |
| C′ | 0 | 29 |

Fisher exact A vs B on token presence: **p = 1.5e-24**. The arms are further
separable by output format — Arm C carries JSON `answer`/`verdict` fields while
A/B carry `\boxed` and `[Agree]`. A judge could identify the condition without
reading content.

Unaffected (within-item): judge stability (0.947 / 0.959 / 0.953 for Q1/Q2/Q5)
and precision 1.000 / recall 0.262. Affected: **every arm-contrastive
adjudication number**, including A 0.000 vs B 0.964 and C 0.136.

**Do not describe any arm contrast here as "blinded".** A re-run would not fix
it — the manipulation is partly an intervention on output format — so this is a
disclosure, not a defect awaiting repair. The paper's organization claim rests
instead on the *mechanical* measures, which involve no judge: functional
collapse 0.976 / 0.846 / 0.872 in Arm B vs 0.000 / 0.120 / 0.000 in Arm A, and
numeric-token duplication as excess over a shuffled null (B−A +0.290 gemma-4,
+0.287 Llama-3.3; gpt-oss excluded per F13).

### Repaired denominator bugs — `graded()` vs `judged()`

The survivorship error above had **four known sites**. Two mattered:

- **Recovery** — fixed as described.
- **First-pass accuracy in Arm C**, one column to the left, same error. Arm C
  first-pass moved gemma-4 0.822 → **0.779**, gpt-oss 0.788 → **0.761**, Llama
  0.295 → **0.281**, C′ 0.825 → 0.810 and 0.773 → 0.740. The A-vs-B headline is
  unchanged (it comes from the paired path).

A self-check now asserts `(1 − first_pass) × n == n_fpw` per cell. If you
recompute a denominator, use `judged()`, and state which of the three
attrition-inclusive counts you used.

### Also worth knowing

- **Grader noise floor: 0.0072** group-level — 20 of 2,790 distinct graded
  strings receive contradictory verdicts across byte-identical prompts at
  temperature 0. Range 0.0017–0.0072 across estimators. **Not 0.0086**; the key
  must be the exact candidate bytes (`candidate_normalized`).
- **Mangled LaTeX escapes**: 135 of 11,498 `final_answer_held` and 176 of 17,486
  `candidate_raw` values contain C0 control characters where a macro was
  intended (`\frac` → `\x0crac`). Preserved as-is so the artifact matches what
  the evaluator actually graded.
- **One adjudication item (T0016) has only 2 reps and a tied Q5 vote.** The
  pooled Arm B rate is 0.964 under the project's aggregation and 0.982 if the
  tie breaks the other way. One item, and it is the only tie.

## Scope and limitations

- **Single benchmark, single domain.** Competition math only. A SciBench
  second-domain campaign is reserved as v1.1.0 (`config/SECOND_DOMAIN_SLOT.md`)
  and is **not** in this release.
- **Three actors, and the effect does not replicate in all three.** gemma-4 is
  clean (recovery 0.222 → 0.051, paired McNemar p=1.95e-08). gpt-oss is weaker
  and **not significant when paired** (0.324 → 0.247, p=0.208). Llama-3.3 does
  **not** replicate (0.014 → 0.015). Llama's null is **not** a floor effect —
  Arm C restores recovery in that same actor (0.096 vs 0.009, p=3.81e-06), so
  the repair channel exists and role labels simply do not open it there.
- **Recovery is oracle-gated.** No cell recovers before the first oracle verdict.
  This measures repair under external feedback, not spontaneous self-correction.
- **The grader shares a checkpoint with one actor.** Relevant to any
  self-grading concern.
- **The pre-registered primary (P4) is null.** All three actor × enforcement
  difference-in-differences contain zero. Two of the three have MDE 0.069 and
  0.075 against plausible effects ≤ 0.040, so only the gpt-oss–gemma DiD
  (MDE 0.033) is an informative null.
- **Adjudication is model adjudication** (`claude-opus-5`), not human
  annotation and not ground truth.
- **Wall-clock timings reflect shared infrastructure**, including queueing.

## Licensing

**Per source — this release does not blanket one licence over source-derived
material.** See `LICENSES/README.md` and `LICENSES/registry.json`.

- **Our derived material** (parquet structure, scripts, docs, manifests):
  **Apache-2.0**.
- **Upstream problems: Omni-MATH-2, Apache-2.0** — verified against the upstream
  Hugging Face API license tag and cross-checked against two files in the
  release registry.
- **Model-generated trajectory text** is governed by the respective model
  providers' terms.

**What upstream text is actually redistributed.** No gold answers — no
gold/reference field exists in any released row. The parquet layer ships no
`problem_text` column. **But problem text is incidentally redistributed inside
transcripts**: agents restate the problem, so a 60-character problem prefix
appears verbatim in `role_messages.text` for 16 of 606 checked problems (2.6%),
and the **raw traces carry the full prompts**. Apache-2.0 permits this with
attribution; it is stated rather than denied, because "only `problem_uid` is
redistributed" is not accurate for the trace layer.

Omni-MATH-2 is marked `evaluation_only_recommended` upstream: we recommend
evaluation and analysis use rather than training.

## Provenance and integrity

Derived from a sha256-manifested frozen snapshot (`raw/MANIFEST.json`, freeze
`2026-09-30T10:09:30Z`). `CHECKSUMS.txt` covers every file; `MANIFEST.json`
records per-trace sha256, rows, bytes, semantic version, freeze commit,
timestamps, arms, actors, domain, backend and config version.

`scripts/validate_artifact.py` re-derives **181 published values** from the
parquet layer and checks them against the project's canonical analysis output —
**181/181 pass**, re-run against the canonical output as regenerated
2026-09-30 14:49Z.

Two `config_version` values appear (`e3afa39849c1b980`, 9,600 rows;
`231b8c4fe205d04b`, 2,000 rows). They differ **only** by the addition of the
Arm C′ entry — every A/B/C prompt, schema and knob is byte-identical across
them, verified by recomputing the hash at each source commit.
