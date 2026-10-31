# Collapse adjudication rubric v1 — FROZEN 2026-09-29, before any judging

**Protocol:** blinded frontier-model adjudication (primary judge: Opus 5).
**This file is frozen.** Any change after the first judgement must be recorded
as a dated amendment below, with pre-amendment results reported alongside.
Rationale: an earlier metric on this project ("P1a v3") was tuned after seeing
agreement and got worse. The protection is to fix every rule before running.

## Unit

One trajectory, presented as its **first three role messages** (one pipeline
pass). This matches the project's primary count-matched collapse rule and
avoids the trajectory-length confound.

## What the judge is NOT told

actor model · arm (A/B/C) · the automated collapse label · task correctness ·
the paper's hypothesis · the expected direction. Agents are presented as
**Agent 1 / Agent 2 / Agent 3** in pipeline order. Presentation order of items
is randomized under a recorded seed.

## The five judgements (each YES/NO, plus a one-line reason)

**Q1 SEMANTIC REDUNDANCY** — Do later agents substantially repeat reasoning
already present in an earlier agent's message?
- YES: Agent 2 restates Agent 1's derivation in different words, adding no new
  step; or reproduces the same answer with the same justification.
- NO: Agent 2 pursues a different decomposition, method, or line of argument.
- *Paraphrase counts as YES.* Identical bytes are a special case of YES, not a
  requirement.

**Q2 FUNCTIONAL REDUNDANCY** — Does a later agent fail to contribute a
meaningful role-specific function beyond what earlier agents supplied?
- YES (redundant): every agent does the same kind of work — e.g. all three
  solve the problem end-to-end and assert an answer.
- NO (not redundant): the agents do *different kinds* of work — e.g. one
  structures the approach, one executes it, one checks it.
- Judge the *kind* of contribution, not its quality or correctness.

**Q3 NEW INFORMATION** — Does any later agent introduce a new derivation, fact,
computation, critique, correction, or decision not already present?
- YES if any later agent adds any of these. NO if later agents only restate,
  reformat, or agree.

**Q4 ANSWER INFLUENCE** — Does a later agent materially change the candidate
answer or the reasoning path?
- YES: the answer changes, or a later agent redirects the method.
- NO: the answer and approach are carried forward unchanged.
- A bare agreement ("[Agree]") is NO.

**Q5 MEANINGFUL DIVISION OF LABOUR** — Taken as a whole, would a reasonable
reader describe this trajectory as exhibiting distinct functional contributions
from three roles?
- This is the headline judgement. It may be YES even if the work is wrong.
- It should be NO when the trajectory is effectively one agent's solution
  repeated or rubber-stamped.

## Worked examples (fixed before judging)

**Example A — Q5 NO.** Agent 1: `\boxed{8}` `[Agree]`. Agent 2: `\boxed{8}`
`[Agree]`. Agent 3: `\boxed{8}` `[Agree]`. Three assertions of one answer, no
structuring, no checking. Q1 YES, Q2 YES, Q3 NO, Q4 NO, Q5 NO.

**Example B — Q5 NO despite differing text.** Agent 1 solves the problem in
full. Agent 2 re-solves it independently by the same route at greater length.
Agent 3 says the work looks correct. Surface text differs substantially;
function does not. Q1 YES, Q2 YES, Q3 NO, Q4 NO, Q5 NO.

**Example C — Q5 YES.** Agent 1 lists givens and an ordered plan without
computing. Agent 2 executes the plan and produces a boxed value. Agent 3
identifies a missing case and routes it back. Q1 NO, Q2 NO, Q3 YES, Q4 YES,
Q5 YES.

**Example D — borderline, decided in advance.** A reviewer that *checks* the
derivation and approves without adding a step: Q3 NO (adds no new content) but
Q2 NO (checking IS its role function). **Q5 turns on whether the other two
agents differ.** This borderline is load-bearing and is recorded as the rubric's
biggest judgement call.

## Output contract
Strict JSON: `{"Q1":"YES|NO","Q2":...,"Q3":...,"Q4":...,"Q5":...,"reason":"<=25 words"}`

## Reporting contract (fixed now)
agreement · precision · recall · confusion matrix · **per-actor** and
**per-arm** breakdowns · judge stability across repeated independent calls ·
inspection of disagreement cases. Never a single aggregate score alone.
