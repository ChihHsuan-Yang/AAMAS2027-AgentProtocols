# Finding 14 — THE RESULT. Organization collapses in every actor; only some pay for it.

**2026-09-29. Reproduced independently by the Master Agent from the raw JSONL
before acceptance. This supersedes the byte-level framing entirely.**

## The table

Functional collapse = do **all three** roles independently assert a boxed
answer (i.e. three solvers, not a division of labour). Paired within problem.

| actor | funcColl A | funcColl B | **B − A accuracy** | n |
|---|---|---|---|---|
| gemma-4-31B | 0.000 | **0.975** | **−0.0301 [−0.0463,−0.0147]** SIG | 1,295 |
| gpt-oss-120b | 0.117 | **0.845** | +0.0070 [−0.0101,+0.0248] | 1,292 |
| Llama-3.3-70B | 0.000 | **0.915** | +0.0366 [−0.0366,+0.1098] | 82 |

## What it says

**Every actor loses the division of labour at essentially the same rate
(0.845-0.975). Their accuracy responses differ, from a significant −0.030 to a
non-significant +0.037. Functional collapse does not predict accuracy cost.**

This is a cleaner and stronger statement than anything the byte metric
supported. It is also the *third independent route* to the same conclusion:

1. blinded adjudication (gemma-4 Arm B judged 0.944 redundant, byte flag 0.000)
2. this functional proxy, on three actors
3. the mechanism (F11): gemma-4's loss is entirely in **recovery**
   (0.490 → 0.045), not in first-pass solving (0.809 → 0.809)

## The third actor did not extend the axis — it showed the axis was mismeasured

The brief asked where Llama-3.3 falls on a collapse-vs-role-value plane. The
answer: **that plane does not exist.** The apparent inverse relationship came
from the byte metric conflating "lost its division of labour" with "emitted
identical strings". Under a functional measure all three actors sit at the same
place on the collapse axis and spread only on the accuracy axis.

## Proxy validation and its limits (checked, not assumed)

- Reproduced by me from raw text: gemma-4 B 0.975, gpt-oss B 0.845,
  Llama B 0.907 (worker reported 0.915 at lower n).
- Agrees with blinded adjudication where both exist, including the cell the
  byte rule misses entirely (gemma-4 Arm B: proxy 0.975 vs adjudicated 0.944,
  byte 0.000).
- **INVALID for Arm C/C′** — the Arm C validator rejects `\boxed`, so 0.000
  there measures the constraint, not behaviour. Circular; must not be reported.
- Prefix-stable (worst deviation 0.119, Arm B prefixes *understate*), so
  Llama's value at partial n is a slight underestimate.
- Llama-3.3's CI is wide (n=82) and its accuracy is 0.22-0.35 overall; it
  corroborates the collapse rate, and must **not** be used for an accuracy claim.

## The paper's contribution, restated

> Removing role instructions destroys the functional division of labour in
> every actor tested. Whether that costs anything depends on the actor, not on
> how much organization was lost. Architecturally restoring the role boundary
> restores the structure and not the capability. **Visible organization is
> therefore not evidence about the mechanism supporting performance.**

## What this retires
- the byte-collapse headline number (F13 sensitivity: no point estimate)
- "the actor that collapses most loses least" (CORRECTION-01)
- any collapse-vs-role-value ordering claim (no such axis)
