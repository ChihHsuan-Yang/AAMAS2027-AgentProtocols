# Finding 09 — P1a is confounded with message length; the review was right (W5a)

**Confirmed by Master on live campaign data, 2026-09-28 20:45.**

## The anomaly that exposed it

Arm B / gpt-oss-120b scored **P1a = 0.846** — apparently the *most* compliant
"Planner" in the study, far above Arm A (0.022) and Arm C (0.034).

Inspecting the messages, the entire content is:

```
\boxed{\dfrac{1}{27}}  [Agree]                    (30 chars)
\[ \boxed{\dfrac{8}{9}} \]  [Agree]               (35 chars)
\boxed{\dfrac{\sqrt{6}}{3}}  [Agree]              (36 chars)
```

The agent shows **no computation because it shows no work at all** — it emits a
bare answer and agrees. P1a ("contains zero evaluated numeric equalities")
scores that as perfect compliance with "do not compute". It is the opposite of
compliance: it is the total collapse documented in F08.

## Why this matters beyond the anomaly

P1a is defined as *absence of a pattern*, so it is mechanically anti-correlated
with message length. Mean planner chars: Arm B/gpt-oss **1,623** vs Arm A/gpt-oss
**5,180**. Any arm that shortens messages gets a free P1a improvement.

This directly threatens the Arm C reading, because Arm C messages are also
shorter than Arm A's. **An Arm C "improvement" in P1a could be brevity, not
division of labor.**

## The fix, already implemented (x2)

Report the **length-robust density** alongside the frozen binary metric:
evaluated equations per 1,000 characters.

| arm | actor | P1a (binary) | **eq per 1k chars** |
|---|---|---|---|
| A | gpt-oss-120b | 0.022 | 2.33 |
| B | gpt-oss-120b | **0.846** | **1.31** |
| C | gpt-oss-120b | 0.034 | **4.27** |
| A | gemma-4-31B | 0.074 | 2.52 |
| C | gemma-4-31B | 0.231 | 2.66 |

The density metric tells a different and more honest story: Arm C/gpt-oss is the
**densest** computer (4.27/1k), not a compliant planner. The binary metric hid
this.

## Disposition
- The frozen P1a is **not** re-defined (the v3 lesson: do not change a validated
  metric after seeing results).
- The density measure is reported **alongside** it as a pre-declared robustness
  check, and the binary/density divergence is itself reported.
- Any Arm C claim about computation must cite the density, not the binary rate.

This is the third independent confirmation that the paper's real finding is
about **answer authorship** (P2, which Arm C does enforce at 1.000) rather than
**cognitive division of labor** (P1a/density, which it does not touch).
