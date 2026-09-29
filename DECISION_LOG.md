# Decision log — AAMAS 2027

## 2026-09-28 17:30 — D1. Third actor: substitute Llama-3.3-70B for gemma-3-27b

**Evidence (live probes by Master, this session):**

| model | result |
|---|---|
| openai/gpt-oss-120b | HTTP 200, 1.9 s |
| google/gemma-4-31B-it | HTTP 200, 0.9 s |
| meta-llama/Llama-3.3-70B-Instruct | HTTP 200, 3.0 s |
| google/gemma-3-27b-it | **HTTP 503 x3** "online but not ready to receive tasks" |

**Decision.** Primary actor panel = `gpt-oss-120b`, `gemma-4-31B-it`,
`Llama-3.3-70B-Instruct`. gemma-3-27b remains a *contingent* fourth if it warms
(INF worker is probing on a 15-min watch).

**Scientific consequence — this is a real cost, recorded honestly.**
gemma3_27b was chosen because it made the **capability-vs-fidelity dissociation**
testable: it is *less capable* than gpt-oss (baseline .425 vs .568) but *more
faithful* (P1a .266 vs .042). That pair is what separates our account from
2608.21747's capability-equalizer account.

Llama-3.3-70B has **no historical PER trajectories**, so its soft-role fidelity
is **unknown until Arm A runs**. The dissociation therefore becomes a
*measured outcome of this experiment* rather than an inherited fact.

**This is not fatal and is arguably cleaner:** Arm A now measures soft-role
fidelity for all three actors on identical problems in one campaign, and the
capability ordering is measured in the same run. The dissociation test becomes
pre-registered rather than retrofitted. But it does mean **we cannot promise in
advance that the panel spans the needed capability/fidelity contrast** — if all
three actors land in the same corner, the discriminating test is weakened and we
must say so.

**Mitigation:** the panel deliberately spans 3 families (OpenAI-OSS / Google /
Meta) and 31B-120B, which maximises the chance of spread. Retain gemma-3-27b in
the manifest so it can be added if the endpoint recovers.

## 2026-09-28 17:25 — D2. Overleaf is near-empty; build locally, sync at the end
Cloned repo contains only a 221-byte main.tex. Manuscript is authored in the
GitHub repo under `paper/` and pushed to Overleaf once it compiles, keeping
experimental code and data out of Overleaf.

## 2026-09-28 17:20 — D3. Do not commit the AAMAS project into the outer `note` repo
A first `git add -A` attempted to stage ~20 embedded repos from the parent
directory and failed. AAMAS2027-AgentProtocols is now its **own** git repo with
its own .gitignore (secrets + parquet + runs excluded).

## 2026-09-28 17:55 — D4. Arm C schema: coerce bare string → single-element array

**Found in the live 6-trajectory smoke, not in dry-run.** One Arm C trajectory
**hard-failed** after 4 consecutive `wrong_type:strategy` rejections. Inspecting
the raw model output: gpt-oss emits `"strategy": "<prose>"` rather than
`["<prose>"]`. The plan content was perfectly good.

**Why this mattered.** Rejecting that measures **JSON-formatting compliance**,
not division of labor. It would have depressed Arm C's completion rate for a
cosmetic reason and biased the arm against the exact hypothesis under test —
a confound of the same family as the retracted E2 v1 metric.

**Fix.** Array-typed fields accept a bare string and coerce it. Every coercion
is recorded as a **soft signal** (`coerced_string_to_array:<field>`) so the rate
is auditable and reportable.

**What was NOT relaxed** — re-verified adversarially after the change:
`additional_property:answer` still rejects, `answer_leak:boxed` still rejects,
`missing_field` still rejects. The load-bearing constraints are untouched.

Replaying the 4 real failures through the fixed validator: 3 now ACCEPTED, 1
still fails only because the stored raw text is truncated at 2000 chars (a log
artifact, not a validator behaviour).

