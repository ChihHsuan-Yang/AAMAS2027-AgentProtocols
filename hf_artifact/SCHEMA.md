# Schema and known defects

Three parquet tables, joined on `trajectory_key`. Read the **Known defects**
section before computing anything: two logged fields do not mean what their
names suggest, and a consumer who does not know this will draw wrong
conclusions from data that looks clean.

Every derived column reuses the definition in the project's canonical analysis
script. Where a definition is subtle, the table that publishes it is named, so
a reader can check this artifact against the paper rather than trusting it.

---

## Experimental design, in one paragraph

Each **trajectory** is one (problem, arm, actor model) run of a three-role
pipeline — planner, executor, reviewer — over a math problem, with an external
**evaluator** ("oracle") that grades a submitted answer PASS/FAIL and can send
the team back to revise. Arms differ only in how role structure is imposed:

| arm | meaning |
|---|---|
| **A** | full role structure — each role has a distinct prompt and schema |
| **B** | role structure removed — the three agents receive the same generic prompt |
| **C** | hard enforcement — role boundaries are validated and violations are rejected and regenerated |
| **Cp** (`C'`) | context control at fixed enforcement — Arm C's machinery, Arm A's context |

Budget is identical in every arm by construction: `MAX_OUTER_ROUNDS=3 x
INNER_ROUNDS=2` = 6 deliberation cycles. Any arm difference in cycles used is
behaviour, not budget.

---

## 1. `data/trajectories.parquet` — 11,600 rows, one per trajectory

The table that reproduces the paper's main tables. Key `trajectory_key` is
unique (verified 11,600/11,600).

### Identity
| column | type | definition |
|---|---|---|
| `trajectory_key` | string | `{problem_uid}\|{arm}\|{actor_model}`. Primary key; join key for the other two tables. |
| `problem_uid` | string | Problem id in the upstream registry (`omni2_NNNN`). **Problem text and gold answers are not redistributed here** — see *Licensing*. |
| `arm` | string | `A`, `B`, `C`, `Cp`. |
| `actor_model` | string | Short name: `gemma-4-31B-it`, `gpt-oss-120b`, `Llama-3.3-70B-Instruct`. |
| `actor_model_full` | string | Vendor-qualified id, e.g. `google/gemma-4-31B-it`. |
| `evaluator_model` | string | Grader model. Constant (`openai/gpt-oss-120b`) across the snapshot. |
| `run_id`, `config_version` | string | Provenance. `config_version` is a hash of the run configuration; it differs between the main campaign and the two supplementary runs. |
| `benchmark_id`, `domain` | string | `omnimath2` / `math` throughout. |

### Correctness — read `final_correct_*` carefully
| column | type | definition |
|---|---|---|
| `graded` | bool | At least one evaluator call happened **and** `correct` is non-null. Trajectories that never produced a gradeable answer are `false`. |
| `first_pass_correct` | int64 | Verdict of the **first** evaluator call (`evaluator_calls.verdict` at `call_index=0`). Null if never graded. |
| `final_correct_prereg` | int64 | **PRIMARY scoring.** Final correctness with ungraded trajectories scored **0**, per the preregistration ("failures to parse are counted as incorrect, not dropped"). |
| `final_correct_asgraded` | int64 | **SENSITIVITY ONLY.** Ungraded trajectories are null (dropped). This carries **8–17% one-sided attrition in Arm C** and flips the sign of the C−A contrast. Never report it as primary. |
| `first_pass_wrong` | bool | `graded AND first_pass_correct == 0`. The denominator for every recovery number. |

> **The two scorings disagree in direction, not just magnitude.** Under PREREG,
> C−A is −0.0225 for gemma-4 (significant negative). Under AS-GRADED it is
> +0.0190 (significant positive). The difference is entirely Arm C's
> survivorship. Reporting AS-GRADED alone reproduces a claim the project has
> retracted.

### Process
| column | type | definition |
|---|---|---|
| `cycles` | int64 | Inner deliberation cycles used (`inner_used`). Out of 6 available. |
| `rounds_used` | int64 | Outer rounds used, out of 3. |
| `submissions` / `evaluator_calls` | int64 | Number of answers submitted to the oracle. Identical by construction (verified: they match on all 11,600 rows). **This counts submissions, not repair opportunity** — a retracted claim once conflated the two. |
| `actor_calls` | int64 | Total actor model calls. |
| `retries` | int64 | Transport-level retries. |
| `n_regeneration_rejects` | int64 | Regeneration events whose validation failed. Non-trivial only in Arm C, where it is the enforcement cost. |
| `wall_time_s`, `started_at`, `ended_at` | double / string | Wall clock. Shared infrastructure, so these reflect queueing as well as work. |
| `n_role_messages` | int64 | Count of planner/executor/reviewer messages (rows in `role_messages` for this key). |

