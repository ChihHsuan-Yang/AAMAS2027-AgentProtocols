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
---

# Role structure in multi-agent LLM problem solving — trajectory dataset

<!-- ANONYMIZED FOR DOUBLE-BLIND REVIEW.
     Do NOT add author names, institution, funding, grant numbers, repository
     URLs, or a citation block until the paper is accepted. See
     RELEASE_PROCEDURE.md. -->

Analysis-ready trajectories from a controlled study of whether **role structure**
in a multi-agent LLM pipeline is load-bearing. 11,600 trajectories, 3 actor
models, 4 conditions, 1,600 competition math problems, with an external oracle
grader in the loop.

This is a **derived** dataset: one row per trajectory, one row per oracle call,
one row per role message. It is built to reproduce the paper's tables, not to
dump raw logs.

**Anonymous during review.** Author, institution, and code repository are
withheld. They will be added on acceptance.

## The finding, in one sentence

Role structure is not load-bearing for generating a first answer, but it can be
load-bearing for **repairing** an initially wrong one.

Removing roles leaves first-pass accuracy unchanged (and for one actor slightly
improves it), while degrading the team's ability to recover from a wrong first
answer — for the clearest actor, recovery falls 0.222 → 0.051. The mechanism is
not premature stopping and not less feedback: every arm holds the same 6
deliberation cycles by construction, and the role-free arm receives *more*
oracle feedback. It is failure to produce a distinct second candidate. Hard
enforcement of role boundaries restores both organization and recovery, but does
**not** improve final accuracy, because it is brittle (8–17% attrition).

The effect is **actor-dependent**, and the dataset is released with the cells
where it does not replicate intact.

## Design

| arm | condition |
|---|---|
| **A** | full role structure (planner / executor / reviewer, distinct prompts and schemas) |
| **B** | role structure removed — three agents, one generic prompt |
| **C** | hard enforcement — role-boundary violations rejected and regenerated |
| **C'** | context control at fixed enforcement |

| actor model | A | B | C | C' |
|---|---|---|---|---|
| gemma-4-31B-it | 1,600 | 1,600 | 1,600 | 400 |
| gpt-oss-120b | 1,600 | 1,600 | 1,600 | 400 |
| Llama-3.3-70B-Instruct | 400 | 400 | 400 | — |

Total 11,600 trajectories over 1,600 Omni-MATH-2 problems. Grader: a fixed
external evaluator model, temperature 0. Budget identical across arms
(3 outer rounds x 2 inner rounds = 6 cycles).

## Contents

| file | rows | what it reproduces |
|---|---|---|
| `data/trajectories.parquet` | 11,600 | the main results tables |
| `data/evaluator_calls.parquet` | 17,486 | the grader noise-floor analysis |
| `data/role_messages.parquet` | 83,320 | collapse, duplication, frozen-answer analyses |
| `manifests/` | — | frozen-snapshot manifest, per-cell census, problem ids |
| `adjudication/` | 171 items / 513 verdicts | blinded model adjudication of the collapse metric |
| `SCHEMA.md` | — | **every column, and the two known defects** |
| `CHECKSUMS.txt`, `VERSION` | — | integrity and provenance |

Total ~39 MB.

## Quick start

```python
import pandas as pd

tr = pd.read_parquet("data/trajectories.parquet")

# first-pass accuracy is flat across arms; recovery is not
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

## Read this before you compute anything

Two logged fields do not mean what their names suggest. **`SCHEMA.md` documents
both in full; this is the short version.**

- **F13 — visible text is truncated for one actor.** For `gpt-oss-120b` in Arm B,
  the runner discarded hidden reasoning whenever visible content was non-empty,
  affecting 81.8% of that cell's messages. Its planner logs a median of **37
  characters at 2.85 chars/sec**, against 4,824 at 195 chars/sec in its own
  Arm A — the work was done and the logger threw it away. The
  `used_reasoning_fallback` flag fired on **0** of the 2,302 sub-100-character
  planner messages, so *the flag's absence is not evidence the defect is absent*.
  **Any text-based measure over gpt-oss Arm B is measuring the instrument.**
  Use `chars_per_sec` to detect it; exclude the cell and say so.

- **F18 — `correct` grades the last SUBMITTED answer, not the last answer HELD.**
  A team that revises after its final submission is scored on the answer it
  abandoned. The two disagree on up to **45.7%** of first-pass-wrong
  trajectories in some cells; 54 are demonstrably under-credited (held answer
  exactly matches gold, graded 0; positive control finds 0 such cases among
  10,734 non-mismatched rows). The mismatch rate is a function of revision
  behaviour — **it is post-treatment, so never use it as a filter or covariate
  in an arm contrast.** Columns `f18_mismatch` and `f18_under_credited` are for
  bounding the effect, not correcting it.

Also: scoring convention matters and flips signs. `final_correct_prereg`
(ungraded = 0) is **primary**; `final_correct_asgraded` (ungraded dropped) is
sensitivity only and carries 8–17% one-sided attrition in Arm C. And the
adjudication files carry a residual blinding leak that `PROTOCOL.md` reports as
fixed — `SCHEMA.md` documents what survived and which numbers it affects.

## Scope and limitations

- **Single benchmark, single domain.** Competition math (Omni-MATH-2) only. No
  claim about other task families.
- **Three actor models, and the effect does not replicate in all three.**
  gemma-4 is clean; gpt-oss is weaker and not significant when paired;
  Llama-3.3 shows a floor effect and does **not** replicate. Cells are released
  intact so this is checkable.
- **Recovery is oracle-gated.** No cell recovers before the first oracle verdict.
  This measures repair under external feedback, not spontaneous self-correction.
- **Conditional analyses are post-treatment.** Anything conditioned on
  first-pass-wrong is descriptive and associational, never causal.
- **The grader is a model.** The measured noise floor is 0.0086 (24 of 2,791
  distinct graded strings receive contradictory verdicts under byte-identical
  prompts at temperature 0). Contrasts smaller than a few times this are not
  resolvable; the dataset lets you check which.
- **Adjudication is model adjudication, not human annotation and not ground
  truth.**
- **Wall-clock timings reflect shared infrastructure**, including queueing.

## Licensing

- **This derived dataset: Apache-2.0.** Problems come from
  [Omni-MATH-2](https://huggingface.co/datasets/martheballon/Omni-MATH-2),
  released under Apache-2.0 (verified on the upstream dataset page, and against
  the upstream license registry). Apache-2.0 permits redistribution of
  derivatives with attribution, so the derived trajectories may carry it.
- **Problem text and gold answers are NOT redistributed here.** Only
  `problem_uid` identifiers. Recover the text by joining to the upstream corpus.
- Model outputs are generated by Gemma, gpt-oss, and Llama family models; their
  respective model terms govern the generated text.
- Attribution to Omni-MATH-2 is preserved above and in `VERSION`.

## Provenance

Derived from a sha256-manifested frozen snapshot. `VERSION` records the source
file hashes; `CHECKSUMS.txt` covers every emitted file. The build verifies the
snapshot hashes before deriving anything and refuses to run on a mismatch, and
the output is deterministic — a rebuild is byte-identical.

`scripts/validate_artifact.py` re-derives **181 published values** from these
parquet files and checks them against the project's canonical analysis output.
All 181 pass.
