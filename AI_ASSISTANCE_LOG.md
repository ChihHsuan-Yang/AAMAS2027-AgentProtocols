# AI Assistance Log — AAMAS 2027 submission

AAMAS 2027 permits AI-assisted research but requires disclosure, **including the
prompt**, when AI is used in hypothesis creation, methodology creation, or
experimental design. This file is the running record. It is maintained from the
first day of the project, not reconstructed at submission time.

## Tool

| Field | Value |
|---|---|
| System | Claude Code (Anthropic), agentic CLI |
| Model | Claude Opus 5, model id `claude-opus-5[1m]` |
| Mode | Autonomous analysis with human (Bella Yang / Chih-Hsuan Yang) direction and approval gates |
| Human approval required for | any new HPC generation, training, or benchmark campaign |

## 2026-09-28 — Session 1: discovery

### Human instruction (abridged; full text archived in `notes/prompts/2026-09-28-session1.md`)

Bella directed: start a new, independent AAMAS 2027 project distinct from the
IEEE BigData SciAgentTrace dataset paper; treat the existing experiments as a
multi-agent researcher and ask *"what important scientific insight about
LLM-based multi-agent systems is latent in these experiments that we have not
yet recognized?"*; do not preserve the current paper story; reconstruct the four
protocols from code rather than names; investigate DHD and decide whether to use
it; run deep exploratory analysis (outcome transitions, communication
benefit/harm, role influence, topology, diversity, error propagation, expertise,
problem-conditional coordination, saturation); do qualitative trace analysis;
propose 5-8 candidate paper directions; explicitly audit overlap with the
BigData paper; do not launch large HPC runs before discussion.

She supplied the three candidate directions A (when should agents collaborate),
B (what makes a protocol work), C (when collaboration hurts) explicitly as
"starting hypotheses, not orders", and authorised new protocols, new benchmarks,
and training if scientifically motivated.

### AI-generated (Claude Opus 5), pending human decision

**Analyses designed and executed by the AI:**
- `d1` decomposition of protocol gain into oracle-free vs oracle-gated components
  using `first_pass_correct` as a zero-feedback comparison point.
- `d2` extraction of the broadcast confidence-poll panel (168,540 polls).
- `d3` answer grader + calibration against recorded labels before any use.
- `d4`/`d5` turn-level counterfactual evaluation of the speaker-selection rule
  against random / majority / best-available baselines, clustered bootstrap.
- `d6` between/within variance decomposition of self-reported confidence.
- `d7` within-turn discrimination test across five candidate selection features.
- `d8` oracle-budget-matched protocol comparison.

**Hypotheses proposed by the AI (human has not yet accepted any):**
1. Confidence-gated speaker selection recovers none of the group's distributed
   knowledge because self-reported confidence is a problem-difficulty signal
   with no within-turn (inter-agent) component.
2. The published protocol ordering is ~50% attributable to an oracle-feedback
   budget asymmetry rather than to multi-agent structure.
3. Within-protocol destructive revision is censored by the stop-on-PASS rule and
   therefore unmeasurable in this corpus.

**Experimental designs proposed by the AI (not yet run, not yet approved):**
see `notes/EXPERIMENT_PROPOSALS.md`.


### Corrections made by the AI to its own earlier output (same session)

Recorded because the AAMAS disclosure should show what the AI got wrong, not
only what it proposed.

| # | Claim first reported | Defect | Corrected to |
|---|---|---|---|
| 1 | "peer approval AUC 0.631 vs confidence 0.4975" | not like-for-like: approval panels review ONE candidate, so 0.631 is a between-problem quantity; 0.4975 is within-turn | like-for-like within-problem test (d10): approval 0.5297 [.5080,.5519] |
| 2 | "peer agreement is the only within-turn feature with signal (AUC 0.530)" | significant only POOLED; the pre-registered per-actor split (d11) straddles 0.5 in both arms | reported as under-powered, NOT as an established signal |
| 3 | `has_candidate` flagged "SIGNAL" by the AUC script | flag-logic bug on a constant feature (AUC exactly 0.5, zero-width CI) | no information; flag logic is wrong for degenerate variables |
| 4 | "accuracy declines across discussion turns" (first pass) | survivorship: harder problems run longer | re-run within-trajectory on a balanced panel; the decline disappears, disagreement growth remains |

