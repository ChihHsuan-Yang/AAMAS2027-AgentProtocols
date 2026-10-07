# S.20 Final report — Bf control: does the role-structured recovery advantage
# survive when the role-free team actually receives the same correctness signal?

**STATUS: COMPLETE — all sections A-J.** The endpoint-drift bridge (H)
returned DRIFT VERDICT: NONE on 400/400 rows; it bounds campaign drift as a
sensitivity check, is never pooled, and does not change the verdict in I.

This file was assembled incrementally so that the parts which had to be fixed
*before* seeing results (method, delivery proof, decision rule, claim
catalogue) were on disk and timestamped ahead of the parts that depend on them.
Sections A-D, G and the claim catalogue in J were written while blind to every
Bf outcome; E, F, I and the J labels were added afterwards.

---

## A. What was verified, and what remains hypothesis

The collaborator's report (`BF_CONTROL.md`, email) was treated as a hypothesis
and tested independently.

**CONFIRMED at byte level.** Arm B's prompts never contained the evaluator's
FAIL verdict or repair hint:

- All 9,600 frozen Omni rows and 2,296 frozen SciBench rows **declare**
  `visibility_policy = ['problem','shared_history','advice']` for arm B.
- `B_GENERIC_PREPEND` has no `${advice}` slot; `build_messages()` never passes
  advice to arm B; `shared_history` only ever receives Planner/Executor/
  Reviewer turns.
- Realized bytes: **2,523 / 2,523** frozen Arm B prompts reconstructed and
  hash-verified against their logged `prompt_sha256_12`; **0** contain
  `"Evaluator feedback: FAIL"`.

Branch SHAs recorded; **no branches merged** (S.19).

Full detail: `BF_S3_PROVENANCE.md`.

## B. The provenance defect, reported separately from the experimental result

S.3 requires this to be documented as its own defect. It is.

| | |
|---|---|
| DECLARED | `['problem','shared_history','advice']` for arms A, B **and** C |
| ACTUAL (B) | `problem` + `shared_history`. No advice slot exists in the template. |
| ACTUAL (C) | has `${advice}` but **no** `${shared_history}` |
| IMPACT | the field is false in **opposite directions** for B and C |

Second-order finding: **3,200 arm-C rows shipped with the wrong string despite
the C fix predating this work by a week** — the constant was corrected without
re-emitting the rows that had already been written with the old value. A
provenance field that disagrees with the realized prompts is worse than an
absent one, because downstream readers trust it.

Full detail: `BF_S3_PROVENANCE.md`.

## C. The Bf design, and what it does and does not hold constant

Validated against S.4's five requirements:

| requirement | status |
|---|---|
| pre-FAIL byte-identical to B | VERIFIED on realized data, **2174/2174** |
| post-FAIL: same string as A's `${advice}`, exactly once | VERIFIED |
| one-cycle lifetime | VERIFIED (see G) |
| consumes no history slot | VERIFIED on realized data, **1650 prompts, 0 displaced** |
| changes nothing else | VERIFIED |

The pre-FAIL identity is measured, not argued. Comparing the logged
`prompt_sha256_12` of the first planner turn — same problem, no feedback yet:

| | Bf vs frozen **B** | Bf vs frozen **A** |
|---|---:|---:|
| Omni | **1600/1600 identical** | 0/1600 |
| SciBench | **574/574 identical** | 0/574 |

The A column is the discriminating control: it must be 0, or the match against
B would be consistent with a hash that ignores the template. Bf is the
role-free prompt and nothing else, until a FAIL arrives.

"Consumes no history slot" is likewise measured. The shared-history window
keeps the last 8 agent turns; if the `[Evaluator]` block displaced one, a Bf
prompt would carry fewer agent turns than its window depth. Counting
`[Planner]`/`[Executor]`/`[Reviewer]` headers inside each hash-verified
realized prompt:

```
hash-verified prompts checked  : 1650
agent-turn count != window size: 0     (must be 0)
max window depth observed      : 8     (the cap)
```

The window is observed **saturated at 8 with the evaluator block present**, so
the check exercises the case where displacement would actually occur rather
than only shallow prompts. The block is additive.

