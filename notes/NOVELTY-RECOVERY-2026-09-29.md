# Novelty audit — role ablation and recovery-after-feedback (2026-09-29)

Commissioned adversarially: find the scoop, do not reassure.
Scope: the newly-formed 5-part claim about role differentiation and recovery.
Prior audits (`NOVELTY-AUDIT.md`, `NOVELTY-AUDIT-ROLES.md`) covered
redundancy / specialization / "does MAS help" and are NOT repeated here.

---

## 1. VERDICT

**PARTIALLY NOVEL, and narrower than the claim as currently written.** Three of
the five sub-claims are substantially anticipated. Sub-claim 1 (role-free matches
role-labeled on first-pass) is **background, not a finding** — it is owned by
2609.04217, 2402.18272 and 2602.03128 and a reviewer will treat it as settled.
Sub-claim 3's *hypothesis* (premature consensus / early convergence) is a crowded
field — at least nine papers name it — so our refutation must be framed as
"we test and reject the standing explanation," never as raising a new one.
Sub-claim 4 is the dangerous one: **the phenomenon of feedback-resistant answer
repetition is already published.** Liang et al.'s Degeneration-of-Thought
(2305.19118) defines it conceptually for self-feedback; Stechly et al.
(2402.08115) run the closest *setting* to ours — a binary oracle "your previous
answer was wrong" backprompt under a retry budget — and 2609.28150 ("Exact
Feedback Is Not Control", posted **six days before this audit**) reports in as
many words that "failed trajectories often repeat earlier outputs" under
complete, correct external verifier feedback. We cannot claim to have discovered
that LLMs restate answers under external correction. **What survives as genuinely
novel is sub-claim 2 and the dissociation in sub-claim 5**: nobody has ablated
role differentiation while holding first-pass accuracy fixed and shown that the
*recovery* conditional is what collapses (0.50 → 0.02–0.05), and nobody has
measured distinct-answer counts per trajectory as the mediating variable across a
role / role-free contrast. The paper must lead with **recovery as a separable
capability that role structure buys**, with answer lock-in as the *measured
mediator* — citing the lock-in literature as the mechanism we inherit, not as one
we found. Reframed that way the contribution holds. Left as written, sub-claims
1, 3 and 4 will each draw a "this is known" and take the paper down with them.

---

## 2. EVERY WORK CHECKED

Ratings: **SCOOPED** (same claim, same evidence type) / **STRONG OVERLAP** (same
claim, different setting or weaker evidence) / **ADJACENT** (related but distinct)
/ **DISTANT**.

### 2a. Self-correction and external feedback

| id | work | rating | what it actually shows |
|---|---|---|---|
| 2609.28150 | Exact Feedback Is Not Control (Jiang et al., 2026-09-23) | **STRONG OVERLAP** | Deterministic verifiers report ALL remaining violations; "failed trajectories often repeat earlier outputs," recurrence predicts lower recoverability. 19 models, 17.4–99.8% final success. Single-agent, no roles, constraint-satisfaction text (length/lexical/compositional) |
| 2402.08115 | On the Self-Verification Limitations of LLMs (Stechly, Valmeekam, Kambhampati) | **STRONG OVERLAP** | Tests a **binary** backprompt saying "the previous answer was wrong but doesn't elaborate" (36/38/60/10% across 4 domains) vs first-error vs all-error vs bare re-prompting. Feedback *content* is largely irrelevant; sound verifier + re-prompting keeps most of the gain. No answer-repetition metric. Single-agent, no roles |
| 2310.12397 | GPT-4 Doesn't Know It's Wrong (Stechly et al.) | ADJACENT | Graph colouring; LLMs no better at verifying than solving; criticism correctness "largely irrelevant" to iterative prompting |
| 2310.08118 | Can LLMs Really Improve by Self-critiquing Their Plans? (Valmeekam et al.) | ADJACENT | Self-critique *diminishes* plan generation; LLM verifiers emit many false positives |
| 2310.01798 | LLMs Cannot Self-Correct Reasoning Yet (Huang et al., ICLR 2024) | **STRONG OVERLAP** (one number) | Scoped to *intrinsic* correction. Oracle labels are used only as a **stopping criterion**, and in that condition performance **improves** (GSM8K 75.9→84.3 GPT-3.5; 95.5→97.5 GPT-4). GPT-3.5 **retains its original GSM8K answer 74.7% of the time** — the closest published analogue to our lock-in rate |
| 2406.01297 | When Can LLMs Actually Correct Their Own Mistakes? (Kamoi et al., TACL 2024) | ADJACENT (inverted) | Concludes "self-correction works well in tasks that can use reliable external feedback." Our result is a **counterexample** to this in the role-free multi-agent case — position as such |
| 2507.02778 | Self-Correction Bench (Tsui, COLM 2026) | ADJACENT | 64.5% blind spot: models fix externally-attributed errors but not identical self-attributed ones. Manipulation is *attribution*, not a wrongness signal. "Wait" cuts the gap 89.3% |
| 2511.21591 | On the Limits of Innate Planning in LLMs | ADJACENT | Tiered corrective feedback helps some pairs; with a legal-move validator **no model solves any 8-puzzle**; models loop. Planning, not answer revision |
| 2608.30413 | DERELAB (EMNLP 2026) | ADJACENT | Models "correctly identify a weakening update yet fail to revise their conclusion." Single-agent defeasible reasoning; evidence, not correctness feedback; no rate given |
| 2501.01457 | Beyond Introspection / DRR | ADJACENT | "Introspection illusion": self-critique inherits the original's biases; external discriminator works better |
| 2410.20513 | Self-correction is Not An Innate Capability | ADJACENT | Models "neither morally sensitive nor able to effectively incorporate external feedback" — **moral** domain only |
| 2602.16066 | Improving Interactive ICL from NL Feedback | ADJACENT | Top models "struggle to integrate corrective feedback on hard reasoning tasks"; training fixes much of it |
| 2602.16488 | Social Meta-Learning | ADJACENT | Baseline LLMs "often struggle to learn from corrective feedback," rarely ask for it |
| 2503.16022 | Corrective In-Context Learning | ADJACENT | Past errors + ground-truth corrections in the prompt **underperform** standard ICL |
| 2601.00828 | Decomposing LLM Self-Correction | ADJACENT | Error-**location** hints hurt all models |
| 2509.25370 | AgentDebug | DISTANT | Root-cause feedback *enables* recovery, +26% relative |
| 2510.21861 | The Mirror Loop | DISTANT | Ungrounded self-loops stall; a verification step restores progress |

