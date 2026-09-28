# ALCF Sophia vLLM — measured throughput ledger

Endpoint: `https://inference-api.alcf.anl.gov/resource_server/sophia/vllm/v1`

Measured 2026-09-28 17:49 (local, America/Chicago) by the AAMAS-2027 infrastructure worker.
Every row below comes from requests actually issued against the live endpoint. Protocol per row: 30 requests, distinct olympiad-style math prompts, `max_tokens=512`, `temperature=0`, at most 1 retry per request on a transient error (429/503/timeout/connection).

## Ladder results

| model | concurrency | throughput (req/min) | mean latency (s) | p90 (s) | error rate | retry rate | out tok/s | verdict |
|---|---|---|---|---|---|---|---|---|
| `gemma-4-31B-it` | 1 | 10.85 | 5.53 | 6.46 | 0.0% | 0.0% | 80 | STABLE |
| `gemma-4-31B-it` | 4 | 42.82 | 5.45 | 6.48 | 0.0% | 0.0% | 315 | STABLE |
| `gemma-4-31B-it` | 8 | 69.58 | 5.98 | 7.69 | 0.0% | 0.0% | 509 | STABLE |
| `gemma-4-31B-it` | 16 | 125.93 | 6.44 | 8.22 | 0.0% | 0.0% | 923 | STABLE |
| `gemma-4-31B-it` | 25 | 142.51 | 7.26 | 8.97 | 0.0% | 10.0% | 1045 | STABLE |
| `gpt-oss-120b` | 1 | 17.40 | 3.45 | 4.47 | 0.0% | 0.0% | 126 | STABLE |
| `gpt-oss-120b` | 4 | 66.09 | 3.47 | 4.16 | 0.0% | 0.0% | 482 | STABLE |
| `gpt-oss-120b` | 8 | 98.86 | 4.24 | 5.18 | 0.0% | 0.0% | 718 | STABLE |
| `gpt-oss-120b` | 16 | 170.40 | 4.83 | 6.35 | 0.0% | 0.0% | 1237 | STABLE |
| `gpt-oss-120b` | 25 | 189.13 | 5.28 | 6.36 | 0.0% | 3.3% | 1364 | STABLE |

### Error / retry detail

| model | concurrency | failed reqs | errors by type | transient events (incl. retried-then-succeeded) |
|---|---|---|---|---|
| `gemma-4-31B-it` | 1 | 0 | none | none |
| `gemma-4-31B-it` | 4 | 0 | none | none |
| `gemma-4-31B-it` | 8 | 0 | none | none |
| `gemma-4-31B-it` | 16 | 0 | none | none |
| `gemma-4-31B-it` | 25 | 0 | none | 429=3 |
| `gpt-oss-120b` | 1 | 0 | none | none |
| `gpt-oss-120b` | 4 | 0 | none | none |
| `gpt-oss-120b` | 8 | 0 | none | none |
| `gpt-oss-120b` | 16 | 0 | none | none |
| `gpt-oss-120b` | 25 | 0 | none | 429=1 |

## Endpoints that could not be measured

| model | observed | evidence |
|---|---|---|
| `google/gemma-3-27b-it` | never became ready | 5 probes over 22:33:00 → 22:47:02 UTC, statuses: 503×4, EXC×1 |
| `meta-llama/Llama-3.3-70B-Instruct` | never became ready | 5 probes over 22:35:26 → 22:49:27 UTC, statuses: 503×4, EXC×1 |

## Resumability / determinism at `temperature=0`

Same request issued 3× per (model, prompt); SHA-256 of the returned message content compared.

| model | prompt | successful reps | distinct outputs | byte-identical? |
|---|---|---|---|---|
| `openai/gpt-oss-120b` | Find the remainder when 7^2025 is divided by 1 | 3/3 | 3 | **NO** |
| `google/gemma-4-31B-it` | Find the remainder when 7^2025 is divided by 1 | 3/3 | 1 | YES |
| `meta-llama/Llama-3.3-70B-Instruct` | Find the remainder when 7^2025 is divided by 1 | 0/3 | 0 | n/a — endpoint returned no completions (503) |
| `openai/gpt-oss-120b` | In triangle ABC, AB=13, BC=14, CA=15. Find the | 3/3 | 3 | **NO** |
| `google/gemma-4-31B-it` | In triangle ABC, AB=13, BC=14, CA=15. Find the | 3/3 | 2 | **NO** |
| `meta-llama/Llama-3.3-70B-Instruct` | In triangle ABC, AB=13, BC=14, CA=15. Find the | 0/3 | 0 | n/a — endpoint returned no completions (503) |

## Recommended concurrency per model

- **`gpt-oss-120b` → concurrency 25** (highest measured point): 189.13 req/min, mean 5.28s, p90 6.36s, 0 failed of 30, 3% of requests hit one retryable 429.
- **`gemma-4-31B-it` → concurrency 25** (highest measured point): 142.51 req/min, mean 7.26s, p90 8.97s, 0 failed of 30, 10% of requests hit one retryable 429.

The ladder never triggered its stop rule: throughput rose monotonically through concurrency 25 on both models and no request failed outright. Concurrency 25 is therefore the **best measured** point, not a measured ceiling — the knee is above it and was not probed (the ladder stopped at 25 by design).