**Standing rule this creates:** a rejection that reflects *formatting* rather
than *role boundary* must be coerced-and-logged, never counted as an
enforcement event. The enforcement rate reported in the paper must be computed
from boundary violations only.

## 2026-09-28 18:15 — D5. Campaign N raised to 1600; ceiling solved by scale, not stratification

**Problem found.** Smoke showed 19/19 correct across all arms. Investigation:
the manifest is representative (baseline acc 0.6126 vs population 0.6121), so
this is small-sample luck — **but** historically on omnimath2:

| stratum | share | can an arm differ? |
|---|---|---|
| solved by all 4 protocols | **73.8%** | no |
| solved by none | 2.9% | no |
| **informative** | **23.3%** | yes |

So at n=400 only **~93 problems** can possibly exhibit an effect. Power for a
moderate main effect: **0.30**. That is a study designed to find nothing.

**Two ways out.**
1. *Stratify* — sample only informative problems. Raises effective n ~4.6x, but
   it conditions on historical outcomes, i.e. **selection on the dependent
   variable**. Would require heavy caveats and invites a fair reviewer attack.
2. *Scale* — sample more problems. Measured throughput (D-H2: 189/142 req/min,
   0% errors) makes this nearly free.

**Decision: scale.** n=1600 gives ~372 informative problems: power **0.82**
moderate / **1.00** large for the main effect, and roughly the n=800 row for the
interaction. Estimated **~4.7 h parallel** at measured rates.

Rejected option 1 because a clean unbiased sample at larger n is strictly better
science than a biased sample with caveats, and the compute is available. The
ceiling stratum will still be **reported** (it is a real property of the
benchmark and bounds any effect), just not selected on.

**Full omnimath2 (n=4181) is also affordable (~12.3 h).** Held as the stretch
option per the deadline-aware policy; will extend if n=1600 completes cleanly
with time in hand.

## 2026-09-28 18:25 — D6. Second Arm C parser bug: LaTeX escapes are invalid JSON

**Found by auditing the smoke's violation breakdown**, not by any agent report.
Arm C showed 41 "formatting/other" violations vs 6 genuine boundary violations,
and **3 hard failures in 9 trajectories**. Decomposition:

| role | constraint | count |
|---|---|---|
| executor | `json_parse_error` | 13 |
| reviewer | `answer_leak:final_answer_phrase` | 6 (genuine) |
| planner | `json_parse_error` | 2 |
| reviewer | `json_parse_error` | 1 |

**Root cause.** The model emits perfectly well-formed JSON containing LaTeX:
`{"derivation": "vertices at $(\pm a, 0, 0)$ ..."}`. In JSON, `\p` is an
**invalid escape**, so `json.loads` rejects it. Same for `\sqrt`, `\frac`,
`\times`. On a *mathematics* benchmark this fires constantly.

**Why it mattered.** These are parser failures, not role-boundary violations.
Counting them would (a) inflate the reported enforcement rate with a bug and
(b) depress Arm C's completion rate for a reason unrelated to division of
labor — biasing the arm against the hypothesis under test. Exactly the D4 error
class, found a second time in a different guise.

**Fix.** On a parse failure, retry once with lone backslashes doubled, which
preserves the LaTeX verbatim in the decoded string. Verified: `\pm`, `\sqrt`,
`\frac`, fenced+LaTeX all parse; and re-verified that
`additional_property:answer`, `answer_leak:boxed`, and `missing_field` **still
reject**. Delivery is permissive; content stays strict.

**Process note.** Both D4 and D6 were invisible to `--dry-run` (stub responses
are well-formed) and only appeared against live models. That is the argument for
running a real smoke before a campaign, and it is why the smoke gates exist.

The 37-row pre-fix smoke is retained as
`results/smoke/smoke_v1_prefix_PREFIX_BUG.jsonl` — **not deleted**, per
[[retraction-is-labelling-not-deletion]]. It must never be pooled with v3.

