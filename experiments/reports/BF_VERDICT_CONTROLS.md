# §15/§20 verdict rule — adversarial controls and three repairs

Scope: `analysis/scripts/bf_verdict.py`, the script that converts the three
paired recovery contrasts into exactly one of §20's four labels.

**All of this was done while blind to every Bf result.** The Omni Bf cell was
still running and no Bf contrast had been computed. That is the only point at
which a decision threshold can legitimately be changed (§15 requires the
decision logic to be predeclared), so the repairs below are timestamped
against a state in which they cannot have been chosen to favour an outcome.
`grep` confirms nothing calls `verdict()` yet: the rule was not yet wired.

## Why the shipped self-test was not evidence

The script's `__main__` ran four worlds I had written myself, each labelled
with the answer I expected. A test built from the author's own imagination
confirms the branches the author remembered writing. It cannot find a
parameter that is never read, and it did not.

## Controls run

| # | Control | Result |
|---|---------|--------|
| C1 | Is every declared parameter actually read in the body? | **FAIL → fixed** |
| C2 | Does swapping b/c change the verdict? (void-harness check) | PASS — labels flip |
| C3 | Exhaustive 7×7×2×2 grid: are all four labels reachable? | PASS — 4/4 reachable |
| C4 | Significant-but-sub-floor region returns the conservative label | PASS — INCONCLUSIVE, floor named |
| C5 | Exact boundary `delta == need` | PASS (see note) |
| C6 | Docstring's own sensitivity claim, frac 1/5…1/2 | **FAIL → docstring corrected** |
| C7 | Premise gate on null / reversed frozen A-vs-B | PASS after repair (3 cases) |
| C8 | Domain-specific floors differ | 0.0570 vs 0.0678, 19% apart |
| C9 | Same data, two domain gaps → different labels | **demonstrates the defect was load-bearing** |

C5 note: my first run reported INCONCLUSIVE at the boundary and I nearly
recorded a boundary defect. The cause was `int()` in *my test input*, which
rounded the constructed margin below the floor. With `ceil` the rule returns
ROLE EFFECT SURVIVES at `delta >= need`, as written. The script was correct;
my control was wrong. Recorded because the misreading is the kind that
becomes a false bug report.

## Defect 1 — the frozen A-vs-B contrast was accepted and ignored

`verdict(ab, abf, bfb, ...)` declared `ab` and never referenced it: zero
occurrences of `ab[` in the body. Every caller would have passed the frozen
A-vs-B numbers believing they constrained the verdict. They did not.

This matters beyond tidiness. The entire control rests on a premise — that A
really did beat B on recovery in the frozen data. If that premise were false
there would be no gap for feedback delivery to explain, and all three labels
other than INCONCLUSIVE would be statements about nothing. The script would
have returned a confident label anyway.

Repair: `ab` is now checked. If the frozen A-vs-B contrast is not significant
*and* positive, the function returns INCONCLUSIVE with `PREMISE FAILS`.
Verified it fires on a null frozen contrast (C7) and on a *significant but
reversed* one (C7c) — the second case matters because a naive `p < ALPHA`
guard would have passed it — and stays silent on the real frozen contrast
(C7b, 37 vs 3 on n=237, p=1.95e-08).

## Defect 2 — one domain's reference gap hardcoded as the default for both

`ab_gap_ref=0.171` is the **Omni** marginal recovery gap. SciBench has its
own. Measured from `/tmp/frozen_sci/scibench_AB.jsonl`, gemma-4, each arm over
its own first-pass-wrong set:

| domain | A | B | gap | floor at 1/3 |
|---|---|---|---|---|
| Omni-MATH | 70/316 = 0.2215 | 16/316 = 0.0506 | 0.1709 | 0.0570 |
| SciBench  | 30/118 = 0.2542 |  6/118 = 0.0508 | **0.2034** | **0.0678** |

19% apart. A SciBench analysis run through the default would have used a
floor 19% too lenient.

C9 shows this was not hypothetical: a world with A-Bf margin +0.0609 and Bf
indistinguishable from B returns **ROLE EFFECT SURVIVES** under the Omni gap
and **INCONCLUSIVE** under SciBench's. Same data, opposite conclusions.

Repair: the parameter is now **required**, with `REF_GAP_OMNI` and
`REF_GAP_SCIBENCH` as named constants. Omitting it is a `TypeError`, not a
silent wrong answer — chosen over a safer default because there is no
defensible default here.

## Defect 3 — the docstring understated its own sensitivity

It claimed varying `SURVIVE_FRAC` over 1/5…1/2 left three labels unchanged
and flipped BOTH CONTRIBUTE to INCONCLUSIVE at 1/2. The first half is
correct. The second understates it — the BOTH world crosses **three** labels:

| SURVIVE_FRAC | floor | label (A-Bf +0.070, Bf-B +0.064) |
|---|---|---|
| 0.200–0.333 | 0.034–0.057 | BOTH CONTRIBUTE |
| 0.375–0.400 | 0.064–0.068 | ROLE EFFECT SURVIVES FEEDBACK MATCHING |
| 0.420–0.500 | 0.072–0.086 | INCONCLUSIVE |

Passing through ROLE EFFECT SURVIVES is the part worth flagging: a reader
checking robustness by testing only the endpoints 1/5 and 1/2 would see BOTH
and INCONCLUSIVE and never learn that the *affirmative* label sits between
them. Corrected in the docstring, with the §20 instruction unchanged and now
better justified: **if the result lands in BOTH, state the margin relative to
the floor and do not present BOTH as threshold-independent.**

## Not done

`SURVIVE_FRAC` itself is unchanged at 1/3. The three repairs fix a parameter
that was ignored, a constant that was wrong for one domain, and a docstring
that misdescribed measured behaviour. None of them moves the threshold, and
no Bf contrast has been computed.
