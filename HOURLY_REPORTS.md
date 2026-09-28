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