**S.6, stated explicitly as the directive requires: A and Bf prompts are NOT
otherwise semantically identical after a FAIL.** Of 241 uids that first-fail in
both frozen A and Bf, only **15 (6.2%)** have a byte-identical first hint. A
and Bf share the evaluator and its prompt; they do not share the realized
string, because the evaluator is sampled per trajectory. Any reading of the Bf
result must carry this caveat.

## D. Delivery actually happened — live gates, both domains

Each domain audited with **its own** runner, problem loader and prompt objects
(S.17: the Omni fix does not prove SciBench delivery).

| | Omni Bf | SciBench Bf |
|---|---:|---:|
| trajectories | 1600 | 574 |
| realized prompts hash-verified | **7608/7608** | **3129/3129** |
| prompts carrying feedback | 2154 | 1071 |
| feedback appearing >1x | 0 | 0 |
| feedback before first FAIL | 0 | 0 |
| metadata flag disagrees with bytes | 0 | 0 |
| generic append altered | 0 | 0 |
| first-FAIL trajectories | 302 | 124 |
| of those, delivered | **302/302** | **124/124** |
| **GATE** | **PASS** | **PASS** |

Both gates were positive-controlled: every must-be-zero counter was shown to
fire on a planted defect, so neither PASS is vacuous.

Disclosure (gold answer appearing in the evaluator block) is **reported, not
gated**, because it is a property of the shared evaluator rather than of
delivery — frozen Arm A discloses at 2.85% on the matched cell, so gating on
zero would fail the paper's own published arm:

| cell | first-FAIL rows | disclosed | rate |
|---|---:|---:|---:|
| frozen A — delivered | 316 | 9 | 2.85% |
| frozen B — withheld | 316 | 5 | 1.58% |
| Bf — delivered | 302 | 4 | 1.32% |

Fisher A vs Bf p = 0.2634. Bf is **not** elevated.

Full detail: `BF_OMNI_LIVE_GATE.md`, `BF_S17_SCIBENCH_LIVE_GATE.md`,
`BF_HINT_DISCLOSURE.md`.

## E. Results per domain — (A) through (E)

Reported **separately per domain, never pooled** (S.14). All three conditions
shown side by side. **These are associations between experimental conditions,
not causal mediators** (S.14).

### (A) First-pass accuracy — the pre-feedback check

| domain | A | B | Bf |
|---|---:|---:|---:|
| Omni-MATH (n=1600) | 1284/1600 = 0.8025 | 1284/1600 = 0.8025 | 1298/1600 = 0.8113 |
| SciBench (n=574) | 456/574 = 0.7944 | 456/574 = 0.7944 | 450/574 = 0.7840 |

A and B are identical by construction (byte-identical prefixes before the first
verdict). Bf differs from both only by sampling noise — it is byte-identical to
B pre-FAIL on realized data (1600/1600 and 574/574, with Bf≠A 0/1600 and 0/574
as the discriminating control, section C). Bf is +0.9 pt on Omni and −1.0 pt on
SciBench, in opposite directions: **the feedback manipulation does not act
before the first verdict**, as designed.

### (B) Recovery denominators (first evaluator verdict incorrect)

| domain | A | B | Bf |
|---|---:|---:|---:|
| Omni-MATH | 316 | 316 | 302 |
| SciBench | 118 | 118 | 124 |

A and B share a denominator because they share their first pass. Bf's differs
because it is a separate sampling of the same prefix — which is why the paired
analysis in (D), not the marginal rates in (C), carries the inference.

### (C) Marginal recovery rates, Wilson 95% CI

| domain | arm | recovered | rate | 95% CI |
|---|---|---:|---:|---|
| Omni-MATH | A | 70/316 | 0.2215 | [0.1792, 0.2705] |
| Omni-MATH | B | 16/316 | 0.0506 | [0.0314, 0.0807] |
| Omni-MATH | **Bf** | **177/302** | **0.5861** | **[0.5298, 0.6402]** |
| SciBench | A | 30/118 | 0.2542 | [0.1843, 0.3397] |
| SciBench | B | 6/118 | 0.0508 | [0.0235, 0.1065] |
| SciBench | **Bf** | **54/124** | **0.4355** | **[0.3515, 0.5234]** |