## 2026-09-28 19:00 — D7. Smoke gates 15/15; MAIN CAMPAIGN LAUNCHED

n=1600 x 3 arms x 2 live actors = **9,600 trajectories**, run-id `main-n1600`,
launched 2026-09-28T23:00:42Z. Authorized by the 15/15 gate pass.

### Two gate-script bugs I found in my own code, both material

**Gate 1 read the wrong field.** `violated_constraint` is nested at
`event['validation_result']['violated_constraint']`, not at the event root. The
flat read reported **0 boundary violations** when there were **5 genuine
`answer_leak:final_answer_phrase` rejections**. I had been one step from
reporting "Arm C never rejects anything — the constraint may not be binding",
which was exactly backwards. Same error class as the E2 v1 metric: a check
inspecting the wrong subject reports a clean result.

**Gate 4 tested the wrong quantity.** It compared *realized mean* actor calls
(A 4.96 vs B 3.78) and failed. But median is **3 in every arm** and the cap is
the shared 30. The mean gap comes from a handful of hard problems triggering
extra rounds — that is **endogenous behaviour we are measuring**, not an
asymmetry we imposed. Equalizing realized calls would have meant suppressing the
dependent variable. Gate redefined to test identical median per-round cost plus
a shared ceiling.

### Hard failures: 2/78 = 2.6%, and the composition matters
One is a **genuine** boundary exhaustion (reviewer kept stating a final answer
across 3 regenerations — Arm C working as designed). One is a residual parse
failure on a 2000-char-truncated executor output. Accepted under a <=5% rule and
logged; the composition is reported, not just the rate.

### Arm C enforcement is real and discriminating
94 validation attempts, 10 rejections, **5 of them boundary**
(`answer_leak:final_answer_phrase`). Separately I planted 4 violations in
realistic shapes — fenced JSON with an answer field, `\boxed` smuggled in prose
*outside* the JSON, a reviewer authoring an answer field, a reviewer stating
"Final Answer" — and the validator caught **4/4**. The checker can fail, so
zero-rejection cells mean compliance, not a broken check.

## 2026-09-28 19:20 — D8. Campaign STOPPED at 121 rows: max_tokens truncation was confounding Arm C

**Caught by monitoring the live campaign, 121 rows in.** Hard failures were
**8/120 = 6.7%**, above my own 5% gate — and **all 8 were in Arm C**
(7 gpt-oss, 1 gemma-4).

### Root cause
Decomposing Arm C rejections by `(constraint, finish_reason)`:

| count | constraint | finish_reason |
|---|---|---|
| **37** | `json_parse_error` | **length** |
| 12 | `answer_leak:final_answer_phrase` | stop |
| 1 | `json_parse_error` | stop |

**74% of Arm C rejections were the model being cut off at max_tokens
mid-JSON** — not a role-boundary violation.

### The subtle part: truncation is NOT arm-specific, but its COST is
Truncation rate over all role messages: **A 8.4%, B 11.3%, C 8.9%** — no
asymmetry in how often models get cut off. The asymmetry is in consequence:
A and B tolerate a truncated prose message; **Arm C rejects unparseable JSON
and eventually hard-fails.** So Arm C pays a structural penalty for requiring
structured output, and that penalty is confounded with the intervention.

Left alone this would have produced a real-looking "hard enforcement lowers
completion/accuracy" result that was actually a token-budget artifact. Third
instance of the same error class (D4 formatting, D6 LaTeX, D8 truncation): a
delivery-level failure masquerading as an enforcement event.

### Two fixes
1. **Root cause:** `MAX_TOKENS` 4096 -> **8192**.
2. **Belt and braces:** salvage a truncated JSON object by closing open
   strings/arrays/objects; salvage recorded as a soft signal so the rate is
   auditable.

**Re-verified after the change:** a truncated object parses; `answer` field,
`\boxed` leak, and missing field still reject; and a *truncated* planner output
that leaks `\boxed` is **still caught** (`answer_leak:boxed`). Delivery
permissive, boundaries strict.

