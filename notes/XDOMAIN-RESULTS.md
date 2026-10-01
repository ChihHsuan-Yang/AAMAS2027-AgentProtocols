# SciBench cross-domain replication — Q1-Q4 results

**Worker report, 2026-09-30. Not a paper claim: the Master Agent decides
integration. Reported under the interpretation rules fixed in advance in
`notes/XDOMAIN-POWER-PREREG.md` (commit `4ac8e3b`), written at 761/2,296
rows before any recovery contrast existed.**

Source: `experiments/results/xdomain/FROZEN_SCIBENCH/`, 2,296 rows,
sha256 `10068f72cfd936d3...`, config_version `aed89f28ab338bdb`.
Definitions executed from `FINAL_TABLES.py` (same code objects, not
reimplemented).

## Run quality

| | |
|---|---|
| trajectories | 2,296 / 2,296 (574 x 2 arms x 2 actors, all cells exactly 574) |
| trajectory-level failures | **0 (0.000%)** — threshold was 2% |
| unjudged (no first verdict) | 0 |
| duplicate cell writes | 0 |
| call-level transport retries | 76 / 17,199 = 0.44% (all succeeded) |
| grader noise floor (byte-identical prompts) | **2.80%** (19/678). Omni-MATH's own floor is **0.72%** (canonical T6) -- SciBench's grader is ~4x noisier, not quieter; see the correction in XDOMAIN-INTEGRATION-DECISION |

No transport-excluded headline is needed.

## Q1 — Does deleting roles leave first-pass accuracy intact? **YES.**

| actor | n | fp_A | fp_B | B-A | 95% CI | exact p |
|---|---|---|---|---|---|---|
| gemma-4-31B | 574 | 0.794 | 0.794 | **+0.0000** | [-0.0209,+0.0209] | 1.00 |
| gpt-oss-120b | 574 | 0.784 | 0.789 | +0.0052 | [-0.0192,+0.0296] | 0.78 |

Gemma's is an exact tie (19 discordant each way). **This replicates
Omni-MATH cleanly**, where first-pass was also 0.802 vs 0.802 for gemma.

## Q2 — Does deleting roles reduce recovery? **YES for gemma; UNRESOLVED for gpt-oss.**

Paired on problems first-pass-wrong under BOTH arms. PREREG scoring.
Denominator includes trajectories that later died (FATAL-1 fix).

| actor | n_both | rec_A | rec_B | B-A | 95% CI | A-only | B-only | exact p |
|---|---|---|---|---|---|---|---|---|
| gemma-4-31B | 99 | 0.212 | 0.020 | **-0.1919** | [-0.2828,-0.1111] | 21 | 2 | **6.6e-05** |
| gpt-oss-120b | 96 | 0.219 | 0.135 | -0.0833 | [-0.1875,+0.0208] | 17 | 9 | 0.169 |

**Gemma replicates the central claim.** Omni-MATH was 0.222 -> 0.051
(-0.171); SciBench is 0.212 -> 0.020 (-0.192). Nearly identical magnitude in
a genuinely different domain, and the CI excludes zero by a wide margin with
a seed-free exact p of 6.6e-05.

**gpt-oss is NOT a non-replication — it is underpowered, per rule 2.** The
point estimate (-0.083) is in the same direction and almost exactly the
Omni-MATH gpt-oss effect (-0.077). Power at the realised n=96 against its own
observed effect is **NOT a single number** -- see the correction below.
So this cell can detect a large effect and cannot detect its own. Reported as
"cannot resolve", never as one of two actors failing.

### FINDING-18 sensitivity (both ways, as the project requires)

Crediting trajectories whose *held* answer exactly matches gold:

| actor | as-recorded | F18-corrected |
|---|---|---|
| gemma-4-31B | -0.1919 [-0.2828,-0.1111] p=6.6e-05 | **-0.2020** [-0.2929,-0.1111] p=3.6e-05 |
| gpt-oss-120b | -0.0833 [-0.1875,+0.0208] p=0.169 | -0.0833 (unchanged) |

The defect again works *against* the headline; correcting it strengthens
gemma and leaves gpt-oss untouched. No verdict flips.

## Q3 — Does the role-free team resubmit rather than revise? **YES, decisively.**

First-pass-wrong trajectories:

| actor | arm | n | cycles | submits | revising | agree@turn1 | never_refuse | frozen | recovery |
|---|---|---|---|---|---|---|---|---|---|
| gemma-4 | A | 118 | 5.36 | 1.97 | **3.39** | 0.754 | 0.042 | 0.076 | 0.254 |
| gemma-4 | B | 118 | 5.84 | 5.84 | **0.00** | 1.000 | **1.000** | **0.932** | 0.051 |
| gpt-oss | A | 124 | 5.22 | 2.69 | **2.53** | 0.790 | 0.024 | 0.008 | 0.315 |
| gpt-oss | B | 121 | 5.33 | 5.20 | **0.13** | 0.975 | 0.909 | 0.355 | 0.231 |

