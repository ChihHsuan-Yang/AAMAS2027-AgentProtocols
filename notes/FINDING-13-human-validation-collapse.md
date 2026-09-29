# Finding 13 — Human validation of the byte-identity collapse measure

**Worker:** human-validation. **Date:** 2026-09-29.
**Rubric frozen and committed BEFORE annotation:** `notes/COLLAPSE_ANNOTATION_RUBRIC.md`
(commit 94d9c5c, one amendment A1 recorded before the first annotation row).
**Data:** `experiments/results/human_validation/SNAPSHOT_campaign_v2_frozen.jsonl`
(7,670 rows, frozen while the campaign was still writing at 7,637/9,600).
**Sample:** n=180, blinded, stratified, seed 20260929. **UNCLEAR: 0.**

## Answer in one line

The exact-collapse flag is **sound but severely incomplete**. Everything it
flags is genuinely redundant (precision 1.000, 0/36 false positives), but it
**misses about two-thirds of the trajectories humans judge to have no division
of labour** (recall 0.343 pooled). Within the only cell where the flag varies
it is **barely better than chance: kappa = 0.083**.

## 1. Agreement: flag vs human Q5 ("meaningful division of labor")

Positive class = collapse / Q5 = NO.

| set | n | TP | FP | FN | TN | raw agr | precision | recall | kappa |
|---|---|---|---|---|---|---|---|---|---|
| **POOLED** (A+B, both actors) *confounded* | 180 | 36 | 0 | 69 | 75 | 0.617 | **1.000** | **0.343** | **0.303** [0.215,0.401] |
| **WITHIN (arm B x gpt-oss)** — the honest number | 72 | 36 | 0 | 33 | 3 | 0.542 | 1.000 | 0.522 | **0.083** [0.000,0.194] |
| Arm A only (flag never fires) | 72 | 0 | 0 | 2 | 70 | 0.972 | — | 0.000 | 0.000 |
| gemma-4 only (flag never fires) | 72 | 0 | 0 | 34 | 38 | 0.528 | — | 0.000 | 0.000 |

The pooled kappa of 0.303 is **mostly the arm A/B contrast**, not the flag's
discrimination: a permutation control (shuffling the flag) gives kappa in
[-0.101, 0.101], so 0.303 is real — but it is arm-membership leaking into the
statistic. The rubric pre-declared this confound and pre-committed to reporting
the within-cell number beside it. **Within the cell where the flag actually
varies, kappa is 0.083.**

## 2. THE MAJOR FINDING — Arm A is *not* judged redundant; Arm B is, everywhere

| arm | actor | n | Q5 = NO (no division of labour) | rate [95% CI] |
|---|---|---|---|---|
| **A** | gpt-oss | 36 | 2 | 0.056 [0.000, 0.139] |
| **A** | gemma-4 | 36 | 0 | **0.000** [0.000, 0.000] |
| **A** | both | 72 | 2 | **0.028** [0.000, 0.069] |
| B | gpt-oss (flag COLLAPSED) | 36 | 36 | 1.000 |
| B | gpt-oss (flag NOT collapsed) | 36 | 33 | 0.917 [0.806, 1.000] |
| B | gemma-4 (flag never fires) | 36 | 34 | 0.944 [0.861, 1.000] |
| **B** | both | 108 | 103 | **0.954** |

**This is the reverse of the feared result, and it is good news for the paper's
A-vs-B contrast.** Arm A's soft role prompts produce real division of labour in
70/72 sampled trajectories. The organization genuinely differentiates when role
instructions are present. The task brief asked that a high Arm A redundancy rate
be "reported loudly" — it is **not** high; it is 2.8%.

The two Arm A exceptions (both gpt-oss, both incorrect) are
`T083` (omni2_4034) and `T144` (omni2_2416): in each the Executor emitted a bare
answer with no derivation, so only one of the two later roles did its job.

## 3. THE PROBLEM — byte-identity understates collapse by roughly 2x

Arm B, restricted to rows the flag calls **NOT** collapsed:

- gpt-oss: 33/36 (0.917) judged **no** division of labour.
- gemma-4: 34/36 (0.944) judged **no** division of labour, and the flag fires
  **0 times in 36**.
- Across all 72 arm-B non-collapsed rows, **36/72 (0.500) have EVERY later role
  mainly restating** (frozen rollup Q3_all).

So in Arm B / gemma-4 the automated measure reports 0.000 collapse while humans
see 0.944 functional redundancy. The two instruments are measuring different
things in that cell, and the project's existing conclusion that "gemma-4 shows
*no* first-pass collapse at all" (COLLAPSE_MEASUREMENT_AUDIT.md, Audit Round 2)
is **an artifact of the byte-level definition, not a property of the organization.**

### What the 69 misses look like (all enumerated in analyze.py output)

They are overwhelmingly one mechanism: **one agent solves the whole problem and
the other two paraphrase it.** The texts differ — often by thousands of
characters — so no hash matches, yet nothing is added. Examples:

- `T023`, `T031`, `T057`, `T098`, `T118`, `T159`, `T175`: planner does the
  complete solve; executor and reviewer re-walk the identical steps.
- `T013`, `T048`, `T055`, `T063`, `T106`, `T117`, `T128`: three full prose
  passes over the same derivation, each labelled "verification".
