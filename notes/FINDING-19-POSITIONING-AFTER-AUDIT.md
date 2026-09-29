# Finding 19 — The claim that survives the novelty audit, and the number that makes it

**2026-09-29. The recovery/premature-consensus audit came back PARTIALLY
NOVEL. Three of five sub-claims are anticipated. This note fixes what we
claim, and supplies the contrast that makes the surviving claim land.**

## 1. I verified the audit's load-bearing claims myself before acting on them

The audit ran with WebSearch blocked and could not do a forward-citation
search — its own stated coverage hole. So I re-fetched the five papers whose
content decides our framing. All five verify:

| id | verified |
|---|---|
| 2609.28150 Exact Feedback Is Not Control | title, 4 authors, abstract. **"failed trajectories often repeat earlier outputs"; "prior recurrence is associated with lower subsequent recoverability"** — real, and the language is *associational*, weaker than the audit's "predicts" |
| 2402.08115 Stechly/Valmeekam/Kambhampati | title, authors verified |
| 2305.19118 Liang et al. Degeneration-of-Thought | **DoT definition verified verbatim in the abstract** |
| 2310.01798 Huang et al. | **full text pulled; every number the audit quoted is exact** (see below) |
| 2503.16814 Oh et al. belief entrenchment | title, 4 authors, abstract verified |

**The audit's most important catch is confirmed, and we were about to make
the error.** From the Huang et al. full text:

> "we use the correct label to determine when to stop the self-correction loop"

Table 2 (oracle): GSM8K **75.9 → 84.3** for GPT-3.5, 95.5 → 97.5 for GPT-4.
Oracle self-correction **IMPROVES** accuracy. Table 3 (intrinsic, no oracle):
75.9 → 75.1 → **74.7**, i.e. it degrades. And §3.3:

> "For GSM8K, 74.7% of the time, GPT-3.5 retains its initial answer."

Note the **74.7 appears twice in that paper meaning two different things** —
round-2 intrinsic accuracy, and the answer-retention rate. Anyone quoting it
from memory has a coin-flip chance of citing the wrong one. Ours is the
retention rate from §3.3.

## 2. The contrast that makes our surviving claim land

Huang's oracle condition is *our* oracle condition: ground truth used to
decide whether to stop or send the system back. So the directly comparable
quantity is **how many points the oracle-gated retry loop buys**. Theirs buys
+8.4. Ours, per arm:

| actor | Arm A (roles) | Arm B (role-free) | Arm C (enforced) |
|---|---|---|---|
| gemma-4 | 80.1 → 84.2 (**+4.1**) | 80.2 → 81.1 (**+0.9**) | 77.6 → 84.4 (+6.8) |
| gpt-oss | 71.4 → 81.1 (**+9.7**) | 76.4 → 82.1 (**+5.7**) | 76.7 → 85.8 (+9.1) |
| Llama-3.3 | 33.2 → 34.1 (+0.9) | 37.1 → 38.0 (+0.9) | 32.6 → 40.9 (+8.3) |

All paired, all CIs exclude zero (gemma-4 A +0.041 [+0.031,+0.052]; B +0.009
[+0.004,+0.015]).

**This is the paper in one table.** Huang et al. showed an oracle loop is
worth ~8 points to a single agent. We show that **the same oracle loop is
worth 4.1 points to a role-labelled team and 0.9 points to the same team with
the labels removed** — a 4.5x difference in what the identical external
correctness signal can buy, produced by nothing but the role prompt. The
oracle signal is held fixed; only the organization varies.

That is the framing that is not owned by anyone in the audit: not Huang (no
multi-agent, no role manipulation), not Jiang 2609.28150 (no roles, no
manipulation that toggles recurrence), not Stechly (no repetition metric, no
roles), not Liang (self-feedback, and multi-agency is his *cure*), not
Dylan 2609.04217 (aggregate success only, no retry conditional).

## 3. What we claim, and what we concede

**CLAIM (survives):**
> Role structure determines how much an external correctness signal is worth.
> Holding the oracle, the budget, and the actor fixed, removing role labels
> cuts the value of the retry loop by 4.5x (gemma-4: +4.1 to +0.9 points),
> because the role-free team stops generating a second distinct candidate.

**CONCEDE (cite, do not claim):**
1. Role-free ≈ role-labelled on first pass — **our control condition**, owned
   by 2609.04217 / 2402.18272 / 2602.03128. Present as "as expected, and
   consistent with prior work."
2. LLMs fail to revise under external feedback — owned by 2609.28150, 2402.08115.
3. Answer repetition / lock-in as a phenomenon — **it already has a name,
   Degeneration-of-Thought** (Liang 2305.19118). Use their name, cite them,
   and claim the *inversion*: DoT is supposed to be cured by multi-agency, and
   we show multi-agency without role differentiation does not cure it.
4. Premature consensus as a hypothesis — 9+ papers name it. We **test and
   reject a standing explanation**; we do not propose it.
5. Recovery-after-failure as a metric — PRECEPT 2603.09641 separates first-try
   from drift recovery.

**MUST NOT WRITE:** "Huang et al. showed LLMs cannot self-correct even with
oracle feedback." It is false and it is the sentence a reviewer of this
literature will catch first.

## 4. Two open items the audit could not close

- **No forward-citation search was possible** (Semantic Scholar 429'd). A
  scoop published *citing* Huang/Stechly/Liang would not have been found. This
  is the residual risk and it should be stated in the decision log, not
  papered over.
- **A prior audit's quotes do not verify.** `NOVELTY-AUDIT-ROLES.md` attributes
  "role-differentiation collapse" and "decorative" to 2609.04217; neither
  phrase is on the abstract page. The substance stands, the quotes must not be
  used until someone reads the PDF. `related.tex` currently paraphrases rather
  than quotes, so nothing needs pulling — but nobody should add those quotes.

## 5. Confound the audit flagged that we must close in the text

2605.08563 (context contamination) reports that leaving failed attempts in
context raises per-step error ~7.1x. Our Arm B accumulates 5.8 failed
submissions in `shared_history` against Arm A's 1.5. **An objector can say Arm
B recovers less because its context is more polluted, not because it lacks
roles.** We have a partial answer already: Arm C sees the same accumulation
and recovers *best* (+6.8 to +9.1). Must be stated explicitly in the
discussion, with the citation.