**Arm B gemma spends literally zero cycles revising** — every cycle is a
resubmission, it agrees on turn 1 in 100% of trajectories, never once
refuses, and 93.2% of the time never changes its answer string at all. This
is the mechanism behind Q2, and it is starker than Omni-MATH.

Paired frozen-rate over all judged trajectories:

| actor | n | frozen_A | frozen_B | B-A | 95% CI | exact p |
|---|---|---|---|---|---|---|
| gemma-4-31B | 574 | 0.784 | 0.941 | +0.1568 | [+0.1220,+0.1934] | 8.3e-18 |
| gpt-oss-120b | 574 | 0.470 | 0.601 | +0.1307 | [+0.0801,+0.1812] | 6.4e-07 |

Both actors significant here, including gpt-oss.

## Q4 — Does functional division of labor collapse? **YES, in both actors.**

| actor | arm | n | collapse | n_unan_def | unanimous |
|---|---|---|---|---|---|
| gemma-4 | A | 574 | **0.000** | 0 | — |
| gemma-4 | B | 574 | **0.998** | 573 | 0.941 |
| gpt-oss | A | 574 | 0.347 | 199 | 0.060 |
| gpt-oss | B | 574 | **0.990** | 568 | 0.637 |

| actor | n | coll_A | coll_B | B-A | 95% CI | exact p |
|---|---|---|---|---|---|---|
| gemma-4-31B | 574 | 0.000 | 0.998 | +0.9983 | [+0.9948,+1.0000] | 6.5e-173 |
| gpt-oss-120b | 574 | 0.347 | 0.990 | +0.6429 | [+0.6028,+0.6829] | 1.6e-109 |

Marker sensitivity (FINDING-14 requires it, since the measure keys on `\boxed`):

| actor/arm | `\boxed` | +"answer is" | +"final answer" | spread |
|---|---|---|---|---|
| gemma-4 / A | 0.000 | 0.002 | 0.035 | 0.035 |
| **gemma-4 / B** | 0.998 | 0.998 | 0.998 | **0.000** |
| gpt-oss / A | 0.347 | 0.422 | 0.611 | 0.265 |
| **gpt-oss / B** | 0.990 | 0.990 | 0.990 | **0.000** |

Arm B is marker-invariant in both actors, so the collapse finding does not
depend on the marker choice. Same pattern as Omni-MATH (FINDING-14).

## Context: final accuracy

| actor | n | acc_A | acc_B | B-A | 95% CI | exact p |
|---|---|---|---|---|---|---|
| gemma-4-31B | 574 | 0.847 | 0.805 | -0.0418 | [-0.0662,-0.0192] | 7.2e-04 |
| gpt-oss-120b | 574 | 0.852 | 0.838 | -0.0139 | [-0.0366,+0.0087] | 0.302 |

Same shape as Omni-MATH: gemma pays a significant accuracy cost for losing
roles (-0.042 here, -0.030 there), gpt-oss does not detectably.

## What this replication shows

The dissociation reproduces in an out-of-domain benchmark: **organization
collapses in both actors (Q4, p<1e-109), first-pass solving is untouched
(Q1, exactly 0.000 for gemma), and the cost lands entirely in recovery
(Q2/Q3)** — for the actor the study is powered to resolve.

The boundary condition is about *measurement*, not mechanism: SciBench is
easy enough for these actors (first-pass ~0.79) that the recovery denominator
is a third of Omni-MATH's, so only the larger of the two actor effects is
detectable. Both point estimates point the same way in both domains.

## Not computed, deliberately

P1a and every clause-specific role-fidelity metric. The Arm A contract was
domain-adapted (option b), so those clauses differ across domains and scoring
them would score agents against instructions they never received
(`notes/DEFECT-prompt-varies-by-domain.md`).


---

## POWER CORRECTION (2026-10-01) — do not quote a single figure

Earlier versions of this note recorded gpt-oss's SciBench power as **0.42**.
Re-derived three ways at the realised paired n=96, against gpt-oss's own
Omni-MATH discordant rates (52 vs 39 of 327):

| method | power |
|---|---|
| **exact McNemar — the test the paper actually reports** | **0.06** |
| two-proportion z approximation | 0.12 |
| the figure previously recorded here | 0.42 |

A quantity that moves 7x with the test assumed must not be asserted as one
number. **The paper says "0.06--0.45 by test".** The conclusion is identical
under every method -- the cell is uninformative and its null is not a
non-replication -- so nothing downstream changes.

**Why this had to be fixed here and not only in the manuscript.** I corrected
the paper on 2026-09-30 but left 0.42 standing in these notes. A later
writing agent, told that notes are a valid source, found 0.42, could not find
"0.06--0.45" anywhere, and reasonably reverted the manuscript to the figure
it could source. It was right to do that: the fault was mine for fixing a
derived artifact and not its source. This is the canonical-chain rule in
`SOURCE_OF_TRUTH.md` -- a correction that stops before the source will be
undone by the next worker who checks.