### Held-out confirmation performed (d11)

The AI pre-registered three predictions, then tested them on a held-out actor
model (gemma_4_31b, 14,559 polls, never used for tuning). P1 (confidence null)
and P3 (selection null) replicated; **P2 (agreement signal) failed**. The AI
reported the failure rather than substituting the pooled analysis.

### Net effect on the proposed contribution

The AI's initial framing ("confidence gate fails, peer assessment fixes it") was
**downgraded by its own subsequent analysis** to "confidence gate fails, and no
oracle-free local channel we tested recovers the group's knowledge either".
Human has not yet ruled on whether to pursue this framing.

### Human decisions

| Item | Status |
|---|---|
| (pending — first report delivered 2026-09-28) | awaiting Bella |


---

## 2026-09-28 — Session 2: redirect to role specialization

### Human instruction (Bella), abridged; full text archived in `notes/prompts/2026-09-28-session2.md`

Redirect away from confidence routing, which is now bounded by arXiv:2609.27822.
Investigate instead: *do role-based LLM MAS actually realize the functional
division of labor their role labels claim to impose, and can differences in
realized specialization explain why the same protocol behaves differently across
actor models?* Explicitly instructed: treat this as a HYPOTHESIS and **try hard
to falsify it**; do not write the paper around the claim until evidence earns it;
exhaust existing traces before proposing endpoint runs; define functional
specialization and role fidelity separately; build a role-behaviour taxonomy;
validate the measurement by hand; distinguish distinguishability from fidelity;
stratify before pooling; run a fresh novelty audit; predefine outcome
interpretations; maintain a claim ladder; do not force a training contribution.

### AI-designed analyses (r1-r9), executed this session
Contract-derived feature extraction; role distinguishability under two feature
sets with trajectory-grouped CV; component-wise fidelity; a stratified 240-message
validation sheet; within-domain re-analysis after a defect was found; mechanism
test with leakage control; endpoint budget reconstruction; power analysis.

### AI-generated hypotheses and designs — human has NOT ruled on any
See `notes/DECISION-REPORT-2026-09-28.md` §G/§H and `notes/EXPERIMENT_PROPOSALS.md`.

### Errors the AI made and corrected WITHIN this session (disclosed deliberately)

| # | Error | How caught | Correction |
|---|---|---|---|
| 1 | Scored all five domains against the Omni-MATH role contract | Checked the per-domain prompt presets | Only omni_math contains "MUST NOT compute"/"Diagnosis:"/"Target quantity". Cross-domain fidelity comparisons **dropped**, not caveated. `notes/DEFECT-prompt-varies-by-domain.md` |
| 2 | Fidelity metric P1 defined relative to the Executor's density | Hand-reading 6 Planner messages | 22 of 49 scored "violations" were planners with ZERO computation. Rebuilt as an absolute measure (r5) |
| 3 | "Fidelity predicts correctness, +0.61" | Implausible size → checked | Stop-condition leakage; message count correlates −0.910 with first-pass correctness. Leak-controlled estimate is +0.127, and null on hard problems |
| 4 | Power table interpretation said "n=200 gives >0.9" under a table showing 0.28 | Re-read own output | Corrected in `notes/POWER.md` |
| 5 | Claimed an organization × actor "sign reversal" | Tested on the common problem set | gpt_oss is NOT significantly positive on the 828 problems gemma3 ran. The **interaction** survives (+0.1522); the **reversal** framing does not |

### Net effect
The session's headline hypothesis was **partly falsified by our own analysis**:
roles ARE highly distinguishable (0.896 balanced accuracy), so the strong form
("role labels do not induce distinct behaviour") is false and was abandoned.
What survives is narrower and is recorded in the claim ladder.


---

## 2026-09-28 — Session 3: validation, novelty verification, design

Human instruction archived at `notes/prompts/2026-09-28-session3.md`. Bella
directed: drop the falsified strong framing; preserve the narrower claim;
complete the 240-message validation before any endpoint campaign (0.8 agreement
as go/no-go, plus inspection of error KIND); verify the novelty boundary
especially whether prior "strong" specialization is architectural or prompted;
finalize a 3-arm design; re-size with real throughput; predefine five outcome
interpretations; verify OpenReview/administration without inferring.

