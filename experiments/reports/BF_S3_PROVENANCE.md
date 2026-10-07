# §3 — the false provenance field: DECLARED / ACTUAL / IMPACT

Status: COMPLETE. Reported separately from the experimental result, per §3:
*"A declaration that disagrees with realized prompts is a provenance defect and
must be documented separately from the experimental result."*

No frozen file was modified. `campaign_v2.jsonl` was read only after verifying
sha256 `e4e53cb117d91129991ce2fe87e336e152fc9ee6ca826d363f2bd5dd240d7130`
against `FROZEN/MANIFEST.json`.

## DECLARED

Every frozen trajectory carries a `visibility_policy` field, written from
`VISIBILITY[self.arm]` at `experiments/runner.py:590`. Read back off the 9,600
shipped rows:

| arm | rows | declared planner visibility |
|---|---:|---|
| A | 3200 | `['problem', 'shared_history', 'advice']` |
| B | 3200 | `['problem', 'shared_history', 'advice']` |
| C | 3200 | `['problem', 'shared_history', 'advice']` |

**All three arms shipped the byte-identical string.** The field that exists
specifically to let the paper assert what each arm saw records no difference
between the arms at all — including for arm C, which is the manipulation.

## ACTUAL

From the templates in `experiments/prompts.py` (which slot each arm's prompt
builder actually interpolates):

| arm | template | `${advice}` | `${shared_history}` |
|---|---|---|---|
| A | `A_SOLVER/EXECUTOR/CRITIC_PREPEND` | **yes** | no |
| B | `B_GENERIC_PREPEND` | **no** | **yes** |
| C | `C_PLANNER/EXECUTOR/REVIEWER_PREPEND` | **yes** | **no** |
| Cp | `CP_*_PREPEND` | yes | yes |

So the single declared string is wrong for B and C in **opposite directions**:
it credits B with an `advice` channel its template cannot interpolate, and
credits C with a `shared_history` channel its template cannot interpolate.

Confirmed on realized bytes rather than on templates alone. Reconstructing
frozen Arm B prompts (gemma-4, first 400 trajectories) and hash-matching each
against the runner's own recorded `prompt_sha256_12`:

| quantity | value |
|---|---:|
| prompts reconstructed | 2,523 |
| hash-verified against the shipped sha | **2,523 (100.0%)** |
| containing `"Evaluator feedback: FAIL"` | **0** |
| mean realized prompt length | 10,108 chars |

A 100% hash match means the reconstruction *is* the prompt the model received.
Zero of those bytes carried the evaluator's verdict.

## IMPACT

**On the collaborator's hypothesis: CONFIRMED.** Arm B never received the
evaluator's FAIL verdict or repair hint, while Arm A received it through
`${advice}`. This is established here on the frozen data directly, not inferred
from current code — §2 forbids the latter and the two could have diverged.

**On the provenance record: the field is unusable as shipped.** It is identical
across arms, so it cannot support any per-arm visibility claim. §3's framing
applies: a declaration that disagrees with realized prompts is worse than an
absent one, because a reader who checks it is actively misled rather than
alerted to a gap.

**On the experimental result: none, by itself.** The field is metadata; it was
never read by the runner to decide what to put in a prompt. No frozen number
changes because of it. What changes is what the frozen numbers can be *said to
show* — which is the Bf control's whole subject and is not settled here.

**Scope limit, stated explicitly.** This section establishes only that the
delivery asymmetry was real. It does **not** establish that the asymmetry
*caused* the A-vs-B recovery gap. That is what the Bf cell tests, and no Bf
result is read in this file.

## A second-order finding

The source comments on `VISIBILITY` say the B entry was "CORRECTED 2026-10-03"
and the C entry "CORRECTED 2026-09-28". Both corrections are present in the
working tree and are accurate against the templates. But the **frozen rows were
written before them**, and 3,200 arm-C rows shipped with the wrong string even
though the C correction predates this investigation by a week.

The lesson is about the repair, not the original bug: correcting the constant
fixes every *future* run and leaves every *shipped* row wrong, with nothing in
the artifact marking it. Any reader of the released `campaign_v2.jsonl` sees
the false string with no indication a correction exists. Noted for §18 as a
manuscript-adjacent exposure; no manuscript text edited.

## What was NOT done

No frozen file modified. `VISIBILITY` not edited — the working-tree entries are
already correct and §21 forbids altering the frozen data. No branch merged. No
Bf result interpreted.
