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

> **v1.1.0.** `data/scibench/trajectories.parquet` (2,296 rows),
> `data/scibench/role_messages.parquet` (13,500) and
> `data/scibench/evaluator_calls.parquet` (3,699) use **exactly these same
> columns** — the build imports the v1.0.0 column definitions rather than
> re-implementing them, and asserts column-name parity against the Omni tables
> at build time. Everything in this document applies to both domains unless a
> section says otherwise. Differences that matter: **no Arm C** in SciBench (so
> no `enforcement_events`, no adjudication), **Arm A's prompt differs by
> domain**, and the **grader noise floor is domain-specific**. See the card.

The table that reproduces the paper's main tables. Key `trajectory_key` is
unique (verified 11,600/11,600).

### Identity
| column | type | definition |
|---|---|---|
| `trajectory_key` | string | `{problem_uid}\|{arm}\|{actor_model}`. Primary key; join key for the other two tables. |
| `problem_uid` | string | Problem id in the upstream registry — `omni2_NNNN` (Omni-MATH) or `scibench:<book>:<item>` (SciBench). **No problem-text or gold-answer column is redistributed here**; see *Licensing* for what transcripts incidentally contain. |
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
| `f18_under_credited` | bool | `f18_mismatch` **and** the held answer exactly matches gold **and** the trajectory was graded 0. A demonstrable under-credit. 62 cases. |
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
floor = (multi["nunique"] > 1).sum() / len(multi)     # 20 / 2790 = 0.0072
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
reasoning trace silently discarded the reasoning. This affected **75.7% of
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
| gemma-4 | 0.171 | 0.000 | 0.363 |
| gpt-oss | 0.164 | 0.066 | 0.258 |
| Llama-3.3 | 0.058 | 0.004 | **0.478** |

509 mismatched first-pass-wrong trajectories; **62 demonstrably under-credited**
(held answer exactly matches gold, graded 0). A positive control on the 10,734
non-mismatched graded rows finds **0** such cases, so 62 is a clean floor, not
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

**Included: the raw frozen traces** (`raw/`, 283 MB) as EXACT BYTES, so their
sha256 verifies against `raw/MANIFEST.json`, plus the derived parquet layer.

**Included: full visible message text** (`role_messages.text`, 36.6 MB). The brief allowed dropping it if it pushed the artifact past
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
| **Gold answers** | **No gold/reference COLUMN exists in any released row, in either domain.** But the grader sometimes names the expected value in its free-text repair hint despite being told not to: Omni-MATH 23 of 17,486 `evaluator_raw` rows (14 of 1,600 problems, 0.9%); SciBench 19 of 3,699 (4 of 574, 0.7%). Corrected in v1.1.0 — the v1.0.0 wording checked columns, not free text. | Any re-grading analysis still needs a join to the upstream corpus; the leak is far too sparse to serve as a gold set. |
| **A `problem_text` column** | The parquet layer references problems by `problem_uid` only. **Note this is not the same as "no upstream text is redistributed"**: agents restate the problem, so problem text appears verbatim inside `role_messages.text` (16 of 606 checked problems) and, at much higher rate, inside the full prompts in `raw/`. See `LICENSES/README.md`. | Join `problem_uid` to the upstream corpus for the canonical text. |
| ~~`regeneration_events[].raw_output_truncated_2000chars`~~ **NOW INCLUDED** | v1.0.0 ships these in `data/enforcement_events.parquet` and in `raw/`. | Rejected Arm C/C′ drafts *can* be inspected, truncated at 2,000 chars mid-string. |
| **`budget`, `visibility_policy` per row** | Constant across the snapshot (1 distinct budget over all 11,600 rows). | Recorded once here and in full in `config/run_config.json`, rather than 11,600 times. |
| **`adjudicate.py`** | It resolves a judge endpoint and a credential helper. | The protocol, rubric, items, key, verdicts, and analysis script are all included; only the transport is not. |
| **Internal logs, `/tmp` files, transient state** | Per the brief. | — |
| **HTTP response bodies inside `error`** — **in the PARQUET layer only** | Some were block pages / tracebacks naming the operating institution — a deanonymization path. | Failure *class* is preserved; only the body is redacted. **`raw/` is NOT redacted**: it ships exact bytes so its sha256 verifies against `MANIFEST.json`, and 14 rows there still carry such a body. This is why the repo is private and why `scripts/preflight_public.py` must pass before it is ever flipped public. |

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

