# TODO — AAMAS 2027 (authoritative task board)

Owner key: **M**=Master, **EXP**=experiment worker, **INF**=infra worker,
**LIT**=literature worker, **WRI**=writing worker, **MEAS**=measurement worker.
DONE = artifact exists **and** Master reviewed **and** validation passed.

## P0 — submission-threatening

| id | task | owner | status | dep | artifact | validation |
|---|---|---|---|---|---|---|
| P0-1 | Verify endpoint auth + live models | M | **DONE** | — | probe output | gpt-oss 200/1.9s, gemma-4-31B 200/0.9s, Llama-3.3-70B 200/3.0s; gemma-3-27b **503 not ready** |
| P0-2 | Clone Overleaf | M | **DONE** | — | /tmp/aamas_ol | cloned, 1 file |
| P0-3 | GitHub repo populate | M | ACTIVE | — | github.com/ChihHsuan-Yang/AAMAS2027-AgentProtocols | push succeeds, no secrets |
| P0-4 | Implement Arms A/B/C + validators + logging | EXP | ACTIVE | P0-1 | experiments/runner.py | dry-run + real 3-traj test output pasted |
| P0-5 | Instrument evaluator_calls | EXP | ACTIVE | P0-4 | runner logs | non-null in smoke output |
| P0-6 | Live concurrency ladder | INF | ACTIVE | P0-1 | throughput ledger | error/latency/throughput per conc level |
| P0-7 | Smoke run + 15 gates | M | TODO | P0-4,P0-6 | smoke JSONL | all gates pass/fail recorded |
| P0-8 | PREREGISTRATION.md committed **before** confirmatory results | M | TODO | P0-7 | git commit hash | commit timestamp precedes run start |
| P0-9 | Third-actor decision | M | **DONE** | P0-1 | THIRD-ACTOR.md | gemma-3-27b 503 → substitute Llama-3.3-70B (different family, verified live) |
| P0-10 | Abstract for Oct 1 | M/WRI | TODO | — | paper/ABSTRACT | result-agnostic, <=300 words |
| P0-11 | OpenReview profiles / reciprocal reviewer | **BELLA** | BLOCKED | — | SUBMISSION_CHECKLIST | manual, cannot verify (403) |

## P1 — central contribution

| id | task | owner | status | dep | artifact | validation |
|---|---|---|---|---|---|---|
| P1-1 | Main campaign (3 arms x 3 actors x omnimath2) | M/EXP | TODO | P0-7 | run JSONL | completeness manifest |
| P1-2 | Analysis pipeline (auto tables/figures) | MEAS | ACTIVE | — | analysis/scripts | runs end-to-end on smoke data |
| P1-3 | Manuscript skeleton + Intro + Related Work | WRI | ACTIVE | — | paper/*.tex | compiles |
| P1-4 | Fig 1 specified-vs-realized diagram | WRI | TODO | — | figures/ | readable at print size |
| P1-5 | Second domain if throughput allows | M | TODO | P1-1 | — | contract reconstructed first |

## P2 — strengthening

| id | task | owner | status | dep | artifact | validation |
|---|---|---|---|---|---|---|
| P2-1 | R4 Reviewer annotation (30 msgs) | MEAS | TODO | — | annotations csv | only if Reviewer claims are made |
| P2-2 | Internal mock AAMAS review | LIT | TODO | P1-3 | review doc | every criticism -> TODO/limitation |
| P2-3 | Novelty matrix refresh | LIT | TODO | — | NOVELTY-*.md | versions pinned |
| P2-4 | RESULT_PROVENANCE for every number | M | TODO | P1-1 | RESULT_PROVENANCE.md | every paper number traceable |

## Carried decisions
- Arm D (role shuffle) **DROPPED_WITH_REASON**: tests a different question; would halve power on the A/B/C contrast.
- Frozen metrics P1a / E2v2 must not change post-hoc (see VALIDATION-FINAL.md). Failed v3 is the cautionary case.
