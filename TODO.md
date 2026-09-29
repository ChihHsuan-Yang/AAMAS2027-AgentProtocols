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


---

## Added 2026-09-28 20:05 — from the mock AAMAS review (all defects independently CONFIRMED by Master)

| id | task | owner | pri | status | validation |
|---|---|---|---|---|---|
| R-1 | Re-designate manipulation check P1a → **P2**; report P1a non-effect as a FINDING | M | **P0** | DONE (D9-R1) | measured: Arm C P2=1.000 both cells, P1a 0.073-0.275 |
| R-2 | Arm C′ context control (shared_history restored) | M | **P0** | DONE (D10) | live probe: C' doubles C context; scoped as PARTIAL control |
| R-3 | Fix false `VISIBILITY["C"]` provenance | M | **P0** | DONE | logged policy now matches templates |
| R-4 | Run C′ cell (~300 problems x 2 actors) | M | **P0** | TODO | C'-C isolates context |
| R-5 | Attrition per arm x actor, prereg Nones→0 rule applied | M | **P0** | TODO | Nones→0 flips ArmC/gpt-oss by 25 pts — must show both |
| R-6 | Two-actor language fixed throughout manuscript (6 places say three) | WRI | **P0** | TODO | grep "three actor" == 0 |
| R-7 | Drop the second-domain claim (runner pins omnimath2) | WRI | **P0** | TODO | no "two domains" in tex |
| R-8 | Length-robust P1a via `eval_eq_density` (Arm C msgs ~6x shorter) | MEAS | P1 | TODO | report alongside frozen P1a, do NOT re-freeze |
| R-9 | Replicate noise floor (Arm A, ~150 problems, second seed) | M | P1 | TODO | temp=0 is nondeterministic; need the floor |
| R-10 | Evaluator independence: gpt-oss grades itself | M | P1 | TODO | re-grade ~200 with 2nd judge, report agreement |
| R-11 | Recompute power on informative stratum PER ACTOR | M | P1 | TODO | gemma-4 .273 / gpt-oss .374, not pooled .233 |
| R-12 | Annotate 20-30 more E2v2 (n=13 too thin) incl. JSON executors | MEAS | P1 | TODO | report bootstrap CI on kappa |
| R-13 | Arm B collapse per actor, stratified informative vs ceiling | M | P1 | TODO | F08 needs stratification |
| R-14 | Fix prompts.py comment: role tags DO leak via shared_history | EXP | P2 | TODO | grep confirms `[Planner]` in Arm B bodies |
| R-15 | Reconcile 0.110 vs 0.890 AUC spelling | WRI | P2 | TODO | one convention |
| R-16 | Report coercion + parse-repair rates per arm x actor | M | P2 | TODO | show coercions did not do the work |
| R-17 | Swap to real AAMAS class; get to 8 pages | WRI | **P0** | TODO | currently 9 pp with stub Results |
| R-18 | Double-blind scrub (repo path, HF org, author GitHub) | M | **P0** | TODO | no identifying URL in PDF |
| R-19 | R4 Reviewer annotation OR remove Reviewer from Arm C claims | MEAS | P1 | TODO | all 5 boundary rejections are reviewer |
| R-20 | Backend straddle check (groupby, 30 min) | M | P2 | TODO | execute the \TODO |

**Rejected from the review:** third actor (endpoints 503/flapping — write the
limitation instead); second organization; full n=4181 stretch. Chasing these
would risk R-2/R-9, which matter more.


---

## Post-pivot board (2026-09-29)

| id | task | pri | status | evidence |
|---|---|---|---|---|
| N-1 | Collapse measurement audit | P0 | **DONE** | determinism 0/1364, normalization raises it, not difficulty-driven |
| N-2 | Count-matched collapse rule adopted as PRIMARY | P0 | **DONE** | earned its keep on the third actor (F12) |
| N-3 | Paired A→B transition table | P0 | **DONE** | gpt-oss n=879 +0.017; gemma-4 −0.029 |
| N-4 | Difficulty stratification (risk #2) | P0 | **DONE** | B−A ≥0 in every stratum |
| N-5 | Stability as n grows (risk #3) | P0 | **DONE** | signs stable at 25/50/75/100% |
| N-6 | MECHANISM: why the actors differ (risk #5) | P0 | **DONE** | recovery 0.490→0.045; first-pass unchanged |
| N-7 | Pre-registration provenance | P0 | **DONE** | Case 2; prereg 22:52:33Z < launch 23:00:42Z |
| N-8 | Single-agent control fairness | P1 | **DONE** | control gets MORE oracle exposure — conservative |
| N-9 | frontier-model adjudication of collapse (risk #1) | P0 | ACTIVE | rubric frozen + snapshot taken |
| N-10 | Functional contribution metrics | P1 | ACTIVE | — |
| N-11 | Manuscript rewrite | P0 | ACTIVE | — |
| N-12 | Third actor completion | P1 | ACTIVE | 140/1200; prelim says first-pass collapse 0.000 |
| N-13 | Novelty audit vs redundancy literature (risk #4) | P0 | **DONE** | 4th group paper found; framing constrained to the inversion |
| N-14 | R4 reviewer annotation OR narrow the claim | P1 | TODO | decide after frontier-model adjudication |
| N-15 | C2 strict-computation arm | P2 | **DROPPED_WITH_REASON** | cannot implement a defensible validator before Oct 8 without risking P0s; v3 is the warning |
| N-16 | Final page budget + AAMAS class swap | P0 | TODO | currently 9pp with acmart substitution |