### 2b. Answer lock-in, perseverance, repetition

| id | work | rating | what it actually shows |
|---|---|---|---|
| 2305.19118 | Encouraging Divergent Thinking / **Degeneration-of-Thought** (Liang et al., EMNLP 2024) | **STRONG OVERLAP** | DoT: "once the LLM has established confidence in its solutions, it is unable to generate novel thoughts later through reflection even if its initial stance is incorrect." **Self**-feedback, single model; the prescribed cure is multi-agent debate/diversity. Conceptually our phenomenon, one level up the stack |
| 2512.20845 | MAR: Multi-Agent Reflexion | **STRONG OVERLAP** (weak evidence) | "the LLM continues to repeat the same errors again and again even with the knowledge that its wrong"; multi-persona debaters raise reflection diversity. No distinct-answer count, no role-free control, no oracle. Visibly unedited abstract — low-quality but claims our shape |
| 2503.13657 | MAST / Why Do Multi-Agent LLM Systems Fail? (Cemri et al.) | ADJACENT | Confirmed modes: **FM-1.2 Disobey role specification, FM-1.3 Step repetition, FM-1.4 Loss of conversation history, FM-1.5 Unaware of stopping conditions, FM-2.1 Conversation reset, FM-3.1 Premature termination.** Step repetition is action-level, not answer-identity, and never tied to a role ablation |
| 2608.19072 | What is Missing from AI Post-Training AI | ADJACENT | **Strategy** lock-in: only 2.1% of adjacent-run transitions change strategy; "the decision to reopen a committed strategy" is the gap. Strategies, not answers; no correctness feedback |
| 2609.32035 | Reasoning Concentrates Errors | ADJACENT | Counts distinct answers (reasoning gives 0.43–0.65× the non-reasoning count) — but across **independent samples**, no feedback, no rounds, no roles |
| 2606.02646 | The Ringelmann Effect in Multi-Agent LLM Systems | ADJACENT | Answer-diversity scaling law; "Thirty dense debating agents produce no more answer diversity than one on MMLU-Hard"; a noise placebo matches self-correction, so gains come from re-evaluation not peer content |
| 2510.08483 | DeepPrune | DISTANT | >80% of parallel traces yield identical final answers; an efficiency result |
| 2604.16027 | Where does output diversity collapse in post-training? | DISTANT | Answer-level diversity as a training diagnostic |
| 2209.12687 | The "A.I. Locked-In Problem" | DISTANT | GPT-3 agents get stuck in a narrative; anecdotal case report |
| 1606.07356 | Analyzing the Behavior of VQA Models | DISTANT | VQA models "stubborn," don't change answers across images. Pre-LLM, wrong sense |

### 2c. Premature consensus / early convergence

| id | work | rating | what it actually shows |
|---|---|---|---|
| 2509.23055 | Peacemaker or Troublemaker | ADJACENT | Sycophancy "collapse[s] debates into premature consensus," below single-agent accuracy; separate debater- and judge-driven pathways |
| 2510.20963 | When and Why Does Multi-Agent Debate Fail? | ADJACENT | Consensus-seeking debate "filters out informative disagreements for premature consensus"; ColMAD gains up to 10pp |
| 2408.13406 | Collaboration Dynamics in FEA | ADJACENT | "Premature consensus caused by redundant reviewers"; affirmation bias 85–92%; 7 role configurations × 4 tasks, 1,120 trials — **more reviewers lowered success** |
| 2502.15153 | When Disagreements Elicit Robustness | ADJACENT | Broad partial disagreement "prevent[s] premature consensus and expand[s] the explored solution space" |
| 2608.20564 | Consilience | ADJACENT | Treats premature consensus as a measurable per-turn state variable |
| 2509.23537 | Beyond the Strongest LLM | ADJACENT | Live vote tallies "amplif[y] herding, which speeds convergence but can sometimes yield premature consensus" |
| 2511.06134 | Maestro | DISTANT | Architectural fix separating divergent and convergent modes |
| 2605.24755 | Delusion-related content detection | DISTANT | Debate hurt accuracy "by inducing premature consensus"; majority voting more robust |
| 2605.24138 | Conversational Patterns in Multi-agent Programming | DISTANT | Calls for better calibration of convergence and stop conditions |

### 2d. Conformity, groupthink, diversity as the active ingredient

