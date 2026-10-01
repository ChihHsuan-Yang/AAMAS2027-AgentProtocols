---
# NOTE: this field carries ONE value and covers THIS PROJECT'S OWN derived
# material only. v1.1.0 is MIXED-LICENCE: Omni-MATH-2 content is Apache-2.0
# and SciBench content is MIT. See LICENSES/README.md, which is the authority.
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
  - config_name: scibench_trajectories
    data_files: data/scibench/trajectories.parquet
  - config_name: scibench_evaluator_calls
    data_files: data/scibench/evaluator_calls.parquet
  - config_name: scibench_role_messages
    data_files: data/scibench/role_messages.parquet
---

# Role structure in multi-agent LLM problem solving — trajectory dataset

<!-- ANONYMIZED FOR DOUBLE-BLIND REVIEW.
     Do NOT add author names, institution, funding, grant numbers, repository
     URLs, or a citation block until the paper is accepted.
     See RELEASE_PROCEDURE.md. -->

A controlled study of whether **role structure** in a multi-agent LLM pipeline
is load-bearing. **13,896 trajectories across two domains** — 11,600 on
competition mathematics (Omni-MATH-2, 1,600 problems, 3 actors, 4 conditions)
and **2,296 on college chemistry and physics (SciBench, 574 problems, 2 actors,
2 conditions, added in v1.1.0)** — with an external oracle grader in the loop.

This release ships **both layers**: the raw frozen traces as exact bytes, and a
normalized analysis-ready parquet layer derived from them.

> **Two domains, two licences, two Arm A contracts.** Omni-MATH-2 content is
> **Apache-2.0**; SciBench content is **MIT**. And **Arm A's prompt is NOT the
> same in both domains** — it was deliberately adapted. Arm B *is* byte-identical.
> Read *Cross-domain (v1.1.0)* before pooling anything.

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

**Second domain — SciBench (v1.1.0), Arms A and B only:**

| actor model | A | B | C | C′ |
|---|---|---|---|---|
| `google/gemma-4-31B-it` | 574 | 574 | — | — |
| `openai/gpt-oss-120b` | 574 | 574 | — | — |

There is **no Arm C in SciBench**, so there is **no `enforcement_events` table
and no adjudication study for that domain**. Those remain Omni-MATH-only.

Grader: `openai/gpt-oss-120b`, temperature 0 — **the same checkpoint as one of
the three actors** — in both domains. Budget identical across arms *and across
domains* (3 outer × 2 inner = 6 cycles), temperature 0, `max_tokens` 8192.
Corpora: 1,600 Omni-MATH-2 competition-math problems, and 574 SciBench
college chemistry/physics problems.

`config/` holds the **exact** prompts, JSON schemas and every knob. The paper is
about role manipulation, so the data is not interpretable without them.

## Contents

| path | what |
|---|---|
| `raw/` | **the frozen traces, exact bytes** — `campaign_v2.jsonl` (9,600), `actor3.jsonl` (1,200), `armCp.jsonl` (800) + `MANIFEST.json`; **`scibench_AB.jsonl` (2,296) + `MANIFEST_SCIBENCH.json`** |
| `data/trajectories.parquet` | 11,600 rows — one per trajectory; the main results tables |
| `data/role_messages.parquet` | 83,320 rows — one per role message; collapse, duplication, frozen-answer analyses |
| `data/evaluator_calls.parquet` | 17,486 rows — one per oracle grading; the noise-floor analysis |
| `data/enforcement_events.parquet` | 29,796 rows — Arm C/C′ validation attempts, **3,489** rejections, regenerations |
| `data/adjudication.parquet` | 513 rows — 171 items × up to 3 reps of model adjudication |
| **`data/scibench/trajectories.parquet`** | **2,296 rows** — SciBench, same 41 columns as the Omni table |
| **`data/scibench/role_messages.parquet`** | **13,500 rows** — SciBench role messages |
| **`data/scibench/evaluator_calls.parquet`** | **3,699 rows** — SciBench oracle gradings |
| `config/` | all 22 Omni prompts, 3 JSON schemas, budgets, visibility policy |
| **`config/prompts_scibench.json`** | **the 16 SciBench prompts + a per-prompt identical/differs table vs Omni** |
| **`config/run_config_scibench.json`** | **the SciBench config: budgets, visibility, denominators, licence** |
| `adjudication/` | the study's protocol, rubric, blinded items, key, verdicts |
| `manifests/`, `LICENSES/` | frozen-snapshot manifest, per-cell census, problem ids; per-source licensing (incl. **`MIT-SciBench.txt`**) |
| **`analysis/SAMPLING_AUDIT.md`** | **the full sampling + denominator audit for both domains** |
| `SCHEMA.md` | every column, and the defects in full |
| `VERSION`, `CHECKSUMS.txt`, `MANIFEST.json` | integrity and provenance |

