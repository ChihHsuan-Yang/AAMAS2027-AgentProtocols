# Scope note before running frontier-model adjudication (2026-09-29)

Two things Bella should know before the Opus-5 run, because they bound what it
can establish.

## 1. The prior pass was NOT human annotation either — relabelling is a correction, not just a rename

`FINDING-13-human-validation-collapse.md` was produced by a **sub-agent (an LLM)
reading trajectory text**, not by a person. Its own limitations section says
"single annotator; no second rater". Calling it "human validation" in my earlier
reports was **inaccurate, and that was my error** — I relayed the worker's
framing without correcting it.

So Bella's instruction does not replace human labour with model labour. It
replaces *unblinded, single-pass, self-reported* model adjudication with
*blinded, rubric-frozen, repeated* model adjudication — which is a genuine
methodological upgrade, and the honest description of the change.

Consequence: every place that says "human validation"/"human annotation" for
**collapse** is factually wrong today and must be fixed regardless of the new
run. P1a/E2v2 provenance is untouched (those were adjudicated by me, the master
agent, reading messages directly, with per-item recorded reasons).

## 2. The adjudication cannot restore the withdrawn headline — and Bella's §8 already anticipates this

Bella's note keeps the candidate headline as *"the model whose organization
collapses the most loses the least performance"*, conditional on the judge
confirming functional collapse.

But the reason that headline was withdrawn (CORRECTION-01) is **not** that the
flagged cases were spurious. Precision was 1.000 — everything the byte metric
catches is real collapse. It was withdrawn because the metric **misses**
gemma-4's collapse entirely (recall 0.343; gemma-4 Arm B judged 0.944
redundant while the flag fires 0.000).

A better judge can only *raise* the measured collapse rate for gemma-4, i.e.
push the two actors closer together. **No adjudication outcome makes gemma-4 the
low-collapse actor.** So:

- If the judge **confirms** functional redundancy in both arms → the corrected
  headline stands: *both actors lose the organization, only one loses accuracy.*
- If the judge finds the flagged cases are **only** surface-level → we narrow
  the word to "exact output duplication" and the headline weakens further.

Either way the pre-correction phrasing does not come back. I am running the
adjudication as instructed because it is the right validation and it decides the
**terminology** (§8's actual operative clause), not because it can reinstate the
withdrawn claim.

## What the adjudication WILL settle
1. Whether the automated metric corresponds to semantic/functional redundancy
   (the terminology question).
2. Whether Arm A is genuinely differentiated — the baseline the whole A-vs-B
   contrast rests on.
3. Judge stability, via repeated independent calls.
4. Per-actor recall, which is the number that killed the scope claim.