---

# Added in v1.0.0 — raw traces, config, and two more tables

## `raw/` — the frozen traces, EXACT BYTES

`campaign_v2.jsonl` (9,600 rows), `actor3.jsonl` (1,200), `armCp.jsonl` (800),
plus `MANIFEST.json`. These are the bytes the analysis ran on, unmodified, so
each file's sha256 verifies against the manifest. Everything in `data/` is
derived from them; `scripts/build_artifact.py` and
`scripts/build_extra_tables.py` both verify the three hashes before deriving
anything and refuse to run on a mismatch.

One JSON object per line. Top-level keys: `problem_uid`, `arm`, `actor_model`,
`evaluator_model`, `domain`, `benchmark_id`, `run_id`, `backend`,
`config_version`, `actor_calls`, `evaluator_calls`, `retries`,
`regeneration_events`, `stopping_condition`, `final_answer`, `correct`,
`hard_failure`, `wall_time_s`, `started_at`, `ended_at`, `rounds_used`,
`inner_used`, `error`, `unavailable_wait_s`, `request_timeout_s`, `budget`,
`visibility_policy`, `messages`, `evaluator_history`.

**`correct` here is the F18-affected field** — the grade of the last *submitted*
answer, while `final_answer` is the last answer *held*. See F18 above.

> **`raw/` is not sanitized.** Because these are exact bytes, 14 rows still
> carry an upstream HTTP error body inside `error` that names the operating
> institution. Harmless while the repo is private; a deanonymization path if it
> is not. `scripts/preflight_public.py` must exit 0 before any public flip.

## `config/` — the experimental configuration

`prompts.json` (all 22 prompt strings), `schemas.json` (the three Arm C/C′ JSON
schemas), `run_config.json` (decoding, budgets, visibility policy, model ids,
config versions), `SECOND_DOMAIN_SLOT.md`. See `config/README.md` for which
prompt belongs to which arm.

## `data/enforcement_events.parquet` — 29,796 rows, one per Arm C/C′ validation attempt

Arms A and B contain **0** rows by construction — there is no schema to enforce.
Arm C has 25,010 and Arm C′ 4,786. Of all attempts, **3,489 are rejections**,
which reconciles exactly with `trajectories.n_regeneration_rejects` for all
1,331 affected trajectories (0 mismatches).

| column | type | meaning |
|---|---|---|
| `trajectory_key` | str | `problem_uid\|arm\|actor_model`; joins to every other table |
| `problem_uid`, `arm`, `actor_model` | str | denormalized for filtering |
| `event_index` | int | position within this trajectory's attempt sequence |
| `role` | str | `planner` / `executor` / `reviewer` |
| `outer_round`, `inner_round`, `attempt_index` | int | where in the loop; `attempt_index` > 0 means this is a retry of a rejected turn |
| `validation_ok` | bool | did the output validate against the role's JSON schema |
| **`was_rejected`** | bool | `not validation_ok` — **this is the rejection flag**; sum it for enforcement cost |
| `was_regenerated` | bool | a replacement turn was actually generated (3,169 events). Distinct from `was_rejected`: a rejection on the last allowed attempt exhausts the allowance and is **not** regenerated — that is the attrition mechanism |
| `violated_constraint` | str | which constraint failed; null when `validation_ok`. Top causes: `answer_leak:final_answer_phrase` (2,220), `json_parse_error` (710), `missing_field:answer` (437) |
| `validation_detail` | str | validator's message (`valid` when OK) |
| `n_violations`, `all_violations` | int, JSON str | all violations, not just the first |
| `soft_signals` | JSON str | non-blocking signals the validator noted |
| `rejected_output_truncated_2000chars` | str | the raw model output for this attempt, truncated at 2,000 chars **mid-string** |
| `finish_reason`, `used_reasoning_fallback` | str, bool | as returned by the backend |
| `latency_s`, `prompt_sha256_12`, `prompt_chars`, `timestamp` | — | call metadata |

