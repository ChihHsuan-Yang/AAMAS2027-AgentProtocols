# STATISTICAL AUDIT — adversarial review of the AAMAS 2027 submission

**Auditor role:** break the inferences, not confirm them.
**Date:** 2026-09-30. **Data:** `experiments/results/FROZEN/`, sha256 re-verified
against `MANIFEST.json` (all three files match).
**Scripts:** `analysis/scripts/stat_audit_*.py`. Nothing under `paper/`,
`figures/` or `FINAL_TABLES.py` was modified.

## Step 0 — independent reproduction (prerequisite)

I re-extracted every trajectory from the frozen JSONL with definitions copied
from `FINAL_TABLES.py`, and reproduced **T1, T2, T4 and T7 exactly** — every
first-pass rate, final accuracy, recovery rate, paired contrast, McNemar count
and attrition figure. The McNemar implementation was checked against
`scipy.stats.binomtest` on 11 input pairs including the degenerate ones: exact
agreement. **No arithmetic errors found anywhere in the headline pipeline.**
Every disagreement reported below is a disagreement about *what was computed*,
not about *whether it was computed correctly*.

## Positive controls (`stat_audit_poscontrol.py`)

Each check was run against a copy of the data corrupted in the shape of the
defect it targets. All five fire correctly:

| control | planted defect | result |
|---|---|---|
| PC1 | extra exhausted Arm C rows | recovery falls monotonically 0.314→0.145 — **fires** |
| PC2 | Arm B outcomes redrawn at Arm A's rate | significant in 2/200 = 0.010 (expect ~.05) — **does not over-fire** |
| PC3 | 20 unchanged-answer "recoveries" | counts exactly 20 — **fires** |
| PC4 | problem-level random effect | clustered interval *narrows* vs unpaired — **fires, and tells us the sign** |
| PC5 | gemma-sized recovery effect planted in Llama | detected at p=1e-06 — **fires** |

---

# FATAL

## FATAL-1. Arm C's recovery claim (A6) is survivorship, and it does not survive removing it

**Attack 4.** A6 states Arm C recovery is "0.412/0.461/0.150 — highest of any
arm, above Arm A in all three actors (paired p ≤ 1.6e-3)". This is computed on
graded trajectories only, while Arm C discards 8.0/9.9/17.0%.

The decisive fact is not a modelling assumption. Of the 354 ungraded Arm C
trajectories, **178 reached at least one evaluator call, and 178 of 178 have
`fp = 0`.** Zero have `fp = 1`. This is structural: a passing first verdict
terminates the loop, so an ungraded trajectory that was graded once is
*necessarily* first-pass-wrong. These rows therefore satisfy the paper's own
definition of the recovery denominator — "P(final correct | first evaluator
verdict incorrect)" — their first verdict exists and is incorrect — and under
the preregistered scoring their final is 0. **They were silently dropped from a
denominator they belong in by definition.** This is an internal inconsistency
between the recovery definition and the preregistered scoring rule, not a
judgement call.

Recomputing with no imputation whatsoever (`stat_audit_a4b_assumptionfree.py`):

| actor | published | assumption-free | Δ |
|---|---|---|---|
| gemma-4 | 0.412 (n=262) | **0.314** (n=344) | −0.098 |
| gpt-oss | 0.461 (n=306) | **0.395** (n=357) | −0.066 |
| Llama-3.3 | 0.150 (n=234) | **0.139** (n=251) | −0.010 |

Arms A and B move by ≤0.002 — the bias is one-sided, exactly as expected.

**The paired significance claim does not survive.** Two of the three stated
p-values are lost:

| actor | published | assumption-free |
|---|---|---|
| gemma-4 | n=171, 12 vs 34, **p=1.6e-03** | n=226, 25 vs 34, **p=0.30** |
| gpt-oss | n=245, 19 vs 45, **p=1.6e-03** | n=291, 30 vs 45, **p=0.105** |
| Llama-3.3 | n=202, 0 vs 19, p=3.8e-06 | n=218, 0 vs 19, **p=3.8e-06** (survives) |

Under the true worst case (all 354 ungraded counted as first-pass-wrong,
including the 204 that never submitted and whose first-pass status is
unobservable), gemma-4 falls to 0.277 and **gpt-oss falls to 0.304, below its
own Arm A of 0.324 — the ordering flips.**

