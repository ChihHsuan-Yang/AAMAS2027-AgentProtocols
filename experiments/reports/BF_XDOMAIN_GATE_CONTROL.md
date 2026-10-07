# §17 SciBench delivery gate — positive-control, run BEFORE the live audit

`/tmp/gate9_xdomain.py` is the instrument §17 depends on. A PASS from an
instrument that has never been shown to produce a FAIL is not evidence
([[positive-control-every-null]]). This control was run while the SciBench Bf
cell did not yet exist, so it cannot have been tuned to the result.

## Known-negative: frozen SciBench arm B, gemma-4 (574 rows)

Arm B is the ideal negative. It uses the **same** `B_GENERIC_PREPEND` /
`B_GENERIC_APPEND` templates the gate reconstructs, on the **same** problems,
from the **same** frozen campaign — but feedback was never delivered to it.
A gate that cannot tell B from Bf is measuring the template, not the delivery.

```
prompts 3438 | match 1725 | mismatch 1713 | fb 0 | delivered 0 | traj_fail 118
SCIBENCH GATE (S.17): FAIL
```

**FAIL, for the right reason.** `fb=0` and `delivered=0` against
`traj_fail=118`: the gate detected zero feedback strings in 118 trajectories
that got a wrong first verdict. That is exactly arm B's documented behaviour
and exactly what the Bf control exists to change.

## The 1713 mismatches are not a reconstruction defect

Half the prompts mismatching looked alarming enough to explain before
trusting any later PASS. Three variants, same rows:

| reconstruction | prompts | match | mismatch | pre-FAIL mismatch |
|---|---|---|---|---|
| gate as written (inject feedback) | 3438 | 1725 | 1713 | **0** |
| inject, no `continue` cascade | 3438 | 1725 | 1713 | **0** |
| **no injection** (arm B's truth) | 3438 | **3438** | **0** | 0 |

`mismatch = 1713` is *exactly* `post_fail_prompts = 1713`, and with injection
disabled every one of the 3438 prompts hash-matches. So the gate reconstructs
arm-B prompts perfectly; the mismatches are the gate inserting an
`[Evaluator]` block that arm B never received. Cause identified, not assumed.

Second variant rules out a confound of my own making: the gate does
`continue` on mismatch, which skips the `shared.append`, so one mismatch
could cascade into every later turn. Disabling the cascade changes nothing
(1713 either way) — the mismatches are independently caused, not a chain.

## What this licenses, and what it does not

Licensed: the gate's FAIL branch fires on real data, its hash comparison
discriminates, and `fb`/`delivered` track actual delivery rather than the
template. A later PASS on `bf_scibench_gemma4.jsonl` is therefore informative.

Not licensed: §17 remains **UNSATISFIED**. This is a negative control on
frozen arm-B rows. The live audit on real Bf rows has not run because the
cell does not exist yet. Per the directive, the Omni fix does not prove
SciBench delivery, and neither does this.

## Note on the leak counter

149 of 3438 arm-B prompts tripped `ans in pr` (bare substring, `len>1`). This
is the counter the gate's own closing note says "must be read case by case,
not as an automatic failure", and it is not part of the PASS/FAIL condition.
Arm B received no hints at all, so none of the 149 can be a hint disclosure —
they are short numerics coinciding with text in the problem or the agents'
own reasoning. Independent confirmation that the substring test is a weak
instrument, consistent with [[substring-match-is-not-a-detector]]; the
measured disclosure rate is in BF_HINT_DISCLOSURE.md, which uses a detector
that also catches word forms.