| id | work | rating | what it actually shows |
|---|---|---|---|
| 2503.16814 | From Belief Entrenchment to Robust Reasoning (TACL) | **STRONG OVERLAP** (mechanism) | "Belief entrenchment": agents "reinforce shared errors rather than correcting them," from biased static initial belief + "homogenized debate dynamics." Fix = "enforcing perspective diversity." No external correctness feedback, no role ablation, no recovery conditional |
| 2511.07784 | Can LLM Agents Really Debate? | ADJACENT | "intrinsic reasoning strength and group diversity are the dominant drivers"; "majority pressure suppresses independent correction." No told-you're-wrong condition |
| 2601.19921 | Demystifying Multi-Agent Debate | ADJACENT | With homogeneous agents and uniform updates "debate preserves expected correctness"; names diversity of initial viewpoints + calibrated confidence as the two missing mechanisms |
| 2410.12853 | Diversity of Thought Elicits Stronger Reasoning | ADJACENT | Mixed medium-model trio 91% GSM-8K vs three Gemini-Pro copies 82% — an explicit homogeneity penalty |
| 2509.05396 | Talk Isn't Always Cheap (ICML MAS WS) | ADJACENT | Accuracy **decreases** over debate rounds even when strong models outnumber weak; models shift correct→incorrect, "favoring agreement over challenging flawed reasoning" |
| 2606.00820 | Not All Flips Are Conformity | ADJACENT | Decomposes flips into spontaneous instability / stance conformity / reasoning persuasion. 37% change under self-reflection alone; strict conformity 29%, 57–77% correct→wrong. **Measures flips, not distinct-answer counts**; no role-free arm |
| 2501.13381 | Do as We Do, Not as You Think (ICLR 2025 Oral) | ADJACENT | BenchForm; conformity rate / independence rate; explicit groupthink framing |
| 2410.12428 | Conformity in Large Language Models (ACL 2025) | ADJACENT | Models align with the majority "regardless of their initial choice or correctness" |
| 2607.05545 | Most LLM Conformity Needs No Speaker | ADJACENT | A no-source repeated wrong answer drove harmful revision in 66.5% of initially-correct cases vs 10.3% for plain re-asking — a **methodological warning for our own retry prompt** |
| 2605.12991 | Not Just RLHF | ADJACENT | "Yield" metric; one correct dissenter cuts yield 54–73 points; fixes belong at pipeline structure |
| 2311.17371 | Should we be going MAD? (Smit et al.) | ADJACENT | MAD does not reliably beat other prompting; tuning **agent agreeableness** is the lever that makes it win |
| 2608.02827 | Emergence of Biased Consensus (ICML 2026) | DISTANT | Phase transition to collective bias; heterogeneity smooths it |
| 2411.04427 | One fish, two fish | DISTANT | Alignment reduces the output diversity debate depends on |

### 2e. Roles, role ablation, role collapse

| id | work | rating | what it actually shows |
|---|---|---|---|
| 2609.04217 | At Equal Inference Cost, Multi-Agent Structure Does Not Beat a Single Frozen Agent | **STRONG OVERLAP** (sub-claim 1) | Planner–Executor–Critic on a frozen 7B. Full team 0.769 vs 0.754, **p = 0.80**, at 1.8× calls; leave-one-in attributes everything to the executor; "the planner and critic evolve to empty or low-impact prompts and rarely change the executor's action." **Only aggregate task success — no retry or recovery metric** |
| 2602.03128 | Architectural Design, Not Only Model Intelligence | **STRONG OVERLAP** (sub-claim 1) | "Role-based conditioning fails to induce specialization"; "role labels should be secondary" |
| 2402.18272 | Rethinking the Bounds of LLM Reasoning (Wang et al.) | **STRONG OVERLAP** (sub-claim 1) | A single agent with a strong prompt ≈ the best discussion method; discussion wins only with no demonstrations |
| 2608.30373 | Beyond Consensus: Downward Bias and Role Asymmetry (Findings EMNLP 2026) | ADJACENT | Three ablations isolate **role prompting** vs multi-round interaction vs score sharing; degradation is due to "asymmetric role prompting rather than the interaction itself"; Symmetric MAD recovers baseline. Judging, not problem solving; no recovery metric |
| 2608.06949 | Does Splitting a Triage Decision Across Agents Hide Bias? | ADJACENT | 9-agent role-differentiated pipeline vs single-agent control: bias indistinguishable (6.9% vs 6.1%, p=0.498) — a clean role-ablation **null**, on bias not recovery |
| 2607.27512 | Belief Coevolution in a Social Network | ADJACENT | Persona-style roles alter individual belief revision "but have minimal effect on population-level consensus"; finetuned specialists do |
| 2507.11198 | Temperature and Persona Shape LLM Agent Consensus | ADJACENT | Mixed personas delay consensus; **no robust accuracy gains**; single agents match or beat MAS in most conditions |
| 2607.21627 | Do Modules Stay in Their Lane? Role Drift | ADJACENT | Role drift in compound systems (from prior audit) |
| 2604.03809 | Representational Collapse in Multi-Agent LLM Committees | ADJACENT | Agents differing only by role prompts collapse representationally (effective rank 2.17/3.0) |
| 2608.09023 | AI-AI co-creation | ADJACENT | Complementary generator-evaluator roles vs **identical-role** AI pairs — a true differentiation ablation, on creativity |
| 2609.14570 | Disentangling Topology and Diversity | ADJACENT | Preferred topology depends on diversity source |
| 2605.15245 | Assistance to Autonomy (SLR) | DISTANT | Names "the Planner-Executor-Reviewer role specialization as the dominant architectural pattern" — useful for motivating our pipeline as representative |

### 2f. Recovery as an explicit metric