### Data handling
The 121 pre-fix rows are quarantined as
`results/main/campaign_v1_TRUNCATION_BUG.jsonl` — retained, never pooled.
`config_version` changes with MAX_TOKENS, so pooling is detectable.

### Cost
~28 h ETA at the observed 333 traj/h (the infra worker's 1.2 h projection
assumed 512-token single calls; real PER trajectories run multi-round with
retries). Restarting costs ~20 min of compute and removes a confound that
would have invalidated the central comparison.

## 2026-09-28 19:45 — D9. Mock review found two paper-killing defects. BOTH CONFIRMED by my own measurement.

I did not take the reviewer's word. I re-derived both from code and data.

### DEFECT 1 (confirmed): the manipulation check names a clause Arm C does not enforce

Measured on **accepted** Planner messages (smoke v3 + campaign v1):

| arm / actor | P1a (no computation) | P2 (no answer) | n |
|---|---|---|---|
| A / gemma-4-31B | 0.061 | 0.976 | 82 |
| A / gpt-oss-120b | 0.075 | 0.650 | 80 |
| **C / gemma-4-31B** | **0.275** | **1.000** | 51 |
| **C / gpt-oss-120b** | **0.073** | **1.000** | 41 |

Arm C drives **P2 to exactly 1.000 in both cells** and leaves **P1a at 0.073-0.275**.
`PLANNER_SCHEMA` + `find_answer_leak` forbid `\boxed` and "Final Answer" — that is
**answer authorship**, not computation. Nothing stops a Planner writing `= 1/27`.

My pre-registered check said "Arm C should drive P1a to ~1.0; if not, the arm is
void." **As written, it fails.** Fourth instance of the project's recurring error
class — a check pointed at the wrong subject.

### DEFECT 2 (confirmed): Arm C runs on ~6x less context, while we log that it does not

Mean prompt characters, from real trajectories:

| role | Arm A | Arm B | **Arm C** |
|---|---|---|---|
| planner | 14,186 | 9,026 | **1,530** |
| executor | 17,413 | 10,920 | **2,750** |
| reviewer | 27,155 | 12,228 | **4,520** |

`shared_history` appears **once** in all of prompts.py — in `B_GENERIC_PREPEND`.
The Arm C templates never interpolate it, yet `VISIBILITY["C"]["planner"]` claims
`shared_history` and that dict is logged per trajectory as ground truth.
**The logged provenance is false**, and any Arm C effect is confounded with a 6x
context reduction.

### Rulings (mine, as lead)

**R1 — Re-designate the manipulation check to P2, and report the P1a result as a
FINDING, not a failure.** "Structurally removing the answer field stops the
Planner *answering* but not the Planner *computing*" is a genuine, on-thesis
second dissociation: it separates output-authorship from cognitive division of
labor, which is precisely the distinction this paper exists to draw. Re-scope
every Arm C claim from "enforces the division of cognitive labor" to "enforces
answer-authorship boundaries". Option B (add a computation constraint and re-run
9,600 trajectories) does not fit in 9 days.

**R2 — Add Arm C-prime: Arm C's schema and parsed-plan routing WITH
`shared_history` restored.** C' - C isolates context; C' - A is the identified
enforcement effect. ~300 problems x 2 actors, affordable at measured throughput.
Without it the central comparison is confounded and I would not submit it.

**R3 — Fix the VISIBILITY dict so logged provenance is true.** A false
provenance field is worse than an absent one.

**R4 — The campaign continues.** Arms A and B are unaffected, and Arm C data
remains valid for the P2 manipulation check and for attrition analysis. C' is
additive, not a replacement.

### Also accepted from the review (queued to TODO)
attrition per arm x actor with the prereg rule applied (the Nones→0 rule flips
the Arm C/gpt-oss sign by 25 points); length-robust P1a via `eval_eq_density`;
replicate noise floor; evaluator independence (gpt-oss grades itself);
two-actor language fixed throughout the manuscript; drop the second-domain claim;
per-actor Arm B collapse stratified by informative-vs-ceiling.

