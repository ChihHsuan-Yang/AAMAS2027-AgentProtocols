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
