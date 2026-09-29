# Collapse annotation rubric — FROZEN BEFORE ANNOTATION

**Written 2026-09-29 by the human-validation worker, BEFORE any annotation was
recorded and BEFORE any aggregate agreement number was computed.**

Purpose: decide whether byte-identical agent outputs in `campaign_v2` represent
genuine **organizational collapse** (the paper's headline word) or a
**serialization / formatting artifact**. The automated flag must be validated
against a human reading of the actual message text.

## Why this file exists and why it is frozen

A prior metric on this project ("v3") was rejected because its definitions were
adjusted after the agreement numbers were seen, and agreement got *worse*. The
protection against repeating that is to fix every decision rule here, in git,
before the first annotation row is written. **Any change to this file after
annotation starts must be recorded as a dated amendment below the freeze
banner, and the pre-amendment numbers must be reported alongside.**

## Data and unit of analysis

- Source: `experiments/results/main/campaign_v2.jsonl`, frozen to
  `experiments/results/human_validation/SNAPSHOT_campaign_v2_frozen.jsonl`
  (7,670 rows at snapshot time; the live campaign was still writing at
  7,637/9,600, so the snapshot is the citable subject).
- **Unit = one trajectory, represented by its FIRST THREE role messages**
  (roles in {planner, executor, reviewer}), i.e. one pipeline pass.
  This matches the project's *primary* count-matched collapse rule
  (`COLLAPSE_MEASUREMENT_AUDIT.md`, Audit Round 2) and avoids the
  trajectory-length confound. Trajectories with fewer than three role messages
  are ineligible for sampling.
- Message text annotated = the `text` field = the raw model completion, the
  same string the automated hash is taken over.

## Automated flag under test

`EXACT_COLLAPSE_FIRST3 = ( len(set(response_sha256_12 for first 3 role msgs)) < 3 )`

This is the flag whose validity is at issue. It is a property of bytes only.

---

# PART 1 — The four redundancy categories

Each category is a property of a **later role relative to what precedes it**
(executor relative to planner; reviewer relative to planner and executor).
Categories are ordered by strength: EXACT ⊂ SEMANTIC ⊂ FUNCTIONAL. A pair can
satisfy FUNCTIONAL redundancy without satisfying SEMANTIC, and SEMANTIC without
satisfying EXACT. GENUINE DIFFERENTIATED ORGANIZATION is the complement of
FUNCTIONAL redundancy at the trajectory level.

## 1. EXACT redundancy

**Definition.** Two role messages are EXACT-redundant if they are byte-identical
after the normalization below — nothing else.

**Frozen normalization N():**
1. Strip a leading/trailing markdown code fence (` ```json `, ` ``` `, ` ```latex `)
   and the fence's language tag.
2. Unicode NFKC normalize.
3. Collapse every run of whitespace (space, tab, newline, non-breaking space,
   thin space) to a single space; strip leading/trailing whitespace.
4. Lowercase.
5. Remove the trailing agreement/route tokens `[agree]`, `[disagree]`,
   `[revise]` and a trailing `.` or `,` left behind.
NOTHING ELSE is normalized. LaTeX is **not** canonicalized: `\dfrac` vs `\frac`
is a real textual difference and is left as one, because the whole question at
issue is whether surface identity is being manufactured. (The project's
"normalized collapse = 0.927" figure strips LaTeX; this rubric deliberately does
not, so that the human EXACT category stays *stricter* than the automated one
and cannot be accused of inflating agreement.)

**INCLUSION.** N(msg_i) == N(msg_j) for two of the three role messages.

**EXCLUSION.** Any difference in mathematical content, any additional or
removed sentence, any different numeric value, any different final answer —
even one character of substantive difference — is NOT exact.

**Worked example (from the rubric development set, line 1, omni2_1004, Arm B):**
planner emits `\boxed{\dfrac{1}{27}}\n\n[Agree]` and executor emits the
identical 30 characters. → **EXACT redundant.** Note the reviewer's
`\boxed{\dfrac{1}{27}}\n[Agree]` (29 chars, one fewer newline) is EXACT under
N() too (whitespace collapsed + `[agree]` stripped), although its raw
`response_sha256_12` differs. **This is a pre-declared expected direction of
disagreement: my EXACT category is slightly broader than the raw-hash flag
because the raw flag is whitespace-sensitive.**

## 2. SEMANTIC redundancy

**Definition.** A later role's message conveys essentially the same reasoning
content as an earlier one — same approach, same derivation chain, same
conclusion — while the surface form differs.

**INCLUSION (any one suffices):**
- The later message restates the earlier derivation in paraphrase, with no step
  that was not already present.
- The later message reformats the earlier content into a different container
  (prose → JSON, LaTeX → plain, bulleted → numbered) without adding a step.
- The later message is a strict *excerpt* of the earlier one (e.g. planner
  gives the full solve; executor emits only its final line).
- The later message reorders or re-labels the same steps.

**EXCLUSION:**
- A later message that adds a justification the earlier one asserted without
  support (e.g. planner says "apply AM-GM"; executor proves the equality case)
  is NOT semantic redundancy — a missing step was supplied.
- A later message that changes a value, corrects an error, or reaches a
  different answer is NOT semantic redundancy.
- A message that is merely *short* is not automatically semantically redundant;
  a one-line correct verdict on someone else's work is a different speech act,
  not a restatement (see FUNCTIONAL, below, for how that is handled).

**Worked example (dev set, line 10, omni2_1003, Arm B):** planner emits the
complete product telescoping, the floor computation, and `\boxed{674}`; the
executor emits only `\[\n\boxed{674}\n\]\n\n[Agree]`. The executor's content is
a strict excerpt of the planner's — **SEMANTIC redundant, not EXACT** (the
bytes differ; the raw-hash flag calls this trajectory NOT collapsed).

## 3. FUNCTIONAL redundancy

**Definition.** A later role adds **no substantive role-specific contribution**
to the joint work product. This is about *contribution*, not about *overlap*: a
message can restate a lot and still contribute (a reviewer who restates then
finds an error contributes), and a message can be textually novel and
contribute nothing (a reviewer who writes fresh prose that only says "looks
correct" adds no role-specific work beyond what a boolean would).

**The contribution test, applied per later role.** Ask: *if this message were
deleted and its predecessor's output passed straight through, would the joint
output or its justification be materially worse?* If NO → functionally
redundant.

**INCLUSION — the later role is FUNCTIONALLY REDUNDANT if:**
- (a) It is EXACT or SEMANTIC redundant (these imply functional redundancy).
- (b) It performs a role function that is not its own and duplicates one already
  performed — e.g. an executor that re-plans instead of executing, when the
  planner already planned.
- (c) It is a bare assent with no localized content: a verdict with an empty or
  contentless critique, a `[Agree]`, or a restated answer with no check
  described. **Decided in advance:** a reviewer whose entire substantive content
  is `accept` / `[Agree]` / an empty critique field is FUNCTIONALLY REDUNDANT,
  because the organization obtains no information from it that the executor's
  own output did not already carry.
- (d) It contributes only formatting/extraction (pulling the answer out of the
  previous message into a box or a JSON field).

**EXCLUSION — the later role is NOT functionally redundant if:**
- It performs a *check that is described*: names what was verified, checks a
  specific step, tests a boundary case, substitutes the answer back. A reviewer
  that says "the derivation correctly simplifies to x+y+z=1 and AM-GM gives the
  bound; answer form matches" has localized the reasoning to specific claims and
  IS contributing verification, even though it introduces no new mathematics.
  **Pre-declared borderline ruling:** described-verification counts as
  contribution (Q2 yes) but NOT as new reasoning (Q1 no). This is the single
  most consequential borderline in the rubric and is fixed here in advance.
- It changes, corrects, rejects, or routes back the candidate solution.
- It supplies a derivation step, a proof of a claimed inequality, a case
  analysis, or a numeric evaluation the predecessor left open.
- It performs its own distinct role function on material the predecessor did not
  cover (e.g. planner decomposes; executor computes — even if the planner
  gestured at the method).

**Worked example (dev set, line 4, omni2_1004, Arm A):** planner gives a
structured plan with givens / target form / lemmas / ordered steps and
*deliberately no answer*; executor carries out the algebra, proves the AM-GM
equality case, and produces `\boxed{1/27}`; reviewer names the two things it
checked (constraint simplification, answer form) and promotes the answer. The
executor supplied steps the plan only named → NOT functionally redundant. The
reviewer described what it verified → NOT functionally redundant under the
pre-declared borderline ruling. → **GENUINE differentiated organization.**

**Counter-worked example (dev set, line 1, Arm B):** every role emits the same
boxed answer. Deleting the executor and the reviewer changes nothing about the
output or its justification. → **FUNCTIONALLY REDUNDANT at both later roles.**

## 4. GENUINE differentiated organization

**Definition (trajectory level).** The trajectory exhibits genuine
differentiated organization if **at least two of the three roles make
materially different contributions** — i.e. at least one later role is NOT
functionally redundant AND the contributions are of different kinds
(decomposition vs execution vs verification), not the same kind performed twice.

**INCLUSION:** planner scopes/structures without solving AND executor solves; or
executor solves AND reviewer performs a described check or a correction; or a
reviewer rejects and the trajectory changes course.

**EXCLUSION:**
- Three agents each producing a full independent solve of the same problem is
  **NOT** differentiated organization — it is replication, not division of
  labor. **Decided in advance:** parallel duplicate solving counts as NO
  division of labor even when the three texts differ substantially, because the
  organizational claim is about *division*, not about *diversity*.
- One agent doing everything while the others assent is NOT differentiated
  organization regardless of how different their texts look.

---

# PART 2 — The five per-trajectory questions

Q1-Q4 are recorded **separately for each later role** (subscript E = executor
relative to planner; subscript R = reviewer relative to planner+executor).
Q5 is recorded once for the trajectory. All are YES / NO / UNCLEAR.

**Q1 — Did the later agent add new reasoning?**
YES if it introduces at least one inferential step, justification, computation,
or case not present in the earlier messages. Described verification of an
existing step is **NO** (frozen above). Restating with different words is NO.
Producing the same answer by a visibly different method is YES.

**Q2 — Did it perform a distinct role function?**
YES if its speech act is the one its role is for and is not a duplicate of an
act already performed: planner→decompose/scope; executor→derive/compute/answer;
reviewer→evaluate/localize/route/correct. A described check is YES. A bare
`accept` / `[Agree]` with no content is NO. An executor that only restates the
planner's answer is NO. An executor that solves is YES even if the planner
sketched the method.

**Q3 — Did it mainly restate or copy?**
YES if, after removing everything already present in earlier messages, little or
no substantive content remains. EXACT and SEMANTIC redundancy both imply YES.
A message that restates *and then* adds a step is NO ("mainly" is the operative
word: judged by whether the novel part carries the message's purpose).

**Q4 — Did it alter the candidate solution?**
YES if the final answer, a numeric value, a derivation step, or the chosen
approach differs after this message from what it would have been before — this
includes rejections and routes that force a revision. Promoting an answer
unchanged is NO. Reformatting the same answer is NO. Extracting the same answer
into a box is NO.

**Q5 — Does this trajectory exhibit a meaningful division of labor?**
The trajectory-level judgement, applied using the GENUINE-differentiated-
organization definition above. YES / NO / UNCLEAR.
**This is the question the automated collapse flag is validated against:**
the paper's claim requires that `EXACT_COLLAPSE_FIRST3 = True` predicts
`Q5 = NO`.

**UNCLEAR is used** when a message is empty, is a transport/parse failure, is
truncated mid-derivation such that its contribution cannot be judged, or the
trajectory has fewer than three role messages. UNCLEAR rows are excluded from
agreement statistics and **reported separately with their count**.

## Frozen rollup rules (so aggregation cannot be chosen later)

- `Q1_any = YES` iff Q1_E or Q1_R is YES. Same form for Q2, Q4.
- `Q3_all = YES` iff Q3_E and Q3_R are both YES (i.e. every later role mainly
  restated). `Q3_any` also reported.
- Q5 is annotated directly, NOT derived from Q1-Q4. It is a separate judgement
  and may disagree with the rollups; any such disagreement is reported, not
  reconciled.

---

# PART 3 — Sampling plan (frozen before drawing)

Target **~180 trajectories**, stratified over:
- arm ∈ {A, B} (the key contrast; C and C' excluded from this validation),
- actor ∈ {gpt-oss-120b, gemma-4-31B-it},
- `EXACT_COLLAPSE_FIRST3` ∈ {True, False},
- `correct` ∈ {0, 1}.

That is 2×2×2×2 = 16 cells, target ~12 per cell, drawn with a fixed seed
(`seed = 20260929`) from eligible rows (≥3 role messages; `correct` not null).

**PRE-DECLARED STRUCTURAL LIMITATION — recorded before annotating.** In the
snapshot, `EXACT_COLLAPSE_FIRST3` is ~0.693 in Arm B / gpt-oss and ~0.000 in
Arm A (both actors) and in Arm B / gemma-4. The collapsed stratum therefore
**cannot** be balanced across arms and actors: it exists almost only in one
cell. Consequences fixed in advance:
1. Cells that are empty are reported as empty; they are not back-filled from
   another cell.
2. Because collapse is near-perfectly confounded with (arm B × gpt-oss), the
   precision/recall/kappa of the automated flag over the *sample* is partly a
   measure of that confound. I will therefore **also** report agreement
   restricted to Arm B / gpt-oss alone, where the flag actually varies. The
   within-cell number is the honest one; the pooled number is reported beside it
   and explicitly labelled as confounded.
3. Arm A collapsed cells are expected to be empty. Arm A's Q5=NO rate is
   therefore measured on non-collapsed Arm A rows, which is exactly the
   quantity the task asks for ("in Arm A, how often do humans judge there is NO
   meaningful division of labor?").

## Blinding

Each sampled trajectory is written to a readable file under an **opaque id**
(`T###`, ordered by a seeded shuffle). The file shows only the problem
statement reference, the three role labels, and the three message texts.
Arm, actor, collapse flag, correctness, hashes, and problem_uid are withheld and
written to a separate key file that is not opened until annotation is complete
and committed.

Role labels (planner/executor/reviewer) are **retained** — they are part of the
organizational structure being judged and Q2 is unanswerable without them. Their
retention is a known partial-blinding limitation: in Arm B the roles are
nominal, and an annotator can sometimes infer the arm from the content. This is
stated rather than mitigated, because removing role labels would make the
primary question unanswerable.

## Pre-declared analysis

1. Agreement between `EXACT_COLLAPSE_FIRST3` and `Q5 = NO`: raw agreement,
   2x2 confusion matrix, precision, recall, Cohen's kappa. Pooled AND
   within-(B, gpt-oss).
2. Enumerate and read every confusion case in both directions.
3. Q1-Q4 rates per arm per actor.
4. Arm A `Q5 = NO` rate, reported prominently whatever it is.

## Pre-declared decision rule for the headline word

- If the flag's kappa vs Q5 is high AND the confusion cases are few and benign,
  "organizational collapse" is supported for the cells where the flag fires.
- **If humans judge NO meaningful division of labor at a high rate in Arm A too
  (where the flag never fires), then byte-identity is measuring a narrow
  surface phenomenon inside a much broader functional one, and the paper may
  not use byte-identity as evidence for the scope of "collapse".** This would be
  reported loudly and would change the headline word.
- If the flag does not track Q5, the flag is a serialization measure and must be
  described as such.

## Rubric development set — EXCLUDED from the sample

Three trajectories were read while writing this rubric, to ground the worked
examples. They are excluded from the annotation sample:
snapshot lines 1, 4, 10 (omni2_1004 Arm B, omni2_1004 Arm A, omni2_1003 Arm B,
all gpt-oss-120b). No aggregate statistic was computed before this file was
written; only these three trajectories were read.

---
**FREEZE BANNER — nothing above this line may be edited after the first
annotation row is recorded. Amendments go below, dated.**

---

## AMENDMENT A1 (2026-09-29, before any annotation row was recorded)

**What changed:** `TARGET_PER_CELL` 12 → 18.

**Why:** the frozen plan specified a target of ~180 trajectories over 2x2x2x2 =
16 cells, i.e. ~12 per cell. On drawing, only **10** of the 16 cells are
non-empty — exactly the structural limitation pre-declared in Part 3 (collapsed
rows exist only in Arm B / gpt-oss). At 12 per cell the sample would be n=120,
below the frozen target. Raising to 18 per cell gives n=180, which honors the
frozen target n. Seed, strata, eligibility and blinding are unchanged.

**Status:** recorded BEFORE the first annotation row. No annotation or
aggregate agreement number had been computed at the time of this amendment.

---

# RESULTS (recorded after annotation was complete; rubric above unchanged)

Full results: `notes/FINDING-13-human-validation-collapse.md`.
Artifacts: `experiments/results/human_validation/` (frozen snapshot, sample key,
blinded file, ANNOTATIONS.jsonl, build_sample.py, analyze.py).

Headline: the exact-collapse flag has **precision 1.000** (0 of 36 fired cases
were judged to have real division of labour) but **recall 0.343** pooled /
0.522 within (arm B x gpt-oss), kappa 0.303 pooled / **0.083** within-cell.
**Arm A: 2/72 judged NO division of labour. Arm B: 103/108 (0.954).**
Byte-identity is a sound but severely incomplete indicator of a much broader
functional phenomenon.
