# S.17 — SciBench Bf live delivery gate (complete cell, n=574)

S.17: *"Do not assume the Omni fix automatically proves SciBench delivery."*
This gate reconstructs SciBench prompts with `runner_xdomain`'s **own**
`load_problems()` and **own** prompt objects, never the Omni ones, and is
hash-verified against each turn's logged `prompt_sha256_12`.

Cell complete: 574/574 rows, runner exited, orchestrator advanced.

## Result

```
realized prompts hash-verified : 3129/3129
prompts carrying feedback      : 1071
feedback appearing >1x         : 0   (must be 0)
feedback BEFORE first FAIL     : 0   (must be 0)
metadata flag disagrees w/bytes: 0   (must be 0)
generic append altered         : 0   (must be 0)
[Evaluator] header malformed   : 0   (must be 0)
first-FAIL trajectories        : 124
of those, feedback delivered   : 124
problems skipped               : 0

SCIBENCH GATE (S.17): PASS
```

`leak = 245` is **reported, not gated**, on the same reasoning as the Omni gate
(BF_HINT_DISCLOSURE.md): SciBench answers are short numerics, so a bare
substring match is frequently coincidental, and disclosure is a property of the
shared evaluator rather than of delivery. Gating on it would reject correct
delivery for a property A and Bf hold in common by design.

## A defect found in the GATE, not the runner

The first run of this gate on the partial file reported **3 mismatches**, all
in one trajectory `scibench:atkins:e3.4(a)(a)`, at prompt indices 3/4/5 — the
whole of cycle 2. The runner's own flag said feedback *was* delivered there;
my reconstruction said it was not. Root cause:

```
evaluator_history[0] = { correctness: None, finish_reason: "length",
                         latency_s: 109.006 }
```

The evaluator hit its token cap mid-reasoning and never emitted a
`Correctness:` line, so `parse_evaluator` returned `None`
(`runner_xdomain.py:758-768`). The runner's branch is

```python
if c == 1:            # runner_xdomain.py:1159 -- only an explicit pass is a pass
    stop = True; ...
# everything else, including None, falls through to the FAIL branch
advice = "Evaluator feedback: FAIL / Score: False\nRepair hint: ..."
evaluator_feedback = advice
```

so `None` **does** deliver feedback. My gate matched only `correctness == 0`
and therefore under-reconstructed. **The runner behaved correctly; the
instrument was wrong.** Fixed by mirroring the runner exactly (`!= 1`), in both
the delivery rule and the `first_fail` denominator so the two cannot diverge.

### Prevalence, measured across every cell

| cell | evaluator calls | `correctness=None` |
|---|---:|---:|
| Bf omni (1600) | 2266 | **0** |
| Bf scibench (574) | 905 | **1** (finish_reason `length`) |
| frozen scibench A+B (2296) | 3699 | 0 |
| frozen omni A / B / C | 3927 / 6081 / 3910 | 0 / 0 / 0 |

One occurrence in 16,788 evaluator calls, confined to this cell. It changes no
frozen number: every frozen arm has zero. It is retained, not dropped — the
runner's handling of it is well defined and the trajectory is valid.

## Positive controls on the CORRECTED gate

A gate edited until data passes must be shown able to fail. Plants mutate a
**copy of the data**, never the gate:

| plant | gate | counter that fired |
|---|---|---|
| P0 baseline (unmodified) | PASS | — |
| P1 one logged flag lies | FAIL | `flag_bad=1` |
| P2 one prompt hash corrupted | FAIL | `mismatch=3` |
| P3 verdicts moved outside the pairing window | FAIL | `delivered 123/124` |
| P4 every verdict forced to PASS (original defect) | FAIL | `mismatch=1407` |

**P5, the regression guard for the fix itself.** First attempt was **void**: it
required a trajectory with `>=2` evaluator calls whose first was a PASS, and
there are **0** such rows — a first-verdict PASS ends the trajectory
(`runner:1160 break`). Its PASS was a plant that never planted, and is not
counted as evidence. Replanted correctly by flipping 5 **real FAIL** verdicts
to `None`; the runner's bytes are unchanged (it already treated them as FAIL),
so a correct gate must still match:

| gate version | same planted data |
|---|---|
| OLD rule (`== 0`) | **FAIL**, mismatch = 42 |
| CORRECTED rule (`!= 1`) | **PASS**, mismatch = 0, delivered 124/124 |

The correction is therefore the right one and not a loosening: it changes the
verdict only on inputs where the runner's own rule says feedback was delivered.

## Comparison with Omni, stated separately

| | Omni Bf | SciBench Bf |
|---|---:|---:|
| prompts hash-verified | 7608/7608 | 3129/3129 |
| first-FAIL trajectories | 302 | 124 |
| delivered | 302/302 | 124/124 |
| must-be-zero counters | all 0 | all 0 |

Both PASS, each on its own runner, its own problem loader and its own prompt
objects. The SciBench conclusion does **not** rest on the Omni audit.

## Scope

Delivery only. This gate says the role-free arm now receives the external
correctness signal in realized bytes; it says nothing about outcomes. No
recovery rate, paired contrast or p-value is computed or read here.