In both domains the Bf interval lies **entirely above** both the A and the B
interval. The A and B intervals are disjoint in both domains (the frozen
contrast, reproduced).

### (D) Paired discordant counts, exact McNemar

Each pair is restricted to problems first-pass-wrong under **both** arms of
that pair, so each row has its own n.

| domain | contrast | n | rate (first arm) | rate (second) | only 1st | only 2nd | exact McNemar p |
|---|---|---:|---:|---:|---:|---:|---:|
| Omni-MATH | A vs B | 237 | 38/237 = 0.1603 | 4/237 = 0.0169 | 37 | 3 | 1.95e-08 |
| Omni-MATH | **A vs Bf** | 241 | 39/241 = 0.1618 | **127/241 = 0.5270** | 7 | **95** | **7.85e-21** |
| Omni-MATH | Bf vs B | 255 | 138/255 = 0.5412 | 5/255 = 0.0196 | 135 | 2 | 1.09e-37 |
| SciBench | A vs B | 99 | 21/99 = 0.2121 | 2/99 = 0.0202 | 21 | 2 | 6.6e-05 |
| SciBench | **A vs Bf** | 100 | 22/100 = 0.2200 | **33/100 = 0.3300** | 8 | **19** | **0.0522** |
| SciBench | Bf vs B | 114 | 46/114 = 0.4035 | 4/114 = 0.0351 | 43 | 1 | 5.12e-12 |

### (E) Final accuracy (never-judged counts as incorrect), paired on all problems

| domain | A | B | Bf |
|---|---:|---:|---:|
| Omni-MATH | 1354/1600 = 0.8462 | 1300/1600 = 0.8125 | **1475/1600 = 0.9219** |
| SciBench | 486/574 = 0.8467 | 462/574 = 0.8049 | **504/574 = 0.8780** |

Paired on the full problem set (no conditioning):

| domain | contrast | only 1st | only 2nd | delta | exact McNemar p |
|---|---|---:|---:|---:|---:|
| Omni-MATH | A vs Bf | 18 | 139 | +0.0756 (Bf−A) | 2.39e-24 |
| SciBench | A vs Bf | 11 | 29 | +0.0314 (Bf−A) | 0.00643 |

On the unconditioned endpoint, Bf beats A significantly in **both** domains,
including SciBench where the recovery-conditioned contrast does not resolve.

### Cycle usage on first-pass-wrong trajectories (context, not an endpoint)

| domain | arm | cycles | submissions | revisions | never declines | one answer |
|---|---|---:|---:|---:|---:|---:|
| Omni-MATH | A | 5.52 | 1.54 | 3.98 | 0.051 | 0.288 |
| Omni-MATH | B | 5.83 | 5.80 | 0.03 | 0.981 | 0.845 |
| Omni-MATH | Bf | 4.08 | 3.21 | 0.87 | 0.530 | 0.066 |
| SciBench | A | 5.36 | 1.97 | 3.39 | 0.042 | 0.076 |
| SciBench | B | 5.84 | 5.84 | 0.00 | 1.000 | 0.932 |
| SciBench | Bf | 4.78 | 3.67 | 1.11 | 0.371 | 0.089 |

Bf sits **between** A and B on revision behaviour while **exceeding both** on
recovery. It is not simply "A without the role labels": it resubmits more than
A and revises less, yet recovers more than either. The B column's 0.981/1.000
"never declines" is the behavioural signature of the defect — a team never told
it was wrong almost never withdraws its answer.

### Robustness: are Bf "recoveries" real answer changes?

Recovery is defined as *first verdict wrong AND final grade correct*, so a
trajectory could in principle "recover" without changing its answer, if a
stochastic evaluator simply re-graded the same string differently. That would
inflate Bf. Checked directly by comparing the graded candidate string on the
first vs last evaluator call of every recovering trajectory:

| domain | arm | recoveries | answer changed | fraction | answer unchanged |
|---|---|---:|---:|---:|---:|
| Omni-MATH | A | 70 | 70 | 1.000 | 0 |
| Omni-MATH | B | 16 | 9 | 0.562 | 7 |
| Omni-MATH | **Bf** | 177 | 174 | **0.983** | 3 |
| SciBench | A | 30 | 30 | 1.000 | 0 |
| SciBench | B | 6 | 0 | 0.000 | 6 |
| SciBench | **Bf** | 54 | 50 | **0.926** | 4 |

