# Finding 10 — When is multi-agent organization load-bearing? (2026-09-29)

**Definition used throughout:** a component of an organization is
**load-bearing** if removing or altering it causes a reproducible degradation in
task performance *under a matched compute and information budget*.

## The headline: the same organizational transition costs one actor 39 points and the other nothing

Matched within problem, Arm A → Arm B, restricted to the transition
**differentiated → collapsed**:

| actor | n | acc under A | acc under B | **B − A** |
|---|---|---|---|---|
| **gpt-oss-120b** | **1,024** | 0.823 | 0.819 | **−0.0039 [−0.0225, +0.0146]** |
| **gemma-4-31B** | 165 | 0.406 | 0.018 | **−0.3879 [−0.4606, −0.3152]** |

The identical loss of organization is **free** for one actor and **catastrophic**
for the other. For gemma-4 the collapsed system essentially stops working
(0.406 → 0.018).

## The collapse measure survives every audit (see COLLAPSE_MEASUREMENT_AUDIT.md)

- determinism ruled out: **0 of 1,364** collapsed groups had identical prompts
- normalization *raises* the rate (0.842 → 0.927), so exact is conservative
- happens on the **first pass** (1,079 round-1 events), not retry convergence
- **not an easy-problem artifact**: gpt-oss collapse is **0.827 on the hardest
  stratum** (0.900 easy, 0.709 medium)

Note the actors differ in *where* they collapse: gemma-4's collapse is
concentrated on hard problems (0.567) and nearly absent on easy ones (0.008).

## Enforcement restores structure without restoring capability

Arm C drives answer-authorship compliance to **1.000** in every cell and cuts
collapse to **0.022/0.045**, yet **C − A ≈ 0** for both actors
(−0.0025 / −0.0098, both CIs spanning zero), and the Planner keeps computing
(density 2.70/3.47 eq per 1k chars vs 2.55/2.08 in Arm A).

The C′ context control rules out the obvious confound: C′ − C is null in both
actors (+0.0179 / −0.0115).

## The degenerate-control question (§19): NO, it is not just a single agent

Using the historical budget-matched `single_agent` protocol on the **same
problems**:

| actor | arm | vs single-agent |
|---|---|---|
| gpt-oss | A | +0.0128 [−0.0048, +0.0304] |
| gpt-oss | **B (collapsed)** | **+0.0248 [+0.0072, +0.0424]** significant |
| gemma-4 | A | −0.0239 [−0.0423, −0.0048] |
| gemma-4 | B | −0.0535 [−0.0718, −0.0343] |

**This is an important guard against overclaiming.** gpt-oss's collapsed team
still *beats* a single agent by 2.5 points. So the three agents are not
functionally one agent — redundant parallel compute under the same evaluator
loop buys something real. What it does **not** buy is anything attributable to
*differentiated roles*.

Equally: gemma-4's three-agent team is **worse** than its own single agent, in
both arms. For that actor the PER organization is actively costly.

## Claim ladder status

- **A (descriptive)** removing role instructions can cause extreme collapse — **SUPPORTED** (0.842 exact, audited)
- **B (actor-specific surprise)** the actor with the largest collapse loses the least — **SUPPORTED**, interaction −0.0450 [−0.0687,−0.0221], and the matched transition table is stronger still
- **C (structural dissociation)** enforcement restores structure, not capability — **SUPPORTED** (P2→1.000, collapse→0.022, C−A null, C′ rules out context)
- **D (functional dissociation)** structural compliance ≠ cognitive division of labor — **PARTIAL**: equation density supports it, but Level-3 functional metrics and human validation are still running
- **E (broad: neither necessary nor sufficient)** — **NOT YET**. Needs D closed, and ideally a third actor.

## What must NOT be claimed
- "roles do not matter" — false; gemma-4 loses 39 points
- "multi-agent systems are just single agents" — false; collapsed gpt-oss beats
  its single agent by +0.025
- Any causal reading of collapse→accuracy: collapse is **post-treatment**. The
  transition table is an *association*, however sharp.

---