**Do not compute an Arm C rejection *rate* per trajectory without deciding your
denominator.** Attempts, turns and trajectories give different answers, and the
attrition caveat above applies to any recovery figure you build from this.

## `data/adjudication.parquet` — 513 rows, one per (item × judge repetition)

171 blinded items, 170 judged 3× and **one (`T0016`) judged only 2×**. Long
form: aggregate to an item before comparing arms.

| column | type | meaning |
|---|---|---|
| `item_id` | str | **anonymized item id** (`T0000`…); the only id the judge saw |
| `repetition_index` | int | 0–2; independent repeated calls on identical input |
| `judge_model` | str | `claude-opus-5` — a MODEL adjudication, not human annotation |
| `judge_temperature` | — | **always null**: not recorded by the harness. Do not infer a value |
| `rubric_version`, `rubric_sha256_12` | str | `RUBRIC_v1`, sha `4f624de5b107` |
| `prompt_sha256_12`, `judged_at_utc` | str | per-call provenance |
| `raw_judge_output` | str | **the raw judge output**, verbatim, so parsing can be audited |
| `judge_error`, `parse_ok` | str, bool | all null / all true in this release |
| `q1_semantic_redundancy` | YES/NO | do later agents substantially repeat earlier reasoning |
| `q2_functional_redundancy` | YES/NO | does a later agent fail to add a role-specific function |
| `q3_new_information` | YES/NO | does any later agent add a derivation, fact, critique or decision |
| `q4_answer_influence` | YES/NO | does a later agent materially change the answer or method |
| **`q5_division_of_labour_present`** | YES/NO | the headline judgement. **Mind the polarity: YES means division of labour IS present.** "No division of labour" is `Q5 == "NO"` |
| `judge_reason` | str | the judge's stated reason |
| `problem_uid`, `arm`, `actor_model`, `run_id`, `config_version` | str | from `KEY.jsonl` — **the unblinding key**, never shown to the judge |
| `trajectory_correct` | float | that trajectory's outcome; **null for 4.7%**. The judge was outcome-blind |
| `automated_collapse_label` | bool | the mechanical `functional_collapse` flag this study validates |
| `trajectory_key` | str | joins to the other tables; 100% resolve |

**Reproducing the published pooled rates.** Majority vote of `Q5` over
repetitions per item, then `Q5 == "NO"`:

```python
import collections, json, pandas as pd

# Tie-break depends on ROW ORDER, so read the verdicts in FILE order.
# (One item, T0016, has a tied Q5 vote -- see the warning below.)
V = [json.loads(l) for l in open("adjudication/VERDICTS.jsonl")]
KEY = {json.loads(l)["tid"]: json.loads(l) for l in open("adjudication/KEY.jsonl")}
byi = collections.defaultdict(list)
for v in V:
    if v.get("parsed"):
        byi[v["tid"]].append(v["parsed"]["Q5"])
maj = {t: collections.Counter(q).most_common(1)[0][0] for t, q in byi.items()}
cells = collections.defaultdict(list)
for t, m in maj.items():
    if t in KEY:
        cells[KEY[t]["arm"]].append(m == "NO")
for arm in sorted(cells):
    v = cells[arm]
    print(f"{arm}: n={len(v)} rate={sum(v)/len(v):.3f}")
# A: n=42 rate=0.000 | B: n=56 rate=0.964 | C: n=44 rate=0.136 | Cp: n=29 rate=0.172
```

**This reproduces the published figures exactly, and a convenience one-liner
over the parquet may not.** `T0016` has only 2 reps and a **tied** Q5 vote — the
only tie in the study — so the Arm B rate is 0.964 or 0.982 purely according to
which verdict the tie-break sees first. `collections.Counter.most_common`
resolves by insertion order, so the result depends on row order: iterating
`VERDICTS.jsonl` in file order gives 0.964 (the published value), while a
`pandas.groupby` over `data/adjudication.parquet` re-orders the rows and yields
0.982. Every other cell is tie-free and agrees under both routes.

**These pooled arm rates carry the condition leak.** They are not blinded
across arms; see the adjudication defect in `README.md`.