## 2026-09-28 20:00 — D10. Arm C-prime implemented; it is a PARTIAL context control, and I will say so

C' = Arm C with `${shared_history}` restored in all three role templates.
Validators, schema, parsed-plan routing, submit-by-reference, budgets: unchanged.
`VISIBILITY` now logs the truth for both arms (D9-R3 done).

**Measured on a live 2-problem probe (mean prompt chars):**

| role | A | C | **C'** |
|---|---|---|---|
| planner | 1,386 | 448 | **634** |
| executor | 9,366 | 1,680 | **3,008** |
| reviewer | 17,476 | 2,936 | **5,520** |

**C' roughly doubles C's context but does NOT reach A.** That is structural, not
a bug: Arm A's history accumulates full raw agent transcripts, while C/C' carry
compact structured objects. Matching A exactly would mean feeding raw prose back
into C', which would destroy the architectural constraint that defines the arm.

**Honest statement for the paper.** C' is a *partial* context control. It
supports the contrast **C' - C = the effect of adding shared history at fixed
enforcement**, which is the clean, identified comparison. It does **not** license
"C vs A is now context-matched". If C' - C is large, context is doing the work
and any C - A difference is not attributable to enforcement. If C' - C is ~0,
the context confound is empirically ruled out at this margin even though the
raw character counts still differ — which is the more useful result and the more
likely one to report.

I will not claim a full context match. Overstating the control would be the same
error the review caught: asserting a property the instrument does not have.

## 2026-09-28 20:02 — D11. Bug found and fixed while wiring C'
CLI upper-cased arm names, turning `Cp` into `CP` and raising
`KeyError: 'CP'` in `VISIBILITY`. Normalizer added. Also noted: `--dry-run`
stubs cover A/B/C only, so Cp cannot be dry-run and must be verified live
(done above). Logged rather than silently worked around.

## 2026-09-28 20:30 — D12. Campaign sizing: harvest-at-n, run C' in parallel

Rate settled at **327 traj/h** (the 696/h reading was a 4-min transient).
n=1600 = 29.4 h. Verified the reviewer's per-actor informative rates from the
release: gemma_4_31b **0.273**, gpt_oss_120b **0.374** (pooled 0.233 was the
wrong unit, as the review said).

Power at the realistic informative rate (~0.32):

| n | informative | main (large) | main (moderate) |
|---|---|---|---|
| 400 | 128 | 0.58 | 0.25 |
| 800 | 256 | 0.88 | 0.43 |
| 1200 | 384 | 0.97 | 0.59 |
| 1600 | 512 | 0.99 | 0.72 |

**Decision.** The runner writes incrementally and the manifest is a deterministic
sorted sample, so **every prefix is itself a valid random sample**. I do not have
to choose n now. Let it run; harvest at whatever n is complete when the writing
window closes, and report the achieved n. Target **n>=800** (0.88 large-effect
power, 14.7 h, finishes ~11:00 local Sep 29). n=1600 is the stretch if
everything else lands early.

**C' runs in PARALLEL, not after.** The reviewer is right that C'-C is the
identified comparison; serializing it behind a 29 h job would risk the whole
control. Endpoint has headroom (ladder was 0% errors to conc 25; campaign uses
24 across two models). Launching C' at modest concurrency on the same manifest
prefix so C' and C share problems exactly.

**Deadline arithmetic.** Abstract Oct 1 (result-agnostic, already drafted).
Paper Oct 8. Even 29 h of generation ends Sep 30, leaving 8 days. Generation is
not the binding constraint — the P0 analysis/writing items are.

## 2026-09-29 15:58 — D12. Third actor FOUND and RUNNING: Llama-3.3-70B-Instruct

