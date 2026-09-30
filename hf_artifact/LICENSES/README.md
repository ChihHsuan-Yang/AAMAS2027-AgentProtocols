# Licensing

`registry.json` is the machine-readable version of this page and is the
authority. Each upstream source carries its **own** licence; this release does
**not** blanket one project licence over source-derived material.

## Three different things, three different licences

| layer | licence | notes |
|---|---|---|
| **Our derived material** — parquet structure, scripts, `SCHEMA.md`, this card, manifests, adjudication protocol/rubric | **Apache-2.0** | authored by us |
| **Upstream benchmark content** (Omni-MATH-2) | **Apache-2.0**, upstream | permissive; attribution preserved |
| **Model-generated trajectory text** | the model providers' terms | gemma-4-31B-it, gpt-oss-120b, Llama-3.3-70B-Instruct |

## Upstream sources

| benchmark | licence | in v1.0.0? | training-use policy |
|---|---|---|---|
| **Omni-MATH-2** | Apache-2.0 | **yes**, 1,600 problems | `evaluation_only_recommended` |
| SciBench | MIT | no — reserved slot | `evaluation_only_recommended` |
| JEEBench | MIT | no | `evaluation_only_recommended` |
| LAB-Bench | CC-BY-SA-4.0 | no | **`do_not_train_upstream_canary`** |
| MaScQA | CC-BY-NC-SA-4.0 | no | `noncommercial_research_only` |

**Only Omni-MATH-2 is actually used in v1.0.0.** The other four are listed
because the release registry covers them and the reserved second-domain slot
will draw on SciBench — whose MIT licence is *not* this release's Apache-2.0
and must be added as its own entry rather than absorbed.

### Verification
Omni-MATH-2 and LAB-Bench were checked **directly against the upstream Hugging
Face API** (anonymous fetch, 2026-09-30): license tags `license:apache-2.0` and
`license:cc-by-sa-4.0` respectively, matching `cardData.license`. All five
agree with two independent files in the SciAgentTrace release registry
(`registry/licenses.parquet` and `registry/benchmarks.parquet`).

## What upstream text this artifact actually redistributes

This matters, because the obligations differ depending on the answer, and an
earlier draft of this card overstated the position.

- **Gold answers: none.** No gold/reference field exists in any released row —
  checked across every parquet column and the released trace rows.
- **The parquet layer ships no `problem_text` column.** Problems are referenced
  by `problem_uid`; `manifests/problem_sample.json` lists the ids only.
- **But problem text IS incidentally redistributed inside transcripts.** Agents
  restate the problem, so `role_messages.text` contains verbatim upstream text:
  a 60-character problem prefix appears for **16 of 606** checked problems
  (2.6%); `evaluator_calls` showed **0 of 606**. In the **raw FROZEN traces**
  the full prompts are present, so upstream text appears there at a much higher
  rate.

Apache-2.0 permits redistributing that text with attribution, so this is
allowed — it is stated plainly rather than denied, because "only `problem_uid`
is redistributed" is **not** an accurate description of the trace layer.

## Recommended use

Omni-MATH-2 is marked `evaluation_only_recommended` upstream. We recommend
using these trajectories for **evaluation and analysis** rather than as
training data. No do-not-train canary applies to v1.0.0 (no LAB-Bench content);
if LAB-Bench is ever added, its canary must be preserved verbatim and its
do-not-train request honoured.

## Attribution

> Problems from **Omni-MATH-2** (https://huggingface.co/datasets/martheballon/Omni-MATH-2), Apache-2.0.
