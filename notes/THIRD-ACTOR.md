# Third actor — evidence and recommendation (2026-09-28)

## What I verified myself (not taken from the agent report)

| check | result |
|---|---|
| PER configs present | **four** actor families have `per_hint_*`: gemma3_27b, gemma4_31b, **gemma4_e4b**, llama31_70b |
| llama rows in the released corpus | **0** (gemma_4_31b 32,780 / gpt_oss_120b 32,780 / gemma3_27b 3,332) |
| `aurora.alcf.anl.gov:22` | **OPEN** right now |
| `sophia.alcf.anl.gov:22` | **OPEN** right now |
| inference-api `/models` | HTTP 404 on the unauthenticated path (expected; needs a token) |

**Correction to the infrastructure report:** it stated "AURORA IS DOWN — verified
2026-09-28" from a status file. I probed the host directly and port 22 is
**reachable**. A note in a status file is not a present-tense check
([[measure-the-subject-not-the-proxy]]). Endpoint *serving* health still needs a
real authenticated POST — the login host being up proves nothing about vLLM.

## Candidates, ranked by evidence of actually working

### 1. `gemma3_27b` — RECOMMENDED
- **3,332 real PER trajectories** already in the corpus; config committed and exercised.
- Already has frozen fidelity measurements (P1a .266, E2v2 .112) and
  first-pass coverage on 833 omnimath2 problems.
- **Scientifically load-bearing, not convenient:** it is the actor that makes
  the capability/fidelity dissociation testable. It is *less* capable than
  gpt_oss (baseline .425 vs .568) but *more* faithful on both metrics. A
  capability-equalizer account and a fidelity account make opposite predictions
  for this pair — that is the contrast that separates us from 2608.21747.
- Known confounds (smallest model, one domain, Crux-only) are real but are
  reduced by the new run, which puts it on the same domains and problems as the
  others.

### 2. `Llama-3.3-70B-Instruct` — best *additional* diversity, if there is room
- Not in any config, but reportedly verified on Sophia 2026-09-25 at ~10k
  rows/hr with zero transport errors. One-line config edit from the llama31 bundle.
- Gives a genuine third *family* at 70B. Adds family diversity that the
  Gemma-heavy panel lacks.
- **Unverified by me.** Needs a live probe before it enters any plan.

### 3. `gemma4_e4b` — config complete, never run, no health data either way.

### 4. `llama31_70b` — **DO NOT PLAN ON THIS.**
Its single PER attempt reached **604/700**; broadcast 374/700; it logged 14
rate-limit backoffs **at concurrency 1**; last seen alive 2026-06-27. The
config's existence is evidence of an abandoned attempt, not of runnability.

## Decision
**Third actor = `gemma3_27b`**, because it is the one that makes the
discriminating test possible, not because it is cheapest. If endpoints prove
healthy and time allows, add `Llama-3.3-70B-Instruct` as a fourth for family
diversity — but only after a live probe.

## Concurrency: my earlier estimates were too optimistic

The design assumed conc 32-64. Evidence from real runs:
- **25 workers** was the fastest clean point for OSS on Sophia (28.9 s/question);
  50 workers was *slower* (31.1 s/q) due to the broadcast long tail plus backoff.
- **conc 8-10** for Gemma-4 on Crux; conc=25 wedged asyncio.
- **conc 64 has no precedent anywhere in the project's notes.**
- **Gemma-4-31B is 4-5x slower per call than gpt-oss-120b** (42.8 s vs 9.0 s
  mean at conc=1). A Gemma arm does not finish in the same wall-clock as an OSS
  arm at equal concurrency.

**Consequence: all wall-clock figures in EXPERIMENT-DESIGN-v2 must be re-derived
at conc<=25, with per-actor latency, and treated as lower bounds until a smoke
ladder is run on the actual endpoint.** This is the single largest threat to
finishing before Oct 8.

## Operational hazards to design against
- **Globus high-assurance timeout returns 401 on a valid, unexpired token.**
  Needs an interactive browser re-auth — it will silently kill an unattended run.
- **Back up `tokens.json` before re-authing** (a prior attempt truncated it to
  0 bytes on a disk-quota error and destroyed a working token).
- **Never run `authenticate` from a worker node** — it rotates the refresh token
  and invalidates every other node mid-run.
- **Pin and log the backend per trajectory.** The same cell measured 9.6x
  different sec-per-ktok between Metis and Sophia, with accuracy .72 vs .93.
  Unpinned backends would confound the actor contrast outright.
- Do not let a watchdog relaunch into a dead backend (a prior run self-inflicted
  an 82-relaunch 429 storm).