| id | work | rating | what it actually shows |
|---|---|---|---|
| 2603.09641 | PRECEPT | ADJACENT | **Explicitly separates "first-try" advantage from "drift recovery" gains** — the closest metric decomposition found. Planning resilience; no role manipulation |
| 2607.06273 | AgentTether | ADJACENT | Reports the fraction of **initially failed** tasks repaired (59.04% on Banking) — a recovery conditional, no roles |
| 2607.18754 | AgentDebugX | ADJACENT | Tasks repaired on rerun after failure (13/73 GAIA) |
| 2606.01416 | Self-Healing Agentic Orchestrators | ADJACENT | "Matched recovery-budget sweep" — budget-matched recovery, our closest methodological precedent |
| 2604.04258 | Context Engineering | ADJACENT | First-pass acceptance 32%→55% reported **separately** from a 91.5% iteration-permitted rate. Human-AI workflow, not agents |
| 2607.17641 | Verify, Repair, Repeat, or Stop? | ADJACENT | Final validity after repair rounds vs initial |
| 2605.08563 | Why Retrying Fails: Context Contamination | ADJACENT | Failed attempts stay in context and raise per-step error rate (cascade ratio ε1/ε0 ≈ 7.1); IID overestimates pass@3 by 17.4pp. **A confound we must rule out** — no answer-identity measurement |
| 2606.29270 | Minority Sentinel | ADJACENT | Flip Precision / Net Gain / "recovery volume" in debate |

### 2g. Critic / reviewer rubber-stamping

| id | work | rating | what it actually shows |
|---|---|---|---|
| 2507.11662 | Let's Think in Two Steps (Self-Grounded Verification) | ADJACENT | Names **agreement bias**: MLLM verifiers "over-validate agent behavior," pervasive and "resilient to test-time scaling"; 13+ models; SGV +25pp failure detection |
| 2408.13406 | Collaboration Dynamics in FEA | ADJACENT | Affirmation bias: 85–92% agreement including on errors |
| 2604.22971 | Peer Identity Bias (TRUST) | ADJACENT | Homogeneous ensembles "amplify identity-driven sycophancy"; one model had near-zero deliberative conflict |
| 2510.07517 | When Identity Skews Debate (ACL 2026) | ADJACENT | Identity-driven sycophancy > self-bias; Identity Bias Coefficient |

### 2h. Self-overlap (same lab / same corpus)

| id | work | rating | note |
|---|---|---|---|
| **2608.14927** | **Cost-Aware Protocol Routing Across Reasoning Tasks (Yang et al.)** | **SELF-OVERLAP — HIGHEST RISK** | **Our own group.** Runs **planner-executor-reviewer (PER)** as one of four protocols on **4,181 competition math problems**, same solver held fixed, plus a "retrospective fixed-order oracle" (92.4% solve). Same pipeline, same domain, same lab. A reviewer who finds this will ask what is new. Must be cited and differentiated in the intro, not buried |
| 2609.27822 | confidence routing audit (Yang et al.) | SELF-OVERLAP | Third paper on this corpus; thin-slicing risk flagged in the prior audit persists |

---

## 3. CLOSEST PRIOR WORK

### 3.1 — 2609.28150, "Exact Feedback Is Not Control" (Jiang, Liu, Wang, Feng; 2026-09-23). **STRONG OVERLAP. The most dangerous paper in this audit.**

Posted six days before this audit. A fixed-budget revision protocol with
deterministic verifiers that surface *every* remaining violation — so feedback
correctness and completeness are held fixed and only model-side revision behavior
varies. 19 open and closed models, final joint success 17.4%–99.8%. The finding
that collides with us: across every constraint family, **failing trajectories
reproduce earlier outputs, and prior recurrence predicts lower subsequent
recoverability.** Matched-state interventions that strip earlier dialogue while
holding the draft and feedback constant change recurrence escape "without
reliably improving final success." Its closing line is effectively our sub-claim 4:
*"Exact feedback makes revision errors observable, but does not make the closed
loop reliable."*

**How we differ, precisely.** (a) Single-agent self-revision against a
programmatic checker; **no multi-agent system and no roles at all** — the word
"controller" there means the revising model, not a persona. (b) Domain is
constraint-satisfaction text generation (exact-length, lexical, compositional),
not math/science reasoning with an answer to be judged right or wrong. (c) Their
feedback enumerates violations; ours is an oracle correctness verdict that returns
the team for another attempt. (d) Crucially, **recurrence is their dependent
variable, not a mediator of anything organizational** — they have no manipulation
that turns recurrence on and off. Ours does: recurrence is 86.6% in the role-free
arm and 3.7% in the role arm on the same problems with the same actor.
**Consequence: we may not claim to have found that external feedback fails to
produce revision, nor that repetition predicts non-recovery. We claim that role
structure is a control variable for it.**

### 3.2 — 2402.08115, Stechly, Valmeekam & Kambhampati, "On the Self-Verification Limitations of LLMs." **STRONG OVERLAP on setting.**

The closest *experimental protocol* to ours in the whole literature. They run
GPT-4 on Game of 24, Graph Colouring and (Mystery) Blocksworld under a **sound
external verifier** with a retry budget, and — this is the part that matters —
they explicitly test a **binary backprompt**: "either the verifier accepts the
solution, stopping the system, or we create a backprompt which says the previous
answer was wrong but doesn't elaborate." That is our oracle gate. Binary feedback
scores 36 / 38 / 60 / 10% across the four domains, statistically level with
first-error (38/37/87/8%) and all-error feedback, and bare re-prompting with no
critique at all gives 28/40/68/9%. Their conclusion: *"the level of feedback often
doesn't seem to matter — as long as the verifier is sound"*, and in two domains
**more** feedback made things worse.