- `T021`, `T076`, `T133`, `T179`: all three agents attempt the *same* job and
  fail the same way; in `T076` they reach three different answers (30, 45, 60)
  with no one adjudicating.
- `T084`, `T102`, `T130`, `T140`, `T147`, `T148`: the answer silently changes
  between roles with no stated reason — an absence of the review function that
  byte-identity cannot see.
- `T136`, `T162`, `T079`: two agents produce nothing usable and one does all
  the work. `T162`: planner and executor both degenerate into infinite
  repetition of one sentence; only the reviewer answers.

**Direction of error is one-sided and benign for soundness:** there were
**zero** cases (0/36) where the flag fired and a human saw real division of
labour. Byte-identity never cries wolf. It just sleeps through most of the pack.

## 4. Q1-Q4 rates per arm per actor (frozen rollups)

| arm | actor | n | Q1 any (new reasoning) | Q2 any (distinct role fn) | Q3 all (every later role restates) | Q3 any | Q4 any (altered solution) |
|---|---|---|---|---|---|---|---|
| A | gpt-oss | 36 | 0.306 | **1.000** | 0.000 | 0.028 | **1.000** |
| A | gemma-4 | 36 | 0.500 | **1.000** | 0.000 | 0.000 | **1.000** |
| B | gpt-oss | 72 | 0.250 | 0.264 | **0.694** | 0.944 | 0.278 |
| B | gemma-4 | 36 | 0.389 | 0.417 | 0.528 | 0.833 | 0.056 |

Per role (E = executor rel. planner; R = reviewer rel. planner+executor):

| arm | actor | Q1E | Q2E | Q3E | Q4E | Q1R | Q2R | Q3R | Q4R |
|---|---|---|---|---|---|---|---|---|---|
| A | gpt-oss | 0.17 | 0.94 | 0.00 | 1.00 | 0.22 | 0.97 | 0.03 | 0.39 |
| A | gemma-4 | 0.47 | 1.00 | 0.00 | 1.00 | 0.17 | 1.00 | 0.00 | 0.31 |
| B | gpt-oss | 0.18 | 0.19 | 0.76 | 0.25 | 0.10 | 0.10 | 0.88 | 0.10 |
| B | gemma-4 | 0.33 | 0.31 | 0.64 | 0.06 | 0.19 | 0.25 | 0.72 | 0.03 |

The cleanest separator is **Q2 (did it perform a distinct role function)**:
1.000 in Arm A vs 0.264/0.417 in Arm B. Q1 (new reasoning) does *not* separate
the arms — in Arm A the reviewer usually checks rather than derives, which the
rubric pre-declared as Q2-yes / Q1-no. That pre-declared borderline is
load-bearing and is the single most consequential judgement call in this report.

## 5. Q5 by correctness

| arm | correct=0 | correct=1 |
|---|---|---|
| A | 2/36 = 0.056 | 0/36 = 0.000 |
| B | 50/54 = 0.926 | 53/54 = 0.981 |

Redundancy is **not** an artifact of failure: in Arm B the *correct*
trajectories are judged redundant slightly more often than the incorrect ones.

## 6. Instrument checks

- **Not degenerate:** Q5 splits 105 NO / 75 YES.
- **Normalization direction confirmed as pre-declared:** my frozen N() calls 8
  extra trajectories duplicate that the raw hash does not, and **0** in the
  other direction — so my EXACT category is strictly broader than the automated
  flag, exactly as Part 1 of the rubric predicted in advance.
- **Permutation control:** shuffled flag gives kappa in [-0.101, 0.101].

## 7. VERDICT FOR THE PAPER

1. **"Collapse" is defensible for the cases where the flag fires.** Precision
   1.000, 36/36. Byte-identical outputs are genuine organizational collapse, not
   a serialization artifact. The headline word survives *for that subset*.

2. **The flag must NOT be used to state the SCOPE of collapse.** It has recall
   0.343 and kappa 0.083 in the only cell where it varies. Any sentence of the
   form "collapse occurs in X% of Arm B" understates the functional phenomenon
   by roughly 2x, and in gemma-4 understates it from 0.944 to 0.000.

3. **The claim "gemma-4 shows no first-pass collapse" must be withdrawn or
   requalified.** It is true of byte-identity and false of division of labour
   (0/36 vs 34/36). The actor contrast that the paper's central interaction rests
   on is, at minimum, much weaker at the functional level than at the byte level.
   Whether it survives at all is now an open question, not a settled one.

4. **Report Arm A's 2.8% loudly and positively.** Role instructions do produce
   real differentiated organization. That strengthens the A-vs-B contrast rather
   than undermining it.

Suggested wording: describe the measure as **"exact output duplication, a
conservative lower bound on organizational collapse"**, cite precision 1.000 and
recall 0.343 from this validation, and state the functional rate (Arm B 0.954,
Arm A 0.028) as the quantity the mechanism claim rests on.

## Limitations

- Single annotator; no second rater, so no inter-annotator reliability.
- Role labels retained (Q2 is unanswerable without them), so blinding is partial
  and the arm is sometimes inferable from content. Pre-declared in the rubric.
- Snapshot is 7,670 of a planned 9,600 rows; arm C/C' excluded by design.
- One domain only (omnimath2) — the campaign contains no other benchmark.
