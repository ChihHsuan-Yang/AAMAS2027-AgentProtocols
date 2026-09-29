# CORRECTION 01 — the byte-level actor contrast is WITHDRAWN

**2026-09-29. Verified independently by the Master Agent from the raw
annotation files (not accepted on the worker's report).**

## What was claimed

That first-pass organizational collapse is **actor-specific**: gpt-oss 0.698,
gemma-4 **0.000**. This underpinned the framing "the actor whose organization
collapses most loses the least."

## What 180 blinded frontier-model adjudications show

| actor / arm | n | **human: NO division of labor** | byte flag fires |
|---|---|---|---|
| gemma-4 / A | 36 | **0.000** | 0.000 |
| gpt-oss / A | 36 | **0.056** | 0.000 |
| **gemma-4 / B** | 36 | **0.944** | **0.000** |
| **gpt-oss / B** | 72 | **0.958** | 0.500 |

**Both actors lose their division of labor at essentially the same rate when
role instructions are removed (0.944 vs 0.958).** The byte-identity metric
sees it in gpt-oss and is blind to it in gemma-4, because gemma-4's agents
paraphrase at length instead of emitting identical strings — thousands of
differing characters, nothing added.

## Ruling: the actor contrast on COLLAPSE is withdrawn

The claim "gemma-4 shows no first-pass collapse" is an artifact of a byte-level
definition. `COLLAPSE_MEASUREMENT_AUDIT.md` and `FINDING-10` are amended.

**What the metric may still be used for.** Precision is **1.000** (0 false
positives in 36 firings): everything it flags is genuine collapse. So it is a
**conservative lower bound on the rate** — usable to say "at least this much
collapse occurred", never to compare *scope* between actors. Recall is 0.343.

## What SURVIVES, and it is still a paper

The **accuracy** side is untouched — it never depended on the collapse metric:

- gemma-4 loses accuracy when roles are removed: **−0.029 [−0.045,−0.013]**
- gpt-oss does not: **+0.008 [−0.010,+0.026]**
- the mechanism holds: gemma-4's first-pass rate is unchanged (0.809→0.809)
  while its **recovery collapses 0.490 → 0.045**

So the honest headline inverts its emphasis:

> **Both actors lose their functional division of labor when role instructions
> are removed — and only one of them loses accuracy.** Visible organizational
> differentiation is therefore not what determines whether the loss is costly.

That is *stronger*, not weaker, than the byte-level story: it removes the
confound that the two actors differed in *how much* organization they lost, and
isolates the finding that identical organizational loss has opposite
consequences.

## Also corrected in the same pass
- **Arm A is NOT redundant** (0.000 / 0.056 judged no-division) — the soft-role
  baseline is genuinely differentiated, which strengthens the A-vs-B contrast.
- The byte metric **understates** collapse ~2x in Arm B (0.954 human vs 0.500
  flag for gpt-oss).

## Annotation caveats, carried into the paper
Single annotator (no inter-annotator agreement), partial blinding (role labels
retained — Q2 is unanswerable without them), snapshot of 7,670 of 9,600 rows,
omnimath2 only.