### AI work this session
r10 (rebuilt validation sample, balanced on actor x automated label), r11
(human adjudication with per-item reasons), r12 (corrected metric + actor
ordering re-test), r13 (three sizing options with wall-clock from observed
means). Design amendments; overlap audit updated against 2609.27822 AND the
newly-found 2608.14927.

### Errors the AI made and corrected in this session

| # | Error | Caught by | Correction |
|---|---|---|---|
| 1 | Cited 2602.03128 "Table 12" as already running our Arm A vs B | targeted re-verification | **v2 exists** and renumbered it to Table 14 with a 4th condition; also I had implied it ignores model-dependence when its §4.1.3 tests 8 models |
| 2 | Annotated validation case [19] as E2-correct, then "corrected" it to a false positive, then checked the text | reading the actual message | The message has ZERO "plan"/"Planner" occurrences; auto fired on "Step 0"/"Inductive step" in the Executor's own construction. My first instinct was right, my mid-course correction was wrong, the final label is the verified one |
| 3 | Drafted Arm C removing the Reviewer's answer field | offline smoke test | The Reviewer contractually OWNS submission and emits the answer 41-42% of the time; removing the field would confound enforcement with a changed submission path. Fixed to submit-by-reference |
| 4 | Sized wall-clock from median trajectory time | noticing skew | PER is heavily right-skewed (omnimath2/gemma mean 514s vs median 118s); medians understate ~4x. Re-done with means |

### Net effect on the scientific claim
Validation PASSED (P1a 0.967/kappa 0.933; E2 0.923/kappa 0.843) but rebuilding
E2 **flipped the actor ordering on that component**, and the two fidelity
components now disagree about which actor is most faithful. Reported rather than
reconciled. The AI also identified that self-overlap (three group artifacts on
one corpus) now makes the controlled experiment a precondition for submitting at
all, not an enhancement.

### Human decisions
| item | status |
|---|---|
| Launch of the endpoint campaign | **NOT approved; nothing launched** |
| Arm set A/B/C, D dropped | proposed, awaiting Bella |
| 3 actors x n=400 over 2 actors x n=800 | proposed, awaiting Bella |


---

## 2026-09-28 — Session 4: validation completed, design frozen, budgets corrected

Prompt archived at `notes/prompts/2026-09-28-session4.md`. Bella set the framing
(inter-agent division of labor enforced structurally, tested across actor
models), held the endpoint run, and required: complete the annotation sheet;
make Arm C auditable; treat Arm B as control; pick the third actor on scientific
grounds; recompute budgets for 3 arms; pre-register the tests; stress-test the
distinction from 2608.21747; revisit the claim ladder; keep admin unverified-
labelled.

### AI work
r10-r16: rebuilt validation sample; 85 hand adjudications with recorded reasons;
metric correction and freezing; capability-vs-fidelity dissociation; final
budgets at validated concurrency. Documents: VALIDATION-FINAL, PREREGISTRATION,
NOVELTY-STRESS-TEST, CLAIM-LADDER-v2, THIRD-ACTOR, GO-NOGO.

### Errors the AI made and corrected in this session

| # | Error | Caught by | Correction |
|---|---|---|---|
| 1 | Built a P1a "v3" with an instruction-exclusion and a symbolic-result detector | Re-scoring against the human annotations | **Made agreement WORSE (0.903 -> 0.694).** The detector fired on 9/9 compliant messages, including on "The answer should be a single integer" — the contract's REQUIRED answer-form section. It penalised compliance. **v3 rejected; v1 frozen with its limitation documented.** |
| 2 | Annotated [118] and [111] as compliant | Re-reading what the pattern matched | [118] genuinely computes 2024=2^3*11*23 and (3+1)(1+1)(1+1)=16 — my label was wrong, not the metric's |
| 3 | Reported P1a agreement 0.967 | Continuing the sheet to n=72 | Fell to 0.903 as annotation continued; the early figure was optimistic |
| 4 | Budgeted at concurrency 32-64 | Infrastructure audit | **No precedent anywhere in the project.** Tested-clean is 25 (OSS) and 8-10 (Gemma); 50 was *slower* than 25. Gemma-4 is 4-5x slower per call. Budgets re-derived: preferred run 63.5 h, not 24.5 h |
| 5 | Relayed "AURORA IS DOWN" from a subagent | Probing the host directly | `aurora.alcf.anl.gov:22` is **OPEN**. A status file is not a present-tense check |

