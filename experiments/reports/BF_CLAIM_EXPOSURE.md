# Claim exposure from the feedback-delivery defect (S.3 / S.18)

Status: CATALOGUE ONLY. No manuscript text has been edited (directive S.18).
Final labels in report section I are provisional until the Bf run completes
and S.13 interpretation is permitted.

## The defect, restated

DECLARED (`runner.py` VISIBILITY["B"], logged per trajectory into all 9,600
Omni rows and all 2,296 SciBench rows):
`["problem", "shared_history", "advice"]`

ACTUAL (realized prompts): `problem` + `shared_history` only. `B_GENERIC_PREPEND`
has no `${advice}` slot, `build_messages()` never passes advice to arm B, and
`shared_history` only ever receives `[Planner]`/`[Executor]`/`[Reviewer]` turns.
Arm B agents never saw the evaluator's FAIL verdict or repair hint.

## Statements that depend on the claim

| Location | Quoted fragment | Exposure |
|---|---|---|
| `paper/main.tex` abstract | "it is neither stopped early nor **given less information**" | DIRECT. The role-free team WAS given less information: the evaluator signal never reached its prompts. |
| `paper/main.tex` abstract | "**The difference appears only after a team is told its answer is wrong.**" | DIRECT. Arm B was never told, in its prompts. |
| `paper/sections/results.tex:131` | "the grid, the agents, the budget, the evaluator and **the hint text are identical by construction**" | DIRECT and most specific. The hint text was constructed identically but delivered only to A. |
| `paper/sections/intro.tex:50` | "not fewer chances, not early stopping and **not less information**" | DIRECT, same claim as the abstract. |
| `paper/sections/intro.tex:43` | "**Once the evaluator tells both teams** their answer is wrong" | DIRECT. The evaluator told only A. |
| `paper/sections/conclusion.tex:8` | "the difference emerged only once **both teams were told** their answer was wrong" | DIRECT. |
| `paper/sections/method.tex:14` | "a team that submits more *consumes* more oracle verdicts" | UNAFFECTED. A statement about verdict consumption/accounting, true regardless of delivery. |

## What is NOT exposed by this defect

* Every first-pass number. B and A are byte-identical before the first verdict;
  first-pass rates equal to four decimals is a property of the shared prefix.
* The role-destruction measurement (own-answer assertion 0.000-0.120 -> 0.846-0.976).
  Measured from realized outputs, independent of evaluator delivery.
* Arm C / Cp results, which have their own (separately corrected, 2026-09-28)
  visibility entry.
* The arithmetic of the A-vs-B recovery contrast itself: 70/316 vs 16/316,
  paired n=237, 37 vs 3, p=1.95e-08 all reproduce exactly from the frozen files.
  What is in question is the INTERPRETATION of that contrast, not its numbers.

## The "more oracle verdicts" argument specifically

The paper's decisive move against the rival explanation is: "every rival
explanation of the form 'the role-free team had less to work with' predicts
FEWER verdicts ... and the role-free team draws MORE."

This argument is weakened in a specific, non-obvious way. The role-free team
did draw more verdicts -- that is a true measurement of evaluator CALLS. But a
verdict it draws and is never shown is not information it has. The count of
verdicts consumed and the information delivered to agents came apart precisely
because of this defect, so the verdict count can no longer carry the
"not less information" conclusion on its own. Bf is the experiment that
separates them.

## Provenance defect, reported separately from the result (S.3)

Independently of how Bf turns out, `visibility_policy` was logged per
trajectory as ground truth and was false for arm B in 11,896 rows
(9,600 Omni + 2,296 SciBench). That is a provenance defect in the released
artifact and must be documented as such, in the same class as the Arm C
entry corrected on 2026-09-28. The field is now corrected in source
(`runner.py` VISIBILITY["B"]), which is also why `config_version` changes and
Bf rows can never silently pool with frozen rows.