**How we differ.** They report only success rates. **They never measure whether
the model re-emits the same answer** — there is no repetition or diversity
statistic anywhere in the paper, and they sample at temperature 1, which
guarantees surface variation they never characterise. They come within one
sentence of our mechanism in an aside about multiple-choice benchmarks being too
easy — *"even a very simple agent can solve an n-choice problem with n−1
critiques — just don't repeat the same answer"* — but as a critique of other
people's benchmarks, not as a measurement of their own system. And there is no
role manipulation: single agent throughout. **Positioning: they established that
feedback content does not matter; we establish what does — whether the system can
generate a second distinct candidate at all, which role structure controls.**

### 3.3 — 2305.19118, Liang et al., "Encouraging Divergent Thinking" (EMNLP 2024). **STRONG OVERLAP, conceptual. This is the name our phenomenon already has.**

Degeneration-of-Thought is defined as: *"once the LLM has established confidence
in its solutions, it is unable to generate novel thoughts later through reflection
even if its initial stance is incorrect."* That is sub-claim 4, stated in 2023.
Two differences carry our contribution. First, **their DoT arises under
self-generated feedback in a single model**; ours persists under an *external
oracle* across six rounds of being told the team is wrong. Second — and this is
the sharper one — **MAD is Liang's prescribed cure for DoT.** Our finding is that
a multi-agent system *does not* escape DoT merely by being multi-agent: strip the
role labels and DoT reappears inside the multi-agent system (86.6% single-answer
trajectories). That is an inversion of their prescription and it is worth stating
in exactly those terms. We must use their term, cite them first, and claim the
inversion — not the phenomenon. Note the related cluster (2501.00430, 2510.09049,
2609.09195) all treat DoT as a known named failure, confirming it is common
currency.

### 3.4 — 2503.16814, Oh et al., "From Belief Entrenchment to Robust Reasoning" (TACL). **STRONG OVERLAP on mechanism-and-cure.**

Names **belief entrenchment** — "agents reinforce shared errors rather than
correcting them" — and decomposes it into biased static initial belief plus
*"homogenized debate dynamics that amplify the majority view regardless of
correctness."* The remedy is *"enforcing perspective diversity."* Structurally
this is our story: homogeneity → entrenchment, heterogeneity → correction.
**Differences:** no external correctness feedback (accuracy is an evaluation
quantity, not an in-loop signal); the manipulation is a prompt framework
(DReaMAD) evaluated by accuracy and win rate, not a clean role/role-free ablation;
and there is no recovery conditional. A reviewer who knows this paper will ask
"isn't role differentiation just your version of perspective diversity?" **We need
a prepared answer**: our role-free arm is not less diverse in *content* — it gets
*more* evaluator rounds — and our manipulation is the label, not the viewpoint.

### 3.5 — 2310.01798, Huang et al., "LLMs Cannot Self-Correct Reasoning Yet" (ICLR 2024). **Widely mis-cited; verify before we cite it.**

Checked in full text because it is the one everyone will assume scoops us. **It
does not, and it is often described wrongly.** Their scope is *intrinsic*
correction. Where oracle labels appear, they are used **only to decide when to
stop the loop** — "we use the correct label to determine when to stop the
self-correction loop" — and in that condition results **improve** (GSM8K 75.9→84.3
for GPT-3.5, 95.5→97.5 for GPT-4; CommonSenseQA 75.8→89.7 and 82.0→85.5). They
explicitly discount these as "indicative of an oracle's performance" only. The
number we actually need from them is different: **GPT-3.5 keeps its original
GSM8K answer 74.7% of the time**, and among the rest is more likely to break a
correct answer than fix a wrong one. That is the published baseline our 86.6% sits
against — same family of measurement, single-agent, self-feedback, one round.
**Do not write that Huang et al. showed LLMs fail to revise under oracle feedback.
They showed the opposite, and a reviewer will catch it.**

---

## 4. WHAT WE MUST CITE

All arXiv IDs below were verified this session by fetching the arXiv abstract page
or the arXiv Atom API record. Author lists and venues are as printed there.
Where I could not verify a field I have left it out rather than guess.

```bibtex
@article{jiang2026exact,
  title   = {Exact Feedback Is Not Control: Evaluating Text-based Closed-Loop Revision in LLMs},
  author  = {Jiang, Haitong and Liu, Chunlin and Wang, Yile and Feng, Yuhong},
  journal = {arXiv preprint arXiv:2609.28150},
  year    = {2026}
}
```
*Position:* cite in the mechanism section **before** we present lock-in. They own
"complete external feedback does not make the revision loop reliable, and failed
trajectories repeat earlier outputs." We extend it from single-agent
constraint satisfaction to a multi-agent reasoning pipeline and, unlike them,
exhibit an intervention (role labels) that switches recurrence on and off.

```bibtex
@inproceedings{stechly2024self,
  title     = {On the Self-Verification Limitations of Large Language Models on Reasoning and Planning Tasks},
  author    = {Stechly, Kaya and Valmeekam, Karthik and Kambhampati, Subbarao},
  booktitle = {arXiv preprint arXiv:2402.08115},
  year      = {2024}
}
```
*Position:* our oracle-gate design descends from their binary-backprompt condition
and must say so. Their result that feedback *content* is irrelevant is the setup
for our question: if content does not matter, what does? Answer: whether a second
distinct candidate is generated at all.