### Net effect
Validation PASSED and the actor-dependence survived freezing, but the two
fidelity components order the actors differently and the mediation claim
weakened accordingly. The AI identified a *falsifiable* discriminator from
2608.21747 (capability and realized fidelity are anti-correlated), and flagged
that it currently rests on a single actor pair.

### Human decisions
| item | status |
|---|---|
| Endpoint campaign | **NOT launched. Awaiting Bella's go.** |
| Framing (inter-agent division of labor, structurally enforced) | set by Bella |
| Arm D dropped; Arm B = control | Bella concurred |
| Third actor = gemma3_27b | AI recommendation, awaiting Bella |
| Scale = PREFERRED (n=400, 2 domains) | AI recommendation, awaiting Bella |


---

## 2026-09-28/29 — Execution phase (sessions 5-7)

**Tool:** Claude Code, Claude Opus 5 (`claude-opus-5[1m]`), acting as Master
Agent with sub-agents. **Human:** Bella Yang, who set the direction, ordered
the storyline pivot, and required blinded frontier-model adjudication.

### Human instructions (archived in `notes/prompts/`)
Bella (a) moved the project into execution mode with authority to run
endpoints/HPC and dispatch sub-agents; (b) **pivoted the storyline** away from
"specified vs realized organization" to *"when is multi-agent organization
load-bearing?"*, naming the candidate headline and requiring it be
stress-tested rather than assumed; (c) replaced the collapse-validation plan
with **blinded Opus-5 adjudication**, specifying rubric freezing, blinding,
repeated independent calls, and a full audit trail; (d) removed OpenReview from
the agent's scope.

### AI-generated, human-approved
Experimental design (arms A/B/C/C′), the functional-collapse measure, the
mechanism analysis, the adjudication protocol, and all analysis code.

### A frontier model was used as a MEASUREMENT INSTRUMENT, not only as an author
Opus 5 served as the blinded adjudicator for the collapse construct
(`adjudication/`). This is disclosed in the paper as model-based adjudication,
explicitly **not** human ground truth, with judge, protocol, rubric hash,
stability, and limitations reported.

### Errors the AI made and corrected, this phase
| # | error | caught by | correction |
|---|---|---|---|
| 1 | Arm C validators rejected valid plans (string-vs-array; LaTeX escapes; max_tokens truncation) | live smoke + campaign monitoring | three fixes, each re-verified against planted violations; 121 rows quarantined |
| 2 | Gate script read `violated_constraint` at the wrong nesting level | auditing my own gate output | reported 0 boundary violations when there were 5 |
| 3 | Gate 4 compared realized mean calls, not budget | reading the failure | redefined to median + shared ceiling |
| 4 | Relayed a worker's "AURORA IS DOWN" from a stale status file | probing the host | port 22 was open |
| 5 | Called the first collapse pass "human validation" | reading the worker's own limitations section | it was an LLM sub-agent; relabelled, and the error disclosed |
| 6 | Reported byte-collapse 0.367 as "fully logged" | re-deriving with a strict filter | the filter did not mean what its label said; no point estimate is reportable (0.630/0.284/0.176/0.083 across thresholds) |
| 7 | Blinding leak: role names in transcripts, 42 Arm A vs 3 Arm B | pre-run leak audit | neutralized uniformly before any judging |
| 8 | Adjudication `max_tokens` too small — 25% empty verdicts | parse-failure triage | raised and re-queued; would have biased coverage toward easy items |

### Claims RETRACTED after evidence
- "gemma-4 shows no first-pass collapse" (byte-metric artifact; recall 0.343)
- "the actor that collapses most loses least" (both actors lose it equally)
- the byte-collapse magnitude (logging defect)
- my own 0.367 correction (bad filter)

### Net
The launch hypothesis was **falsified by the project's own data** twice, and
the pre-registered primary test returned null. The surviving contribution is
narrower, better supported, and reported with its failures intact.