### Behavioural flags
| column | type | definition |
|---|---|---|
| `reviewer_first_route` | string | The reviewer's route on its **first** turn: `agree`, `planner`, `executor`, `continue`. Null if the reviewer never emitted a route. |
| `reviewer_never_declines` | bool | The reviewer routed `agree` on every turn — never sent work back. |
| `functional_collapse` | bool | All three of the first-pass planner/executor/reviewer messages contain a `\boxed{}` answer, i.e. each role independently asserted an answer instead of performing its role. **Null when the trajectory has fewer than 3 role messages.** Meaningful for arms A/B only (in C/Cp the planner schema has no answer field, so the marker means something different). |
| `unanimous_first_pass` | bool | All three first-pass messages boxed **the same** normalized answer. Null if any of the three has no boxed answer. |
| `frozen_answer` | bool | The trajectory's whole sequence of distinct answers has length ≤ 1 — the team never produced a second distinct candidate. Computed over all planner/executor/reviewer messages, using `\boxed{}` plus (in C/Cp) the JSON `answer` field. |
| `n_distinct_answers` | int64 | Length of that distinct-answer sequence. |
| `final_answer_held` | string | The answer the team last **held** at the end. |
| `last_submitted_answer` | string | The answer last **submitted** to the oracle. See F18 — these are not the same thing. |

### Outcome and failure
| column | type | definition |
|---|---|---|
| `hard_failure` | string | Non-null when the run aborted, e.g. `regeneration_exhausted:reviewer:answer_leak:final_answer_phrase`. Concentrated in Arm C. |
| `attrition` | bool | `NOT graded`. 0–2.5% in A/B, **8.0/9.9/17.0% in Arm C**. This is the brittleness the paper reports. |
| `stopping_condition` | string | How the run ended: `reviewer_agree_then_evaluator_pass`, `max_rounds_exhausted_after_fail`, `hard_failure`, `runtime_error`, … |
| `error` | string | Exception class and message. **Sanitized**: three error classes embedded an upstream HTTP response body (one of which named the operating institution). The failure class is preserved; the body is replaced with `[upstream response body redacted]`. |

### Defect indicator columns
| column | type | definition |
|---|---|---|
| `f18_mismatch` | bool | `final_answer_held != last_submitted_answer` after normalization. See F18. |
| `f18_under_credited` | bool | `f18_mismatch` **and** the held answer exactly matches gold **and** the trajectory was graded 0. A demonstrable under-credit. 54 cases. |
| `f13_n_low_chars_per_sec` | int64 | Count of this trajectory's role messages emitting <10 visible characters per second of latency — the F13 signature. See F13. |

---

## 2. `data/evaluator_calls.parquet` — 17,486 rows, one per oracle grading

Reproduces the **grader noise-floor** analysis.

| column | type | definition |
|---|---|---|
| `trajectory_key` | string | Join key to `trajectories`. |
| `problem_uid`, `arm`, `actor_model` | string | Denormalized for convenience. |
| `call_index` | int64 | 0-based order within the trajectory. `0` is the first pass. |
| `candidate_raw` | string | The candidate answer string **exactly as the evaluator received it**. |
| `candidate_normalized` | string | Whitespace removed, `$` delimiters stripped. **This is the correct join key for noise-floor work** (see below). |
| `verdict` | int64 | `1` = PASS, `0` = FAIL. |
| `is_first_pass` | bool | `call_index == 0`. |
| `latency_s`, `finish_reason`, `timestamp` | | Call metadata. |
| `evaluator_raw` | string | The grader's full response text, including its stated reason. Kept so a reader can audit verdicts rather than trust them. |

### The noise floor, and the key that gets it wrong
The evaluator prompt contains only the problem, the candidate string, and gold.
It does **not** contain the arm, the actor identity, or the derivation. So for a
fixed `(problem_uid, candidate_normalized)` the prompt is byte-identical at
temperature 0, and any verdict disagreement within that group is pure sampling
nondeterminism — it cannot be arm bias. That makes it a free, airtight control:

```python
g = ec.groupby(["problem_uid", "candidate_normalized"]).verdict.agg(["nunique", "size"])
multi = g[g["size"] >= 2]
floor = (multi["nunique"] > 1).sum() / len(multi)     # 24 / 2791 = 0.0086
```

> **Do not group on `final_answer_held`.** An earlier analysis did, and got
> 0.0143 — inflated ~6x, because it pairs gradings of *different strings* and
> counts their legitimate disagreement as noise. It also produced a spurious
> per-arm asymmetry (Arm A "13x noisier than Arm B", p=0.0017) that vanished
> (p=0.580) on the correct key, and a "self-favouring grader" signal that
> **reversed sign**. 95.6% of the discordant pairs under the wrong key involved
> an F18 mismatch. The wrong key measures F18, not the grader.

---

## 3. `data/role_messages.parquet` — 83,320 rows, one per role message

Full visible text of every planner/executor/reviewer message, **included**. See
*What is and is not included* for why.

| column | type | definition |
|---|---|---|
| `trajectory_key` | string | Join key. |
| `message_index` | int64 | Position in the trajectory's original message list. Preserves order; not contiguous, because non-role messages are excluded. |
| `role` | string | `planner`, `executor`, `reviewer`. |
| `outer_round`, `inner_round`, `attempt_index` | int64 | Position in the deliberation loop. |
| `rejected` | bool | The message was rejected by Arm C's boundary validator and regenerated. 3,489 rows. **Exclude these when analysing what the team actually saw.** |
| `text` | string | Visible content. **Subject to F13 — see below.** |
| `n_chars` | int64 | `len(text)`. |
| `latency_s` | double | Generation latency. |
| `chars_per_sec` | double | `n_chars / latency_s`. Null when latency is 0/absent. **The F13 discriminator.** |
| `used_reasoning_fallback` | bool | Flag intended to record that hidden reasoning was substituted for empty content. **This flag is unreliable — see F13.** |
| `route` | string | Reviewer only: `agree`, `planner`, `executor`, `continue`. |
| `answer_owner_after_turn` | string | Reviewer only: who owns the answer after this turn. |
| `validation_ok`, `violated_constraint` | bool / string | Schema validation outcome. |
| `prompt_sha256_12`, `response_sha256_12` | string | 12-hex-char digests. **Two messages sharing a `response_sha256_12` are byte-identical.** Check `prompt_sha256_12` too: identical outputs from identical prompts are not evidence of role collapse. |
| `prompt_chars` | int64 | Prompt size. |
| `finish_reason`, `timestamp` | string | Call metadata. |

---

## Known defects — read before analysing

These are real defects in the instrument, disclosed because the data looks
clean without them. Neither is repairable from the logs.

### F13 — visible content is truncated relative to hidden reasoning (gpt-oss, Arm B)

**What happened.** The runner captured the model's `reasoning` field *only when
`content` was empty*. A short visible `content` alongside a long hidden
reasoning trace silently discarded the reasoning. This affected **81.8% of
gpt-oss Arm B messages**. The flag meant to record the substitution,
`used_reasoning_fallback`, fired on only 5.7% of them — and on **0 of the 2,302**
gpt-oss Arm B planner messages under 100 visible characters. *The flag's absence
is not evidence the defect is absent.*

**How to detect it.** `chars_per_sec`. A model that genuinely emitted 37
characters is fast; a model whose reasoning was discarded is slow but logs short.

| actor / arm | median `n_chars` | median `chars_per_sec` |
|---|---|---|
| gpt-oss / A | 4,824 | **195.16** |
| **gpt-oss / B** | **37** | **2.85** |
| gemma-4 / B | 1,876 | 149.89 |
| Llama-3.3 / B | 1,892 | 93.15 |

gpt-oss's Arm B planner is ~68x slower per visible character than its own Arm A
planner. It spends ~27 s to emit 37 characters. **The work was done and the
logger threw it away.**

**What this invalidates.** Any text-based measure over gpt-oss Arm B messages —
length, duplication, byte-identity, "did the planner abstain". A byte-identity
metric fired at 0.846 for gpt-oss and ~0.000 for the other two actors *not*
because gpt-oss rubber-stamps but because its visible output was reduced to a
boxed answer, and identical boxed answers are byte-identical. That metric was
measuring the logger.

**The correct framing** is **observed-duplication vs instrument-failed**, not
two model behaviours. Two of three actors show planners that visibly write full
solutions; the third is uninstrumented. Reporting gpt-oss's short planner as a
*behaviour* attributes a logging defect to the model.