Total ~382 MB (v1.1.0 adds ~30 MB). Raw and derived layers are consistent by
construction: each build verifies its snapshot sha256 before deriving anything
and refuses on mismatch. The v1.1.0 build additionally **asserts that every
v1.0.0 file is byte-unchanged**, so "additive" is verified rather than promised.

**Separating the domains is always a filter**, never a guess: every row carries
`benchmark_id` (`omnimath2` / `scibench`) and `domain` (`math` / `science`),
one distinct value per table, and the two domains live in separate parquet
files as well.

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

## Cross-domain (v1.1.0) — SciBench, and what does **not** transfer

### The Arm A contract is NOT the same in both domains. Read this first.

| prompt | Omni-MATH-2 vs SciBench |
|---|---|
| `A_SOLVER_PREPEND` (planner) | **DIFFERS** — domain-adapted |
| `A_EXECUTOR_PREPEND` | **DIFFERS** — domain-adapted |
| `A_CRITIC_PREPEND` / `A_CRITIC_APPEND` (reviewer) | **DIFFERS** — domain-adapted |
| `A_SOLVER_APPEND`, `A_EXECUTOR_APPEND` | identical |
| **`B_GENERIC_PREPEND` / `B_GENERIC_APPEND`** | **BYTE-IDENTICAL** (asserted in code at build time) |
| `EVALUATOR_PREPEND` | **DIFFERS** — adapted for units / sig-figs / scientific notation |
| `EVALUATOR_APPEND`, all `C_*` | identical |

**5 of 16 prompts differ.** Both prompt sets ship in full
(`config/prompts.json`, `config/prompts_scibench.json`), and
`prompts_scibench.json._COMPARISON_TO_OMNIMATH` gives a per-prompt
identical/differs flag with sha256 prefixes so you can check this yourself.

**Why adapt rather than reuse.** Arm B's generic prompt contains no domain
language at all. Leaving Arm A's math-specific wording ("competition-level
mathematics", "olympiad-style") in a chemistry benchmark would make the arms
differ in **two** ways — role structure *and* domain fit — and the domain-fit
difference runs **against** Arm A. Adapting A restores a single-variable
manipulation. Every structural clause of A is preserved (role separation,
DELTA, required structure, Diagnosis/Fix Instruction, answer ownership,
routing tags); only domain nouns and the answer-form enumeration change.

**Consequence — do not compute these across domains.** P1a and every
clause-specific role-fidelity metric. Scoring SciBench agents against
Omni-MATH's clauses would score them against instructions they never received.
The evaluator adaptation is **common mode**: byte-identical across arms A and B
*within* SciBench, so it cannot manufacture an A-vs-B difference — it only sets
the difficulty floor.

### What replicates

Paired on problems first-pass-wrong under **both** arms — the same population
the Omni-MATH headline uses:

| domain | actor | n | A recovers only | B recovers only | B−A | exact McNemar p |
|---|---|---|---|---|---|---|
| Omni-MATH | gemma-4 | 237 | 37 | 3 | −0.1435 | 1.95e-08 |
| **SciBench** | **gemma-4** | **99** | **21** | **2** | **−0.1919** | **6.60e-05** |
| **SciBench** | gpt-oss | 96 | 17 | 9 | −0.0833 | 0.169 (**unresolved**) |

The two gemma effects are **not distinguishable**: a two-proportion test on the
discordant rates gives **z=1.04, p=0.300** (pooled variance) or **z=0.95,
p=0.342** (unpooled) — re-derived here from the released tables. *The campaign
notes record z=1.06, p=0.289; we could not reproduce that exact pair and quote
ours. The conclusion is identical under all three — the effects are
indistinguishable — and none of them is evidence that the effects are the
**same**, only that this comparison cannot separate them.* First-pass accuracy moves by **exactly
0.000** for gemma (0.794 vs 0.794), as in Omni-MATH. Functional collapse goes
0.000 → 0.998. Arm B spends **0.00** cycles revising and never once declines.

### What must NOT be claimed from this

- ❌ "The result generalizes across domains." **One actor** replicated in **one**
  further domain.
- ❌ "Replicates across two benchmarks" / "two of three actors" — Llama-3.3 was
  **never run** on SciBench.
- ❌ Any **pooled** SciBench+Omni statistic. The two actors' effects differ by a
  factor of two; pooling averages a detectable effect with an undetectable one.
- ❌ Any cross-domain P1a or clause-specific fidelity comparison (see above).
- ❌ Reading gpt-oss's SciBench null as **absence** of an effect. See below.

### gpt-oss's SciBench cell resolves nothing — it is not a non-replication

Its point estimate (−0.083) is in the same direction and almost exactly its own
Omni-MATH effect (−0.077), but at n=96 the cell is **underpowered against an
effect of that size**. This was pre-registered at 761/2,296 rows, *before* any
recovery contrast existed, precisely so the reading could not be chosen
afterwards.

**Power, stated honestly.** The campaign notes record 0.42. We could not
reproduce that figure and report the spread instead — against this cell's own
observed effect at n=96:

| method | power |
|---|---|
| **exact McNemar, two-sided — the test actually used for the p-value** | **0.26** |
| bootstrap-CI rule (the project's own), two-sided | 0.36 |
| McNemar normal approximation | 0.35 |
| unpaired two-proportion z, two-sided | 0.33 |
| exact McNemar, one-sided | 0.40 |
| unpaired two-proportion z, one-sided | 0.45 |

Every method lands **below** the 0.42 in the notes, and the test that produced
the reported p=0.169 gives **0.26**. The qualitative conclusion is unchanged and
in fact strengthened: this cell **cannot resolve its own effect** and a
consumer must not read its null as absence. Against a *gemma-sized* effect the
same cell has power ≈0.99, so it could have detected a large effect and did
not. **Do not quote 0.42 from the notes; quote 0.26 with the test named, or the
range.**

### Denominators — both domains, in full

| | Omni-MATH-2 | SciBench |
|---|---|---|
| upstream pool | 4,181 matched | **692 published** |
| present in the release registry | — | **580** |
| carrying the runnable slice | — | **574** (`text_only`) |
| **actually run** | **1,600** (38.3%) | **574 — ALL of them** |
| selection | uniform random, **seed 20270101** | **none — no sub-sampling, no seed** |

**Omni-MATH's 1,600 is a uniform random draw of the whole 4,181 pool** — not
tier-specific, not difficulty-stratified, not purposive. It is not
distinguishable from the pool: two-sample **KS D=0.0251, p=0.449** on
`difficulty_score`, and **chi-square p=0.106** on source subset. Drawn by
`runner.load_problems(n=1600, seed=20270101)`; re-derivable with
`analysis/scripts/audit_sampling.py` in the project repo; its output ships
here as **`analysis/SAMPLING_AUDIT.md`**.

**SciBench ran every problem it could run — 574 of 574, no sampling step.**
Two subtractions get there, and they are **independent, not the same items
counted twice**:

- **580 → 574:** 6 released rows lack the `text_only` slice this protocol
  requires. All six are listed by `problem_uid` in **`analysis/SAMPLING_AUDIT.md`, shipped in this artifact**.
- **692 → 580: NOT RECOVERABLE FROM THIS RELEASE, and no reason is asserted.**
  The released problems table contains only rows that survived the upstream
  build, so the 112 excluded items are absent from it entirely and carry no
  reason code. **An earlier draft of that audit asserted a reason — figure/table
  items plus collisions — and it was retracted as an inference presented as a
  measurement.** Establishing the 112 would require diffing the upstream
  SciBench release against this table. It does not affect any denominator
  reported here, because the denominator is the 574 actually run.

Separately, 6 of the 580 rows carry `conflicting_source_id_disambiguated`;
these are a **disjoint** set from the 6 missing the slice.

**`574 matched` is not `574 total benchmark`.** Say which of 692 / 580 / 574
you mean.

---

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

A consumer who does not read this section will trip over them. **F13 and F18
reproduce in the second domain**, and the grader noise floor is
**domain-specific** — each has its own subsection below.

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

### F18 in SciBench — it reproduces, and again runs **against** the headline

The defect transfers to the second domain. Among first-pass-wrong trajectories:

| actor | arm A | arm B |
|---|---|---|
| gemma-4 | **0.288** | 0.000 |
| gpt-oss | 0.105 | 0.017 |

**49 mismatched** first-pass-wrong trajectories, **2 demonstrably
under-credited** (held answer exactly matches gold, graded 0). The positive
control on the 2,247 non-mismatched graded rows finds **0** such cases, so 2 is
a clean floor rather than a matching artifact — the same control, and the same
result, as the Omni-MATH layer.

**Same direction as Omni-MATH: it is concentrated in the arm that revises, so
correcting it WIDENS the gap.** Re-scoring on the held answer moves gemma-4's
paired recovery contrast from −0.1919 (p=6.6e-05) to **−0.2020 (p=3.6e-05)**,
and leaves gpt-oss **exactly unchanged** at −0.0833 (p=0.169). **No verdict
flips in either domain.** Primary analysis stays as recorded — the
pre-registered outcome and the conservative direction.

As in v1.0.0: `f18_mismatch` is for **bounding, not correcting**, and must
never be used as a filter or covariate in an arm contrast — the mismatch rate
is a function of revision behaviour, which *is* the treatment.

### The grader noise floor is domain-specific — 2.80% here vs 0.72% on Omni-MATH

Disagreement rate across **byte-identical** candidate strings graded at
temperature 0, keyed on exact candidate bytes:

| domain | discordant / multi-graded groups | floor |
|---|---|---|
| Omni-MATH-2 | 20 / 2,790 | **0.0072** |
| **SciBench** | **19 / 678** | **0.0280** |

**The SciBench grader is ~4× noisier**, which is unsurprising: it must judge
unit equivalence, significant figures and scientific notation rather than
symbolic equality. The gemma effect (−0.19) is far larger than this floor, but
**do not compute "effect ÷ floor"** — that statistic is **withdrawn** project-wide
in both domains; dividing an effect size by a disagreement rate is not a valid
operation, and grader noise largely cancels in a paired contrast anyway.

> **A note on a figure you may see elsewhere.** The campaign notes compare
> SciBench's 2.80% against "9.35% on Omni-MATH". **That 9.35% is not an
> Omni-MATH measurement from this project** — it traces to a finalizer-
> nondeterminism figure recorded on a *different* project and was carried over
> as a comparison. Measured on this release's own frozen data by the same
> method, Omni-MATH's floor is **0.0072** (0.0086 under the superseded
> whitespace-stripped key). So SciBench's grader is ~4× *noisier* than
> Omni-MATH's, not 3× quieter. **Use 0.0072 vs 0.0280.**