**Severity: FATAL** for A6 as written. The ordering claim survives in the
point estimates; the *significance* claim does not, for two of three actors.

**Required change — A6, delete:**
> "recovery 0.412/0.461/0.150 — highest of any arm, above Arm A in all three actors (paired p ≤ 1.6e-3)"

**Replace with:**
> Arm C's recovery exceeds Arm A's in all three actors, but the margin is
> substantially survivorship. Computing recovery on every trajectory with a
> recorded incorrect first verdict — including those later exhausted, which the
> preregistration scores 0 — gives 0.314/0.395/0.139 against Arm A's
> 0.222/0.324/0.015. On that denominator the paired A-vs-C contrast remains
> significant only for Llama-3.3 (p=3.8e-06); gemma-4 (p=0.30) and gpt-oss
> (p=0.105) do not. Under the worst case that also counts the never-submitted
> trajectories, gpt-oss's Arm C recovery falls below its Arm A. **We therefore
> claim that enforcement restores recovery for Llama-3.3 only, and report the
> other two as directionally consistent but not resolvable against attrition.**

Same change required in `results.tex` §R5 ("paired-significant in all three
($p=1.6\times10^{-3}$, $1.6\times10^{-3}$, $3.8\times10^{-6}$)") — that
parenthesis must go.

**Note this is a strictly better position than the one you feared.** The
survivorship is *bounded*, not unbounded, because the first-pass verdict of the
178 informative rows is recorded rather than imputed. Llama-3.3's result — the
one A6 singles out as "the only cell where a manipulation restores its
recovery" — is completely unharmed, because Llama's Arm C loses mostly
never-submitted trajectories (51 of 68) rather than graded-once ones.

---

# SERIOUS

## SERIOUS-1. The paper asserts a Holm correction that was never applied

**Attack 3.** `method.tex:63` and `results.tex:6` both state "P1–P5 carry a
Holm correction."

- `holm` appears **0 times** in `FINAL_TABLES.py`.
- `holm` appears **0 times** in `FINAL_TABLES_OUTPUT.txt`.
- **Zero** adjusted p-values of any kind appear in the frozen output.
- The only p-values in the entire frozen pipeline are T4's six McNemar values.
  P1, P2, P3 and P5 are reported as bootstrap CIs and **have no p-value at
  all**, so no correction is even computable from what is reported.
- A `holm()` function does exist, in `analysis/scripts/x1_analyze_campaign.py`.
  Its only surviving output, `x1_interaction.csv`, is dated **2026-09-28
  17:34**, before the campaign finished, and its DiDs (+0.050/−0.055/−0.105) do
  not match the frozen T14 (+0.0175/+0.0400/+0.0225). It is a pilot artifact
  and is not the source of any paper number.

This is a **false statement about the methods** — the single most damaging
class of finding in review, because a reviewer can verify it from the
artifact in one grep.

The good news: I applied the promised correction (sign-flip permutation p,
Holm across the 7 computable preregistered tests) and **nothing changes**. P4
was null before and after. P3's one significant cell survives (gemma C−A raw
p=0.007, Holm p=0.042). The claim was true in substance and false in fact.

**Required change — `method.tex:63` / `results.tex:6`, either:**
(a) actually run it — add the permutation p-values and Holm-adjusted column to
`FINAL_TABLES.py` and report them (the numbers are in
`stat_audit_a3_multiplicity.py` §3.3); or
(b) change the sentence to:
> Primary endpoints are reported as bootstrap intervals clustered by problem;
> Holm adjustment across P1–P5 does not alter any verdict (gemma-4's C−A
> survives at Holm p=0.042; P4 remains null in all three pairs).

Option (a) is strongly preferred: the preregistration committed to it.

**On the wider family:** the paper reads 27 bracketed CIs in prose and the
frozen output computes 38. FWER if all were null: 0.75 and 0.86 respectively.
This is *not* a reason to correct across all of them — most are descriptive —
but it is a reason not to add any more. **The gemma-4 headline is immune**:
raw p=1.9e-08, Bonferroni over all 38 contrasts = 7.4e-07.

## SERIOUS-2. "Floor effect" for Llama-3.3 is falsified by the paper's own Arm C