`f13_n_low_chars_per_sec` (trajectory level) and `chars_per_sec` (message level)
are provided so you can filter. A reasonable rule: exclude gpt-oss Arm B from
any visible-text claim, and state the exclusion.

### F18 — `correct` grades the last SUBMITTED answer, not the last answer HELD

**What happened.** The runner sets `correct` from the grade of the last answer
**submitted to the oracle**, while `final_answer` records the answer the team
last **held**. A team that submits an answer, gets FAIL, revises to a better
answer, and then runs out of budget before resubmitting is scored on the
answer it *abandoned*.

**How often.** Among first-pass-wrong trajectories:

| actor | arm A | arm B | arm C |
|---|---|---|---|
| gemma-4 | 0.171 | 0.000 | 0.244 |
| gpt-oss | 0.164 | 0.066 | 0.216 |
| Llama-3.3 | 0.058 | 0.004 | **0.457** |

409 mismatched first-pass-wrong trajectories; **54 demonstrably under-credited**
(held answer exactly matches gold, graded 0). A positive control on the 10,734
non-mismatched graded rows finds **0** such cases, so 54 is a clean floor, not
an artifact of the matching.

**Why Arm B is ~0.** Arm B resubmits on nearly every cycle, so its last held and
last submitted answers coincide. **The mismatch rate is a function of revision
behaviour, which is the treatment.** Do not use `f18_mismatch` as a covariate or
a filter in an arm contrast — it is post-treatment and correlated with the
outcome by construction.

**Use `f18_mismatch` / `f18_under_credited` to bound, not to correct.** Rescoring
on the held answer answers a *different question* than the paper asks, and gold
answers are not redistributed here, so the recomputation is not available in
this artifact anyway.

### Minor: mangled LaTeX escapes in answer strings

135 of 11,498 `final_answer_held` values (1.2%) and 176 of 17,486
`candidate_raw` values (1.0%) contain C0 control characters where a LaTeX macro
was intended — `\f` became `\x0c` (`\frac` → `\x0crac`), `\b` became `\x08`
(`\binom` → `\x08inom`). This is an upstream escape-handling bug, **preserved
as-is** so that this artifact matches what the evaluator actually graded. The
free-text `role_messages.text` column is essentially unaffected (<0.01%). If
you normalize these, do it in your own analysis layer and say so — rewriting
them here would silently break reproduction of the graded verdicts.

---

## What is and is not included

**Included: full visible message text** (`role_messages.text`, 36.6 MB of the
39 MB artifact). The brief allowed dropping it if it pushed the artifact past
~200 MB. It does not: the source is 283 MB of JSONL, but the role text is 178 MB
raw and compresses to 36.6 MB under zstd in a columnar layout. Since the
frozen-answer, duplication, and functional-collapse analyses **cannot** be
reproduced without it, and it fits comfortably, it is included. This is the
main judgement call in the artifact and it went toward completeness.

**Included:** the grader's full response text (`evaluator_calls.evaluator_raw`),
so verdicts can be audited rather than trusted.

**Excluded, deliberately:**

| excluded | why | consequence |
|---|---|---|
| **Problem text and gold answers** | Upstream Omni-MATH-2 content; redistributing the evaluation set here adds contamination surface for no analytic gain. | Join `problem_uid` to the upstream corpus to recover them. Any re-grading analysis needs that join. |
| **`regeneration_events[].raw_output_truncated_2000chars`** | Pre-validation drafts, truncated at 2,000 chars mid-string. The accepted text is already in `role_messages`, and `n_regeneration_rejects` + `violated_constraint` carry the enforcement-cost signal. | You cannot inspect the *content* of a rejected Arm C draft, only that it was rejected and which constraint it violated. |
| **`budget`, `visibility_policy` per row** | Constant across the snapshot (1 distinct budget over all 11,600 rows). | Recorded once in this document rather than 11,600 times. |
| **`adjudicate.py`** | It resolves a judge endpoint and a credential helper. | The protocol, rubric, items, key, verdicts, and analysis script are all included; only the transport is not. |
| **Internal logs, `/tmp` files, transient state** | Per the brief. | — |
| **HTTP response bodies inside `error`** | One was a block page naming the operating institution — a deanonymization path. | Failure *class* is preserved; only the body is redacted. |

Constant across the snapshot, recorded here once:
`budget = {max_actor_calls: 30, max_evaluator_calls: 6, max_regenerations: 3,
max_transport_retries: 4, max_outer_rounds: 3, inner_rounds: 2, temperature: 0.0,
max_tokens: 8192}`; `evaluator_model = openai/gpt-oss-120b`;
`benchmark_id = omnimath2`; `domain = math`.

