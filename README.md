# When Is Multi-Agent Organization Load-Bearing?

AAMAS 2027 submission. **Abstract Oct 1, full paper Oct 8 (AoE), 8 pages main
text + unlimited references, double-blind.** Target area: GAAI.

**Bella submits manually.** The agent's job ends at a submission-ready package
— see `SUBMISSION_CHECKLIST.md`, section *"Bella — manual submission actions"*.

## The result

Multi-agent LLM systems are specified as role diagrams (Planner → Executor →
Reviewer) and those diagrams get read as *mechanism*. We ask when the
organization is actually **load-bearing** — defined as: removing or altering it
causes a reproducible performance degradation under matched compute and
information budgets.

Holding agents, call budget, context policy, verifier and grading fixed, we
delete role instructions (Arm B) and separately make the division of labor
structurally unrepresentable (Arm C), across three actors on ~9,000 matched
Omni-MATH trajectories.

> **Deleting role instructions destroys the functional division of labor in
> every actor tested (0.845–0.975). What differs is what it costs: one actor
> loses accuracy (−0.029 [−0.045,−0.013]), another does not (+0.007
> [−0.011,+0.025]). How much organization an actor loses does not predict
> whether losing it is costly.**

Not degeneration to a single agent — a collapsed team still beats its
budget-matched single agent (+0.025 [+0.007,+0.042]). Architectural enforcement
drives answer-authorship compliance to 1.000 and moves accuracy for neither
actor. Mechanism: role removal leaves the vulnerable actor's first-pass solve
rate unchanged and destroys its **recovery** (0.490 → 0.045), because without
roles the team reaches near-total unanimity and cannot escape a wrong consensus.

## Start here

| file | what it is |
|---|---|
| `CLAIM_STATUS.md` | **read first** — what is supported, withdrawn, and why |
| `notes/FINDING-14-THE-RESULT.md` | the central result |
| `notes/FINDING-11-mechanism.md` | why the actors differ |
| `adjudication/` | blinded Opus-5 adjudication: rubric, protocol, verdicts |
| `RESULT_PROVENANCE.md` | every headline number → run, script, commit |
| `notes/NUMBER-REFRESH-REQUIRED.md` | figures needing a final-n refresh |
| `OVERLAP_AUDIT.md` | separation from four prior artifacts on this corpus |
| `AI_ASSISTANCE_LOG.md` | AAMAS-required disclosure |
| `SUBMISSION_CHECKLIST.md` | what Bella does manually |

## Reproduce

```bash
python3 experiments/make_manifest.py 1600          # deterministic problem set
python3 experiments/runner.py --n 1600 --arms A,B,C \
    --actors "openai/gpt-oss-120b,google/gemma-4-31B-it" --concurrency 24
python3 scripts/verify_paper_numbers.py            # every headline figure, live
python3 adjudication/build_sample.py && python3 adjudication/adjudicate.py --reps 3
python3 adjudication/analyze.py
```

Raw trajectory JSONL (~180MB) is **not** in git; it regenerates from the
manifest + runner. Derived results and all analysis code are committed.

## Standing rules
1. Calibrate any measure against a validated reference before using it.
2. Stratify before pooling — two Simpson's reversals found in this project.
3. Never quote a number from a data cut other than the reported n.
4. A retracted number stays visible and struck through, never deleted.
5. No HPC campaign, and no claim, without the artifact that supports it.
