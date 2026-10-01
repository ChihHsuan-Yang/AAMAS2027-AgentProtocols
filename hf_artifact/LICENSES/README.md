# Licensing

`registry.json` is the machine-readable version of this page and is the
authority. Each upstream source carries its **own** licence; this release does
**not** blanket one project licence over source-derived material.

> ## ⚠ v1.1.0 IS MIXED-LICENCE — DO NOT BLANKET-APPLY ONE LICENCE
>
> This release now ships **two upstreams under two different licences**.
> **Omni-MATH-2 is Apache-2.0. SciBench is MIT.** Neither is applied over the
> other, and this project's own Apache-2.0 statement covers **neither**.
>
> Filter by `benchmark_id` / `domain` to know which terms apply:
>
> | `benchmark_id` | `domain` | upstream licence | n problems | added |
> |---|---|---|---|---|
> | `omnimath2` | `math` | **Apache-2.0** | 1,600 | v1.0.0 |
> | `scibench` | `science` | **MIT** | 574 | **v1.1.0** |
>
> The repository's Hugging Face `license:` metadata field can carry only **one**
> value. It is set to `apache-2.0` **for this project's own derived material**.
> That field is **not** a statement about SciBench content. This page and
> `registry.json` are the authority.

## Four different things, four different licences

| layer | licence | notes |
|---|---|---|
| **Our derived material** — parquet structure, scripts, `SCHEMA.md`, this card, manifests, adjudication protocol/rubric | **Apache-2.0** | authored by us |
| **Upstream benchmark content — Omni-MATH-2** (`domain='math'`) | **Apache-2.0**, upstream | permissive; attribution preserved |
| **Upstream benchmark content — SciBench** (`domain='science'`) | **MIT**, upstream | *different licence*; Copyright (c) 2023 Xiaoxuan Wang |
| **Model-generated trajectory text** | the model providers' terms | gemma-4-31B-it, gpt-oss-120b, Llama-3.3-70B-Instruct |

## Upstream sources

| benchmark | licence | in v1.0.0? | training-use policy |
|---|---|---|---|
| **Omni-MATH-2** | Apache-2.0 | **yes**, 1,600 problems | `evaluation_only_recommended` |
| **SciBench** | **MIT** | **yes — 574 problems, added in v1.1.0** | `evaluation_only_recommended` |
| JEEBench | MIT | no | `evaluation_only_recommended` |
| LAB-Bench | CC-BY-SA-4.0 | no | **`do_not_train_upstream_canary`** |
| MaScQA | CC-BY-NC-SA-4.0 | no | `noncommercial_research_only` |

**Two upstreams are used: Omni-MATH-2 (Apache-2.0) and SciBench (MIT).** The
other three are listed because the release registry covers them. SciBench's MIT
licence is kept as its own entry and is *not* absorbed into the Apache-2.0
material, exactly as `SECOND_DOMAIN_SLOT.md` required before the slot was filled.

### Verification

**SciBench — MIT, checked three independent ways (2026-09-30):**
1. The upstream `LICENSE` file, fetched **anonymously** from
   `raw.githubusercontent.com/mandyyyyii/scibench/main/LICENSE` — reads
   `MIT License` / `Copyright (c) 2023 Xiaoxuan Wang`.
2. The GitHub API for that repository — `spdx_id: MIT`.
3. `registry/licenses.parquet` **and** `registry/benchmarks.parquet` in the
   SciAgentTrace release registry — both record `license_id = MIT` and
   `training_use_policy = evaluation_only_recommended`.

All three agree. **MIT ≠ Apache-2.0**; the two upstreams are kept separate.

**Omni-MATH-2 — Apache-2.0**, re-verified for v1.1.0 against the upstream
Hugging Face API (anonymous fetch, 2026-09-30): tag `license:apache-2.0`,
matching `cardData.license`. Unchanged from v1.0.0. LAB-Bench was likewise
checked (`license:cc-by-sa-4.0`). All five sources agree with the two registry
files.

## What upstream text this artifact actually redistributes

This matters, because the obligations differ depending on the answer, and an
earlier draft of this card overstated the position.

- **Gold answers: no gold COLUMN, but a small measured leak in grader free text.**
  No gold/reference *column* exists in any released row, in either domain. That
  was the claim v1.0.0 checked, and it remains true. It did **not** cover free
  text the grader wrote. Measured for v1.1.0, in both domains: the evaluator
  sometimes names the expected value inside its repair hint, despite being
  instructed not to reveal ground truth —
  **Omni-MATH-2: 23 of 17,486 `evaluator_raw` rows, 14 of 1,600 problems (0.9%)**;
  **SciBench: 19 of 3,699 rows, 4 of 574 problems (0.7%)**.
  Both licences permit redistributing answer text with attribution, so this is
  allowed; it is **stated rather than denied**, and the v1.0.0 wording is
  corrected rather than left standing. It is an incidental disclosure, not a
  gold-answer column, and it is far too sparse to reconstruct a gold set.
- **The parquet layer ships no `problem_text` column.** Problems are referenced
  by `problem_uid`; `manifests/problem_sample.json` lists the ids only.
- **But problem text IS incidentally redistributed inside transcripts.** Agents
  restate the problem, so `role_messages.text` contains verbatim upstream text.
  Measured identically in both domains (60-character problem prefix):

  | domain | `role_messages.text` | `evaluator_calls` |
  |---|---|---|
  | Omni-MATH-2 | **16 of 606** (2.6%) | 0 of 606 |
  | **SciBench** | **0 of 574** (0.0%) | 0 of 574 |

  SciBench's rate is *lower*, not zero-by-construction: its problems are short
  numeric chemistry/physics items that agents paraphrase into tables of givens
  rather than restate verbatim. In the **raw FROZEN traces** the agent turns
  still restate problem content, so upstream text appears there at a higher rate
  in both domains.

Apache-2.0 (Omni-MATH-2) and MIT (SciBench) both permit redistributing that
text with attribution, so this is allowed — it is stated plainly rather than
denied, because "only `problem_uid` is redistributed" is **not** an accurate
description of the trace layer in either domain.

## Recommended use

**Both** upstreams actually used are marked `evaluation_only_recommended`:
Omni-MATH-2 and SciBench. We recommend using these trajectories for
**evaluation and analysis** rather than as training data, in both domains. No
do-not-train canary applies to v1.1.0 (no LAB-Bench content); if LAB-Bench is
ever added, its canary must be preserved verbatim and its do-not-train request
honoured.

## Attribution

> Problems from **Omni-MATH-2** (https://huggingface.co/datasets/martheballon/Omni-MATH-2), Apache-2.0.
>
> Problems from **SciBench** (https://github.com/mandyyyyii/scibench), MIT —
> Copyright (c) 2023 Xiaoxuan Wang. Permission notice preserved per the MIT
> terms; see `MIT-SciBench.txt`.