```bibtex
@inproceedings{liang2024encouraging,
  title     = {Encouraging Divergent Thinking in Large Language Models through Multi-Agent Debate},
  author    = {Liang, Tian and He, Zhiwei and Jiao, Wenxiang and Wang, Xing and Wang, Yan and Wang, Rui and Yang, Yujiu and Shi, Shuming and Tu, Zhaopeng},
  booktitle = {Proceedings of EMNLP},
  year      = {2024},
  note      = {arXiv:2305.19118}
}
```
*Position:* adopt "Degeneration-of-Thought" as the name for what we measure, credit
it, then state the inversion — DoT is supposed to be cured by multi-agency, and we
show multi-agency without role differentiation does not cure it.

```bibtex
@article{oh2026belief,
  title   = {From Belief Entrenchment to Robust Reasoning in LLM Agents},
  author  = {Oh, Jihwan and Jeong, Minchan and Ko, Jongwoo and Yun, Se-Young},
  journal = {Transactions of the Association for Computational Linguistics},
  year    = {2026},
  note    = {arXiv:2503.16814}
}
```
*Position:* the nearest mechanism-and-cure precedent. Distinguish explicitly: their
lever is perspective diversity in content, ours is the role label while content
diversity moves the *other* way (role-free gets more evaluator rounds).

```bibtex
@inproceedings{huang2024large,
  title     = {Large Language Models Cannot Self-Correct Reasoning Yet},
  author    = {Huang, Jie and Chen, Xinyun and Mishra, Swaroop and Zheng, Huaixiu Steven and Yu, Adams Wei and Song, Xinying and Zhou, Denny},
  booktitle = {International Conference on Learning Representations (ICLR)},
  year      = {2024},
  note      = {arXiv:2310.01798}
}
```
*Position:* cite for the **74.7% answer-retention** baseline and to state clearly
that their scope is intrinsic correction — their oracle condition *improves*
results. Our contribution is the multi-agent, oracle-in-the-loop case they did not
run.

```bibtex
@article{kamoi2024when,
  title   = {When Can LLMs Actually Correct Their Own Mistakes? A Critical Survey of Self-Correction of LLMs},
  author  = {Kamoi, Ryo and Zhang, Yusen and Zhang, Nan and Han, Jiawei and Zhang, Rui},
  journal = {Transactions of the Association for Computational Linguistics},
  volume  = {12},
  pages   = {1417--1440},
  year    = {2024},
  note    = {arXiv:2406.01297}
}
```
*Position:* inherit their methodology (already a standing decision from
`NOVELTY-AUDIT.md` F02) **and** present our role-free arm as a counterexample to
their finding that "self-correction works well in tasks that can use reliable
external feedback" — reliable external feedback is exactly what our role-free arm
has, and it recovers at 0.02–0.05.

```bibtex
@article{cemri2025why,
  title   = {Why Do Multi-Agent LLM Systems Fail?},
  author  = {Cemri, Mert and Pan, Melissa Z. and Yang, Shuyi and Agrawal, Lakshya A. and others},
  journal = {arXiv preprint arXiv:2503.13657},
  year    = {2025}
}
```
*Position:* map our failure onto MAST explicitly. Verified modes: FM-1.2 Disobey
role specification, FM-1.3 Step repetition, FM-1.5 Unaware of stopping conditions,
FM-3.1 Premature termination. State that our failure is **not** FM-3.1 (we refuted
premature stopping) and is **adjacent to but distinct from** FM-1.3 (step
repetition is action-level within a trajectory; ours is answer-identity across
oracle-gated attempts). Pre-empting this mapping is cheaper than being handed it.

```bibtex
@article{dylan2026equal,
  title   = {At Equal Inference Cost, Multi-Agent Structure Does Not Beat a Single Frozen Agent},
  author  = {Dylan, David and Brennan, Aoife and Murphy, Cian and O'Sullivan, Niamh and Kelly, Conor and Walsh, Saoirse},
  journal = {arXiv preprint arXiv:2609.04217},
  year    = {2026}
}
```
*Position:* concede sub-claim 1 to them (0.769 vs 0.754, p=0.80; planner and critic
evolve to empty prompts). Then state the delta in one sentence: they measured only
aggregate success and therefore could not see that the critic's contribution is
concentrated entirely in the post-failure conditional.

```bibtex
@article{stechly2023gpt4,
  title   = {GPT-4 Doesn't Know It's Wrong: An Analysis of Iterative Prompting for Reasoning Problems},
  author  = {Stechly, Kaya and Marquez, Matthew and Kambhampati, Subbarao},
  journal = {arXiv preprint arXiv:2310.12397},
  year    = {2023}
}

@article{smit2024mad,
  title   = {Should we be going MAD? A Look at Multi-Agent Debate Strategies for LLMs},
  author  = {Smit, Andries and Duckworth, Paul and Grinsztajn, Nathan and Barrett, Thomas D. and Pretorius, Arnu},
  journal = {arXiv preprint arXiv:2311.17371},
  year    = {2024}
}

@article{wang2024rethinking,
  title   = {Rethinking the Bounds of LLM Reasoning: Are Multi-Agent Discussions the Key?},
  author  = {Wang, Qineng and Wang, Zihao and Su, Ying and Tong, Hanghang and Song, Yangqiu},
  journal = {arXiv preprint arXiv:2402.18272},
  year    = {2024}
}

@article{du2023improving,
  title   = {Improving Factuality and Reasoning in Language Models through Multiagent Debate},
  author  = {Du, Yilun and Li, Shuang and Torralba, Antonio and Tenenbaum, Joshua B. and Mordatch, Igor},
  journal = {arXiv preprint arXiv:2305.14325},
  year    = {2023}
}
```
*Position (these four together):* the debate-efficacy backdrop. Smit supplies the
"tune agent agreeableness" lever; Wang supplies "a well-prompted single agent
matches discussion" (sub-claim 1 again); Du is the origin point. One paragraph,
not a section.

