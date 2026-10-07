# Sec.16 bridge — the verdict label is constrained by n, fixed BEFORE the run

Written before the drift cell is launched. No bridge data exists yet.

## What was checked

`analysis/scripts/bf_drift.py` was re-controlled against the current file.
Sign convention verified against the module's own docstring and call site:
`b` = frozen-only success, `c` = bridge-only success, `delta = (c-b)/n`.
(My first control harness inverted b/c and produced a negative CI on a positive
shift. The script was correct; the harness was wrong and is fixed.)

## Controls at the planned n=400

| world | b | c | delta | p | 95% CI | verdict |
|---|---|---|---|---|---|---|
| pure null | 56 | 53 | -0.007 | 0.848 | [-0.059, +0.044] | SMALL (underpowered) |
| small +0.02 | 48 | 53 | +0.013 | 0.691 | [-0.037, +0.062] | SMALL (underpowered) |
| material +0.08 | 24 | 55 | +0.077 | 0.00064 | [+0.035, +0.120] | **MATERIAL** |

MATERIAL fires correctly and only on the material world.

## The limit: NONE is not reachable at n=400

Sweeping 40 seeds on a **pure null** (true drift exactly zero):

| n | verdicts over 40 null seeds |
|---|---|
| 400 | SMALL(underpowered) 39, MATERIAL 1 |
| 800 | NONE 27, SMALL(underpowered) 12, SMALL 1 |
| 1200 | NONE 34, SMALL(underpowered) 4, SMALL 2 |
| 1600 | **NONE 40** |

`NONE` requires the paired CI to sit inside ±0.05. At n=400 with ~27%
discordance the CI half-width is ≈0.05, so the branch is essentially
unreachable: **a perfectly clean bridge will report SMALL(underpowered), not
NONE.** The 1/40 MATERIAL at n=400 is the expected α=0.05 false positive.

## How the Sec.16 verdict must therefore be read

- **MATERIAL** is informative at n=400 — it fired only on real drift.
- **SMALL(underpowered)** at n=400 is the *expected* output of a clean bridge.
  It must be reported as "drift not resolved at this n", **not** as "drift
  detected" and not as "no drift".
- **NONE** should not be expected or claimed at n=400.

This is a property of the planned design, recorded before any bridge data
exists so the label cannot be chosen after seeing the result. Per Sec.16 the
bridge is never pooled with the frozen campaign regardless of verdict.

## Not changed

`bf_drift.py` is unmodified. n=400 is the directive's figure and is **not**
altered here (Sec.21 forbids changing n unilaterally). This report states what
that n can and cannot support; any decision to widen it is the user's.

## Launch provenance (S.7: do not launch a duplicate)

Checked before touching the endpoint, 2026-10-06 ~15:45.

The bridge cell is **not launched by hand**. `experiments/run_bf.sh` already
sequences it as cell 3:

```
[ "$ONLY" = all ] || [ "$ONLY" = bridge ] && \
  job runner.py 400 A "$D/bridgeA_omnimath_gemma4_n400.jsonl" bridgeA-gemma4-n400
```

The orchestrator is alive and stepping through cells in order:

```
pid 57011  elapsed 04:06:45  bash experiments/run_bf.sh /tmp/aamas_bf/experiments/results/bf
  +- pid 78873  python3 experiments/runner_xdomain.py --n 574 --arms Bf ...   (cell 2)
```

Cell 1 closed cleanly in its own log
(`bf-gemma4-n1600 COMPLETE`, `FINISHED done=1600 correct=1475 errors=0
unavailable_skips=0`) and cell 2 started, which is what establishes that the
script is advancing rather than stalled on one cell.

The stanza is written `A || B && C`, which in POSIX shell is left-associative
and therefore does **not** mean "(A or B) and C". Verified rather than assumed:

| ONLY | bridge stanza |
|---|---|
| all | RUN |
| scibench | skip |
| bridge | RUN |

Since cells 1 and 2 both ran off the same pattern, `ONLY` is `all`, so the
bridge fires. **No manual launch** — S.7 forbids duplicating a run already in
progress or scheduled, and two concurrent n=400 Arm A cells writing one path
would corrupt both.

Fresh Arm A rows land in `bridgeA_omnimath_gemma4_n400.jsonl`, a path distinct
from every frozen file and from both Bf cells, so the bridge cannot be pooled
by accident (S.16).