## Functional contribution: what actually changes hands (added 2026-09-29)

Answer extraction corrected per arm (Arm C/C' answers live in the JSON `answer`
field, not in `\boxed`; the first pass of this analysis reported spurious zeros
for those arms and is superseded).

| actor / arm | planner emits an answer | executor emits one | executor ≠ planner |
|---|---|---|---|
| gpt-oss / A | 0.17 | 0.91 | 174/184 (0.95) |
| **gpt-oss / B** | **0.90** | 0.95 | **200/1088 (0.18)** |
| gpt-oss / C | **0.00** | 0.92 | n/a — planner emits none |
| gemma-4 / A | 0.00 | 0.97 | n/a |
| **gemma-4 / B** | **0.98** | 0.99 | **50/1224 (0.04)** |
| gemma-4 / C, C' | **0.00** | 0.43 / 0.36 | n/a |

Three things follow.

**1. Arm B is not "roles blurred" — it is every agent answering.** Under generic
prompts 90-98% of *planners* emit a final answer (vs 0.00-0.17 in Arm A), and
the executor then reproduces it unchanged in 82% (gpt-oss) to 96% (gemma-4) of
cases. The pipeline becomes three independent solvers that agree, not a
division of labor.

**2. Arm A does have a real functional boundary, and it is asymmetric.**
gemma-4's planner *never* answers (0.00) and gpt-oss's rarely does (0.17) — the
soft role prompt genuinely suppresses answer authorship. Where gpt-oss's planner
does answer, the executor overrides it 95% of the time, i.e. the executor is
doing independent work rather than copying.

**3. Arm C enforces the boundary absolutely** (planner answers 0.00 in every
cell), confirming the manipulation from a second, independent measurement.

**A caveat I will not bury:** gemma-4's Arm C executor emits a parseable answer
in only 0.43 of trajectories (0.36 in C'), versus 0.97 in Arm A. Some of that is
the JSON-extraction path, not necessarily missing answers — the grader reads the
trajectory's `final_answer`, not this field, so accuracy is unaffected. But it
means this particular table under-counts gemma-4 Arm C and must not be read as
"the executor stopped answering". Flagged for the functional-metrics worker.

---

## THE SHARPEST VERSION (count-matched rule, 2026-09-29)

Re-running the transition table under the count-matched (first-pipeline-pass)
collapse rule gives the cleanest statement of the phenomenon:

| actor | transition | n | acc A | acc B | B − A |
|---|---|---|---|---|---|
| **gpt-oss-120b** | **differentiated → COLLAPSED** | **879** | 0.895 | 0.912 | **+0.0171 [+0.0023,+0.0319]** |
| gpt-oss-120b | differentiated → differentiated | 381 | 0.651 | 0.648 | −0.0026 [−0.0499,+0.0446] |
| **gemma-4-31B** | **differentiated → differentiated** | **1266** | 0.849 | 0.820 | **−0.0292 [−0.0450,−0.0134]** |

Read together, this is the paper in three lines:

1. **gpt-oss loses its organization on 879 problems and gets slightly BETTER**
   (+0.017, CI excludes zero). Losing the division of labor is not merely free —
   in the first-pass-collapse subset it is marginally beneficial.
2. **gemma-4 never collapses on the first pass at all** (0.000) and *still*
   loses accuracy when role instructions are removed (−0.029, CI excludes zero).
   So its loss is **not** mediated by visible organizational collapse.
3. Therefore **visible collapse and performance loss are dissociated in both
   directions**: collapse without loss (gpt-oss), and loss without collapse
   (gemma-4).

Point 3 is stronger than the original framing. The earlier reading — "the actor
that collapses most loses least" — is true but incomplete; the count-matched
analysis shows gemma-4's penalty arrives **without any visible collapse to
explain it**. Whatever role instructions do for gemma-4, it is not sustaining
output differentiation.

**This also retires a tempting but wrong explanation.** One could have said
gemma-4 loses accuracy *because* its organization degrades. Under the
count-matched rule that mechanism is unavailable: there is no first-pass
degradation to blame.
