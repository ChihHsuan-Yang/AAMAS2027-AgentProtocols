# Independent mock review #2 — WEAK ACCEPT (confidence 3/4)

**2026-09-30. Reviewer saw only the paper text, split into three chunks.
No notes, no scripts, no data, no prior review. Five earlier attempts at
this review stalled; this one succeeded in 3 tool calls.**

## Movement

Review #1: **weak reject** (3 blockers: page limit, text off the page,
a p-value that did not reconcile with its own CI).
Review #2: **weak accept**, and the earlier blockers are gone.

Its closing position: restate the claims to their actual support and it is
acceptable.

## The three blockers, all real

1. **"In all three actors" applies to collapse, not recovery.** The abstract
   opens with it two sentences before the recovery claim. gemma-4 is clean
   (ITT-equivalent, p=2e-08), gpt-oss weak (paired p=0.246), Llama absent.
2. **The logging defect may reach the primary collapse measure.** 93.4% of
   gpt-oss's Arm B first passes contain an affected message, and collapse is
   defined as "all three assert an answer" — exactly the judgment you cannot
   make when the derivation was discarded.
3. **The conclusion does not follow through on §5.8**: gemma-4's team loses
   to its own budget-matched single agent in both arms, and gemma-4 is the
   actor carrying the recovery result.

## Blocker 2, tested rather than argued

The reviewer's hypothesis is empirically checkable, so I checked it before
asking anyone to write prose. Restricting to first passes where **no**
message carries the F13 signature (visible chars/sec < 10):

| actor | arm | all messages | unaffected only | n |
|---|---|---|---|---|
| gpt-oss | A | 0.120 | **0.118** | 1,236 |
| gpt-oss | B | 0.846 | **0.821** | 106 |
| gemma-4 | B | 0.976 | 0.976 | 1,595 |

**The collapse survives on clean messages.** The defect is not manufacturing
it. One sentence of evidence answers a blocker that would otherwise have
required re-running an arm.

## Llama Arm C denominator, shown

Reviewer asked for construction, not assertion: attempted 400 -> received a
verdict 349 -> **first verdict wrong 251** (the denominator), of which 17
later died in regeneration and score 0; 35 recovered -> **0.139**.
Survivors-only would be 0.150, so including the dead is the conservative
direction, and the claim is not a function of which trajectories survived.

## The criticism most worth acting on

> "All 24 references are LLM-era; the paper engages **none** of the MAS
> organizational literature (Moise+, OperA, TAEMS) that has treated exactly
> 'what is a role contract and when does it bind' for two decades. For this
> venue that omission is conspicuous."

This is the best-value finding in the review for an AAMAS audience, and no
number audit would ever have produced it. Queued.

## One reviewer point that is already moot

It reports "no cross-domain check at all; the second domain was designed and
dropped." **The reviewer read a pre-SciBench extraction.** SciBench landed
in Limitations after the text was extracted. Not a defect in the review —
a timing artifact of my own pipeline, recorded so nobody treats it as an
open finding.

## What it credited, unprompted

- The gemma-4 ITT identity: *"the cleanest available answer to the
  post-treatment objection, and it is earned, not asserted."*
- R4: *"The control is not doing less work; it is doing more."*
- Self-adversarial reporting, including refusing the survivorship-positive
  Arm C reading: *"I rarely see this."*

## Two soundness items to consider

- Executor plan-adherence validated at **n=13**; a kappa of 0.843 there has
  a CI covering nearly everything, yet it is reported as clearing a 0.80
  threshold.
- P1a agreement **falls** with n (0.967 at n=30 -> 0.903 at n=72), which
  suggests it has not stabilized.

Both are measurement-validation claims, not headline results, but a careful
reader will land on them.