```bibtex
@article{yang2026cost,
  title   = {LLMs Can Predict Failure Risk, But Struggle to Predict Which Collaboration Protocol Pays Off: Cost-Aware Protocol Routing Across Reasoning Tasks},
  author  = {Yang, Chih-Hsuan and Jiang, Jingyan and Yang, Cheng-Hau and Vasudevan, Vikram and Zheng, Huihuo and Vishwanath, Venkatram and Thakur, Rajeev},
  journal = {arXiv preprint arXiv:2608.14927},
  year    = {2026}
}
```
*Position:* **cite our own prior work explicitly and early.** It uses the same PER
protocol on 4,181 competition math problems with the same solver-fixed design. The
differentiator to state in one sentence: that paper asks *which protocol to route
to and at what cost*; this paper asks *what inside the protocol produces recovery*,
and answers with a role ablation and a trajectory-level lock-in measurement. Not
citing it is the single easiest way to get a thin-slicing rejection.

Also cite, one line each, in related work: 2507.11662 (agreement bias in verifiers
— why our reviewer rubber-stamps), 2606.00820 (flip decomposition — the
methodological ancestor of our distinct-answer count), 2605.08563 (context
contamination — the confound we rule out), 2603.09641 (PRECEPT — prior art for
separating first-try from recovery), 2509.23055 (sycophancy → premature consensus
— the hypothesis we test and reject).

---

## 5. WHAT WE MUST NOT CLAIM

1. **Do not claim that removing roles leaves first-pass accuracy unchanged as a
   finding.** 2609.04217 (p=0.80 on a matched-cost Planner-Executor-Critic),
   2402.18272 and 2602.03128 own it. It is our *control condition*, and should be
   presented as "as expected, and consistent with prior work."
2. **Do not claim to be first to show LLMs fail to revise under external
   feedback.** 2609.28150 owns it for complete verifier feedback; 2402.08115 owns
   the binary "your answer was wrong" backprompt setting.
3. **Do not claim to have discovered answer repetition / lock-in.** Liang et al.
   named it Degeneration-of-Thought in 2023; MAR (2512.20845) states it verbatim
   for iterated reflection; MAST FM-1.3 is "Step repetition." Use the existing
   name.
4. **Do not write that "Huang et al. showed LLMs cannot self-correct even with
   oracle feedback."** False. Their oracle condition improves accuracy; oracle
   labels there are a stopping rule. This sentence would be caught immediately.
5. **Do not claim premature consensus / early convergence as a novel hypothesis,
   nor imply nobody had proposed it.** Nine-plus papers name it (2509.23055,
   2510.20963, 2408.13406, 2509.23537, 2608.20564, MAST FM-3.1, …). Frame our
   result strictly as a refutation of a standing explanation.
6. **Do not claim novelty for "diversity is the active ingredient in debate."**
   Owned by 2503.16814, 2601.19921, 2410.12853, 2511.07784. Our lever is the role
   *label* under content-diversity conditions that run the other way — say that
   precisely, or it collapses into their claim.
7. **Do not claim to be first to report recovery-after-failure as a metric.**
   PRECEPT (2603.09641) separates first-try from drift recovery; AgentTether
   (2607.06273) reports repair rate conditioned on initial failure. Our novelty is
   the *contrast across a role ablation*, not the metric's existence.
8. **Do not claim novelty for observing role collapse.** 2602.03128, 2609.04217,
   2604.03809, 2607.21627 and MAST FM-1.2 all have it. Sub-claim 5's contribution
   is only the **dissociation** — surface collapse with recovery preserved.
9. **Do not describe the reviewer agent's over-acceptance as a new observation.**
   2507.11662 named it "agreement bias"; 2408.13406 measured 85–92% affirmation.
10. **Avoid "LLM agents cannot update their beliefs given evidence" as a general
    statement.** DERELAB (2608.30413) and the belief-updating cluster (2512.02914,
    2509.23936, 2512.18489) already occupy it, and our evidence is about answer
    identity in one pipeline, not beliefs in general.
11. **Do not present the 2.5x-more-evaluator-calls result without ruling out
    context contamination** (2605.08563: cascade ratio ~7.1). More rounds in a
    contaminated context is a known independent degradation path; if we do not
    address it, a reviewer will offer it as the alternative explanation for why
    more feedback did not help.

---

## 6. SEARCH COVERAGE

**Tool status. WebSearch was BLOCKED for the whole session** — Vertex AI
organization policy `constraints/vertexai.allowedPartnerModelFeatures` refuses the
`web_search` feature for this model. Every query below was run through WebFetch
against the arXiv Atom API (`export.arxiv.org/api/query`), arXiv abstract pages,
`ar5iv.labs.arxiv.org` rendered full text, raw GitHub, or Google Sites.
**Semantic Scholar returned HTTP 429** on its one attempt (same failure as the
2026-09-28 audit). No DBLP, no OpenAlex, no venue proceedings were searched.

