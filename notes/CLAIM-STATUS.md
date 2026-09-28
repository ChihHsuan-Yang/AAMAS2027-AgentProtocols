# Claim status board — what survives, what does not

Updated 2026-09-28 after d1-d11. Keep this current; it is the single place that
says which numbers are safe to put in a paper.

## ESTABLISHED — replicated on held-out actor model, ready to write

| # | Claim | Evidence | Strength |
|---|---|---|---|
| E1 | **Confidence-argmax speaker selection ≈ random.** | gpt_oss +0.0049 [−0.0130,+0.0234]; gemma −0.0012 [−0.0152,+0.0135] | very strong; tight, two actors, two sites |
| E2 | **Because self-confidence has no within-item component.** Between-problem AUC 0.5967; within-turn AUC ≈ 0.5 in all four independent slices (labbench×2 actors, jeebench, mascqa) | d6, d11 | very strong; this is the mechanism |
| E3 | **The unclaimed headroom is large and stable.** Disagreement turns: deployed 0.384/0.356 vs group-contains-answer 0.771/0.706; gap **+0.387 [.367,.407]** and **+0.350 [.325,.377]** | d11 | very strong, both actors |
| E4 | **Single-agent iteration has zero oracle-free effect** (+0.0023 [−0.0064,+0.0108]); its full +22 pts is the ground-truth retry loop. Multi-agent retains a real oracle-free effect (PER +14.6, broadcast +17.0) | d1, d8, n=6,551 paired | strong |
| E5 | **Within-protocol destructive revision is censored** (right→wrong ≡ 0.0000, stop-on-PASS) | d1 | structural, verifiable by inspection |
| E6 | **36% of confidence polls fail to parse**, fallback score = 1, silently silencing that agent | d2 | descriptive, exact |
| E7 | **PER's "hard role separation" is not obeyed.** Planner forbidden to compute, yet 58.7% of its messages carry numeric equations vs Executor 61.0% (diff −0.023 [−0.030,−0.018]). Separation holds only for answer commitment (boxed 0.150 vs 0.564). | d12, 145,411 messages | strong, descriptive |

## NOT ESTABLISHED — do not write these

| # | Claim | Why it failed |
|---|---|---|
| X1 | "Peer agreement is a usable within-turn signal" | pooled AUC 0.5296 [.5058,.5529] excluded 0.5, but the pre-registered per-actor split does not (gpt_oss .5258 [.4916,.5591]; gemma .5259 [.4931,.5568]). Under-powered, not demonstrated. |
| X2 | "Peer assessment beats self-assessment as a selection signal" | the original 0.631-vs-0.4975 comparison was between-problem vs within-turn. Like-for-like: 0.5297 vs 0.4975 — much smaller, and X1 applies. |
| X3 | "Selecting by agreement/plurality improves accuracy" | +0.0109 [−0.0057,+0.0277] pooled; both per-actor splits include 0. |
| X4 | "Collaboration sometimes destroys correct answers" (within protocol) | unmeasurable here — see E5. Requires the P1 blind-verifier arm. |
| X5 | "Deliberation degrades accuracy over turns" | survivorship artifact; disappears on a balanced within-trajectory panel. What remains: disagreement *grows* (+0.204 [+0.126,+0.286]). |
| X6 | "Planners that compute do better" (pooled 0.645 vs 0.500) | **Simpson's reversal** — sign flips in all 3 cells (labbench .429→.125; omnimath2/gemma .870→.431; omnimath2/oss .988→.718). Pooled direction is composition. Even stratified it is confounded by difficulty. |

## NOVELTY STATUS (added 2026-09-28, see NOVELTY-AUDIT.md)

Being *true and replicated* is not the same as being *novel*. Re-scored:

| claim | novelty | prior art |
|---|---|---|
| E1 confidence-argmax ≈ random | **ANTICIPATED** | MARGIN 2605.22949 §8.1 (Table 9, "at or below a coin flip"); 2607.28317 (threshold δ*) |
| E2 no within-item component | **ANTICIPATED** | 2605.24299 — rank-one confidence matrix, τ=0.037/0.025, same mechanism |
| E3 large unclaimed headroom | novel *as stated for a live protocol*, but weak alone | — |
| E4 oracle-feedback confound | **ANTICIPATED** | Kamoi et al. TACL 2024 — named-offender table. Inherit, do not claim. |
| E5 censored destructive revision | plausibly novel as a *measurement-impossibility* claim | adjacent to Kamoi |
| E6 poll parse-failure silencing | novel, but a small systems observation | — |
| E7 role separation not obeyed | **not checked in the audit** — needs its own search before claiming | — |
| — the self/peer/random 3-arm contrast | **OPEN** (verified: MetaCogAgent has no confidence-argmax arm) | closest: 2606.15419, 2601.17152 — each ran 2 of 3 legs |

**Consequence:** the strong, replicated half of our results is the *already-published*
half. The open half is the one that **failed held-out confirmation** (X1-X3).
That is the central tension Bella has to resolve.

## The paper this supports

A mechanism-and-limit paper built on E1-E3, with E4/E5 as the methodological
warning:

> A standard confidence gate in LLM multi-agent deliberation is worth nothing
> (E1) for an identifiable structural reason (E2), while the group demonstrably
> holds the answer it fails to surface (E3). We searched the observable
> alternatives and none replicates across actor models — so the failure is not a
> bad choice of signal but a property of what is locally observable.

Plus: the benchmark-validity half (E4, E5) — protocols compared under an
oracle-bearing verifier with unequal retry budgets overstate structural effects,
and stop-on-PASS makes the harm side unmeasurable.

**Both halves are negative/limitative results.** That is what the data supports.
It is publishable at AAMAS as a soundness-and-mechanism contribution, but Bella
should decide explicitly whether she wants a negative-result paper, because the
alternative is to spend the HPC budget hunting for a positive mechanism with no
offline evidence that one exists.


---

# 2026-09-28 (session 3) — post-validation status

## Framing (per Bella): the strong claim is dropped

NOT: "role labels fail to induce distinct behavior" (our own data refutes it).
INSTEAD: **prompted roles can be behaviorally distinguishable while differing
substantially in whether they realize the intended functional contract, and that
realization appears actor-dependent.**

## Validation outcome (P0 gate)

| measure | agreement | kappa | verdict |
|---|---|---|---|
| P1a Planner-does-not-compute | 0.967 | 0.933 | PASS, errors conservative |
| E2 Executor-uses-plan (v1) | 0.923 | 0.843 | PASS, but the one error was SYSTEMATIC |

E2 was rebuilt (v2). Consequence: **the E2 actor ordering flipped** — gemma3
fell 0.833 → 0.112 because its apparent plan-use was "Step N" in its own
working. P1a is unchanged.

**Gate: passed, with a caveat that matters.** The actor-dependent differences
remain large and significant on both components, so we do not stop. But the two
components now **disagree about which actor is most faithful**:

- P1a: gemma3 (.266) > gemma_4 (.111) > gpt_oss (.042) — aligns with PER advantage
- E2v2: gemma_4 (.243) > gemma3 (.112) > gpt_oss (.062) — does not

A single fidelity scalar would have hidden this. Any mediation claim must now
name *which* component mediates, chosen in advance.

## Net effect on the ladder

- Claim 1 (weak form): **held** — separability is formatting-driven; 0.90 overall
  vs 0.71 computation-only vs 0.77 length-only control.
- Claim 2: **held and validated** — actor differences survive the corrected metric.
- Claim 3 (mediation): **weakened further.** Only 2 actors have both fidelity and
  first-pass coverage, and the two fidelity components now point different ways.
- Claim 4 (causal): untested; requires the experiment.

## The binding constraint is now overlap, not novelty

Both 2609.27822 and 2608.14927 are observational analyses of this corpus by this
group. **A third observational analysis is the definition of thin-slicing.**
So: the controlled arms are not an enhancement, they are the precondition for
submitting at all. If the experiment does not run, do not submit.
