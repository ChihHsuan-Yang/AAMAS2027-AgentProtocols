# S.5 — `test_bf_delivery.py`: run it, then prove it can fail

Directive S.5: run the test, **do not stop at "the test passed"**, positive-control
it, and **do not commit the planted failure**.

Worktree `/tmp/aamas_bf`, detached on `origin/control-rolefree-feedback`.
Every plant below lived only in a `tempfile.mkdtemp()` copy of `experiments/`,
run against the **unmodified** test, and was deleted. Residue check at the end.

## 1. The run

```
16/16 PASS   (8 checks x {runner, runner_xdomain}),  exit 0
```

That alone is not evidence. A passing suite is consistent with a test that
cannot fail.

## 2. Positive controls (7 planted defects)

Harness soundness was established first: `test_bf_delivery.py` does
`sys.path.insert(0, Path(__file__).resolve().parent)`, so a copied tree imports
**its own** copy, and `PYTHONPATH` was unset. Plants therefore reach the code
under test.

| # | planted defect | property attacked | result |
|---|---|---|---|
| D1 | `if arm == "Bf" and evaluator_feedback:` -> `if False:` | delivery happens at all | DETECTED |
| D2 | remove `evaluator_feedback = ""` | **one-cycle lifetime** | **PLANT PASSED** |
| D3 | Bf text differs from B pre-FAIL | pre-FAIL byte-identity | DETECTED |
| D4 | logged flag lies | metadata/bytes agreement | DETECTED |
| D5 | deliver before any FAIL | no early delivery | DETECTED |
| D6 | Bf gets a string != A's `${advice}` | same string as A | DETECTED |
| D7 | contaminate arm B (original defect, inverted) | B stays withheld | DETECTED |

6 of 7 detected. **D2 is a real coverage gap**, and it is on a property S.4
names explicitly, so it is reported rather than filed as noise.

## 3. Diagnosing D2 — three candidates, run down

A passing plant has three causes (weak check / missed plant / void harness).
Harness was already excluded. Separating the other two took two probes.

**Probe 1 (all-FAIL stub) — WRONG INSTRUMENT, reported here so it is not
mistaken for a null.** Forcing every evaluator call to `Correctness: 0` gave
*byte-identical* output on both sides:

```
lifetime PRESENT : CYCLES=6 PROMPTS=18  per-prompt=[0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
lifetime REMOVED : CYCLES=6 PROMPTS=18  per-prompt=[0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
```

Identical output on both sides of a difference test must be explained before it
is believed. The explanation: with a new FAIL every cycle, `runner.py:907`
re-assigns `evaluator_feedback = advice` each time, **overwriting** the deleted
clear at `:892`. The plant is unobservable by construction under this stub.

**Probe 2 (one FAIL, then reviewer routes `continue`) — CORRECT INSTRUMENT.**
Exploiting `runner.py:898` (`if approve and current_answer is not None:`), a
reviewer that does not agree consumes no verdict, so later cycles run with no
new feedback to re-set. The conditions now separate:

```
lifetime PRESENT (correct) : prompts=18 evaluator_calls=1  prompts carrying feedback = 3
lifetime REMOVED (D2 plant): prompts=18 evaluator_calls=1  prompts carrying feedback = 15
  PRESENT per-prompt: [0,0,0,1,1,1,0,0,0,0,0,0,0,0,0,0,0,0]
  REMOVED per-prompt: [0,0,0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
```

The defect is detectable; the shipped test simply cannot see it.

## 4. Why the shipped test cannot reach it

`StubResponder` is FAIL-then-PASS, which terminates the trajectory at cycle 2:

```
shipped StubResponder: prompts=6  cycles=2  evaluator_calls=2
  stopping_condition = reviewer_agree_then_evaluator_pass
  per-prompt marker  = [0, 0, 0, 1, 1, 1]
```

The test asserts over `pf[3:6]` — the cycle **after** the FAIL. There is no
prompt at index >= 6, so **no cycle exists in which persisted feedback could
appear**. The gap is in stub reachability, not in an assertion's wording.

Per S.21 the test is **not weakened, and not strengthened here either**: S.4
forbids altering the Bf design without reporting first, and the same caution is
applied to its verification harness mid-campaign. Adding an all-FAIL or
`continue`-routing stub to `test_bf_delivery.py` is the obvious repair and is
recommended, but is left for the user to approve.

## 5. S.17 — `runner_xdomain` audited separately

Not inferred from Omni. Same two probes, against `runner_xdomain.py`
(anchor `:1154`):

```
lifetime PRESENT : shipped stub -> carrying=3   one-FAIL probe -> carrying=3
lifetime REMOVED : shipped stub -> carrying=3   one-FAIL probe -> carrying=15
```

Identical finding in both domains: same blind spot under the shipped stub, same
correct behaviour under the probe.

## 6. The property IS positively evidenced on realized data

The unit test does not cover the lifetime, so the claim must rest elsewhere.
It rests on the live Omni gate — and that coverage was itself controlled, not
assumed.

`gate9.py:58` clears `evfb` at each reviewer turn, i.e. the reconstruction
*assumes* the one-cycle lifetime. If the runner had persisted instead, those
reconstructions would not match the runner's logged `prompt_sha256_12`. Tested
by running a variant whose only change is removing that clear:

| reconstruction | hash-verified | prompts carrying feedback | gate |
|---|---:|---:|---|
| clears after one cycle (as shipped) | **7608/7608** | 2154 | PASS |
| persists (variant) | 6516/7608 | 1668 | FAIL |

1,092 mismatches. The 7,608/7,608 match is therefore a positive measurement of
the one-cycle lifetime across the whole Omni Bf cell, not an untested assumption.

**Correction to an earlier working note:** the covering statistic is the hash
verification, **not** `multi`. `multi` counts a marker appearing twice *within
one prompt*; persistence puts it once in each of several *later* prompts, so
`multi` stays 0 under the persist variant. A report citing `multi == 0` as
evidence of the lifetime would have been wrong.

## 7. Scope limits

- Probes use dry-run stubs; they test control flow, not model behaviour.
- The SciBench live equivalent of Section 6 is pending that cell's completion
  (`/tmp/gate9_xdomain.py`); Section 5 covers the static/stub half of S.17 only.
- D2's repair is recommended, not applied.

## 8. Residue check (S.5: do not commit the planted failure)

```
grep -rn "lifetime removed|PERSIST-VARIANT|planted-one-shot|if False:" experiments/ analysis/scripts/
  -> no matches

experiments/runner.py:892          evaluator_feedback = ""   # one-cycle lifetime, as ${advice} in A
experiments/runner_xdomain.py:1154 evaluator_feedback = ""   # one-cycle lifetime, as ${advice} in A

git status --porcelain -> only untracked additions (bf_drift.py, bf_verdict.py,
                          bf_freeze.py, reports/). No tracked file modified.
scratch dirs /tmp/s5* -> none remain.
```

## Verdict

`test_bf_delivery.py` **PASSES and is genuinely load-bearing for 6 of the 7
properties probed**. It does **not** cover the one-cycle lifetime in either
runner. That property is instead evidenced by the live Omni gate's 7,608/7,608
hash-verified reconstruction, shown by a persist-variant control to be sensitive
to exactly this defect.
