# Bf control — result package for the human authors

One-page summary of the role-free + feedback-delivered (Bf) control.
Written 2026-10-06 at handoff. **The storyline is yours to choose** — nothing in
the manuscript was edited, and this file deliberately does not propose wording.

## What changed

The original role-free arm (**B**) did not actually receive the evaluator's
FAIL verdict or repair hint, even though the frozen run metadata recorded that
it did. The role-structured arm (**A**) did receive it. So the published
A-vs-B recovery comparison varied **two** things at once: role structure *and*
whether the team was ever told it was wrong.

## New control

**Bf = role-free + evaluator feedback delivered.** Identical to B in every
respect except that the FAIL/hint is placed into the next agent's prompt, which
is what A had all along. Same actor (`gemma-4-31B-it`), same evaluator
(`gpt-oss-120b`), same problems, same budgets, same endpoint. Delivery was
verified by hash-reconstructing every actor prompt, not by trusting a metadata
flag: feedback reached an agent in **302/302** (Omni) and **124/124**
(SciBench) of first-pass-wrong Bf trajectories.

## Key results

Recovery = *first evaluator verdict wrong* **and** *final answer correct*.
Denominator is each arm's own first-pass-wrong set.

| | Omni-MATH | SciBench |
|---|---|---|
| Structured **A** | 0.2215 (70/316) | 0.2542 (30/118) |
| Original **B** | 0.0506 (16/316) | 0.0508 (6/118) |
| **Bf** | **0.5861** (177/302) | **0.4355** (54/124) |

Paired (exact McNemar, problems first-pass-wrong under both arms):

| contrast | Omni-MATH | SciBench |
|---|---|---|
| A vs B | p = 1.95e-08 | p = 6.6e-05 |
| A vs Bf | p = 7.85e-21 (Bf ≫ A) | p = 0.0522 (undetermined) |
| Bf vs B | p = 1.09e-37 | p = 5.12e-12 |

## Interpretation

**FEEDBACK DELIVERY EXPLAINS ORIGINAL GAP** in both domains, under the reading
fixed *before* the run in `BF_CONTROL.md`. Once the role-free arm is given the
same correctness signal, it does not merely close the gap to A — on Omni-MATH
it overtakes A outright, and on SciBench the A-vs-Bf difference is no longer
resolved. The old A-vs-B recovery gap is attributable to who was told they were
wrong, not to role structure.

## Still valid from the original paper

- Role removal strongly changes **division-of-labour behaviour**; that is a
  separate measurement and is untouched by this confound.
- **First-pass** findings are unaffected: feedback cannot act before the first
  verdict, and first-pass rates are near-identical across arms (Omni 0.8025 A /
  0.8025 B / 0.8113 Bf; SciBench 0.7944 / 0.7944 / 0.7840).
- Structural-enforcement analyses remain separate from this specific confound.

## Claims that must change

Any statement that **A and B received the same external correctness signal**,
and any statement attributing the **A-vs-B recovery gap specifically to role
structure**. `BF_CLAIM_EXPOSURE.md` lists the affected manuscript sites.

## Useful new observation

Bf recoveries are overwhelmingly **genuine answer revisions**, not stochastic
re-grading of an unchanged string: 174/177 = 0.983 (Omni) and 50/54 = 0.926
(SciBench), against 1.000 for A. The re-grading artifact this check was looking
for shows up in **B** instead (7/16 Omni and 6/6 SciBench "recoveries" involve
no answer change) — consistent with a team never told it was wrong. Correcting
for it would lower B further and *widen* the Bf-vs-B gap.

## Two caveats you should carry forward

1. **Endpoint drift is only partly cleared.** The S.16 bridge returns
   `DRIFT VERDICT: NONE`, but that label is emitted by a `bounded` predicate
   that reads first-pass and final only and **never consults the recovery CI**.
   Recovery is the primary endpoint and its CI, [−0.0419, +0.1980], is not
   bounded. Recovery drift is **unresolved at n=400**. §I of the final report
   also shows the headline verdicts survive subtracting the worst-case drift.
2. **The bridge number is re-run-sensitive.** `run_bf.sh` writes fixed
   filenames, and was run twice; the surviving bytes give 338/400 where the
   superseded pass implies 327/400, flipping the drift delta's sign (+0.0200 vs
   −0.0075). Both sit inside the reported CI. See `BF_DATA_CUSTODY.md`.

## Where everything is

GitHub — branch `control-rolefree-feedback`:

| what | path |
|---|---|
| full A–J report + verdict | `experiments/reports/BF_FINAL_REPORT.md` |
| pre-registered reading | `experiments/BF_CONTROL.md` |
| machine-readable results | `experiments/results/bf/BF_SUMMARY.json` |
| data custody, hashes, two-chain account | `experiments/reports/BF_DATA_CUSTODY.md` |
| manuscript sites to revisit | `experiments/reports/BF_CLAIM_EXPOSURE.md` |
| main analysis | `analysis/scripts/bf_control.py` |
| endpoint-drift analysis | `analysis/scripts/bf_drift.py` |
| verdict rule | `analysis/scripts/bf_verdict.py` |
| delivery unit tests | `experiments/test_bf_delivery.py` |
| freeze + verify tool | `experiments/bf_freeze.py` |
| freeze manifest (current bytes) | `experiments/results/bf/FROZEN_BF/MANIFEST.json` |
| manifest of the superseded pass | `experiments/results/bf/MANIFEST_BF.json` |

Raw trajectories are **not in git** (~42MB, gitignored by the same convention
as the original campaign). They live in the private HF dataset below and in the
local staging tree `hf_artifact/raw/bf/`.

Hugging Face — `AgentsSci/AAMAS2027-Roles`, **PRIVATE**, under
`controls/rolefree_feedback/gemma4/`. Bf is a **separate control artifact**: the
frozen v1.1.0 campaign was not overwritten or mutated, and Bf rows must never be
silently pooled into it.

Verify any copy of the raw rows:

```bash
python experiments/bf_freeze.py --verify <dir>/FROZEN_BF <dir>
```
