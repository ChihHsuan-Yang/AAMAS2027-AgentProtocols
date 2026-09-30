# Independent mock review #1 — WEAK REJECT

**2026-09-30. Reviewer saw the PDF only: barred from every project file,
note, script, and dataset. That was the point — everyone else who has looked
at this work already knows what it is supposed to say.**

## Verdict

**Weak reject, confidence 4/5.** Reviewer's own summary: *"a genuinely careful
paper that I would like to accept, and which I am rejecting largely on grounds
it created for itself."*

Three blockers, all verified by me independently:

1. **~0.5 page over the limit.** 539 main-text words on page 9.
2. **Text printed off the physical page.** Page 6 has a word at xMax 614.8 on a
   612pt page.
3. **Table 2's p-value does not reconcile with its own CI.** Printed 2e-8;
   the interval implies ~1.4e-5. 2e-8 is the §5.4 recovery test's value.

## The blocker I should have caught: our page check was column-blind

The check used everywhere in this project compares y-coordinates against the
REFERENCES heading. **REFERENCES sits at the top of the RIGHT column of page
9.** In a two-column layout every word in the LEFT column then has y GREATER
than the heading — so 539 words of main text were invisible to the check,
which dutifully reported "11 words above REFERENCES" (the two running heads)
and read as a pass.

Reading order is (column, y), not y. `scripts/pagecheck.py` now orders that
way, asserts the heading was found, and exits nonzero on violation.

**This is the fourth time in this project a check has passed by looking at
the wrong thing**, and the second where the *reported* quantity was right and
the *subject* was wrong. The earlier trim worker even warned that an ABSENT
heading would make the check vacuous — I added the assert for that case and
did not ask whether a heading that WAS found could still be measured wrongly.

## What the reviewer credited (unprompted)

Worth recording, because these were expensive to do and a hostile reader
noticed them:

- Self-refuting our own validation instrument in the results section
  ("unusual and correct").
- Publishing the as-graded analysis that would have made our story and
  declining to use it: *"the most creditable sentence in the paper."*
- The 2.85 ch/s tell for the logging defect: *"exactly the right instrument.
  Most papers would have reported a 0.722 abstention rate and called it the
  most compliant Planner in the study."*
- The gemma-4 ITT reparameterization — verified our algebra independently.
- Format: *"no Tz, no Tc, uniform 10.96pt baselines... the overrun was not
  achieved by compression."*

## Substantive findings we had not caught

- **Arm B consumes ~1.8x Arm A's oracle verdicts** (1.95 vs 1.11 evaluator
  calls). We apply this accounting to the single-agent control and not to our
  own main contrast. Direction favours us; the claim "a test of organization,
  not of scale" is unqualified and should not be.
- **The Reviewer's answer-assertion rate is never reported** — "the planner
  carries the entire signal" is a three-way decomposition with two terms.
- **§5.6's Arm C rates do not compose into Table 3** (+0.0024/+0.0494/+0.0633
  vs −0.0225/−0.0050/+0.0175). Different denominators; §5.4 teaches the reader
  to do exactly this composition and we never say it doesn't apply here.
- **"We reject premature consensus"** overreaches. We refuted premature
  *stopping*. Consensus-then-resubmission is arguably premature consensus
  confirmed.
- Three count inconsistencies: 11,600 vs C′ "400 per actor"; Llama recovery
  printed as both 0.014 and 0.015; 171 adjudicated vs 42+56+44=142.
- **No figures at all.** Reviewer flagged this as an accessibility gap.

## Path back

Reviewer: *"If the authors resolve Q1 convincingly and the length is fixed
without gutting §7, this is a weak accept and I would argue for it."*