**Why.** Two actors cannot establish the inverse collapse/accuracy relationship.
A third actor tests whether it is a pattern or a two-model anecdote.

**Probe (real POSTs; no /models route exists; 3 rounds over ~10 min).**

| model id | 15:38Z | 15:40Z | 15:47Z | verdict |
|---|---|---|---|---|
| `meta-llama/Llama-3.3-70B-Instruct` | 200 | 200 | 200 | **LIVE 3/3** |
| `meta-llama/Meta-Llama-3.1-70B-Instruct` | 200 | 200 | 200 | **LIVE 3/3** (spare) |
| `openai/gpt-oss-20b` | 200 | 200 | — | live 2/2 (spare) |
| `google/gemma-4-E4B-it` | 200 | — | — | live 1/1 (spare) |
| `google/gemma-3-27b-it` | timeout | 503 | 503 | **DEAD 0/3** |

404 `endpoint_not_found` (do not exist): all Qwen ids tried, all Mistral ids,
`meta-llama/Llama-3.1-70B-Instruct` (the `Meta-` prefix is required),
`deepseek-ai/DeepSeek-R1`, `microsoft/phi-4`, `google/gemma-2-27b-it`,
`nvidia/Llama-3.1-Nemotron-70B-Instruct-HF`, `argonne-private/AuroraGPT-Tulu3-SFT-0125`.

Chose **Llama-3.3-70B-Instruct**: live in all 3 rounds, a different vendor and
family from both incumbents, and 70B sits between 31B and 120B.

**Validated before launch, not assumed.**
- Real 8192-token generation: complete `\boxed{6}` answer, `finish_reason=stop`.
- 9/9 pipeline smoke across A,B,C, zero errors.
- Capacity ladder 4/8/16 parallel: 0 errors, no latency penalty even with
  campaign_v2 running. Relaunched at concurrency 24 (ETA 19.5 h -> 8.1 h).

**`config_version` differs from campaign_v2 — and it is metadata-only.**
actor3 runs `231b8c4fe205d04b`; campaign_v2 holds `e3afa39849c1b980` in memory
(pre-8420b8d). Chased rather than assumed:
- `ALL_PROMPTS`: **zero** keys added, removed, or changed. All 8 A/B keys byte-identical.
- `SCHEMAS`: untouched (schemas.py not in the commit).
- The hash moved **only** because the `VISIBILITY` *documentation* dict gained a
  corrected Arm C provenance label and a new `Cp` entry.
- **Behavioural proof:** 19 round-1 planner prompts spanning A, B and C are
  byte-identical (`prompt_sha256_12`) across the two config versions. 0 mismatches.
- Evaluator is `openai/gpt-oss-120b` in both. No verifier drift.

Conclusion: actor3 is poolable with campaign_v2. The differing hash is a relabel.

**Collapse metric: a message-count confound, and the headline survives it.**
The project rule (`x2_campaign_tables.py:149-156`) flags any duplicate hash among
*all* role messages, so trajectories with more messages get more chances to
collapse. Llama-3.3 emits ~2x more role messages (mean 13.5 vs 6.6), so its
project-rule number is not directly comparable. Stratifying campaign_v2 by
message count separates two phenomena that share one metric:

| actor | arm | nmsg=3 | 4-9 | 10+ |
|---|---|---|---|---|
| gpt-oss-120b | B | **0.813** | 0.823 | 0.966 |
| gemma-4-31B | B | **0.000** | 0.100 | 0.978 |

gpt-oss collapses at 0.813 in *minimal* 3-message trajectories; gemma-4's 0.179
comes almost entirely from long trajectories (0.978 at 10+, 0.000 at 3). Under a
count-matched rule (first 3 role messages) the contrast is **starker**, not
weaker: gpt-oss B 0.698 vs gemma-4 B 0.000. The headline is robust; report the
count-matched rule alongside the project rule.