---

## Adjudication files

`adjudication/` holds the blinded model-adjudication study that validates the
automated collapse metric. **It is model adjudication (Opus 5), not human
annotation and not ground truth**, and must be described that way.

| file | contents |
|---|---|
| `ITEMS_blinded.jsonl` | 171 blinded transcripts. Judge sees only `=== Agent 1/2/3 ===`. |
| `KEY.jsonl` | Unblinding key: actor, arm, `auto_collapse`, correctness. Withheld from the judge. |
| `VERDICTS.jsonl` | 513 verdicts (171 items x 3 reps), raw + parsed, with model, rubric sha, prompt sha, timestamp. |
| `RUBRIC_v1.md` | Frozen before the first judgement (sha `4f624de5b1073940`). |
| `SAMPLING_MANIFEST.json` | Seed, strata, per-cell counts, pre/post-neutralization item hashes. |
| `PROTOCOL.md` | Method, including defects found mid-run. Endpoint details redacted for review. |
| `build_sample.py`, `analyze.py` | Sampling and analysis. Author's home path removed from `build_sample.py`. |

### A residual blinding leak, found in this artifact's review — read this

`PROTOCOL.md` reports that 45 items leaked literal role names
(`Planner`/`Executor`/`Reviewer`), that these were concentrated 42 in Arm A vs 3
in Arm B ("a near-perfect arm signal"), that all role tokens were "neutralized
to `Agent-P/E/R` uniformly across every item", and that **post-fix residual
leaks: 0**.

**The neutralization renamed the tokens; it did not remove the signal.** The
strings `Agent-P` / `Agent-E` survive in the released blinded items, and their
*presence* has the same near-perfect arm distribution the original leak had:

| arm | items containing `Agent-P/E/R` | rate |
|---|---|---|
| **A** | 42 / 42 | **1.000** |
| **B** | 3 / 56 | 0.054 |
| C | 0 / 44 | 0.000 |
| Cp | 0 / 29 | 0.000 |

Fisher exact, A vs B: **p = 1.5e-24**. (Verified against the released file,
whose sha256 matches `items_sha256_after_neutralization` in the manifest — so
this is the file the judge actually saw, not a stale copy.)

The rename made the *token* uninformative while leaving its *presence*
informative, because Arm A's prompts mention roles and Arm B's do not. A judge
that keyed on "does this transcript refer to other agents by label at all"
could separate Arm A from Arm B almost perfectly. **`PROTOCOL.md`'s "residual
leaks: 0" is true of the string and false of the signal**, and this artifact
ships the protocol claim and the contradicting data together rather than
quietly fixing either.

What this does and does not threaten: the adjudication's load-bearing output is
**recall** — the byte metric misses gemma-4's collapse — and recall is estimated
within actors across arms. But arm-contrastive adjudication numbers (Arm B
"no division of labour" 0.964 vs Arm A 0.000) are **not** protected by the
blinding that `PROTOCOL.md` claims. Treat them as potentially leak-informed
until re-run on items with the presence signal removed (drop the tokens
entirely, or insert an equivalent token into every item in every arm).

Other blinding checks on the released items, all clean: no actor names
(`gemma`/`gpt-oss`/`llama`), no arm labels, no `problem_uid`, no `run_id`, no
`config_version`, no collapse-label words.

---

## Reproducing the paper's numbers

`scripts/validate_artifact.py` checks **181 values** from this artifact against
the project's canonical analysis output — cell census, first-pass and final
accuracy, recovery, frozen-answer rate, functional collapse, cycles and
submissions, the grader noise floor, the F18 mismatch and under-credit counts,
and the F13 planner-shape signature. All 181 pass.

```bash
python3 scripts/validate_artifact.py     # exits nonzero on any mismatch
```

`scripts/build_artifact.py` regenerates the parquet from the frozen snapshot. It
verifies the snapshot's sha256 before deriving anything and refuses to build on
a mismatch; output is deterministic (a rebuild is byte-identical).

> One discrepancy worth recording: an internal finding note quotes 4,072 median
> chars and 178.1 ch/s for the gpt-oss Arm A planner. The frozen snapshot gives
> **4,824** and **195.16**. The note predates the freeze; the canonical analysis
> output is authoritative and is what this artifact matches. The F13 conclusion
> is unaffected — it rests on the ~68x ratio, not on either figure.
