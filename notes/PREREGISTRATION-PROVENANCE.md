# Pre-registration provenance (P0, Bella §14/§16/§17) — 2026-09-29

Established from git history, not from recollection. This resolves the
Case 1 / Case 2 question Bella posed. **It is Case 2 — the unfavourable one —
and the paper will say so.**

## The timeline, from the repository

| event | timestamp | source |
|---|---|---|
| PREREGISTRATION.md committed | **2026-09-28 17:52:33 -0500 = 22:52:33Z** | commit `e89e6c4f` |
| campaign v1 first trajectory | 23:00:42Z | earliest `started_at` in campaign_v1 |
| campaign v2 (final) first trajectory | 23:26:56Z | earliest `started_at` in campaign_v2 |

**The pre-registration precedes the first confirmatory trajectory by 8
minutes**, and precedes the final campaign by 34 minutes. No confirmatory
result had been inspected at commit time.

## What the pre-registration actually said, as committed

Verbatim from commit `e89e6c4f`:

> *"This is also the manipulation check.* Arm C should drive **P1a** to ≈1.0 by
> construction. **If it does not, Arm C did not engage and every downstream
> result from it is void.**"

And in "What would make us NOT submit":

> "- Arm C fails its manipulation check (P1 null)."

## The verdict: CASE 2

The pre-registration genuinely expected **no-computation fidelity (P1a)** to
approach 1.0. It did not. Measured Arm C P1a: **0.117 (gpt-oss) / 0.253
(gemma-4)** on accepted planner messages, against P2 (answer authorship) at
**1.000** in every cell.

Further, checking the **launch-time validator** (`schemas.py` at commit
`e89e6c4f`): it contains **zero** computation-related constraints. The Arm C
implementation was never capable of enforcing P1a. The manipulation check named
a clause the intervention did not implement.

## How this is reported — no history is rewritten

The paper will state:

> We pre-registered that architectural enforcement would drive the Planner's
> abstention-from-computation to ceiling, and treated that as the manipulation
> check. **It did not.** The implemented constraint removes the Planner's answer
> field, which enforces *answer authorship* (compliance 1.000 in every cell) but
> places no restriction on computation, which persisted at or above the
> soft-role rate. We report the stronger manipulation objective as **failed**,
> and the weaker one as **achieved**.

This is not a rescue. It is a second dissociation, and it is *on-thesis*:
**structural compliance does not imply cognitive division of labor.** But it is
reported as a failed objective first, and an insight second.

## Related provenance the paper must also carry

- **The pre-registered PRIMARY test (P4, actor × enforcement interaction on
  accuracy) is NULL.** Predeclared Pattern E: *"the central causal theory fails.
  Do not force it."* Reported as such.
- **B−A was NOT a pre-registered primary endpoint.** It appears in the committed
  file only as secondary/exploratory ("A − B (role-instruction contribution;
  replication of a published null)"). The headline finding is therefore
  **post-hoc**, and will be labelled post-hoc in the manuscript. Scientific
  importance does not license relabelling provenance.
- Amendments 1-3 (actor panel, discriminating contrast, enforcement-rate
  definition) were committed in the same `e89e6c4f` commit, i.e. also before
  any confirmatory result.
