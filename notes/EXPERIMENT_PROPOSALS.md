# Experiment proposals — AAMAS 2027 (NOT YET APPROVED, NOT YET RUN)

Per Bella's instruction §21/§33: no major generation/training campaign launches
before discussion. These are costed proposals.

---

## P0 — "Who should speak?" : the selection-channel experiment

> **REVISED 2026-09-28 after d10/d11.** The constructive hypothesis did NOT
> survive held-out confirmation (see FINDING-04). P0 is now a falsification test:
> does ANY oracle-free within-item channel exist? Expected outcome has shifted
> toward null. Effect sizing must use AUC~0.53 and per-turn deltas of ~+0.01,
> not the +0.27 figure that appeared in the superseded FINDING-03 table.

### Question
When a group of LLM agents must choose one member to contribute, does the
*source* of the selection signal (self-report vs peer-report) determine whether
the group recovers the knowledge it already holds?

### Hypothesis
H1 (ours): self-confidence has no inter-agent component, so argmax-confidence
selection ≈ random; peer assessment of *others' candidates* does have one, so
peer-ranked selection beats random.
H2 (rival): nothing recoverable — no local signal separates a right agent from a
wrong one on the same item, and the 74.9% ceiling is unreachable in principle.
H3 (rival): any gain from peer selection is really a majority-vote effect, not
peer *judgement*.

### Intervention
One protocol, four selection rules. Everything else byte-identical (same agents,
personas, prompts, discussion budget, memory mode, evaluator, decoding):
  A1 `argmax-confidence` — the deployed rule (reproduction / control)
  A2 `random-speaker` — the null the deployed rule must beat
  A3 `peer-rank` — each agent privately scores the OTHER agents' poll candidates;
      speaker = argmax of summed peer score  ← isolates inter-agent judgement
  A4 `plurality` — speaker = an agent holding the modal candidate
      ← separates H3 (vote) from H1 (judgement), since A3 and A4 differ only in
        whether peers *evaluate* or merely *agree*

### Controls
Fixed: agent count (3), topology, rounds, personas, token budgets, temperature 0,
evaluator model and prompt, problem set, actor models. Only the argument to the
speaker-selection function changes. A2 gives the noise floor; empty-of-signal
arms are cheap and non-optional.

### Scale
labbench (1,509 problems, exact MCQ grader, highest disagreement rate 37.6%)
+ jeebench (515) as a second domain.
2 actor models (gpt_oss_120b, gemma_4_31b) × 4 arms × ~2,000 problems
= ~16,000 trajectories. At the measured labbench broadcast median (29 model
calls, 110k tokens/trajectory): **≈460k calls, ≈1.8B tokens**. Trim to
labbench-only, 800 problems for the pilot: ≈2.3B→**370M tokens, ~93k calls**.

### Expected outcomes
- A3 > A1 ≈ A2, and A3 > A4 → peer *judgement* carries selection signal (H1, strongest result).
- A3 ≈ A4 > A1 ≈ A2 → the usable signal is agreement, not judgement (still publishable, weaker).
- A3 ≈ A1 ≈ A2 → H2: the information is not locally recoverable. **This is also a
  real finding** and the paper survives as a negative result with a mechanism.

### Paper impact
Supports/falsifies the central claim. Without it we have an observational null
plus a suggestive but non-comparable peer signal.

### Priority **P0**

---

## P1 — Blind verifier: removing the oracle from the loop

### Question
How much of the measured multi-agent advantage survives when the verifier does
not see the answer?

### Hypothesis
The oracle-free structural gain measured observationally (+14.6 PER / +17.0
broadcast) is an upper bound on what a blind-verifier system achieves, because
first-pass answers still benefit from role structure but the retry loop loses its
information source.

### Intervention
Replace the ground-truth Evaluator with a **blind verifier** (same model, same
retry budget, sees only problem + candidate, no `${result}`). Run baseline /
single / PER / broadcast under it.

### Controls
Identical retry budgets across arms — this is the point: the existing corpus
confounds structure with oracle budget, so the new run fixes budget explicitly.

### Scale
4 protocols × 1 actor × 800 labbench + 500 omnimath2 problems ≈ 5,200
trajectories. ≈150k calls.

### Expected outcomes
If single_agent's gain collapses to ~0 and multi-agent keeps a reduced gain, the
decomposition in Finding 02 is causally confirmed. If all collapse, the corpus's
entire accuracy ladder is an oracle artifact — a strong, uncomfortable, publishable claim.

### Priority **P1** (makes the paper causal rather than decompositional; also
enables measuring destructive revision, which stop-on-PASS currently censors)

---

## P2 — Deferred-note recovery

Cheap ablation: agents scoring ≥65 but not selected currently get their intent
written to a *private* note. Flip that to a *public* note (all other machinery
fixed). Isolates whether suppression or privacy is what loses the information.
~2 arms × 800 problems ≈ 46k calls. Run only if P0 shows a recoverable signal.

---

## Not proposed

- **DHD extension.** Conflicts with the already-public AAAI *Wrong but Useful*
  paper; different observational unit; no workload fields. Out of scope.
- **New benchmark.** Not needed: labbench already supplies an exact grader, a
  high disagreement rate, and genuine domain knowledge requirements. Adding a
  benchmark would test generalization, not the mechanism. Revisit only if P0
  succeeds and a reviewer-facing generality claim is wanted — jeebench +
  mascqa already in hand serve that role.
- **Training.** See report §H: not yet justified. A learned selector is only
  worth training if P0 shows a within-turn signal exists to learn from. Training
  a policy over a channel with AUC 0.4975 would be method-for-its-own-sake.
