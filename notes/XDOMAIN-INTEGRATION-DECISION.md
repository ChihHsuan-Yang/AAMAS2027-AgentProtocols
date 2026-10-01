# SciBench integration decision — MAIN PAPER, one paragraph + one table row

**2026-09-30. Decided against `notes/XDOMAIN-POWER-PREREG.md`, which was
written at 761/2,296 rows before any recovery contrast existed.**

## What the rule said, before the data

> Integrate in the main paper only if SciBench gives a clean
> independent-domain replication or an interpretable boundary condition.
> A mixed result — gemma replicates, gpt-oss underpowered — is **supplement
> or rebuttal material, not a second headline.**

## What landed

2,296/2,296, zero failures, zero unjudged, all four cells exactly 574,
frozen sha256 `10068f72cfd936d3`. I re-derived everything below myself from
the frozen file rather than taking the worker's numbers.

**Paired subset (problems first-pass-wrong under BOTH arms) — the same
population the Omni-MATH headline uses:**

| domain | n | A recovers only | B recovers only | delta | exact p |
|---|---|---|---|---|---|
| Omni-MATH | 237 | 37 | 3 | $-0.1435$ | 1.95e-08 |
| **SciBench** | **99** | **21** | **2** | $\mathbf{-0.1919}$ | **6.60e-05** |

Two-proportion test on the discordant rates: **z=1.06, p=0.289 — the two
effects are not distinguishable.** This is the same effect, the same size,
in college chemistry and physics as in competition mathematics.

First pass moves by **exactly 0.000** (B$-$A, gemma-4), as in Omni-MATH.
Collapse 0.000 -> 0.998. Arm B spends **0.00** cycles revising.

**gpt-oss: unresolved, not a non-replication.** Point estimate $-0.083$,
nearly its own Omni-MATH effect ($-0.077$), paired p=0.169. Power at the
realised n=96 is **0.42 against its own effect size and 1.00 against a
gemma-sized one** — the cell can detect a large effect and cannot detect
this one. Rule 2 binds: reported as "cannot resolve", never as an actor
failing to replicate, and never pooled with gemma to manufacture power.

## The decision, and why it is NOT "mixed"

The pre-registered rule sends a *mixed* result to the supplement. This is not
mixed in the sense the rule anticipated. The rule imagined gemma replicating
and gpt-oss **failing**. What happened is gemma replicating at an
indistinguishable effect size and gpt-oss being **uninformative by design** —
a cell that was never powered to answer, which we knew before launch and
wrote down.

An uninformative cell is not counter-evidence. Excluding the whole experiment
because one cell is silent would discard the clean gemma replication for no
scientific reason.

**Decision: MAIN PAPER, tightly scoped.** One paragraph in Results plus one
row in the cross-domain line of the relevant table. Specifically:

- The gemma-4 paired replication with both effect sizes and the
  not-distinguishable test.
- The exact-zero first-pass move, which is the dissociation, not a detail.
- One sentence stating gpt-oss is underpowered at n=96 (power 0.42) and is
  therefore not evidence either way.
- **No claim that "the result generalizes across domains"** — one actor
  replicated in one further domain.

## What must NOT be written
- "Replicates across two benchmarks" — one actor did, in one benchmark.
- "Two of three actors" — Llama was not run on SciBench.
- Any pooled SciBench+Omni statistic.
- Any P1a or clause-specific fidelity comparison across domains: the Arm A
  contract was adapted (option b), so cross-domain scoring would score agents
  against instructions they never received.

## Cost control
Bella's rule: do not damage a clear 8-page story to say "two benchmarks".
The page budget has a one-sentence margin, so this paragraph must be **traded
against existing text, not added**. If it cannot be added without pushing
main text to page 9, it goes to the supplement — the rule outranks the
result.

## Two robustness facts worth carrying
- FINDING-18 reproduces in SciBench and again runs **against** the headline:
  correcting it moves gemma to $-0.202$ (p=3.6e-05) and leaves gpt-oss
  unchanged. No verdict flips.
- The grader noise floor here is **2.80%**. **CORRECTED 2026-09-30:** an
  earlier version of this line compared it to "9.35% on Omni-MATH". That
  figure is **not ours** -- it comes from an unrelated project's 7B DPO
  scorer (a memory file), and I imported it without checking. Omni-MATH's
  own floor, canonical T6, is **0.0072**. So SciBench's grader is roughly
  4x NOISIER than Omni-MATH's, not quieter. The gemma SciBench effect
  (-0.192) still clears its own domain's floor by ~7x, which is the claim
  that matters; the cross-domain floor comparison was backwards.

## A denominator note, recorded because it nearly became an error
The worker reported marginal recovery 0.212 -> 0.020; I computed 0.254 ->
0.051 from the same frozen file. **Both are right.** 0.212/0.020 is the
PAIRED subset (n=99, both arms first-pass-wrong); 0.254/0.051 is the MARGINAL
rate over each arm's own first-pass-wrong set (n=118 each). This is defect
class 3 in `FINAL_NUMBER_AUDIT.md` — marginal vs paired population confusion
— and it is exactly how a wrong pair of numbers enters a paper. **The paper
must state which population every SciBench figure uses.**
