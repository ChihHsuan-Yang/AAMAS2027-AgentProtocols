# CLAIM_STATUS — every claim, its label, its evidence, its finding note

**Rewritten 2026-09-30 against `APPROVED_CLAIMS.md`, which is the authority.**
**Re-synced later the same day after `STATISTICAL_AUDIT.md` forced corrections to
A3, A6, A8 and A10 and added two dead claims.**

`APPROVED_CLAIMS.md` is owned by the Master Agent and is the source of
scientific truth. This file is a navigational index to it: same claims, same
scope, plus the evidence pointer and the finding note for each. **Where the
two ever disagree, `APPROVED_CLAIMS.md` wins and this file is the one that is
wrong.**

Numbers come from `analysis/out/FINAL_TABLES_OUTPUT.txt`, produced by
`analysis/scripts/FINAL_TABLES.py` against `experiments/results/FROZEN/`.
No number in this file was computed any other way.

Labels:
- **SUPPORTED** — measured on the frozen snapshot, survives its own audit, may be asserted *within its stated actor scope*.
- **EXPLORATORY** — real measurement, but post-treatment / descriptive / underpowered. May be reported, never as a causal or headline claim.
- **FALSIFIED — DO NOT RESURRECT** — was believed, then refuted. Reintroducing one is a regression, not a rewrite.

---

# ⛔ FALSIFIED — DO NOT RESURRECT

**Read this section before writing a single sentence of prose.** Every entry
below was asserted in this project by someone who believed it. Eleven of them
were killed by our own follow-up measurement or by the adversarial statistical
audit. They are listed first because
the failure mode is not inventing them — it is *re-deriving* them from an old
note, or reaching for one because it makes a paragraph flow better.

`APPROVED_CLAIMS.md`: *"No worker may reintroduce a dead claim because it
makes the prose cleaner."*

