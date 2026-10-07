# §17 — SciBench (runner_xdomain.py) delivery audit: static half

Directive §17: *"Do not assume the Omni fix automatically proves SciBench
delivery. Audit `runner_xdomain.py` separately given its domain-adapted
prompts/evaluator wording."*

This file records the **static** half only. The live half (hash-verified
realized prompts on real SciBench rows) is pending the SciBench cell and is
NOT reported here. A static audit cannot establish delivery; it can only
establish whether the two runners could differ in principle.

## What was compared

| Component | Omni `runner.py` | SciBench `runner_xdomain.py` | Result |
|---|---|---|---|
| `build_messages` Bf branch | L684 | L946 | **byte-identical**, sha256[:12] `bf31b0375edd` |
| FAIL path setting `evaluator_feedback` | — | — | **byte-identical** (incl. the no-answer branch) |
| `parse_evaluator` | — | — | **byte-identical** |
| `evaluate()` call + history append | — | — | **byte-identical** |
| Prompt templates | `P.*` from shared `prompts.py` | same module | shared, not copied |

A caution worth recording: the string `if arm in ("B", "Bf"):` occurs **twice**
in each file — once in the dry-run stub (`respond`, L436 / L698) and once in the
live `build_messages` (L684 / L946). The first match is the stub. Grepping for
the branch and reading the first hit audits a fixture, not the runner.

## What is genuinely domain-adapted

Only the **data**, not the code:

- `gold = problem.get("reference", "")` — identical expression in both (L628 / L890)
- the reference is built at load: `ref = "Final answer: {}".format(r["answer"])`
  (L977 / L1247), plus an optional official solution in the xdomain loader
- SciBench answers are **short numerics** (e.g. `24 atm`); Omni answers are
  longer expressions

That difference matters for exactly one property: **leak checking**. A short
numeric answer can appear in a repair hint by coincidence far more easily than
a long LaTeX expression can, so the xdomain leak check must be read
case-by-case rather than as a pass/fail count. `/tmp/gate9_xdomain.py` is
written that way deliberately.

## A structural guarantee, stronger than the empirical count

`gold` is passed only into `evaluate()` (as `result=`). It does **not** appear
anywhere inside `build_messages` in either runner — verified by substring on
the extracted function body. So the gold answer cannot reach an actor prompt
through the prompt builder in either domain.

This does not make the live leak check redundant. The hint text is *generated
by the evaluator model*, which has seen the gold answer, and may quote it back.
That is a model-behaviour leak, not a plumbing leak, and only the realized
prompts can rule it out.

## Status

- Static: the Bf mechanism is the same mechanism in both runners, not a copy
  that drifted.
- Live: **PENDING.** Not claimed. §17 is not satisfied until the
  hash-verified gate runs on real `bf_scibench_gemma4.jsonl` rows.
