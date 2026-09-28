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