| # | dead claim | why it is dead | note |
|---|---|---|---|
| D1 | "the model whose organization collapses most loses least performance" | Rested on byte-metric coordinates (gpt-oss 0.846 vs gemma-4 0.173). Under the functional measure the ordering **REVERSES**. The scope contrast does not exist. | **F22** |
| D2 | monotone unanimity → recovery damage across actors | Not monotone at final n: unanimity gemma .955 > Llama .896 > gpt-oss .780, but damage gemma −.171 > gpt-oss −.077 > Llama +.000. | freeze |
| D3 | "gemma-4 shows no first-pass organization collapse" | Byte-metric artifact — gemma-4 paraphrases instead of duplicating bytes. Blinded adjudication judges it **0.857**. | **F13** |
| D4 | preregistered actor × enforcement interaction on accuracy | P4 is **null**; all three pairwise DiDs contain zero (T14). | prereg |
| D5 | "hard enforcement universally improves accuracy" | True only under as-graded scoring, which carries **8–17% one-sided survivorship** in Arm C. Under preregistered scoring gemma-4 goes significantly **negative**. | **F24** |
| D6 | "Arm B gets 2.5× more repair opportunity" | Wrong unit. `evaluator_calls` counts **submissions**, not opportunity. Every arm holds the same 6 cycles by construction. | **F17** |
| D7 | "per-opportunity, Arm B recovers better" | Matched on a post-treatment variable (submissions). Matched on cycles the sign reverses. | **F17** |
| D8 | "no accuracy claim is resolvable above scorer noise" | Built on the wrong grading key (`final_answer` instead of the evaluator's actual input). The per-arm "noise asymmetry" was 100% the F18 defect, and it reverses under the correct key. | **F21** |
| D9 | "roles prevent premature stopping" | Refuted **by construction** — MAX_OUTER_ROUNDS 3 × INNER_ROUNDS 2 = 6 cycles in every arm. Arm B receives *more* evaluator feedback, not less. | **F17** |

| D10 | "Arm C recovery is highest of any arm, above Arm A in all three actors (p ≤ 1.6e-3)" | The recovery denominator dropped 173 trajectories with a first incorrect verdict that then died in regeneration. Corrected, two of three paired p-values are lost (0.298, 0.105). | **STATISTICAL_AUDIT FATAL-1** |
| D11 | Llama-3.3's null recovery is a **"floor effect"** | Arm C restores recovery in that same actor (0.096 vs 0.009, p=3.8e-06), so the channel exists and is movable. ~80% power at 0.04–0.05 against an effect of 0.171. It is a genuine null specific to the ROLE manipulation. | **STATISTICAL_AUDIT SERIOUS-2** |

## Four more that must not come back

These are not in the `APPROVED_CLAIMS.md` dead table but are withdrawn in the
record and would be equally wrong to assert:

| dead claim | why | note |
|---|---|---|
| "gpt-oss's Arm B planner rubber-stamps / is degenerate" | It is **uninstrumented**: 2.85 visible chars/s vs 195 in its own Arm A. 28 seconds to emit 37 characters. Our logger discarded the reasoning. Calling it a behaviour attributes our defect to the model. | **F22** |
| "gpt-oss self-favours as a grader" | Artifact of the matching key. On identical prompts it looks *dis*favoured 16–0. A quantity that flips sign when the key is corrected is an artifact of the key. | **F21** |
| noise floor = 0.0395, or 0.0023, or 0.0014 | Three superseded values. The settled figure is the **group-level 0.0086** (24/2791), range 0.0020–0.0086. Earlier notes quoting 0.0092 predate the final freeze. | **F21, F23** |
| "Huang et al. showed LLMs cannot self-correct even with oracle feedback" | **FALSE.** Their oracle condition *improves* accuracy (GSM8K 75.9 → 84.3). This is the sentence a reviewer of this literature catches first. | **F19** |

---

# ✅ SUPPORTED

Actor scope is part of every claim. A claim asserted outside its scope is a
different, unsupported claim.

### A1 — Removing roles destroys functional division of labor. **ALL THREE ACTORS.**
Blinded Opus-5 adjudication: Arm B "no division of labor" **0.964** (n=56) vs
Arm A **0.000** (n=42). Per actor in Arm B: Llama 1.000, gpt-oss 1.000,
gemma-4 0.857.
Evidence: T23; reproduce with `python3 adjudication/analyze.py`.
Guard: **byte duplication is a LOWER BOUND ONLY** (precision 1.000, recall
0.262) and must never carry this claim alone. Note: **F13, F15, F22**.

### A2 — Removing roles does not hurt first-pass accuracy. **ALL THREE ACTORS.**
gemma-4 0.802 → 0.802 (+0.0000 [−0.0150,+0.0156]); gpt-oss 0.713 → 0.763
(+0.0503 [+0.0333,+0.0672], **improves**); Llama 0.308 → 0.316 (+0.0077, null).
Evidence: T3.
Guard: **state as consistent with prior role-ablation work — NOT our novelty**
(dylan2026equal, orogat2026architectural, wang2024rethinking). It is our
control condition. Note: **F19**.

### A3 — The cost appears after failure. **GEMMA-4 CLEAN; GPT-OSS WEAKER; LLAMA NOT.**
- gemma-4: recovery 0.222 → 0.051. Paired on problems wrong under both arms:
  A-only recovers 37, B-only 3, McNemar exact **p = 2e-08**. Strongest result
  in the paper.
- gpt-oss: marginal 0.324 → 0.249, but the **paired** contrast is **p = 0.246**
  — must be described as weaker and not significant when paired.
- Llama-3.3: 0.014 → 0.015. **A genuine null, NOT a floor effect.** Its
  recovery channel exists and is movable — architectural enforcement raises it
  to 0.096 vs 0.009 (p=3.8e-06) — so the absence is specific to the
  *role-instruction* manipulation. ~80% power against an effect of 0.04–0.05
  against a gemma effect of 0.171: informative for a gemma-sized effect,
  uninformative below ~0.04. **The recovery result does not replicate in the
  weakest actor and we do not explain that away.**

Evidence: T3, T4. Note: **F11, F14, F17**; corrected by **STATISTICAL_AUDIT
SERIOUS-2** — "floor effect" is now a dead claim, falsified by our own Arm C.

### A4 — It is not premature stopping, and not less feedback.
Same 6 cycles in every arm by construction. gemma-4 first-pass-wrong: Arm A
5.52 cycles / 1.54 submissions / 3.98 revising; Arm B 5.83 / 5.80 / 0.03.
Arm B receives **more** evaluator feedback.
Evidence: T5. Note: **F17** (this claim exists *because* F17 corrected D6/D9).

### A6 — Enforcement restores organization. It restores RECOVERY only for Llama-3.3.
**CORRECTED 2026-09-30 — `STATISTICAL_AUDIT` FATAL-1 found a denominator bug.**
The recovery denominator was implemented as `graded(r) and fp==0`, silently
dropping 173 trajectories that received a first (incorrect) verdict and then
died in regeneration. All 173 have `fp==0` — structural, since a passing first
verdict ends the loop — so they meet the definition and score 0 under
preregistered scoring.

Corrected recovery: gemma-4 **0.314** (was 0.412), gpt-oss **0.395** (was
0.461), Llama **0.139** (was 0.150). Arms A and B move by ≤ 0.002.
Paired A-vs-C after correction: gemma-4 p=0.298 and gpt-oss p=0.105 are **no
longer resolvable**; Llama-3.3 p=**3.81e-06** survives intact (0.096 vs 0.009).

**MAY CLAIM:** Arm C restores organization (adjudicated no-division 0.136) and
un-freezes answers (0.119/0.092/0.072, lowest of any arm). Arm C restores
recovery **for Llama-3.3**; for gemma-4 and gpt-oss the direction is consistent
but not resolvable against Arm C's attrition.
**MAY NOT CLAIM:** "recovery highest of any arm, above Arm A in all three
actors." **Dead.**
Evidence: T23 for organization; **T1 now carries the corrected recovery**
(fixed in commit `ba28977`; cross-check
`analysis/scripts/stat_audit_a4b_assumptionfree.py`). Any artifact still
showing 0.412/0.461/0.150 is pre-`ba28977` and stale.

### A7 — But enforcement does not improve final accuracy, because it is brittle.
Preregistered scoring: C−A = −0.0225 (gemma-4, **significantly negative**),
−0.0050 (gpt-oss, null), +0.0175 (Llama, null). Attrition 8.0% / 9.9% / 17.0%
vs 0.0–2.5% in A/B.
Evidence: T2, T7.
Guard: the claim is **NOT "hard roles are better."** It is *"organization
preserves revisability, but enforcing it is brittle."* Note: **F24**.

### A8 — Grader noise floor.
**0.0086** group-level (24/2791 distinct graded strings receive contradictory
verdicts across identical prompts at temp 0); range 0.0020–0.0086 across
estimators. Guard: **do NOT report "effect / floor = 3.9×".** Dividing an effect size by a
disagreement rate is not a valid operation, and grader noise largely cancels in
a paired contrast. Instead propagate the per-call disagreement rate into the
bootstrap — same three verdicts: gemma-4 [−0.0488,−0.0175] **SIG**, gpt-oss
null, Llama null.
Evidence: T6. **T27 prints the invalid ratio — do not quote it.**
Note: **F21, F23**; corrected by **STATISTICAL_AUDIT SERIOUS-4**.

### A9 — Single-agent control. **BOTH DIRECTIONS, ALWAYS TOGETHER.**
gpt-oss A +0.0131, B +0.0294 (collapsed team beats its single agent);
gemma-4 A −0.0225, B −0.0563 (**team is WORSE than its single agent**).
Guard: **never quote gpt-oss alone.** Provenance: **NOT in the frozen
snapshot** — it comes from the historical released corpus, and that must be
stated wherever it is used.
Evidence: T17.

### A10 — The preregistered primary (P4) is null — and the Holm correction must be RUN.
All three pairwise difference-in-differences contain zero. **But the claim that
P1–P5 carry a Holm correction is FALSE of the reported analysis**: `holm`
appears nowhere in `FINAL_TABLES.py` or its output, and a reviewer verifies
that with one grep. Applying it changes nothing (gemma C−A Holm p=0.042; P4
still null), so **the fix is to run it, not to reword**.

Two of three P4 DiDs have MDE 0.069 and 0.075 at n=400 against plausible
effects ≤ 0.040, so **only the gpt-oss−gemma DiD (MDE 0.033) is an informative
null. Say which is which.**
Evidence: T14. Note: **F24** (the not-submit condition was evaluated and not
triggered — narrowly, and only because the preregistration's own exclusion rule
scores ungraded as incorrect); **STATISTICAL_AUDIT SERIOUS-1, SERIOUS-5**.

---

# 🔶 EXPLORATORY

Real measurements that may appear in the paper as description, never as the
headline and never causally.

### A5 — The mechanism is failure to produce a distinct second candidate.
Frozen-answer rate among first-pass-wrong: gemma-4 A 0.288 vs B 0.845.
Reviewer never declines in 98.1% of gemma-4 Arm B vs 5.1% of Arm A.
**Rubber-stamping is a SYMPTOM of answer lock-in, not established as its root
cause.** All of this is post-treatment conditioning: descriptive,
associational, **never causal**.
Evidence: T1, T5. Note: **F16 → F17** (F16's quantitative claims are retracted;
its qualitative conclusion survives).
Framing constraint: answer lock-in already has a name — Liang's
**Degeneration-of-Thought**. Cite `liang2024divergent` and claim only the
**inversion** (multi-agency is the prescribed cure; role-free multi-agency
does not escape it).

### Context contamination is real but does not account for the arm gap.
Recovery falls with accumulated context inside *every* arm. Matched on pooled
context quartile the arm gap survives in Q1–Q3 — **but gpt-oss Q4 reverses**
(A 0.070 vs B 0.192). All three statements travel together.
Evidence: T22. Note: **F20**.
Caveat: context volume is itself downstream of treatment.

### Planner–executor duplication, measured against a shuffled null.
Excess-over-null B−A: gemma +0.291, Llama +0.300, gpt-oss +0.510.
Guard: **gpt-oss's row is not interpretable** — its Arm B numeric-token sets
have median size 1, and a Jaccard over 1–2 token sets is not a duplication
measure. It is excluded from the duplication claim.
Evidence: T10, T21. Note: **F22 addendum**.
Guard: report **excess-over-own-null**, never raw Jaccard, never the B−A
difference of raw Jaccards (the null is not flat across arms).

### C′ − C context control.
PREREG: gemma-4 +0.0450 [+0.0125,+0.0775] SIG; gpt-oss −0.0125, null.
AS-GRADED: both null. A **partial** control — C′ restores shared history but
Arm C also changes the output schema, so it does not vary one thing alone.
Evidence: T15.

### The Reviewer's critique function is largely unexercised.
The Reviewer accepts on its first turn in 70–79% of Arm A trajectories and
93.7–99.5% of Arm B. Decision: **narrow the Reviewer claim rather than annotate
further** (R4 / N-14).
Evidence: `notes/R4-DECISION.md`.

---

# 🚫 MUST NOT CLAIM (novelty audit, binding)

Not falsified — *not ours*. Asserting one is a novelty error, not a factual one.

- **First-pass parity as OUR finding** — owned by dylan2026equal, orogat2026architectural, wang2024rethinking. Present as "as expected, consistent with prior work."
- **Being first to show LLMs fail to revise under external feedback** — jiang2026exactfeedback, stechly2024selfverification.
- **Discovering answer lock-in** — it is Liang's Degeneration-of-Thought. Cite `liang2024divergent`; claim only the inversion.
- **Premature consensus as a novel hypothesis** — 9+ papers name it. We *test and reject* a standing explanation; we do not propose it.
- **"Diversity is the active ingredient in debate."**
- **NEVER** write "Huang et al. showed LLMs cannot self-correct even with oracle feedback." It is false (see D-list above).

---

# ⚠️ CAVEATS THAT TRAVEL WITH THE RESULTS

Not optional. Each one must accompany the number it qualifies, in the same
paragraph — a caveat one paragraph away from its number reads as an
endorsement of the paragraph it is not in.

1. **Recovery is oracle-gated.** The evaluator sees gold. **No cell recovers before the first oracle verdict** — T25 is 0 in all nine cells. None of this is unaided self-correction.
2. **F13 logging defect.** gpt-oss's Arm B planner is **UNINSTRUMENTED** (2.85 ch/s vs 195 in its own Arm A), not abstaining. Bounds both the duplication claim and any collapse-*mode* interpretation.
3. **F18 scoring defect.** The recorded grade is the grade of the last *submitted* answer, not the answer the team last *held*. 54 trajectories demonstrably under-credited; positive control 0 of 10,734. The defect penalises exactly the revising arms — it works **against** our headline, so correcting it strengthens the result, and it must still be disclosed.
4. **Every conditional analysis is post-treatment.** Conditioning on first-pass-wrong, on cycles, on context volume, on answer movement — all descriptive.
5. **Adjudication is MODEL adjudication.** Not human annotation, not ground truth. State the judge, the blinded protocol, the rubric hash, and the stability.
6. **Temperature 0 is not deterministic on this endpoint.** No per-trajectory claim is made.
7. **Llama-3.3 is much weaker on this benchmark** (Arm A 0.307 vs ~0.80). Its contrasts sit on a ~0.31 base. Same-direction evidence; never a matched third point.
8. **Arm C carries differential attrition** (8–17% vs 0.0–2.5%). Report it beside every Arm C figure, not only in limitations.
9. **One benchmark, one domain.** omnimath2, math. No second-domain claim — the runner pins omnimath2.
10. **T27 still prints an invalid statistic.** Its "effect ÷ floor = 3.9x clears" line is on the dead list above but `FINAL_TABLES.py` still emits it — never quote a T27 ratio. T1's Arm C recovery had the same status until commit `ba28977` regenerated it; it is now correct at 0.314/0.395/0.139.
11. **The evaluator grades its own family.** gpt-oss-120b is the evaluator and one of the three actors. R-10 (evaluator independence with a second judge) is **UNTESTED**; the identical-prompt control rules out bias *on the answer string* only, and does not upgrade it.

---

# Where the old board went

The pre-2026-09-30 version of this file carried a live "post-pivot board" with
claim ladders A–E and per-session correction logs. That history is preserved
in git (`git log -p CLAIM_STATUS.md`) and in `DECISION_LOG.md`,
`notes/CLAIM-LADDER-v2.md`, and `notes/CORRECTION-01-actor-contrast-withdrawn.md`.

**Those notes contain numbers computed on earlier cuts** (n≈9,030 and smaller)
and several claims now on the dead list above — e.g. recovery "0.490 → 0.045",
collapse "0.698", noise floors of 0.0395/0.0023/0.0014/0.0092. They are kept
readable because a retraction that deletes its own evidence kills the repair it
prescribes. **Do not source a number from them.** Everything current is in
`analysis/out/FINAL_TABLES_OUTPUT.txt`.