**Attack 8.** `results.tex` §R3 says Llama "recovers at 0.015 in both arms
because at 0.307 first-pass accuracy it is too weak a solver **for the recovery
channel to exist at all**." A6 then says Llama's Arm C is "the only cell where
a manipulation restores its recovery (0.150 vs 0.015, p=4e-06)."

These two sentences contradict each other. A channel that does not exist cannot
be restored. **Llama Arm C recovers at 0.150 — 35 recoveries out of 234 — with
paired A-vs-C 0 vs 19, p=3.8e-06.** The recovery channel demonstrably exists
and is demonstrably movable; what is absent is a *role-instruction* effect on
it. And this is the one Arm C recovery result that fully survives FATAL-1.

The distinguishing test you asked for is exactly this: a floor predicts no
manipulation moves it; a genuine absence predicts the channel is movable by
something other than the manipulation under test. **Arm C is that test, it was
already run, and it rejects the floor.**

Power is not the excuse either. At Llama's n and discordance the A-vs-B test
has ~80% power at a true A-recovery excess of 0.04–0.05; the gemma effect is
0.171, and PC5 confirms a planted gemma-sized effect is detected at p=1e-06.
**The Llama null is informative against a gemma-sized effect** and
uninformative only below ~0.04.

**Required change — A3, replace:**
> "Llama-3.3: 0.015 → 0.015. **FLOOR EFFECT. Does NOT replicate. Say so.**"

**with:**
> Llama-3.3: 0.015 → 0.015, a genuine null, not a floor. Its recovery channel
> exists and is movable — architectural enforcement raises it to 0.150
> (p=3.8e-06) — so the absence is specific to the role-instruction
> manipulation. The test has ~80% power against an effect of 0.04–0.05 and the
> gemma effect is 0.171, so this is an informative null for a gemma-sized
> effect and uninformative below ~0.04. **The recovery result does not
> replicate in the weakest actor and we do not explain that away.**

Corresponding edits in `results.tex` §R3 (delete "for the recovery channel to
exist at all") and `limitations.tex` ("a floor effect rather than a null" —
this has it exactly backwards).

This change *costs* you the convenient excuse and *buys* you a sharper claim:
the effect is actor-conditional on realized fidelity, which is the paper's own
thesis.

## SERIOUS-3. The T22 context reversal is an artifact of the pooled quartile cut

**Attack 6.** `results.tex` §R4 reads a directional reversal off T22: "in
gpt-oss's top quartile the ordering reverses (0.070 vs 0.192): where context is
longest, Arm A's own contamination costs more than the roles return. **All
three statements stand.**"

Quartiles are cut on the *pooled* A+B context distribution, and context is
nearly a function of arm (AUC(arm | context) = 0.22 for gpt-oss). The
consequence is severe cell imbalance: gpt-oss Q1 is 12 Arm A rows against 198
Arm B rows (A share 0.06), Q4 is 158 vs 52. The "quartiles" are not matched
strata; they are arm indicators in disguise.

Re-cutting quartiles **within arm** (each arm on its own distribution,
~116 vs ~94 per cell, balanced by construction):

| quartile | recA | recB | B−A |
|---|---|---|---|
| Q1 | 0.784 | 0.330 | −0.455 |
| Q2 | 0.313 | 0.202 | −0.111 |
| Q3 | 0.155 | 0.266 | +0.111 |
| Q4 | 0.043 | 0.200 | +0.157 |

The reversal does not vanish under a within-arm cut — it *persists* in Q3 and
Q4. But the pooled Q1 figure the paper also cites (A=1.000, n=12) is built on
twelve trajectories and is not a usable estimate.

There is a second, independent problem. `ctx_chars` counts **visible**
characters, and the paper's own F13 logging defect discards gpt-oss Arm B's
reasoning traces (75.7% of its role messages). Measured against latency — a
defect-independent proxy — gpt-oss Arm B generates for *longer* per trajectory
than Arm A (568s vs 479s) while logging *half* the characters (29,078 vs
54,978). **Its low context quartile placement is partly the logger, not less
context.** Re-cutting T22 on latency instead of characters keeps the reversal
(Q4 B−A = +0.101) but moves every cell count materially (Q1 goes from 12/198 to
112/98).

**Severity: SERIOUS.** The qualitative conclusion survives; the specific
numbers quoted in the prose do not, and the n=12 cell should never have been
quoted.