## Pairing preflight (run BEFORE any bridge row exists)

The bridge is a paired design, so a silently partial join would shrink n
without any error. Checked in advance:

```
frozen campaign_v2.jsonl                       9600 rows
  frozen Arm A, actor gemma-4-31B-it           1600 rows
  unique uids 1600, duplicated 0
  run_id         main-n1600-v2     (1600/1600)
  config_version e3afa39849c1b980  (1600/1600)

bridge uid set, runner.load_problems(400, seed 20270101)
  400 uids, 400 unique
  overlap with frozen Arm A: 400/400
```

Every bridge problem has exactly one frozen Arm A counterpart: the paired n is
the full 400, and the join cannot half-match. The frozen side carries a single
`run_id` and a single `config_version`, so the comparison is against one
homogeneous cell rather than a mixture.

Note the frozen `config_version` `e3afa39849c1b980` differs from Bf's
`25a04a554afcd006`; that is the pooling guard working as intended and is not a
drift signal — the bridge arm is A on both sides, which is what isolates
endpoint drift from configuration change.

## The bridge's `config_version` differs from frozen A — why that is NOT drift

The bridge rows carry `config_version = 25a04a554afcd006`; frozen Arm A carries
`e3afa39849c1b980`. The bridge's whole premise is "both sides are Arm A, same
prompts, same budget, so any difference is endpoint drift", so a differing
configuration hash looks like it invalidates the design. It does not, and the
reason was checked rather than argued.

`config_version_hash()` (`runner.py:136-171`) is a **global** digest: it hashes
*every* entry of `P.ALL_PROMPTS` and the *whole* `VISIBILITY` dict, not the arm
being run. Adding the `Bf` arm therefore changes the hash for every arm,
including arms whose own prompts were never touched. The field is a pooling
guard — it is designed to be conservative and to move on any setup change —
not a measure of whether Arm A changed.

The question that actually matters is whether Arm A's realized bytes moved.
Tested on the paired rows available at the time of writing (64 of the eventual
400):

```
FIRST PLANNER prompt sha identical: 64/64
   omni2_102   frozen=c52cefcb90b9  bridge=c52cefcb90b9
   omni2_1021  frozen=6f4733f887f2  bridge=6f4733f887f2
   omni2_1027  frozen=8ddc214f98e4  bridge=8ddc214f98e4

budget             identical = True
request_timeout_s  identical = True
evaluator_model    identical = True
visibility_policy  identical = True
```

The first planner prompt depends only on the problem text and the Arm A
template, so byte-identity proves the Arm A prompt did not change between
campaigns. The four knobs the drift comparison rests on are also identical,
`visibility_policy` included — the per-row field records the arm's own policy,
which is unchanged for A even though the global dict grew.

So the two sides differ in the endpoint and the calendar, which is exactly what
the bridge is built to measure, and not in the prompts, the budget, or the
evaluator. This check is repeated over all 400 rows when the cell completes.

---

## POST-RUN ADDENDUM (appended 2026-10-06, after the bridge completed)

Everything above this line is the pre-run record and is **left unedited**, including
the prediction that turned out to be wrong.

**The bridge returned NONE.** The prediction above — that NONE was essentially
unreachable at n=400 and a clean bridge would report SMALL(underpowered) — was
**incorrect**.

Cause: the null simulation drew the two arms **independently** at the marginal
rate, giving discordance 2p(1−p) ≈ 0.27 at p ≈ 0.82. Two re-runs of the same
system on the same problems are positively correlated. Realized discordance is
**9.0%** (first-pass) and **7.5%** (final), so the paired CI half-width is
≈0.029, not ≈0.05, and the NONE branch is reachable.

The error was in the null model, not the instrument: `bf_drift.py`,
MATERIAL_DELTA = 0.05 and ALPHA = 0.05 are unchanged from the pre-run versions.
Holding the observed point estimates fixed but imposing the *assumed* 27%
discordance reproduces the predicted SMALL, confirming the discrepancy is
entirely the discordance assumption.

Direction of the error: the note **understated** power. It did not make a
favourable label easier to reach.

Post-run positive controls on the real 400-row file (planting drift of known
size, in both directions) are reported in section H of `BF_FINAL_REPORT.md`,
together with the finding that the `bounded` test backing NONE constrains
first-pass and final accuracy only — **not** the recovery endpoint.