**Status.** `results/main/actor3.jsonl`, run-id `actor3-n400`, n=400 x A,B,C =
1200 trajectories, resumable. The n=400 manifest is a strict subset of n=1600
(same seed), so all three actors are comparable on the identical 400 problems.

## 2026-09-29 16:55 — D13. Two cross-worker corrections from the third-actor run

### (1) CLAIM_STATUS DROPPED_WITH_REASON is out of date on the live-model fact

`CLAIM_STATUS.md` drops the three-actor ordering claim (G1) saying
"gemma-3-27b and Llama-3.3-70B both 503". **Llama-3.3-70B is not 503.** Probed
with real POSTs at 15:38Z, 15:40Z, 15:47Z and again at 16:50Z: **HTTP 200 every
time**, and it has been generating continuously since 15:52Z. `P0-9` in TODO.md
already records the same conclusion ("substitute Llama-3.3-70B, verified live"),
so the two boards disagree. gemma-3-27b IS dead (0/3, 503 "online but not ready").

G1's drop reason should be re-examined against `results/main/actor3.jsonl`
rather than left as a stale endpoint fact.

### (2) The adjudication sample drew Llama-3.3 from an IN-PROGRESS run

`adjudication/SAMPLING_MANIFEST.json` contains
`('Llama-3.3-70B-Instruct','A'/'B'/'C', False)` = 71/74/79 trajectories, sampled
while `actor3.jsonl` was ~12% complete (it is still writing now). Two
consequences, one benign and one not:

**Completion-order bias is real.** Measured on campaign_v2/gemma-4 by taking
prefixes in `ended_at` order — an early prefix over-represents SLOW, LONG
trajectories:

| prefix | n | mean role msgs | collapse (project rule) |
|---|---|---|---|
| first 5% | 194 | 7.37 | 0.170 |
| first 10% | 388 | 7.13 | 0.149 |
| first 20% | 776 | 6.64 | 0.122 |
| FULL | 3883 | 6.09 | 0.108 |

**But the count-matched rule the adjudication actually uses is robust to it:**
gpt-oss arm B first-12% `first3`=0.623 vs FULL 0.692; every 0.000 cell stays
0.000. So the sample is *usable*, not invalid.

**The real limitation is a missing cell, not bias.** All 42 Llama items are
`auto_collapse=False`, because at n=238 Llama-3.3 has **zero** count-matched
collapse positives in any arm (A 0/79, B 0/81, C 0/81). There is no
`(Llama, *, True)` stratum to sample, so the adjudication cannot measure
**precision** on this actor — only recall. Given that recall is exactly what
killed the metric for gemma-4 (0.343 pooled, 0.000 on gemma-4), this is the
cell that matters, and it is the one Llama can speak to.

Verified this is a property of the actor and not an instrument fault:
**3,235 of 3,235 `response_sha256_12` values recomputed from `text` match
exactly (0 mismatches).** Llama-3.3's three roles genuinely emit different text.

### (3) Consequence for the third-actor deliverable — my own framing was wrong

I had been preparing to report Llama-3.3's position on a "collapse rate vs B-A"
plane against gpt-oss (0.846) and gemma-4 (0.173). **Those coordinates are from
a withdrawn metric** (CORRECTION-01: precision 1.000 but recall 0.343; gemma-4
Arm B judged 0.944 functionally redundant while the byte flag fires 0.000).
Placing a third actor on that plane would extend a retracted measurement.

The third actor's byte-collapse numbers will still be reported — as byte-level
output duplication, labelled as such — but the *inverse-relationship* question
must be answered with the adjudicated measure, not the byte flag. This is a
scope correction to my own task, recorded before the numbers exist.

## 2026-09-29 17:00 — D14. A functional collapse proxy that tracks the adjudicated label (Arms A/B only)

**Problem.** The byte rule is withdrawn for under-detection (recall 0.343; it
scores gemma-4 Arm B 0.000 while adjudication judges it 0.944 redundant). Under
the count-matched rule Llama-3.3 is 0.000 in **every** arm, so the third actor
cannot be positioned on the collapse axis at all. Normalized-text equality does
not fix this (gemma-4 Arm B still 0.000) — it shares the same blind spot.