**Required change — `results.tex` §R4, replace the quoted figures:**
> "within Arm A alone, gpt-oss recovery falls 1.000 → 0.070 across pooled context quartiles … ($0.662$ vs $0.151$, gemma-4; $0.656$ vs $0.293$, gpt-oss) … but in gpt-oss's top quartile the ordering reverses ($0.070$ vs $0.192$)"

**with within-arm quartiles**, and add: "Quartiles are cut within arm, because
the pooled cut places 198 of 377 Arm B trajectories in Q1 against 12 Arm A and
is therefore an arm indicator rather than a matched stratum. For gpt-oss the
context measure is additionally distorted by the logging defect of
§\ref{subsec:logging}; cutting on latency instead preserves the reversal."

Drop the "All three statements stand" sentence — one of the three rested on
n=12.

## SERIOUS-4. The noise-floor ratio is not a valid operation (A8)

**Attack 5.** A8 compares an effect size (a difference of two accuracy means,
0.0338) to a disagreement rate (P(a graded string receives contradictory
verdicts), 0.0086) and reports the ratio, 3.9×. These are different quantities
and the ratio has no inferential interpretation. Three specific problems:

1. Grader noise is **largely common to both arms** — the same grader grades
   both — so it substantially cancels in a paired difference. The final graded
   string is byte-identical across arms on 74.2% / 50.9% / 42.7% of paired
   problems; on those rows the grader's verdict *and its noise* are shared and
   contribute exactly zero to the contrast.
2. The residual is a **variance** contribution that shrinks as 1/√n, not a
   constant **bias floor**.
3. "Effect ÷ probability = 3.9×" is dimensionally a ratio of a mean difference
   to a probability.

**There is a defensible replacement, and it delivers the same three verdicts.**
Propagate grader noise into the interval: flip each graded outcome
independently with q=0.0072 (the per-call rate, least favourable) inside the
bootstrap:

| actor | observed B−A | clean CI | noise-propagated CI | verdict |
|---|---|---|---|---|
| gemma-4 | −0.0338 | [−0.0488,−0.0187] | **[−0.0488,−0.0175]** | SIG |
| gpt-oss | +0.0163 | [+0.0006,+0.0325] | **[−0.0013,+0.0331]** | null |
| Llama-3.3 | +0.0025 | [−0.0325,+0.0376] | [−0.0350,+0.0375] | null |

gemma survives, gpt-oss becomes null, Llama stays null — **exactly the three
conclusions A8 already draws**, reached by a coherent route.

**On the estimate itself: I tried to break it and could not.** `prompts.py`
`EVALUATOR_PREPEND` templates only `${task_description}`, `${solution}`,
`${result}` — no history — so the evaluator prompt *is* a deterministic
function of (problem, raw candidate), and the "identical evaluator prompts"
wording is justified. T6 groups on the *normalised* candidate, which merges 173
groups containing distinct raw strings; recomputing on the exact raw key gives
**0.0072, lower than the published 0.0086**. The published floor is
conservative. Keep the estimate; fix the operation.

**Required change — A8, replace:**
> "gemma-4's B−A clears it 3.9x."

