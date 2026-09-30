# `config/` — the exact experimental configuration

The paper is *about* role manipulation. The manipulation lives in these files,
so the data is not interpretable without them.

| file | what it is |
|---|---|
| `prompts.json` | all 22 prompt strings, verbatim, keyed by name |
| `schemas.json` | the three Arm C / C′ JSON schemas (planner, executor, reviewer) |
| `run_config.json` | decoding, budgets, visibility policy, model ids, config versions |
| `SECOND_DOMAIN_SLOT.md` | the reserved slot for the SciBench campaign |

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

## Two config versions, and what actually differs

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