### F13 reproduces in SciBench, in the same cell

`gpt-oss-120b` Arm B is uninstrumented here too: planner median **123 chars at
20.0 chars/sec** and executor/reviewer at **8.6 / 7.7 chars/sec**, against
**2,726 chars at 212 chars/sec** for its own Arm A planner. 34–64% of that
cell's role messages fall below 10 chars/sec. gemma-4 is clean in both arms
(≥127 chars/sec throughout).

**Any text-length measure over `gpt-oss-120b` Arm B is invalid in this domain
too.** Detect with `chars_per_sec`, never with `config_version`.

Two things are *better* here: there are **no mangled LaTeX escapes** (0 of
2,296 `final_answer_held`, 0 of 3,699 `candidate_raw`, versus ~1% in
Omni-MATH), and **no attrition at all** — 0 hard failures, 0 unjudged, all four
cells exactly 574.

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

- **Two benchmarks, two domains — but the second is a partial replication.**
  Competition math (Omni-MATH-2, 3 actors, 4 arms) and college
  chemistry/physics (SciBench, **2 actors, 2 arms only**). SciBench has no
  Arm C, no Arm C′, no Llama-3.3 and no adjudication study. **One actor
  (gemma-4) replicated in the second domain; the other cell cannot resolve its
  own effect (power ≈0.26).** This is not "the finding generalizes".
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
> **MIXED LICENCE as of v1.1.0 — do not blanket-apply one licence.**
> Filter by `benchmark_id` to know which terms govern which rows.

| content | licence | verified |
|---|---|---|
| **Omni-MATH-2 problems** (`benchmark_id='omnimath2'`) | **Apache-2.0** | upstream HF API tag `license:apache-2.0` + `cardData.license`, anonymous fetch, cross-checked against two registry files |
| **SciBench problems** (`benchmark_id='scibench'`) | **MIT**, © 2023 Xiaoxuan Wang | upstream `LICENSE` file fetched anonymously + GitHub API `spdx_id: MIT` + two registry files — **three independent sources, all agreeing** |
| **This project's derived material** (parquet structure, scripts, docs) | Apache-2.0 | authored by us |
| **Model-generated trajectory text** | the model providers' terms | — |

SciBench's MIT is **not** absorbed into the Apache-2.0 material; its verbatim
notice ships at `LICENSES/MIT-SciBench.txt` as the MIT terms require. The HF
`license:` metadata field carries one value and describes **our own** material
only. `LICENSES/README.md` and `LICENSES/registry.json` are the authority.

**What upstream text is actually redistributed.** The parquet layer ships no
`problem_text` column and no gold-answer column, in either domain.

- **Problem text is incidentally redistributed inside transcripts.** Agents
  restate the problem: a 60-character problem prefix appears verbatim in
  `role_messages.text` for **16 of 606** Omni-MATH problems (2.6%) and **0 of
  574** SciBench problems (0.0% — short numeric items get paraphrased into
  tables of givens). The **raw traces carry more** in both domains.
- **Gold answers: no column, but a small measured leak in grader free text.**
  The evaluator was instructed never to reveal ground truth and occasionally
  names the expected value in its repair hint anyway: **Omni-MATH 23 of 17,486
  `evaluator_raw` rows (14 of 1,600 problems, 0.9%)**; **SciBench 19 of 3,699
  rows (4 of 574 problems, 0.7%)**. v1.0.0 stated "no gold/reference field
  exists in any released row" — true at the **column** level, which is what was
  checked, but it did not cover free text the grader wrote. **Corrected here
  for both domains rather than left standing.** Far too sparse to reconstruct a
  gold set, and permitted under both licences with attribution.

Both upstreams are marked `evaluation_only_recommended`: we recommend
evaluation and analysis use rather than training, in **both** domains.

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
