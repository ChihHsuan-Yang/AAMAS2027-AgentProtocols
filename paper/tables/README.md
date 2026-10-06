# `paper/tables/` --- generated tables

**Every file in this directory is generated. Do not hand-edit one: the next
run of the generator overwrites it, and a hand-typed number has no
provenance.**

```
python3 analysis/scripts/mk_tables.py           # regenerate all tables
python3 analysis/scripts/mk_tables.py --check   # verify, write nothing
```

Regeneration is **byte-identical**: the generator stamps the canonical
input's mtime rather than wall-clock time, so a rerun that changes a file
means the *data* changed.

## Disposition --- where each table goes

Every table has a declared disposition, and the last column is **read off
the two documents' sources at generation time**, not asserted --- so it says
*which* document inputs each table, and a table inputted by neither is
reported as an orphan rather than quietly passing.

| file | reader-facing name | disposition | `\input` now? |
|---|---|---|---|
| `main_role_collapse.tex` | Functional collapse per actor | **MAIN** | **main paper** |
| `main_recovery.tex` | First pass and recovery, marginal and paired | **SUPPLEMENT** | **supplement** |
| `scibench_replication.tex` | Cross-domain replication, both actors | **SUPPLEMENT** | **supplement** |
| `structural_enforcement.tex` | Enforcement: check, attrition, both scorings | **SUPPLEMENT** | **supplement** |
| `single_agent_comparison.tex` | Budget-matched single agent, both directions | **SUPPLEMENT** | **supplement** |
| `prereg_endpoints.tex` | Pre-registered endpoints incl. P4 and Holm | **SUPPLEMENT** | **supplement** |
| `context_quartiles.tex` | Recovery by context quartile (directional only) | **SUPPLEMENT** | **supplement** |

**Why only one is in the main paper.** The page limit is hard and the
narrative carries its numbers in prose and two figures. The supplement
tables are the complete numeric backing a reviewer may want; the main paper
must stay readable **without** them, pointing at them and never depending on
them.

**The supplement is assembled** at `paper/supplement.tex` --- a second document in this same project, sharing this directory, so a regenerated table lands in both at once and the two cannot disagree. It `\input`s all 6 supplement tables; no table is an orphan.

## Where the numbers come from

No result literal is typed into the generator. Every figure is parsed out of
one of:

| canonical input | covers |
|---|---|
| `analysis/out/FINAL_TABLES_OUTPUT.txt` | all Omni-MATH figures |
| `analysis/scripts/xdom_analyze.py` (executed) | SciBench cross-domain |
| `analysis/scripts/stat_audit_a7_power.py` (executed) | MDE column only |

`FINAL_TABLES_OUTPUT.txt` is regenerated with
`python3 analysis/scripts/FINAL_TABLES.py` against
`experiments/results/FROZEN/` (frozen at 2026-09-30T10:09:30.201557,
11600 trajectories).

`xdom_analyze.py` does **not** reimplement the definitions. It execs
`FINAL_TABLES.py` and rebinds `judged`, `is_fpw`, `fp`, `fin_prereg`,
`ansseq`, `func_collapse` to the SciBench rows, so the recovery denominator
is the *same code object* as Omni-MATH's. Reimplementing that denominator
from memory is the bug that cost this project a FATAL finding.

## Denominators --- read this before quoting any figure

Three different populations appear across these tables. They are **not**
interchangeable, and conflating them has already produced one error here.

| population | definition |
|---|---|
| **cell** | every trajectory in an actor $\times$ condition cell |
| **marginal first-pass-wrong** | trajectories in that cell whose **first** evaluator verdict was incorrect. Computed **per condition**, so the two conditions have *different* denominators |
| **paired first-pass-wrong** | problems first-pass wrong under **both** conditions. One shared denominator. **This is the test.** |

The recovery denominator is `judged(r) and fp(r)==0`: a recorded incorrect
first verdict, **including** trajectories that later died in regeneration.
Those score $0$ under the pre-registered rule. It is **not** `graded(r)` ---
that was the FATAL-1 survivorship bug, and it silently dropped 150
structurally-enforced trajectories that all meet the definition.

First-pass accuracy uses the same `judged(r)` denominator, for the same
reason.

## The tables

### `main_role_collapse.tex` --- manuscript Table 1
- **Question.** Does deleting the role instructions destroy the division of
  labor, and does the answer depend on the instrument?
- **Input.** `FINAL_TABLES_OUTPUT.txt` sections T1, T18, T20, T23.
- **Denominator.** Cell population; first pipeline pass only (the first three
  role messages). Adjudication is a 171-trajectory judged subsample.
- **Status.** Exploratory. The role-structured/role-free contrast was
  pre-registered as secondary.
- **Appears.** Results, R1, one column.
- **Carry these caveats.** Byte duplication is a **lower bound**
  (precision $1.000$, recall $0.262$) and never carries the claim alone. The
  adjudication is outcome-blind but **not** condition-blind --- never call it
  blinded. The role-structured level is marker-dependent
  ($0.000$--$0.892$); read it as "low", not a point estimate. The sensitivity
  note is re-derived from T20 at generation time, not transcribed.

### `main_recovery.tex` --- manuscript Table 2
- **Question.** Does the cost of deleting roles fall on producing the first
  answer, or on repairing a wrong one?
- **Input.** `FINAL_TABLES_OUTPUT.txt` sections T1, T3, T4.
- **Denominator.** **Both panels are printed, labelled, and must not be read
  across.** Upper = marginal (per-condition $n_\mathrm{fpw}$, shown in
  parentheses for every figure). Lower = paired ($n_\mathrm{both}$).
