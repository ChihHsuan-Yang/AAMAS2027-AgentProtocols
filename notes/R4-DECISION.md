# R4 decision (N-14): narrow the Reviewer claim rather than annotate

**2026-09-29. Ruling by the Master Agent.** Bella's instruction (§32/§37) was:
finish R4 if Reviewer behaviour stays in the final claim, otherwise narrow the
claim and remove the unnecessary Reviewer-fidelity language. I measured first,
then decided.

## Measurement: the Reviewer rarely exercises its critique function

Share of trajectories where the Reviewer **accepts on its first turn**:

| actor | A | B | C | C' |
|---|---|---|---|---|
| gemma-4-31B | 0.792 | **0.995** | 0.972 | 0.972 |
| gpt-oss-120b | 0.697 | **0.937** | 0.858 | 0.875 |

A Reviewer is present in ~100% of trajectories, but in the soft-role arm it
rubber-stamps 70-79% of the time, and once roles are removed it accepts
essentially always (0.937-0.995). The critique function is largely unexercised
in the arms the paper is about.

## Decision: NARROW, do not annotate

**Rationale.** Annotating the 30 held Reviewer messages would validate a
construct that the data shows is barely operative. It would spend a day of
effort to support a claim the paper does not need and should not make. The
paper's mechanism (F11) is about **escaping wrong consensus**, which is driven
by whether the three agents *disagree*, not by whether the Reviewer critiques
well.

**What the manuscript will therefore do:**
1. **Remove** any claim about Reviewer *fidelity* or Reviewer *specialization*.
2. **Keep** the Reviewer in the protocol description (it is part of PER) and in
   the Arm C boundary description, since the Reviewer's answer-authorship
   constraint is real and measured (it produces the boundary rejections).
3. **Report the accept-on-first-turn rates above as a finding**, because they
   are informative: the review stage is mostly inert, and it becomes *more*
   inert when roles are removed. That is consistent with, and supportive of,
   the redundancy story.
4. State plainly in Limitations that Reviewer *behaviour* was not
   human-validated, and that no claim rests on it.

**Consequence for the earlier flagged risk.** VALIDATION-FINAL.md noted that R4
would become Arm C's manipulation check *if* the constrained critique interface
were reported as a contribution. Under this ruling it is not reported as a
contribution, so no unvalidated manipulation check enters the paper. The open
flank is closed by narrowing, which is the cheaper and more honest option.

**Reversal condition:** if the human-validation worker's annotations show the
Reviewer doing substantive work that this accept-rate measure misses, revisit.