Bf recoveries are genuine answer revisions at essentially the same rate as A
(0.983 and 0.926 vs 1.000). The artifact this check was looking for is present
instead in **arm B**, where 7/16 (Omni) and 6/6 (SciBench) of the few
"recoveries" involve no answer change at all — consistent with a team that was
never told it was wrong and never revised. Removing those non-revising rows
would *lower* B further and widen the Bf-vs-B gap, so the verdict is not an
artifact of this definition. Reported, not applied: the recovery definition is
the paper's own and was not altered.

## F. Three-way decomposition old B -> Bf -> structured

Measured on the **paired** scale, each step on its own paired set (the three
n's differ and the steps are therefore not additive — this is reported as three
contrasts, not a partition of one gap):

### Omni-MATH

| step | from | to | change | paired n | exact McNemar p |
|---|---:|---:|---:|---:|---:|
| old B → Bf (deliver the feedback) | 0.0196 | 0.5412 | **+0.5216** | 255 | 1.09e-37 |
| Bf → structured A (add the roles) | 0.5270 | 0.1618 | **−0.3651** | 241 | 7.85e-21 |
| old B → structured A (the frozen contrast) | 0.0169 | 0.1603 | +0.1435 | 237 | 1.95e-08 |

### SciBench

| step | from | to | change | paired n | exact McNemar p |
|---|---:|---:|---:|---:|---:|
| old B → Bf (deliver the feedback) | 0.0351 | 0.4035 | **+0.3684** | 114 | 5.12e-12 |
| Bf → structured A (add the roles) | 0.3300 | 0.2200 | **−0.1100** | 100 | 0.0522 |
| old B → structured A (the frozen contrast) | 0.0202 | 0.2121 | +0.1919 | 99 | 6.6e-05 |

**Reading.** The first step — merely delivering the evaluator signal to the
role-free team, changing nothing else — moves recovery by **+0.52 (Omni)** and
**+0.37 (SciBench)**, i.e. **3.6x and 1.9x the entire frozen A-vs-B gap** it was
meant to explain. The second step, adding the role structure on top, is
**negative in both domains**. The role-free team given the same correctness
signal does not merely close the gap; it overshoots A.

Per S.15, this is not forced into a binary narrative and no secondary metric is
used to rescue a null: the decomposition is reported as measured, including the
sign reversal on the second step, and SciBench's unresolved p=0.0522 is reported
as unresolved rather than read as a null or as a win.

## G. Pre-registered decision rule and instrument audits

Everything in this section was fixed **while blind to every Bf outcome**.

**`bf_verdict.py`** — 9 adversarial controls; three defects found and repaired
while blind, including a declared parameter (`ab`, the frozen A-vs-B premise)
that was accepted and never read, and one domain's reference gap hardcoded as
the default for both. Per-domain floors, independently re-derived in this
report's S.13 check:

| domain | A | B | gap | floor (1/3) |
|---|---|---|---|---|
| Omni-MATH | 70/316 = 0.2215 | 16/316 = 0.0506 | 0.1709 | 0.0570 |
| SciBench | 30/118 = 0.2542 | 6/118 = 0.0508 | 0.2034 | 0.0678 |

**S.13 gate — `bf_control.py` must reproduce the frozen paper numbers, or STOP.**
Both domains PASS, evaluated on the full frozen cells, by importing the
script's own functions rather than reimplementing them:

| domain | required | reproduced |
|---|---|---|
| Omni | 70/316 vs 16/316; paired 37 vs 3, n=237 | all exact (p = 1.95e-08) |
| SciBench | 30/118 vs 6/118; paired 21 vs 2, n=99 | all exact (p = 6.6e-05) |

**S.11 infra policy** was fixed in six points while both cells had **zero**
infra failures, and the drop path was proven to bind (1600 -> 1593 on 7 planted
rows) so the policy is not inert. Final accounting: **0 infra-failure rows in
either cell.**

