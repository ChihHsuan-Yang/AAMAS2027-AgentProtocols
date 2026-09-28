# Finding 07 — Role realization: measured, stratified, and partly deflated

**Date:** 2026-09-28. Supersedes the F05 regex clue entirely.

## Two constructs, deliberately not merged

**Distinguishability** = can behaviour alone reveal which role wrote a message?
**Fidelity** = does each role perform the function it was assigned?

They dissociate sharply, and that dissociation is the finding.

## 1. Roles ARE highly distinguishable — this is counterevidence to the hypothesis

5-fold grouped by trajectory (never split a trajectory across folds):

| feature set | 3-way balanced accuracy |
|---|---|
| all features (incl. prompt-template markers) | 0.9416 |
| **function-only** (template markers removed) | **0.8964** |

Planner vs Executor, AUC: all features 0.9985, function-only 0.9954.
Chance = 0.333 / 0.500. **The strong form of "role labels do not induce
distinct behaviour" is FALSE.** It must be abandoned.

## 2. But distinguishability rides on FORMAT, not on the governed function

Single-feature AUC, Planner vs Executor:

| feature | AUC |
|---|---|
| numbered steps (format) | 0.110 (i.e. 0.890 inverted) |
| `\boxed` answer commitment | 0.707 |
| message length | 0.517 |
| **computation density** | **0.604** |
| arithmetic operator | 0.543 |

Permutation importance ranks `f_numbered_steps` (0.068), `f_boxed` (0.050),
`n_chars` (0.047) far above `eval_eq_density` (0.013). Restricting to
computation features alone drops AUC from 0.995 to **0.714** — barely above the
length-only nuisance control (0.768).

**So: the roles are separable by how they FORMAT output and whether they commit
an answer, not by the division of cognitive labour the contract governs.**
That is the defensible, non-trivial version of the hypothesis.

## 3. Fidelity is component-wise and uneven (omnimath2, the only full contract)

Planner, gpt_oss_120b: abstains-from-answer **0.540**, decomposes 0.960,
declares answer form 0.936, **abstains-from-computation 0.042**.

Two "MUST NOT" clauses in the same prompt block; one is honoured and one is not.
Only 4.2% of gpt_oss Planner messages contain no computed value; the median
Planner message carries **8** evaluated equations.

Executor plan-consumption is the weakest component anywhere: **0.164**
(gpt_oss) — the plan is injected into its prompt and it references it in one
message in six.

## 4. The actor effect is large, ordered, and on identical prompts

Within omnimath2 both actors get a byte-identical Planner prompt.

| actor | Planner: no computation | Executor: uses plan |
|---|---|---|
| gemma3_27b | 0.266 [.252,.281] | 0.833 [.821,.845] |
| gemma_4_31b | 0.111 [.104,.118] | 0.441 [.431,.450] |
| gpt_oss_120b | 0.042 [.038,.045] | 0.164 [.157,.170] |

All pairwise differences exclude zero (e.g. gemma3−gpt_oss = +0.225
[+0.210,+0.239]; exec plan-use gemma_4−gpt_oss = +0.277 [+0.265,+0.288]).
**Same organization, same prompt, very different realized division of labour.**

## 5. Organization × actor reversal reproduces, oracle-free

| domain | actor | PER | Broadcast | bcast − per |
|---|---|---|---|---|
| omnimath2 | gemma3_27b | 0.520 | 0.382 | **−0.1381 [−0.1669,−0.1080]** |
| omnimath2 | gpt_oss_120b | 0.728 | 0.786 | **+0.0577 [+0.0460,+0.0694]** |
| labbench | gpt_oss_120b | 0.436 | 0.455 | +0.0188 [−0.0065,+0.0435] |

Broad, not item-driven: gemma3 has 169/833 discordant items (142 PER-only-right
vs 27 broadcast-only-right); gpt_oss has 623/4176 (432 vs 191).

**Suggestive alignment:** the actor with the highest role fidelity (gemma3) is
the one for which PER *beats* broadcast; the lowest-fidelity actor (gpt_oss) is
the one for which PER *loses*. **N = 3 actors. This is not a regression and
cannot be one.** It is the reason to run the experiment, not a result.

## 6. Does fidelity predict success? Yes, but far less than it first appeared

**Leakage found and removed.** Trajectory-mean fidelity vs first-pass
correctness gave +0.61/+0.38 — an artifact. Message count correlates **−0.910**
with first-pass correctness (PER halts on `[Agree]` + PASS, so failures
accumulate low-fidelity retry rounds). Same stop-condition hazard the BigData
provenance file documents.

Restricting to `planner_0` — emitted before the Executor runs and before any
verdict exists, so strictly pre-outcome — and to the single clause:

| actor | compliant | violating | difference |
|---|---|---|---|
| gemma3_27b | 0.371 (n=426) | 0.244 (n=1128) | **+0.127 [+0.077,+0.179]** |
| gpt_oss_120b | 0.621 (n=309) | 0.494 (n=5767) | **+0.127 [+0.071,+0.180]** |

Two independent actors, identical point estimate.

**Then stratified by difficulty** (proxy: did the one-shot baseline solve the
same problem?):

| actor | hard problems | easy problems |
|---|---|---|
| gemma3_27b | +0.0245 [−0.0175,+0.0664] | +0.171 [+0.096,+0.244] |
| gpt_oss_120b | +0.0676 [−0.0026,+0.1426] | +0.0845 [+0.0565,+0.1084] |

**The effect is confined to problems the model could already solve.** On hard
problems it is null in both actors. Compliance is also itself difficulty-linked
(gemma3: 0.250 when baseline fails vs 0.341 when it succeeds), so residual
confounding remains even within strata.

Honest statement: *planner role-compliance is associated with success on
tractable problems, is not detectably associated on hard ones, and remains
observationally confounded.* Nothing here licenses a causal claim.

---

## CORRECTION (same day): the "sign reversal" is weaker than the pooled numbers

The audit's strongest surviving card was that we have a **sign reversal** where
the closest prior work (2609.14570) has only magnitude shrinkage. Tested properly:

gemma3_27b ran only 833 of omnimath2's 4,181 problems. Comparing it to gpt_oss
on *all* 4,176 compares different problem sets. On the **828 common problems**:

| actor | broadcast − PER (common set) | significant? |
|---|---|---|
| gemma3_27b | **−0.1365 [−0.1655, −0.1075]** | yes |
| gpt_oss_120b | **+0.0157 [−0.0121, +0.0423]** | **NO** |
| **interaction (paired, same problems)** | **+0.1522 [+0.1135, +0.1896]** | **yes** |

So:
- The **interaction is real and large**, paired on identical problems. That part
  is solid and is the defensible claim.
- The **"reversal" framing is not supported on the matched set.** gpt_oss's
  +0.058 advantage came from the 3,348 problems gemma3 never ran; restricted to
  the common set it is indistinguishable from zero. What we have is
  "PER strongly preferred by one actor, no preference by the other" — a
  crossover in point estimates but only one significant arm.

**Do not write "sign reversal."** Write "a significant organization × actor
interaction, in which one actor shows a large PER advantage and the other shows
none." That is what survives, and it is still stronger than a pure shrinkage,
but it is not the two-significant-opposite-signs object I claimed earlier.

This also raises the stakes on the third actor model: with only one significant
arm, a reviewer can reasonably ask whether gemma3 is simply an outlier.