**Proxy.** `frac_ALL3_boxed` = fraction of trajectories in which all three of
the first three role messages independently assert a `\boxed` answer. This
operationalizes the rubric's own Q2 YES example — "every agent does the same
kind of work: all three solve the problem end-to-end and assert an answer" —
so it targets *function*, not text overlap.

**Validation against the adjudicated Q5 rates (FINDING-13), all four cells:**

| arm | actor | adjudicated Q5=NO | `frac_ALL3_boxed` | byte first3 |
|---|---|---|---|---|
| A | gpt-oss | 0.056 | 0.117 | 0.000 |
| A | gemma-4 | 0.000 | 0.000 | 0.000 |
| B | gpt-oss | 0.954 | 0.845 | 0.691 |
| B | gemma-4 | **0.944** | **0.975** | **0.000** |

Max deviation 0.109; it recovers the cell the byte rule misses entirely.

**SCOPE LIMIT — not valid for Arm C, and the reason is circularity.**
Arm C's validator rejects `\boxed` outright (`schemas.py:98`,
`answer_leak:boxed`). Arm C's 0.000 therefore measures the *constraint*, not
behaviour. Verified directly: 1 boxed occurrence across all sampled Arm C role
messages. **Report this proxy for Arms A and B only** — which is where the
headline B−A contrast lives anyway.

**Third actor under this proxy (n≈85/arm, run still in flight):**
Llama-3.3 Arm A 0.000, Arm B **0.906**. For comparison, Arm B: gpt-oss 0.845,
gemma-4 0.975. On the *functional* measure all three actors lose the division
of labour in Arm B — consistent with the corrected headline in
`notes/ADJUDICATION-SCOPE-NOTE.md` ("both actors lose the organization, only one
loses accuracy"), now with a third actor pointing the same way.

This is a proxy validated against 4 adjudicated cells, not a replacement for
adjudication. The `(Llama, *, True)` stratum is still missing from the
adjudication sample, so Llama's precision remains unmeasured.

### D14 addendum (17:28) — sensitivity of the functional proxy to its answer-marker

D14 chose `\boxed` as the answer-assertion marker. That choice was made before
testing alternatives, so I tested it after the fact against the adjudicated
cells. Three markers, scored on mean absolute error vs the FINDING-13 rates:

| marker | max err | mean err |
|---|---|---|
| `\boxed` (D14's choice) | **0.108** | **0.051** |
| `\boxed` OR "answer is" | 0.169 | 0.076 |
| `\boxed` OR "final answer" | 0.561 | 0.235 |

`\boxed` is the best-calibrated of the three, so D14's number stands — but it
was luck, not method, and the margin is not large enough to call the proxy
token-independent.

**Arm A is token-sensitive; Arm B is not.** Llama-3.3 Arm A moves 0.000 ->
0.538 across markers, gpt-oss 0.121 -> 0.617. Arm B moves only 0.846 -> 0.982
across all actors and markers. So any *absolute* Arm A figure from this proxy
is unreliable and should not be quoted; the Arm B figures are stable.

**The D14 conclusion survives all three markers** — this is the check that
matters, and it passes in all 9 actor x marker cells:

| marker | gpt-oss B-A | gemma-4 B-A | Llama-3.3 B-A |
|---|---|---|---|
| `\boxed` | +0.726 | +0.975 | +0.910 |
| `\boxed`/"final answer" | +0.234 | +0.728 | +0.421 |
| `\boxed`/"answer is" | +0.635 | +0.979 | +0.876 |

Arm B functional collapse is high (0.846-0.982) for **every actor under every
marker**, B-A is large and positive in all 9 cells, and Llama-3.3 always falls
between the two incumbents. The magnitudes are marker-dependent; the finding
that all three actors lose the division of labour in Arm B is not.