**S.5 unit test**: `test_bf_delivery.py` passes 16/16 and 6 of 7 planted
defects are detected. It does **not** cover the one-cycle lifetime in either
runner — the shipped stub is FAIL-then-PASS and ends before a cycle in which
persistence could appear. That property is instead evidenced on realized data:
re-running the Omni gate with a reconstruction that *persists* the feedback
drops hash verification from **7608/7608 to 6516/7608**, so the clean match is
a positive measurement of the lifetime, not an assumption. The test was not
weakened, and no planted failure was committed.

Full detail: `BF_VERDICT_CONTROLS.md`, `BF_S13_GATE.md`, `BF_S11_INFRA_POLICY.md`,
`BF_S5_UNIT_TEST_AUDIT.md`, `BF_FIELD_READ_AUDIT.md`.

## H. Endpoint-drift bridge

**COMPLETE.** Fresh Arm A n=400 against the frozen Arm A rows on the same 400
problems, run by the campaign orchestrator (not launched by hand; S.7). 400/400
rows, 0 infra failures, 0 duplicate uids, `arms = ['A']`.

**DRIFT VERDICT: NONE** — "no detectable drift, and the CIs exclude drift
≥ 0.05."

| endpoint | frozen | bridge | paired delta | 95% CI | p |
|---|---|---|---:|---|---:|
| first-pass | 318/400 = 0.7950 | 320/400 = 0.8000 | +0.0050 | [−0.0244, +0.0344] | 0.868 |
| final | 330/400 = 0.8250 | 338/400 = 0.8450 | +0.0200 | [−0.0068, +0.0468] | 0.200 |
| recovery (unpaired) | 12/82 = 0.1463 | 18/80 = 0.2250 | +0.0787 | [−0.0419, +0.1980] | CI includes 0 |

### The bridge number is re-run-sensitive (found at handoff)

`run_bf.sh` defaults to `TAG=${TAG:-gemma4}` and writes a fixed filename, so it
was run twice into the same three paths ~13 h apart. The current bytes
(**chain 2**, the ones analysed above and frozen) overwrote an earlier pass
(**chain 1**), which survives only as `experiments/results/bf/MANIFEST_BF.json`
— its rows are gone and cannot be re-analysed.

The two Bf cells differ by ≤1 trajectory between chains, so the headline
Bf-vs-A and Bf-vs-B contrasts in §D/§E are insensitive to this. **The bridge is
not**: chain 2 gives 338/400 (delta **+0.0200** vs the frozen 330/400), chain 1
implies 327/400 (delta **−0.0075**). The point estimate changes sign. Both are
small and both fall inside the CI reported above, so `NONE` is unlikely to
flip — but the drift estimate is demonstrably re-run-sensitive at n=400, which
is a second reason (alongside the `bounded`-predicate defect in §I) to read
`NONE` as weak evidence rather than a certificate. Re-running would yield a
third chain, not a reconciliation. Full account: `BF_DATA_CUSTODY.md`.

### NONE was predicted to be unreachable. Why it was returned anyway

`BF_DRIFT_POWER.md`, written before any bridge row existed, predicted that at
n=400 the `NONE` branch was essentially unreachable and that a clean bridge
would report SMALL(underpowered). It returned NONE. **The prediction was wrong,
and the reason is a mis-specified null, not a change to the instrument.**

That power note assumed ~27% discordance, which is what you get when the two
arms are drawn *independently* at the marginal rate (2p(1−p) ≈ 0.27 at
p ≈ 0.82). Two re-runs of the same system on the same problem are positively
correlated, not independent. Realized discordance is **36/400 = 9.0%**
(first-pass) and **30/400 = 7.5%** (final), so the paired CI half-width is
≈0.029 rather than ≈0.05, and the branch is reachable.

The prediction understated power. It did not bias the label: re-running the
rule at the *assumed* 27% discordance while holding the observed point
estimates fixed gives CIs of [−0.0459, +0.0559] and [−0.0309, +0.0709] — i.e.
SMALL, exactly as predicted. The threshold was never moved; the data were
simply more reproducible than the null model allowed for. `bf_drift.py` is
unmodified, and MATERIAL_DELTA = 0.05 and ALPHA = 0.05 are the values fixed
before the run.