**with:**
> Grader noise is propagated into the bootstrap by flipping each graded outcome
> with the per-call disagreement rate (0.0072). Under that perturbation
> gemma-4's B−A remains significant ([−0.0488,−0.0175]) while gpt-oss's becomes
> null and Llama-3.3's stays null. **We do not compare an effect size to a
> disagreement rate as a ratio**; the two are different quantities and grader
> noise largely cancels in a paired contrast (the final graded string is
> identical across arms on 74% of gemma-4's paired problems).

Same edit in `results.tex` §R3 ("clears it by $3.9\times$") and
`limitations.tex` ("by $3.9\times$").

## SERIOUS-5. Two of three P4 DiDs cannot detect any plausible interaction

**Attack 7.** A10 says the preregistered primary is null and should stay
visible. Correct — but "null" needs its MDE attached, and the three DiDs are
not comparable:

| DiD pair | n | observed | MDE @80% | can it see a plausible interaction? |
|---|---|---|---|---|
| gpt-oss − gemma-4 | 1600 | +0.0175 | **0.0325** | marginally — yes at 0.040 |
| Llama − gemma-4 | 400 | +0.0300 | **0.0693** | **no** |
| Llama − gpt-oss | 400 | +0.0150 | **0.0748** | **no** |

The largest per-actor C−A main effect is |−0.0225|, so a true interaction is
plausibly ≤0.040. The two Llama DiDs cannot detect that; they would need
n≈2,134 and n≈2,490 paired problems to reach 80% power at 0.030, against 400
available. **Only one of the three DiDs is an informative null.**

`experiments.tex` already says "a null on P4 means 'no large interaction
detected', not 'no interaction'" — good, but it does not say the two Llama
contrasts cannot detect a *medium* one either.

**Required change — A10, replace:**
> "All three pairwise difference-in-differences contain zero. Keep visible."

**with:**
> All three pairwise difference-in-differences contain zero. Only the
> gpt-oss−gemma-4 contrast (n=1,600, MDE 0.033 at 80% power) is an informative
> null against an interaction of the size the main effects make plausible
> (≤0.040). The two Llama contrasts (n=400, MDE 0.069 and 0.075) **cannot
> detect an interaction of any plausible size** and are reported as
> uninformative rather than as evidence of absence.

---

# COSMETIC / NO CHANGE REQUIRED

## Attack 2 — bootstrap clustering unit: no conclusion changes

The resampling unit is **correct** for the headline contrasts. Resampling a
paired difference vector *is* a problem-level cluster bootstrap when both arms
of a problem move together, which they do. Explicit cluster bootstraps
reproduce every published interval to within 0.0006.

Two places resample arms *independently* and are technically wrong:
`FINAL_TABLES.py` T3 (recovery CI) and T14 (P4 DiD). I recomputed both with a
proper problem-level cluster bootstrap. **Width changes by a factor of
0.91–1.10 and not one significance verdict flips.** PC4 explains why the error
is benign: with a shared problem-level effect the clustered interval is
*narrower* than the unpaired one, so ignoring the pairing is conservative here,
not anti-conservative.

Worth a one-line fix in the code for correctness; **not worth a paper change**,
and not a finding a reviewer can use against you.

## Attack 6 — post-treatment conditioning: labelling is sufficient, with one exception

I screened every conditioning variable by AUC(arm | variable) among
first-pass-wrong. `cycles/submissions used` (AUC 0.87–0.99) and `reviewer never
declines` (0.80–0.96) are near-deterministic in the arm. **But the paper
reports these as rates *by arm*, which is a description of the treatment and is
legitimate.** It does not condition on them and compare arms inside, which
would be vacuous. T16 is the one place that conditions on unanimity, and it is
honest about the empty cells (gemma Arm A has 0 unanimous trajectories of 316;
the table prints `nan` rather than a number).

**Nothing in the mechanism section needs to be cut** except the T22 figures
covered in SERIOUS-3. The "descriptive, associational, never causal" labelling
is doing real work and is sufficient elsewhere.

## A5's "rubber-stamping is a SYMPTOM, not a root cause" hedge is correct and should stay

## F18 scoring defect: verified conservative

Recoding the 54 under-credited trajectories moves gemma's paired McNemar from
37 vs 3 (p=1.9e-08) to **47 vs 3 (p=3.7e-11)**. The defect runs against the
claim, as `limitations.tex` states. Confirmed.

---

# How hard I tried to break the gemma-4 result, and what happened

This was the main target. I could not break it. Six independent attacks:

**1. Is the marginal recovery contrast even identified?** For gemma-4,
`d_fp = +0.000000` **exactly** (0.802500 vs 0.802500). Since
`d_final = d_fp·(1−rec_A) + (1−fp_B)·d_rec` holds as an identity, and the
first term vanishes, **gemma-4's recovery contrast is an exact
reparameterisation of the intention-to-treat effect**: −0.1709 × (1−0.8025) =
−0.0338 = the observed ITT, to four decimals, residual +0.0000. A quantity
algebraically equal to a non-post-treatment estimand cannot be a
post-treatment-conditioning artifact. **This is the strongest single defence
the paper has and it is not currently stated.** (The two first-pass-wrong sets
are equal in size but differ in membership — 237 shared of 316 each — so
"coincidentally equal" is the right phrase; the algebra needs only the means
to be equal, which they are.) *This defence does not extend to gpt-oss
(d_fp=+0.053) or Llama (+0.008)* — for those two the recovery contrast is not
pinned by the ITT and remains genuinely post-treatment.

**2. Selection story S1 — arm-independent repair probability.** If each problem
has a latent repair probability not depending on arm, discordance is
exchangeable and McNemar tests exactly that. Simulating the
variance-maximising member of S1 at the observed pooled rate: **P(|diff| ≥ 34)
= 0 in 200,000 draws.** Any selection story must make repair probability
arm-dependent, which *is* the effect.

**3. Selection story S3 — recovery is a grader flip, not a repair.** Two
independent refutations. (a) **Wrong sign**: Arm B gets 5.80 grader draws per
first-pass-wrong trajectory against Arm A's 1.54, so more noise-recoveries
should accrue to *B*, and B recovers *less*. (b) **Wrong mechanism**: a
noise-recovery requires the answer to be unchanged. **All 37 A-only recoveries
changed their answer; 37/37.** All 3 B-only recoveries did not change theirs;
0/3. Quantitatively, noise can manufacture ~1.2 of Arm A's 70 recoveries (1.7%)
but ~10.9 of Arm B's 16 (68%). **The noise story, taken seriously, makes the
gap wider.**

**4. Selection story S2′ — differential error depth.** The best remaining
story: the paired stratum could contain shallow Arm A errors and deep Arm B
ones, so A recovers more with no difference in repair *ability*. I killed this
by restricting to the **94 paired problems where both arms' first wrong answer
is the byte-identical string** — error depth held exactly constant by
construction. **13 A-only vs 0 B-only, p=2.4e-04.** On the complement (143
problems, different starting errors): 24 vs 3, p=4.9e-05. Both halves hold.

**5. Draw-count confound.** Restricting to the 236 pairs where Arm A got no
more grader draws than Arm B: **37 vs 2, p=2.8e-09.** The confound runs against
the result. Within the identical-starting-error subset, the 13 A-only
recoveries averaged 2.31 draws — Arm A recovers more with fewer chances.

**6. Multiplicity.** Bonferroni over all 38 CIs in the frozen output:
p=7.4e-07.

**Verdict: the gemma-4 recovery result is the most robust thing in the paper.**
It survives every attack I could construct, and two of them (noise, F18) make
it stronger. I recommend adding the ITT-reparameterisation argument (attack 1)
to §R3 — it converts the headline from "a post-treatment conditional we label
honestly" to "algebraically equal to the randomised contrast," which is a
categorically stronger position and costs nothing.

**Suggested addition to `results.tex` §R3:**
> For gemma-4 the first-pass rates are identical to four decimals
> ($0.8025$ in both arms), so the recovery contrast is an exact
> reparameterisation of the intention-to-treat effect:
> $-0.1709 \times (1-0.8025) = -0.0338$, the observed B$-$A final-accuracy
> difference. For this actor the recovery decomposition therefore carries no
> post-treatment selection beyond that already present in the randomised
> contrast. **This does not extend to gpt-oss**, whose first-pass rates differ
> by $+0.050$.

---

# Summary table

| # | finding | severity | claim affected |
|---|---|---|---|
| F1 | Arm C recovery denominator excludes 178 recorded first-pass-wrong rows; 2 of 3 paired p-values lost | **FATAL** | A6, results.tex §R5 |
| S1 | "P1–P5 carry a Holm correction" is false of the reported analysis | SERIOUS | method.tex:63, results.tex:6 |
| S2 | "Floor effect" for Llama falsified by the paper's own Arm C | SERIOUS | A3, results.tex §R3, limitations |
| S3 | T22 pooled quartiles are arm indicators; n=12 cell quoted; context measure hit by F13 | SERIOUS | results.tex §R4 |
| S4 | Effect-size ÷ disagreement-rate is not a valid operation | SERIOUS | A8, results.tex §R3, limitations |
| S5 | 2 of 3 P4 DiDs cannot detect any plausible interaction | SERIOUS | A10, experiments.tex |
| — | bootstrap clustering unit | COSMETIC | none — no verdict changes |
| — | post-treatment labelling elsewhere | COSMETIC | none — labelling is sufficient |
| — | gemma-4 headline | **SURVIVES 6 ATTACKS** | strengthen A3 with the ITT identity |