### arXiv API queries (field-scoped, 20–30 results each)
1. `all:"self-correct" AND all:"large language models"`
2. `abs:"multi-agent" AND abs:"premature consensus"`
3. `abs:"conformity" AND abs:"LLM"` (478 total hits, top 25 read)
4. `abs:"debate" AND abs:"diversity" AND abs:"language model"`
5. `abs:"anchoring" AND abs:"language model" AND abs:"feedback"` — **null result**, all hits architectural not cognitive
6. `abs:"external feedback" AND abs:"self-correction"`
7. `abs:"change their answer" OR abs:"answer perseverance" OR abs:"belief persistence" OR abs:"stubborn"` — 325 hits, **no LLM-relevant results**; term choice wrong
8. `abs:"multi-agent" AND abs:"failure" AND abs:"taxonomy" AND abs:"LLM"`
9. `abs:"recovery" AND abs:"LLM agents" AND abs:"error"`
10. `abs:"same answer" AND abs:"rounds" AND abs:"agents"` — only 2 hits, too narrow
11. `abs:"critic" AND abs:"agreement bias" OR abs:"rubber-stamp" OR abs:"LLM-as-a-judge" AND abs:"reject"`
12. `abs:"role" AND abs:"ablation" AND abs:"multi-agent" AND abs:"LLM"`
13. `abs:"corrective feedback" AND abs:"language model"`
14. `abs:"told" AND abs:"wrong" AND abs:"answer" AND abs:"language model"` — **0 results** (over-conjoined)
15. `abs:"persona" AND abs:"multi-agent" AND abs:"no effect" OR abs:"role-free" OR abs:"generic agent"`
16. `abs:"sycophancy" AND abs:"multi-agent"`
17. `ti:"Should we be going MAD"`
18. `abs:"degeneration-of-thought" OR abs:"Encouraging Divergent Thinking"`
19. `abs:"update their beliefs" OR abs:"belief updating" AND abs:"evidence" AND abs:"LLM"`
20. `abs:"echo chamber" AND abs:"agents" AND abs:"language"`
21. `ti:"Rethinking the Bounds of LLM Reasoning" OR ti:"Improving Factuality and Reasoning…" OR ti:"ChatEval"`
22. `abs:"retry" AND abs:"budget" AND abs:"agent" AND abs:"verifier"`
23. `abs:"answer diversity" OR abs:"distinct answers" AND abs:"debate" OR abs:"rounds"`
24. `abs:"role specialization" AND abs:"error correction" AND abs:"LLM"` — **0 results** (over-conjoined)
25. `abs:"oracle" AND abs:"feedback" AND abs:"multi-agent" AND abs:"reasoning"`
26. `abs:"first-pass" OR abs:"first attempt" AND abs:"accuracy" AND abs:"agents" AND abs:"feedback"` — mostly ASR false positives
27. `abs:"revision" AND abs:"verifier" AND abs:"fails to" AND abs:"reasoning"`
28. `abs:"role differentiation" AND abs:"agents"`
29. `abs:"Planner" AND abs:"Executor" AND abs:"Reviewer" AND abs:"LLM"`
30. `abs:"lock-in" AND abs:"agents" AND abs:"language model"`
31. `abs:"repeated" AND abs:"identical" AND abs:"response" AND abs:"feedback" AND abs:"model"` — **this query found 2609.28150**, the closest paper; it surfaced in nothing else
32. `co:"AAMAS" AND abs:"multi-agent" AND abs:"LLM" AND abs:"role"` — **1 result only**
33. `ti:"GPT-4 Doesn't Know It's Wrong" OR ti:"Can LLMs Really Improve by Self-critiquing" OR ti:"On the Self-Verification Limitations"`

### Full-text / abstract-page fetches (verified individually)
2503.13657 (abs + PDF outline), 2310.01798 (abs + **ar5iv full text**, oracle
section and Table 2 read directly), 2406.01297, 2402.08115 (**ar5iv full text**,
binary-feedback condition and Table 1 read directly), 2511.21591, 2606.00820,
2503.16814, 2507.02778, 2511.07784, 2512.20845, 2609.34444, 2605.08563, 2609.32035,
2606.02646, 2608.19072, 2608.30373, 2509.05396, 2609.04217, 2608.30413, 2608.14927,
2609.28150, plus the MAST GitHub README and the MAST Berkeley site.

### Coverage holes — state these whenever citing this file
- **WebSearch unavailable.** Anything not on arXiv is invisible to this audit.
- **Semantic Scholar 429'd; DBLP and OpenAlex not attempted.** No citation-graph
  forward search was possible, so recent papers citing Huang/Stechly/Liang were
  never enumerated. **This is the biggest hole** — forward citations of
  2310.01798 and 2305.19118 are exactly where a scoop would live.
- **AAMAS coverage is one paper.** The `co:"AAMAS"` stamp query returned a single
  hit. AAMAS 2026 proceedings were not checked. For an AAMAS submission this is
  not acceptable as final coverage.
- **MAST's 14 modes are only 6/14 recovered** (FM-1.2, 1.3, 1.4, 1.5, 2.1, 3.1),
  from PDF bookmark strings — the GitHub README, the Berkeley site and the abs
  page all withhold the full list (it lives in a figure image). The remaining 8
  could contain a mode matching us exactly. **Read the MAST PDF figure directly
  before submission.**
- Several abstract-only readings are marked as such above; 2606.00820, 2503.16814
  and 2511.07784 were assessed from abstracts and their full texts may contain a
  distinct-answer or recovery metric that would upgrade their rating.
- **Cross-check against the prior audit:** `NOVELTY-AUDIT-ROLES.md` states that
  2609.04217 "coins 'role-differentiation collapse'" and calls the roles
  "decorative." **Neither phrase appears on the arXiv abstract page I fetched
  today.** The substance (planner/critic evolve to empty prompts, gains attributed
  solely to the executor) is real and confirmed, but those two quoted phrases are
  unverified and must not be quoted in the paper until someone reads the PDF.
