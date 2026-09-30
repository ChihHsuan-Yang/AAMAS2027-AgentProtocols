# Finding 25 — The adjudication blinding is NOT arm-blind, and A1's headline
# contrast is not protected by it

**2026-09-30. Found by the artifact worker, verified independently here
against the file whose sha256 matches `items_sha256_after_neutralization`,
i.e. the bytes the judge actually saw.**

## 1. What the protocol claims

`adjudication/PROTOCOL.md` records that a blinding leak was found (45 items
carried literal role names, 42 in Arm A vs 3 in Arm B) and neutralized by
replacing them with `Agent-P` / `Agent-E` / `Agent-R`, with "residual
leaks: 0".

**That is true of the strings and false of the signal.** The tokens were
renamed; their *presence* was not equalized.

## 2. The measurement

Items whose transcript contains an `Agent-P/E/R` token at all:

| arm | has token | none |
|---|---|---|
| **A** | **42** | **0** |
| **B** | **3** | **53** |
| C | 0 | 44 |
| Cp | 0 | 29 |

Fisher exact, A vs B, on token presence: **p = 1.5e-24**.

Every Arm A item carries the marker. Almost no Arm B item does. A judge that
noticed only "does this transcript label its speakers at all" could separate
Arm A from Arm B essentially perfectly — without reading a word of content.

## 3. It is worse than one leak: the arms are structurally distinguishable

Even with role tokens fully removed, the arms differ in surface form because
the *manipulation itself* changes the output format:

| cue | A | B | C | Cp |
|---|---|---|---|---|
| JSON `"answer":` field | 0/42 | 0/56 | **39/44** | **27/29** |
| `\boxed` | 37/42 | **56/56** | 2/44 | 0/29 |
| `[Agree]` | 24/42 | **51/56** | 0/44 | 0/29 |
| `"verdict":` field | 0/42 | 0/56 | **40/44** | **26/29** |

Arm C is identifiable from the JSON schema alone. Arm A vs B is separable by
role-token presence. **No amount of string substitution fixes this**, because
the intervention is partly an intervention on output format.

## 4. What this does and does not invalidate

**NOT affected — these are within-arm or within-actor:**
- Judge stability (Q1-Q5 all-reps-agree 0.895-0.959). Measured on repeated
  calls over identical items.
- Precision 1.000 / recall 0.262 of the automated flag against adjudication.
  Both computed within the same items.
- Per-actor comparisons inside one arm.

**AFFECTED — every arm-contrastive adjudication number, including A1's
headline:**
- "Arm B judged no-division-of-labor 0.964 vs Arm A 0.000"
- "Arm C restored to 0.136"

These are exactly the comparisons a judge able to identify the arm could
produce without reading content. **We cannot claim these are blinded.**

## 5. What we may still say

The adjudication remains **outcome-blind** — the judge never saw accuracy,
recovery, or our hypothesis — and **stability-validated**. What it is not is
**condition-blind**.

Permitted framing:
> A frontier model, blind to outcomes and to our hypothesis but able in
> principle to infer the condition from transcript format, judged division of
> labor absent in 0.964 of role-free trajectories against 0.000 with roles.

**Not permitted:** "blinded adjudication confirms", where blinded is read as
condition-blinded. That is the current wording in A1 and in the manuscript.

## 6. Why a fix is not available before the deadline

A genuinely condition-blind protocol requires normalizing transcripts to a
common surface form across arms before judging — which would itself destroy
the differences being judged (the whole point of Arm C is that its schema
differs). The honest move is disclosure, not a re-run.

**A re-run would not fix it and must not be attempted as cover.**

## 7. Corroborating evidence the conclusion still holds

The arm-contrastive adjudication is not our only evidence for A1:
- The functional collapse measure (0.976 / 0.846 / 0.872 in Arm B vs
  0.000 / 0.120 / 0.000 in Arm A) is computed mechanically from message
  content, with no judge involved.
- The content-level duplication measure (excess over a null pairing, +0.29 to
  +0.30, replicated across two actors) likewise.

So A1 survives on mechanical measures. What weakens is the *validation* role
the adjudication was performing — it can no longer be cited as independent
blinded confirmation of the arm contrast, only as a stability-checked,
outcome-blind second opinion.

## 8. Action
- `APPROVED_CLAIMS.md` A1: strike "blinded" as applied to arm contrasts.
- `paper/`: rewrite every occurrence of "blinded adjudication" that carries an
  arm comparison. Add the leak, the 42/0 vs 3/53 table, and the structural
  cues to limitations. This is a disclosure, and it must be in the main text
  where the adjudication is first used, not only in limitations.
- `adjudication/PROTOCOL.md`: correct "residual leaks: 0".
