# Finding 06 — Which organization wins depends on the model, and the sign flips

**Status:** paired, oracle-free, n=6,551. Robust in the large cells.

## The comparison

PER and Broadcast both use **3 agents**. They differ in *organization*:
hierarchy + role specialization + routing (PER) vs peers + shared transcript +
confidence-gated speech (Broadcast). Comparing them at **first submission**
removes the oracle-budget confound, so this is a reasonably clean contrast of
two organizational forms at fixed agent count.

Pooled: **broadcast − PER = +0.0237 [+0.0133, +0.0339]**. Peers beat hierarchy.

Except they don't, everywhere:

| benchmark | actor | PER | Broadcast | difference |
|---|---|---|---|---|
| omnimath2 | gpt_oss_120b | 0.728 | 0.786 | **+0.058 [+0.047,+0.069]** |
| labbench | gpt_oss_120b | 0.436 | 0.455 | +0.019 [−0.007,+0.044] |
| omnimath2 | **gemma3_27b** | **0.520** | 0.382 | **−0.138 [−0.168,−0.109]** |

Same problems, same organization, opposite sign. On gemma3_27b, hierarchy beats
peer deliberation by 13.8 points; on gpt_oss_120b (same benchmark) peers win by
5.8. Both intervals are far from zero.

## Reading it

The natural explanation ties to Finding 01: broadcast's peer organization routes
the group's output through a **confidence-argmax gate**, and that gate is worth
nothing. A weaker model presumably produces noisier self-reports and more
divergent candidates, so it pays a larger price for having its contribution
selected by an uninformative rule. PER has no such gate — the Reviewer routes on
*content*, not on self-reported confidence.

That is a hypothesis, not a demonstration: gemma3_27b appears in only one
benchmark (833 omnimath2 problems) and is the smallest model in the panel, so
model capability, model family, and serving site are all confounded with it.

## Why it matters

"Which multi-agent topology is better" has no model-independent answer here. Any
paper (or practitioner guideline) that ranks organizational forms from a single
actor model is reporting an interaction as if it were a main effect. This is a
concrete, quantified instance of a generalization failure that the MAS literature
routinely risks — and it costs nothing extra to measure, because the matched
design already supports it.

## Caveat that must travel with this number

gemma3_27b is a single 833-problem cell in a single domain. The *existence* of a
sign flip is solid; its attribution to model capability is not. A third actor
model would settle it, and one is already available in the corpus
(gemma_4_31b) — but **gemma_4_31b has no first_pass_correct coverage**
(first-pass is recorded only for labbench and omnimath2 at 50%/54.5%, and the
gemma_4_31b rows fall outside it). So closing this needs either a re-derivation
of first-pass from traces or a small new run. Logged, not claimed.
