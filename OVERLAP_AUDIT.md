# Overlap Audit — AAMAS 2027 vs IEEE BigData 2026 (SciAgentTrace)

AAMAS prohibits substantially similar concurrent archival submissions and
thin-sliced contributions. This audit is deliberately conservative: where a
candidate direction reduces to "another characterization of the released
corpus", it is rejected here rather than defended.

## The BigData paper's contribution (as frozen in its MASTER_TODO §1)

Positioned as **large-scale ML workload characterization backed by a released
corpus**. Its claims are about: execution-layer traces, request structure,
elapsed-time/token/request workload axes, held-out predictability (R² ladders),
tail concentration, infrastructure sensitivity, matched-design sampling
efficiency, provenance/availability masks. Its unit is the **trajectory as a
workload object**. Vocabulary: workload, serving, execution layer, scale.

Notably, the BigData paper **explicitly records as a non-finding** the one
outcome-shaped result it found (trace shape "predicts" correctness at AUC≈1.0),
because it is stop-condition leakage.

## Proposed AAMAS contribution

| BigData contribution | Proposed AAMAS contribution | Shared evidence | New evidence | Why technically distinct |
|---|---|---|---|---|
| Corpus of 68,892 trajectories with execution-layer fields; schema; provenance | *No dataset claim at all.* The corpus is an instrument. | the released parquet files | turn-level **confidence-poll panel** (168,540 polls) that the BigData paper never opens, never describes, and does not use | different object: BigData's unit is the trajectory; ours is the **within-turn agent decision** |
| Workload axes diverge (tokens ≠ time ≠ requests) | Speaker-selection rule recovers **none** of the group's distributed knowledge; confidence has a between-problem but no within-turn component | — | d4-d7: counterfactual turn-level scoring of suppressed candidate answers | BigData makes no claim about message selection, agent influence, or aggregation |
| Held-out R² for predicting workload from run features | Protocol accuracy ladder is ~50% oracle-feedback artifact; single-agent iteration has **zero** oracle-free effect | `first_pass_correct` field exists in the release | d1/d8: the decomposition, the paired design, and the interpretation are new | BigData never analyzes accuracy causally; it reports accuracy only as a descriptive column |
| Stop-condition leakage documented as a **reuse hazard** for others | Same stop rule shown to **censor destructive revision**, making "collaboration rarely harms" unfalsifiable on this corpus | the observation that stopping is outcome-dependent | d1: right→wrong = exactly 0 within protocol, and what that invalidates | BigData frames it as a data-reuse caveat; we make it a **statement about what MAS experiments of this shape can and cannot measure** |
| — | **New protocol arms** (blind verifier; selection-rule ablation) | — | entirely new runs | no counterpart in BigData |

## Directions REJECTED by this audit (self-policed)

- *"Characterize deliberation length vs outcome across the five domains."*
  Rejected: this is a dataset characterization result. It is BigData's genre even
  though BigData did not print it.
- *"Cost-per-correction Pareto frontier across protocols."* Rejected: the SC26
  project already computed `utility_resource_frontier.csv`; it is a workload/
  efficiency claim and sits inside BigData's declared scope.
- *"Release the poll panel as a new sub-dataset."* Rejected: makes the dataset the
  contribution again, and would be a thin slice of the same release.

## DHD: excluded, and why

DHD (Diverse Hypothesis Deliberation) is the core asset of a **third, already
public** paper — *Wrong but Useful* (AAAI-WBU, released as
`AgentsSci/AAAI_Wrong-but-Useful`). Using DHD's message-level attribution here
would create overlap with that paper rather than with BigData. Additionally DHD
has a different observational unit (fixed message pool + leave-one-out replay),
which AI4S reviewer 1 already flagged as non-comparable with the end-to-end
protocols. **Decision: DHD is out of scope for the AAMAS paper.**

## Residual risk

The two papers share raw artifacts. Mitigations:
1. The AAMAS paper must not claim the dataset, its schema, or its scale as a
   contribution, and must cite the resource as prior/companion work (blinded).
