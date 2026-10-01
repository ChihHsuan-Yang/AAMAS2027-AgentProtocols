# `config/` — the exact experimental configuration

The paper is *about* role manipulation. The manipulation lives in these files,
so the data is not interpretable without them.

| file | what it is | domain |
|---|---|---|
| `prompts.json` | all 22 prompt strings, verbatim, keyed by name | Omni-MATH-2 |
| `schemas.json` | the three Arm C / C′ JSON schemas (planner, executor, reviewer) | Omni-MATH-2 |
| `run_config.json` | decoding, budgets, visibility policy, model ids, config versions | Omni-MATH-2 |
| **`prompts_scibench.json`** | **the 16 SciBench prompts + `_COMPARISON_TO_OMNIMATH`, a per-prompt identical/differs table** | **SciBench (v1.1.0)** |
| **`run_config_scibench.json`** | **SciBench budgets, visibility, denominators, licence** | **SciBench (v1.1.0)** |
| `SECOND_DOMAIN_SLOT.md` | the second-domain slot — **now FILLED**; kept as a promise-vs-outcome record | — |

> ## ⚠ ARM A IS NOT THE SAME CONTRACT IN BOTH DOMAINS
>
> **Arm A was domain-adapted for SciBench; Arm B was NOT.** 5 of 16 prompts
> differ: the three Arm A role prompts (planner / executor / reviewer prepends
> and the critic append) and the evaluator. `B_GENERIC_PREPEND` and
> `B_GENERIC_APPEND` are **byte-identical** across domains — asserted in code
> at build time, so the A-vs-B manipulation is demonstrably the same one.
>
> Both prompt sets ship in full. `prompts_scibench.json._COMPARISON_TO_OMNIMATH`
> gives a per-prompt `identical_to_omnimath` flag with sha256 prefixes and
> character counts, so you can verify this rather than take it on trust.
>
> **Consequence:** do **not** compute P1a or any clause-specific role-fidelity
> metric across domains — it would score agents against instructions they never
> received. The evaluator adaptation is **common mode** (identical across A and
> B within SciBench), so it cannot manufacture an A-vs-B difference.
>
> **Why adapt at all?** Arm B's prompt has no domain language. Leaving Arm A's
> "competition-level mathematics" wording in a chemistry benchmark would make
> the arms differ in *two* ways — role structure and domain fit — with the
> domain-fit difference running **against** Arm A. Adapting A keeps it a
> single-variable manipulation.

### One stale-looking line that is deliberately left alone

`run_config.json` still contains `second_domain_slot.status = "NOT PRESENT IN
v1.0.0"`. That sentence is **scoped to v1.0.0 and remains true**, and the file
is a v1.0.0 artifact whose sha256 is published in `VERSION.release_history` —
editing it would break the hash chain that lets anything published against
v1.0.0 stay checkable. The SciBench configuration lives in its own file,
`run_config_scibench.json`. **Read the two files per domain; do not expect the
v1.0.0 file to describe v1.1.0.**

## Which prompt is which arm

| arm | prompts | what it does |
|---|---|---|
| **A** | `A_SOLVER_*`, `A_EXECUTOR_*`, `A_CRITIC_*` | three *distinct* role prompts — planner, executor, reviewer |
| **B** | `B_GENERIC_*` | the ablation: one generic prompt used for **all three** agents |
| **C** | `C_PLANNER_*`, `C_EXECUTOR_*`, `C_REVIEWER_*` + `schemas.json` | hard enforcement — output must validate against the role's JSON schema or it is rejected and regenerated |
| **C′** | `CP_*` (appends are shared with C) | Arm C with `shared_history` restored — isolates context loss from schema enforcement |
| grader | `EVALUATOR_*` | the external oracle, `openai/gpt-oss-120b`, temperature 0 |

A prompt is assembled as `PREPEND + <problem/context> + APPEND`. Arm A's
`A_SOLVER_APPEND` interpolates `${role_description}`.

**The A-vs-B contrast is a pure prompt-text manipulation.** `run_config.json`
→ `visibility_policy_per_arm` shows A and B are byte-identical in what each
agent can see: `["problem", "shared_history", "advice"]` for all three roles in
both arms. Only the prompt text differs. Arms C and C′ additionally change
visibility, and that is stated there rather than left to be inferred.

## Budgets, held constant across every arm

3 outer rounds × 2 inner rounds = **6 deliberation cycles**, temperature **0**,
`max_tokens` **8192**, ≤30 actor calls, ≤6 evaluator calls, ≤3 regenerations
per turn (Arm C/C′ only), ≤4 transport retries, 300 s request timeout.

The identical cycle budget is what rules out "the role-free arm just stopped
earlier" — it could not have.

## Config versions

**SciBench has its own:** `aed89f28ab338bdb`, single-valued over all 2,296 rows
and **not poolable** with the Omni-MATH hashes — the hash covers every prompt
plus `benchmark_id` and `slice_id`, all of which changed. That is the field
doing its job. Recomputed from `runner_xdomain.py` at build time and asserted
equal to the value stamped on the rows.

### The two Omni-MATH config versions, and what actually differs

`data/trajectories.parquet.config_version` takes two values. They differ
**only** by the addition of the Arm C′ entry; every A/B/C prompt, schema and
knob is byte-identical across them. `run_config.json` → `config_version`
documents this with the recomputation that verifies it.

## A limitation worth reading before you trust this field

`config_version` hashes prompts, schemas and decoding/budget knobs. It does
**not** hash the logging code, so it cannot tell instrumented rows from
uninstrumented ones — the F13 logger fix left the hash unchanged. Measured
directly, that fix did not reach any frozen row (gpt-oss Arm B planner median
37 chars before the fix commit, 36 after), so the release is uniform in this
respect. Detect F13 with `chars_per_sec`, never with `config_version`.

## Redactions

Two values are withheld for double-blind review, both marked in place:
the inference endpoint URL and the local problems-parquet path. Both identify
the operating institution. No credential appears in this artifact; the auth
helper is excluded entirely.
