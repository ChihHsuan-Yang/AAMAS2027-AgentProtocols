# Hourly reports — AAMAS 2027 execution

## H1 — 2026-09-28 ~17:45 (first hour of execution mode)

### Status
Execution infrastructure stood up. **Endpoint verified live and authenticated.**
No scientific results yet; nothing is claimed.

### Verified by Master personally (not taken from any agent)
| check | result |
|---|---|
| Globus token → real POST | **HTTP 200, 1.8 s** (Sophia vLLM) |
| gpt-oss-120b | 200 / 1.9 s |
| gemma-4-31B-it | 200 / 0.9 s |
| **Llama-3.3-70B-Instruct** | 200 / 3.0 s |
| gemma-3-27b-it | **503 "online but not ready"** (x4, plus worker watch) |
| metis / minerva endpoints | 404 endpoint_not_found — Sophia is the only live route |
| Arm C validators, 6 adversarial cases | **6/6 correct** incl. `answer_leak:boxed`, `answer_leak:final_answer_phrase` |
| Analysis pipeline positive control | recovers a planted +0.15 interaction |
| Analysis pipeline negative control | correctly finds **no** interaction |
| Secret scan of all tracked files | clean |

### Key decision (D1): third actor substituted
gemma-3-27b is not serving. Panel is now **gpt-oss-120b / gemma-4-31B / Llama-3.3-70B**
— three different families, 31B-120B.
**Honest cost:** gemma3 was the actor that made the capability-vs-fidelity
dissociation testable from historical data. Llama-3.3-70B has no historical PER
trajectories, so its soft-role fidelity is unknown until Arm A runs. The
dissociation test becomes **measured in this campaign and pre-registered**,
rather than inherited — cleaner, but we cannot promise in advance that the panel
spans the needed contrast. Recorded in DECISION_LOG.md.

### Agents
| agent | task | status |
|---|---|---|
| EXP | Arms A/B/C runner, validators, instrumentation | ACTIVE — schemas.py delivered and independently verified by me |
| INF | live concurrency ladder, throughput ledger, gemma3 watch | ACTIVE — endpoint_lib + gemma3 probe running |
| WRI | manuscript skeleton, Intro/Related/Measurement/Method | ACTIVE |

### Built by Master directly
- `TODO.md` (P0-P3 board), `DECISION_LOG.md`, this file
- Deterministic matched manifests: n=400 (sha 94955e7f…) and n=25 smoke
  (sha 04009d74…), smoke verified ⊆ main so smoke trajectories are reusable
- `analysis/scripts/x1_analyze_campaign.py` — the pre-registered tests
  (P1-P5, Holm-corrected, permutation p, fairness audit, Arm C manipulation
  check), **validated on synthetic positive and negative controls before real data**
- GitHub repo populated and pushed (75 files, no secrets)

### Experiments
None launched. Smoke is gated on the runner landing.

### Next hour
1. Review EXP runner output; demand the real 3-trajectory proof, not a claim.
2. Run the 15-gate smoke (3 arms × 3 actors × 25 problems ≈ 225 trajectories).
3. Commit PREREGISTRATION.md **before** any confirmatory result is inspected.
4. If smoke passes, launch the main campaign automatically.

### For Bella (manual only — I cannot do these)
- OpenReview profiles for all intended authors (API gives 403 to me).
- Reciprocal-reviewer requirement, if AAMAS 2027 has one.
- Final author list — still recorded as "interim / on hold".

---

## H2 — 2026-09-28 ~18:05

### 1. Overall status
**Live pipeline works end to end.** Smoke running against two actors. Two
material changes since H1: a **50x throughput correction** and an **Arm C bug
caught in the live run that dry-run could not have found**.

### 2. Biggest change: the campaign is ~50x cheaper than I told you
Measured ladder, 30 real requests per level, **0% errors at every level**:

| model | best stable conc | throughput | p90 latency |
|---|---|---|---|
| gpt-oss-120b | 25 | **189 req/min** | 6.4 s |
| gemma-4-31B-it | 25 | **142 req/min** | 9.0 s |

**N=400, 3 arms, 2 actors ≈ 1.2 h parallel / 2.3 h sequential** — not the 63.5 h
I projected in the go/no-go. My earlier figure came from *historical* PER
wall-times that bundled queueing and a slower era of the service. The measured
number supersedes it. **Consequence: n=400 is trivially affordable, and n=800 or
a second domain are now live options.**

### 3. Arm C bug — found live, fixed, and it mattered
A trajectory **hard-failed** after 4 consecutive `wrong_type:strategy`
rejections. Cause: the model emits `"strategy": "<prose>"` instead of
`["<prose>"]`. The plan content was fine.

This would have **depressed Arm C's completion rate for a formatting reason**
and biased the arm against the hypothesis under test. Fixed: array fields coerce
a bare string and log `coerced_string_to_array:<field>` as an auditable soft
signal. Re-verified adversarially that `additional_property:answer`,
`answer_leak:boxed`, and `missing_field` **still reject**. Replaying the 4 real
failures: 3 now accepted.

**Standing rule added:** formatting rejections are coerced-and-logged, never
counted as enforcement events. The paper's enforcement rate uses **role-boundary
violations only**.

### 4. Second finding: temperature=0 is NOT deterministic
Identical request x3: gpt-oss-120b returned **3 distinct outputs**;
gemma-4-31B returned 3 identical on one prompt, 2 distinct on another.
**Consequence:** no result may be attributed to a single trajectory, and
re-running a cell will not reproduce it byte-for-byte. Paired designs and CIs
over problems remain valid; per-trajectory anecdotes do not. Will be stated as
a limitation.

### 5. Endpoint reality — the actor panel shrank
Only **2 of 4** models serve. Llama-3.3-70B **worked at 17:32 and was 503 by
17:47** — it flaps. gemma-3-27b never became ready across 5 probes.
Campaign is now **actor-incremental**: it runs with what is live and resumes to
add an actor if an endpoint recovers. It does not block.

**Pre-registered consequence, written before results:** with two actors, P4 is a
single difference-of-differences and **cannot separate a capability ordering
from a fidelity ordering**. If we finish with two actors, the
capability-vs-fidelity dissociation is reported **UNRESOLVED**, not spun.

### 6. Verified, not trusted
- Manuscript compiles: **9 pages, 0 errors, 0 undefined refs/cites, 0 overfull**.
  I audited **every decimal literal** against the frozen sources — all correct.
- Caught the writing agent quoting **0.164**, a retracted v1 value, from
  FINDING-07. It self-corrected; I then added a **retraction banner** to
  FINDING-07 so the trap cannot catch the next drafter.
- Arm C validators: 6/6 adversarial cases before the fix, re-verified after.

### 7. PREREGISTRATION committed 22:52:34Z — before any confirmatory result
With three dated amendments (actor panel, discriminating contrast, enforcement-
rate definition).

### 8. Next
Finish smoke → evaluate the 15 gates → launch the main campaign. Given measured
throughput I intend **n=400 x 3 arms x all live actors**, then extend to a second
domain or n=800 with the time saved.