- **Status.** Exploratory/post-hoc, stated as such.
- **Appears.** Results, R3, full width.
- **Carry these caveats.** Recovery conditions on a post-treatment variable:
  descriptive, never causal. Significance is exact McNemar, never a bootstrap
  bound --- one such label was seed-dependent. Only gemma-4 survives pairing;
  gpt-oss is directional, Llama-3.3 is a genuine null of the role
  manipulation.

### `scibench_replication.tex` --- manuscript Table 3
- **Question.** Does the dissociation hold outside mathematics?
- **Input.** `xdom_analyze.py`, against
  `experiments/results/xdomain/FROZEN_SCIBENCH/` (frozen
  2026-09-30T23:26:47.198588+00:00, 2296 trajectories).
- **Denominator.** First pass paired over all 574 problems; recovery paired on
  first-pass wrong under both conditions --- roughly a sixth the size, which
  is the whole reason gpt-oss cannot resolve.
- **Status.** Interpretation rules were fixed in advance
  (`notes/XDOMAIN-POWER-PREREG.md`), written before any recovery contrast
  existed. The replication itself is confirmatory of the Omni-MATH result.
- **Appears.** Results, R3b, full width.
- **Carry these caveats.** gpt-oss is **underpowered, not a
  non-replication**: its point estimate matches Omni-MATH's. Llama-3.3 was
  not run. SciBench's own grader is noisier than Omni-MATH's. No
  clause-specific fidelity metric crosses domains --- the contract was
  domain-adapted, and scoring across them would score agents on clauses they
  never received.

### `structural_enforcement.tex` --- manuscript Table 4
- **Question.** If the division of labor is enforced at the interface rather
  than requested, what comes back?
- **Input.** `FINAL_TABLES_OUTPUT.txt` sections T1, T2, T7, T11.
- **Denominator.** Manipulation check over planner messages; frozen answer and
  recovery over marginal first-pass-wrong; accuracy over the full cell
  (pre-registered) and over graded-only (as-graded). **Attrition sits beside
  the two accuracy columns because it is the reason they disagree.**
- **Status.** P1 and P3 pre-registered; the recovery column exploratory.
- **Appears.** Results, R5, full width.
- **Carry these caveats.** The authorship column is `1 -` T11's
  `authored-free`, which is a *freedom* rate --- the manuscript read that axis
  inverted once, and the complement is now taken once, in code. Enforcement
  restores recovery **for Llama-3.3 only**; for the other two the direction is
  consistent but not resolvable. "Highest of any arm, above role-structured in
  all three actors" is a **dead claim** and must not reappear. The as-graded
  column is survivorship and is sensitivity only.

### `single_agent_comparison.tex` --- manuscript Table 5
- **Question.** Was a collapsed team ever really multi-agent --- would one
  agent on the same budget have done as well?
- **Input.** `FINAL_TABLES_OUTPUT.txt` section T17.
- **Denominator.** Problems present in both our campaign and the external
  corpus, joined by `problem_uid`.
- **Status.** Exploratory; responds to a standing objection.
- **Appears.** Results, final subsection, one column.
- **Carry these caveats.** **Not from the frozen snapshot** --- it is a
  previously released trace corpus, and that must be said wherever the
  numbers appear. **Both directions, always together**; never quote gpt-oss
  alone. **The two actor arms were produced in separate runs**, so
  each direction is a sound guard and *the gap between actors is not*. The
  caption carries all three.

### `prereg_endpoints.tex` --- supplement
- **Question.** What was promised before the data existed, and what happened
  to each promise?
- **Input.** `FINAL_TABLES_OUTPUT.txt` sections T2, T14, T29, plus
  `stat_audit_a7_power.py` for the MDE column only.
- **Denominator.** P3/P4 over the full cell under pre-registered scoring.
  **The MDE column is a different population** --- see below.
- **Status.** **Pre-registered.** This is the table that reports the primary
  test.
- **Appears.** Supplement, full width.
- **Carry these caveats.** **P4, the pre-registered primary, is null before
  and after Holm**, and is reported as the failure of the thesis it was
  written to test. P1 failed as written and was re-designated --- reported,
  not hidden. P2 and P5 carry no $p$-value, so the Holm family is P3's three
  contrasts and P4's three DiDs. Only one of the three P4 nulls is
  informative; the two Llama-3.3 contrasts cannot detect an interaction of
  any plausible size.

#### MDE and the difference-in-differences are different populations
They are not arithmetically consistent and neither can be derived from the
other:

- the **difference-in-difference** differences two per-actor means, each
  computed on that actor's own problem set (1,600 and 400 problems);
- the **MDE** is computed on problems shared by *both* actors, where the
  Llama-3.3/gemma-4 observed difference is $+0.0300$ rather than the
  $+0.0400$ the effect column prints.

Both are right for their own question. The MDE is quoted only as a
detectability scale.

## Terminology

Internal arm codes (`A`, `B`, `C`, `Cp`) are stable identifiers in code, raw
data and provenance notes, and **never appear in a rendered table**. The
mapping lives in exactly one place --- `ARM_LABEL` in the generator --- and
the generator asserts the absence of bare arm codes in its own output before
writing. A violation is a hard failure, not a warning.

| internal | reader-facing |
|---|---|
| A | role-structured |
| B | role-free |
| C | structurally enforced |
| C' | context-restored |