2. No figure or table may be shared between the two papers.
3. The central AAMAS claim must rest on at least one **new experimental arm**
   that does not exist in the release, so the paper is not evaluable as
   "reanalysis of a released corpus".

---

# UPDATE 2026-09-28 — audit against our OWN two arXiv papers

The binding constraint is no longer external scooping. It is **self-overlap /
thin-slicing**, which AAMAS polices explicitly. Three artifacts now exist on one
corpus, two of them ours and public:

| artifact | contribution | verified |
|---|---|---|
| **arXiv:2609.27822** Jiang, Zheng, Thakur, **Yang** | audits the **confidence-routed broadcast** protocol; separates routing / calibration / commitment | abs fetched, authors confirmed |
| **arXiv:2608.14927** **Yang**, Jiang, Yang, Vasudevan, Zheng, Vishwanath | **cost-aware protocol routing** — predicting which of the 4 protocols pays off | abs fetched, authors confirmed |
| IEEE BigData SciAgentTrace | the dataset/resource | in-repo |

## Distinctness table

| axis | 2609.27822 | 2608.14927 | **proposed AAMAS** |
|---|---|---|---|
| protocol | Broadcast | all four, as choices | **PER** (broadcast only as the comparison organization) |
| object | one scalar (confidence) and its three uses | protocol-level routing decision | **the functional division of labor inside one organization** |
| unit | poll / turn / candidate | trajectory / problem | **role message**, and the role's contract compliance |
| question | is the router picking correctly? | which protocol should we run? | do prompted roles instantiate the intended functions, and does enforcing them change anything? |
| method | observational audit | predictive modelling | **observational measurement + a controlled intervention** |
| intervention | recalibration, alternative routers | none (routing policy) | **generic / soft / architecturally-enforced roles** |

## The hard constraint this places on us

Both prior papers are **observational analyses of the existing corpus**. A third
observational analysis of the same corpus is exactly what "thin-sliced" means,
however different the question.

**Therefore: the AAMAS paper is not viable without the new controlled arms.**
The existing-trace work (r1-r12) is the *motivation and the instrument*, not the
contribution. If the experiment does not run, we should not submit.

This is a stronger conclusion than the earlier draft of this audit and it
supersedes it.

## Self-rejected again
- *"Measure role fidelity across the five domains and report the variation."*
  Rejected: observational, same corpus, third slice. Also invalid as such
  (see DEFECT-prompt-varies-by-domain.md).
- *"Show PER and Broadcast rank differently by actor."* Rejected: adjacent to
  2608.14927's protocol-routing framing and observational.

## Double-blind hazard
Both papers are by this author group on this corpus. Cite them in third person
("prior work audits...", "a companion resource releases..."), never "our".
Avoid naming the HF org `AgentsSci` or the GitHub account in the submitted text.


---

# UPDATE (session 4) — the intellectual object, stated once

Per Bella: the AAMAS paper claims novelty in **none** of confidence routing,
calibration, commitment, protocol routing, or dataset/resource contribution.

**The intellectual object is: specified roles vs realized inter-agent organization.**

| our prior artifact | its object | ours |
|---|---|---|
| arXiv:2609.27822 | one scalar (confidence) and its three uses inside broadcast | — |
| arXiv:2608.14927 | which protocol to run (routing across protocols) | — |
| IEEE BigData SciAgentTrace | the corpus as a resource | — |
| **AAMAS 2027** | — | **whether a specified division of labor is realized, and whether enforcing it structurally changes the organization's effectiveness across actor substrates** |

None of the three prior artifacts measures role behaviour, and none contains an
intervention. The measurement suite (validated, κ 0.81/0.84) and Arm C are both
new. That is the separation.

**Standing constraint, unchanged and now firmer:** all three prior artifacts are
*observational analyses of this corpus*. A fourth observational analysis is
thin-slicing by definition. **The controlled arms are the precondition for
submitting, not an enhancement.**