Marginal return is falling, though: gpt-oss-120b gained only 11% throughput going 16→25 (170.40→189.13 req/min) while mean latency rose 9% and the first 429 appeared. gemma-4-31B-it gained 13% (125.93→142.51) with retry rate going 0%→10%. Concurrency 16 is the conservative choice on a shared endpoint; 25 is safe if the client retries 429 (all 4 observed 429s succeeded on the first retry).

### What this means for caching / resume

`temperature=0` is **not** a determinism guarantee on this endpoint. 4 of the 4 measurable (model, prompt) cells varied across repeats; only 1 of 4 was byte-identical across all 3 reps. gpt-oss-120b returned 3 distinct outputs for 3 identical requests on both prompts. This is the expected consequence of continuous batching: batch composition changes the reduction order in the GPU kernels, so logits differ in the last bits and greedy decoding can tip at a near-tie token.

Consequences for the campaign:

- Resume is **safe** in the sense that matters: a cached trajectory is a valid sample and re-running a missing one gives another valid sample. Cache on (model, prompt, params) and never re-request a completed call.
- Re-running a call will **not** reproduce a prior byte-identical output, so the cache must store the response text, not a hash of it.
- Any claim of exact reproducibility from a seed/temperature argument is false here and should not appear in the paper. Report the campaign as sampled-at-temperature-0, not deterministic.

## Note on prior evidence

Prior project evidence held that concurrency 50 was slower than 25. Nothing measured here contradicts that — this ladder stopped at 25 and so never tested 50.


## Campaign projection (task 4)

Campaign shape: **3 arms x 3 actors x N problems**, 8.4 actor calls + 1.2 evaluator calls per trajectory (historical PER logs). Arms run sequentially per actor; different actors run in parallel on separate model endpoints.

Rates used are the measured best-stable points above. Evaluator placed on `gpt-oss-120b`.

> **Only 2 of the 3 actor endpoints the design calls for are live.** Scenario A is fully measured. Scenario B fills the third actor with the slowest measured rate — that row is an ASSUMPTION, not a measurement.

### A. 2 measured actors only (what the endpoint supports RIGHT NOW)

Actor rates: `gpt-oss-120b` 189.13 req/min (measured), `gemma-4-31B-it` 142.51 req/min (measured)

| N | trajectories | actor calls | evaluator calls | SEQUENTIAL total (h) | PARALLEL, evaluator overlapped (h) | PARALLEL, evaluator after (h) |
|---|---|---|---|---|---|---|
| 100 | 600 | 5040 | 720 | **0.58** | **0.29** | 0.36 |
| 200 | 1200 | 10080 | 1440 | **1.16** | **0.59** | 0.72 |
| 400 | 2400 | 20160 | 2880 | **2.32** | **1.18** | 1.43 |

Per-actor generation hours (the parallel makespan is the largest of these):

- N=100: `gpt-oss-120b` 0.22 h, `gemma-4-31B-it` 0.29 h; evaluator 0.06 h
- N=200: `gpt-oss-120b` 0.44 h, `gemma-4-31B-it` 0.59 h; evaluator 0.13 h
- N=400: `gpt-oss-120b` 0.89 h, `gemma-4-31B-it` 1.18 h; evaluator 0.25 h

### B. 3 actors, 3rd ASSUMED at slowest measured rate (142.51 req/min)

Actor rates: `gpt-oss-120b` 189.13 req/min (measured), `gemma-4-31B-it` 142.51 req/min (measured), `actor3_ASSUMED` 142.51 req/min (ASSUMED)

| N | trajectories | actor calls | evaluator calls | SEQUENTIAL total (h) | PARALLEL, evaluator overlapped (h) | PARALLEL, evaluator after (h) |
|---|---|---|---|---|---|---|
| 100 | 900 | 7560 | 1080 | **0.91** | **0.29** | 0.39 |
| 200 | 1800 | 15120 | 2160 | **1.81** | **0.59** | 0.78 |
| 400 | 3600 | 30240 | 4320 | **3.63** | **1.18** | 1.56 |

Per-actor generation hours (the parallel makespan is the largest of these):

- N=100: `gpt-oss-120b` 0.22 h, `gemma-4-31B-it` 0.29 h, `actor3_ASSUMED` 0.29 h; evaluator 0.10 h
- N=200: `gpt-oss-120b` 0.44 h, `gemma-4-31B-it` 0.59 h, `actor3_ASSUMED` 0.59 h; evaluator 0.19 h
- N=400: `gpt-oss-120b` 0.89 h, `gemma-4-31B-it` 1.18 h, `actor3_ASSUMED` 1.18 h; evaluator 0.38 h

**Read-out.** Even at N=400 the campaign is a matter of hours, not days: 2.32 h sequential / 1.18 h parallel in the fully-measured 2-actor scenario, and 3.63 h / 1.18 h in the 3-actor scenario. Throughput is not the binding constraint — **endpoint availability is.** Two of the four candidate models were dead for the entire measurement window.

These projections assume the measured rate is sustained for the whole campaign and exclude client-side overhead, prompt-construction time, and any 503 outage. The 429s seen at concurrency 25 mean a real campaign should budget retry headroom.