### NONE positive-controlled on the real file

A verdict of "no drift" is exactly the result that must be proven non-vacuous
(S.5's rule, applied here). Drift of known size was planted into the actual 400
bridge rows and the label was required to move:

| planted | total final delta | verdict |
|---:|---:|---|
| +0 (unmodified) | +0.0200 | **NONE** |
| +2 rows (+0.0050) | +0.0250 | SMALL |
| +4 rows (+0.0100) | +0.0300 | **MATERIAL** |
| +12 rows (+0.0300) | +0.0500 | **MATERIAL** |
| +32 rows (+0.0800) | +0.1000 | **MATERIAL** |
| −32 rows (−0.0800) | −0.0600 | **MATERIAL** |

The instrument is responsive on this file in both directions and NONE is not a
default. The four saved pre-run control worlds re-run clean as well
(null→NONE, small→SMALL, material→MATERIAL).

Note that MATERIAL fires at a *total* final delta of +0.0300, below the stated
0.05 floor. That is the **recovery** channel crossing first: at +4 planted rows
the recovery CI becomes [+0.0027, +0.2511] and `rec_big` fires. This makes the
rule stricter than its headline threshold, not laxer, so it does not weaken a
NONE.

### What NONE does and does not certify

Read the branch, not the word. The `bounded` test is:

```python
bounded = (abs(fp_lo) < MATERIAL_DELTA and abs(fp_hi) < MATERIAL_DELTA
           and abs(fi_lo) < MATERIAL_DELTA and abs(fi_hi) < MATERIAL_DELTA)
```

It constrains **first-pass and final accuracy only**. The recovery CI is not
required to be bounded for NONE to be returned, and here it is not bounded:
[−0.0419, +0.1980] against a 0.05 floor.

**Recovery is this report's primary endpoint.** So, stated precisely:

- Drift in first-pass and final accuracy is **excluded** below 0.05.
- Drift in recovery rate is **not resolved** at n=400. Point estimate +0.0787,
  upper bound +0.1980.

This is a limitation of the bridge as specified, found by reading the branch
that fired rather than its label. It is reported, not repaired: changing the
`bounded` test after seeing the result would be choosing the rule from the
data.

### The unresolved recovery drift cannot overturn the S.15 verdict

Bf is a fresh run and A/B are frozen, so any positive endpoint drift inflates
Bf. The conservative correction therefore *subtracts* the drift from every Bf
margin. Pushed through the unmodified `bf_verdict.verdict()`:

| correction | Omni A-vs-Bf | Omni Bf-vs-B | Sci A-vs-Bf | Sci Bf-vs-B | both domains |
|---|---:|---:|---:|---:|---|
| none (observed) | −0.3651 | +0.5216 | −0.1100 | +0.3684 | FEEDBACK DELIVERY EXPLAINS ORIGINAL GAP |
| point +0.0787 | −0.2864 | +0.4429 | −0.0313 | +0.2897 | FEEDBACK DELIVERY EXPLAINS ORIGINAL GAP |
| worst case +0.1980 | −0.1671 | +0.3236 | +0.0880 | +0.1704 | FEEDBACK DELIVERY EXPLAINS ORIGINAL GAP |

The label is unchanged at every level, and so is the branch that produces it
(Omni `bf_beats_a`; SciBench `bf_wins and a_null`). Worth stating plainly: at
the worst case SciBench's A-vs-Bf margin **changes sign** (−0.1100 → +0.0880),
so under maximal assumed drift Arm A nominally leads Bf — but +0.0880 is still
inside what that domain's p = 0.0522 leaves undetermined, the `a_null` branch
still holds, and Bf-vs-B at +0.1704 still clears the 0.0678 floor by 2.5×. The
conclusion does not rest on the unresolved channel.

### Prompt identity and non-pooling

Arm A first-planner prompt sha is **identical on 400/400** paired problems. The
`config_version` differs (bridge `25a04a554afcd006` vs frozen
`e3afa39849c1b980`) because that field is a global hash over all prompts and
the whole VISIBILITY dict, and the Bf entry was added to it; Arm A's realized
bytes are unchanged. This is the same provenance-field hazard documented in
section B, in a benign direction.

The bridge is **not pooled** into any results table (S.16). It is frozen
alongside the Bf cells in `FROZEN_BF` — permissible because `bf_freeze.cell()`
records `"arms"` per cell, so the bridge self-labels `["A"]` and cannot be
misread as Bf data.

Full detail: `BF_DRIFT_POWER.md` (pre-run), this section (post-run).

## I. Verdict

Produced by calling the pre-registered `bf_verdict.verdict()` (section G) once
per domain with the measured contrasts and that domain's own reference gap —
**not** read off by eye.

# **FEEDBACK DELIVERY EXPLAINS ORIGINAL GAP**

Both domains return this label. They reach it by **different branches**, which
must be reported, not just the shared label:

| domain | branch taken | reason returned by the rule |
|---|---|---|
| Omni-MATH | `bf_beats_a` | "feedback delivery OVERSHOOTS: Bf beats A by +0.365 (p=7.85e-21) and Bf beats B by +0.522. The A-vs-B recovery gap cannot be a role effect. **FLAG FOR REVIEW: this reverses the original direction and is not a case the paper anticipates.**" |
| SciBench | `bf_wins and a_null` | "Bf beats B by +0.368 (p=5.12e-12) while A vs Bf is unresolved (p=0.0522)" |

The verdict is **not** BOTH CONTRIBUTE, so the S.20 margin-to-floor disclosure
for BOTH does not apply. The relevant threshold disclosures for the label that
did fire:

* **Omni-MATH is not threshold-marginal.** Floor = 0.0570; the A-vs-Bf margin
  is −0.3651, which clears the floor in the overshoot direction by 0.3081,
  at p = 7.85e-21.
* **SciBench is threshold-marginal on p, but the label is not.** Its A-vs-Bf
  p = 0.0522 sits 0.0022 above ALPHA = 0.05. This was tested rather than
  asserted: re-running the rule with p nudged to 0.0499 returns **the same
  label**, switching only the branch (`a_null` → `bf_beats_a`) and therefore
  only the strength of the wording. The SciBench margin (−0.1100) already
  exceeds its floor (0.0678) in the overshoot direction by 0.0422, so the
  alpha crossing changes how emphatically the label is stated, not which label
  it is.
* Both domains are driven by the **Bf-vs-B** contrast, which is overwhelming in
  each (p = 1.09e-37 and 5.12e-12) and far above each floor.

### Mandatory caveats carried with this verdict

1. **S.6, verbatim: do not claim that A and Bf prompts are otherwise
   semantically identical after FAIL. They are not.** Of 241 uids that
   first-fail in both frozen A and Bf, only 15 (6.2%) have a byte-identical
   first hint. A and Bf share the evaluator and its prompt, not the realized
   string, because the evaluator is sampled per trajectory. The comparison is
   "same channel, same construction, independently sampled text", not "same
   bytes".
2. **S.14: these are not causal mediators.** The decomposition in F is three
   measured contrasts on three different paired sets, not a mediation model.
3. **Bf is not a drop-in replacement for B in the paper's design.** It differs
   from frozen B by exactly one thing (the delivered block) but was collected in
   a later campaign; its `config_version` differs and it must never be pooled
   with the frozen campaign (S.12).
4. The endpoint-drift bridge (H) bounds how much of any A-vs-Bf difference
   could be campaign drift rather than condition. It returned **NONE** — a
   branch the pre-run power note predicted was unreachable at n=400, because
   that note assumed independent arms and the realized run-to-run discordance
   is ~9%, not ~27%. NONE here certifies first-pass and final accuracy only;
   **recovery drift is not resolved at n=400** (point +0.0787, upper bound
   +0.1980). Correcting every Bf margin by that upper bound leaves the verdict
   and both branches unchanged (section H).
5. The verdict is not an artifact of the recovery definition: Bf recoveries are
   genuine answer revisions (0.983 Omni, 0.926 SciBench), essentially matching
   A at 1.000 (section E, robustness check). The non-revising "recoveries" are
   concentrated in arm B, and excluding them would widen the Bf-vs-B gap.

### What this does and does not establish

**Does:** the A-vs-B recovery gap reported in the paper cannot be attributed to
role structure, because a role-free team that is given the same correctness
signal — and nothing else changed — recovers at least as well as the
role-structured team, and in Omni-MATH substantially better.

**Does not:** show that role structure is useless in general. It shows that *on
this benchmark, with this protocol, for the post-feedback recovery endpoint*,
the measured advantage tracked who was told they were wrong, not who had roles.
Arms C/Cp, the role-destruction measurement, and all first-pass results are
untouched by this (section J).

## J. Per-claim exposure

Catalogued and labelled, **not edited** (S.18). The manuscript has not been
modified and no storyline change is proposed here; these are the labels the
measurement supports.

| Location | Quoted fragment | Label |
|---|---|---|
| `paper/main.tex` abstract | "it is neither stopped early nor **given less information**" | **NO LONGER SUPPORTED.** The role-free team was given less information: the evaluator signal never reached its prompts (0 of 9,600 Omni and 2,296 SciBench arm-B prompts carried it). |
| `paper/main.tex` abstract | "**The difference appears only after a team is told its answer is wrong.**" | **NO LONGER SUPPORTED** as a statement about roles. The difference appears after a team is *told*; Bf shows that being told, not having roles, is what moves recovery. |
| `paper/sections/results.tex:131` | "the grid, the agents, the budget, the evaluator and **the hint text are identical by construction**" | **NO LONGER SUPPORTED.** The hint text was *constructed* identically and *delivered* only to A. The clause is the most specific statement of the defect. |
| `paper/sections/intro.tex:50` | "not fewer chances, not early stopping and **not less information**" | **NO LONGER SUPPORTED.** Same claim as the abstract. |
| `paper/sections/intro.tex:43` | "**Once the evaluator tells both teams** their answer is wrong" | **NO LONGER SUPPORTED.** The evaluator told only A. |
| `paper/sections/conclusion.tex:8` | "the difference emerged only once **both teams were told** their answer was wrong" | **NO LONGER SUPPORTED.** |
| the "more oracle verdicts" argument | "every rival explanation ... predicts FEWER verdicts ... and the role-free team draws MORE" | **NEEDS QUALIFICATION.** The verdict *count* is correctly measured and the direction is real. But a verdict drawn and never shown is not information held; count and delivered information came apart precisely here. The count can no longer carry the "not less information" conclusion on its own. |
| `paper/sections/method.tex:14` | "a team that submits more *consumes* more oracle verdicts" | **UNAFFECTED.** A statement about verdict accounting, true regardless of delivery. |
| all first-pass accuracy figures | — | **UNAFFECTED, and positively confirmed.** A and B are byte-identical pre-verdict; Bf reproduces the prefix on realized data (1600/1600, 574/574). |
| role-destruction measurement (own-answer assertion 0.000–0.120 → 0.846–0.976) | — | **UNAFFECTED.** Measured from realized outputs, independent of evaluator delivery. |
| arms C / Cp | — | **UNAFFECTED.** Separate visibility entry, separately corrected 2026-09-28. |
| the *arithmetic* of the A-vs-B contrast (70/316 vs 16/316; paired n=237, 37 vs 3, p=1.95e-08) | — | **SUPPORTED AS WRITTEN.** Every figure reproduces exactly from the frozen files (S.13 gate, both domains PASS). What is in question is the interpretation, not the numbers. |

**Separately from all of the above (S.3):** `visibility_policy` was logged per
trajectory as ground truth and was false for arm B in **11,896 released rows**
(9,600 Omni + 2,296 SciBench). That is a provenance defect in the released
artifact, in the same class as the Arm C entry corrected on 2026-09-28, and it
stands independently of how Bf turned out.

Full catalogue: `BF_CLAIM_EXPOSURE.md`.

---

## Prohibitions observed (S.21)

n unchanged (1600 + 574); no early stopping; no model substituted; evaluator
unaltered; frozen data unmodified and re-verified byte-identical; Bf never
pooled into the frozen campaign; no selective reruns; **no manuscript text
edited**; storyline unchanged; **no branches merged**; nothing published to HF;
no tokens or auth material printed, logged or committed.
