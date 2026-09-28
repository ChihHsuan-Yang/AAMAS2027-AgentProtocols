# Novelty audit — role specialization (2026-09-28)

**Verdict: (b) partially anticipated — worse than the confidence audit.**
Three of four sub-claims are anticipated; two appear in abstracts/design
principles of accepted papers.

## Verified by me personally (fetched abs pages, titles confirmed)

| id | title | authors |
|---|---|---|
| 2602.03128 | Architectural Design, Not Only Model Intelligence, Governs Multi-Agent LLM Performance | Orogat, Rostam, Mansour |
| 2609.04217 | At Equal Inference Cost, Multi-Agent Structure Does Not Beat a Single Frozen Agent | Dylan et al. |
| 2609.14570 | Disentangling Topology and Diversity in Multi-Agent LLMs | Shernazarov et al. |
| 2607.21627 | Do Modules Stay in Their Lane? Role Drift in Compound LLM Systems | Cao, Srinivasan, Bakker |
| 2503.13657 | Why Do Multi-Agent LLM Systems Fail? (MAST) | Cemri et al. |
| **2608.14927** | **Cost-Aware Protocol Routing Across Reasoning Tasks** | **Yang, Jiang, Yang, Vasudevan, Zheng, Vishwanath** |

### I read 2602.03128's full text to check the most damaging claim. It holds.

Verbatim from its design principles:
> **"Role-based conditioning fails to induce specialization."**
> "Principle 4: Specialization should be procedural; role labels should be
> secondary. Encode expertise as workflows, not as role names."
> "Role labels and generic planning interfaces fail to activate domain
> knowledge... **Role naming or lightweight prompt modifications are
> insufficient.**"

Their §4.1.4 crosses role labels × {role-prompt, planning-based,
expert-guided procedural} with model/data/prompts/metrics fixed. **This is our
Q2 experiment, already run, in an accepted SIGMOD 2027 paper.**

## Per-claim ruling

| sub-claim | ruling | who owns it |
|---|---|---|
| Q1 roles don't instantiate distinct functions | **ANTICIPATED ×4** | 2604.02770 (46.4%/43.4% overstepping); 2604.03809 (effective rank 2.17/3.0); 2604.00026 (cosine 0.85); MAST **FM-1.2 "Disobey role specification"** |
| Q2 separate label / soft instruction / hard constraint | **HALF-ANTICIPATED** | 2602.03128 owns label-vs-soft-procedural. **Hard/architectural enforcement is unclaimed** — the audit found 0 hits for constrained-decoding role enforcement |
| Q3 organization × actor mediated by realized specialization | **PARTIALLY — the mediation survives** | 2609.14570 publishes "preferred topology depends on diversity source" but *manipulates* specialization without measuring it; 2604.27228 *measures* model-dependent role fidelity (28pp) without linking it to organization choice |
| Q4 controlled role ablation at fixed budget | **ANTICIPATED** | 2609.04217 does exactly this on Planner-Executor-Critic, coins **"role-differentiation collapse"**, calls the roles **"decorative"** |

## What actually survives

1. **The mediation, closed end-to-end.** Nobody measures realized specialization
   and uses it to explain which organization wins. 2609.14570 and 2604.27228
   each hold one half.
2. **A sign REVERSAL, not a shrinkage.** 2609.14570 reports magnitude shrinkage
   (2.83 → 0.17). Ours is +0.058 vs −0.138, opposite signs, both CIs far from 0.
3. **Hard architectural enforcement.** 2602.03128's strongest arm is still a
   *prompt* (expert-guided procedure). An arm where violation is *impossible*
   is open.
4. **An open question handed to us in writing.** 2609.04217 attributes role
   collapse to "a property of the substrate, a 7B with no headroom for a second
   distinct role" — on ONE backbone, so they cannot test it. Our multi-actor
   corpus can.

## Things that would draw "this is known"

Leading with E7 (Planner computes) = MAST FM-1.2, quantified three times.
Proposing Q4 as a contribution = 2609.04217.
Proposing label-vs-prompt as the intervention = 2602.03128 Principle 4.

## Self-overlap now involves THREE group papers on one corpus

- **2609.27822** (Yang et al.) — confidence routing audit, broadcast
- **2608.14927** (Yang et al.) — cost-aware protocol routing across the same protocols
- IEEE BigData SciAgentTrace — the dataset

A reviewer finding three papers on this corpus will raise thin-slicing whatever
the question. The AAMAS paper needs a visibly different **object** (behavioural
trace measurement + a real intervention arm), not merely a different question.

## Coverage holes
- WebSearch blocked (org policy). Semantic Scholar effectively 1 query/session.
- AAMAS coverage = arXiv comment stamps only; misses non-arXiv'd AAMAS papers.
- **Note:** 2602.03128 is filed as a *database-systems* paper. It would not
  surface in an LLM-MAS-only search. Assume more such papers exist.
