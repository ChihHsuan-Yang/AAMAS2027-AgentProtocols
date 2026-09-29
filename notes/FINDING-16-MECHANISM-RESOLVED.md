# Finding 16 — The stopping-vs-diversity question, RESOLVED. It is neither.

**2026-09-29. Bella's §5-§8 question: does role removal destroy recovery
because differentiated reasoning disappears, or because the role-free system
reaches premature agreement and closes the repair channel?**

**Answer: the premature-stopping hypothesis is REFUTED, and the diversity
hypothesis needs restating. The mechanism is answer LOCK-IN.**

## 1. Premature stopping is refuted — B gets MORE repair opportunity, not less

Conditional on needing a retry (>1 evaluator call):

| actor / arm | P(>1 eval call) | eval calls given retry | recovery given retry |
|---|---|---|---|
| gemma-4 / A | 0.081 | 2.29 | **0.509** |
| **gemma-4 / B** | **0.196** | **5.81** | **0.050** |
| gpt-oss / A | 0.218 | 2.58 | 0.438 |
| gpt-oss / B | 0.228 | 4.70 | 0.254 |
| Llama-3.3 / A | 0.020 | 3.00 | 0.333 |
| **Llama-3.3 / B** | **0.667** | **5.69** | **0.021** |

Arm B is **more** likely to enter the repair loop and consumes **2.5x more**
evaluator feedback. The reviewer's high first-turn accept rate does not close
the channel. Whatever is wrong, it is not lack of opportunity.

## 2. Holding opportunity fixed, B recovers BETTER — which inverts the story

Recovery at matched evaluator-call counts, gpt-oss (the only actor with enough
cells):

| eval calls | Arm A | Arm B |
|---|---|---|
| 2 | 0.600 (n=160) | **0.851** (n=47) |
| 3 | 0.271 (n=96) | **0.500** (n=30) |
| 4 | 0.161 (n=31) | **0.310** (n=29) |

**Per unit of repair opportunity, the role-free team is not worse.** So the
aggregate recovery deficit cannot be a per-attempt capability deficit either.

## 3. The real mechanism: a bimodal split into ANSWER LOCK-IN

The evaluator-call distribution shows what is actually happening:

| actor / arm | 1 call | 2-5 calls | **budget exhausted (≥6)** |
|---|---|---|---|
| gemma-4 / A | 0.92 | 0.08 | **0.000** |
| **gemma-4 / B** | 0.80 | 0.02 | **0.184** |
| gpt-oss / A | 0.78 | 0.22 | **0.000** |
| **gpt-oss / B** | 0.77 | 0.12 | **0.104** |

Arm A degrades gracefully (2-5 calls, then resolves). Arm B **skips the middle
and jumps to exhausting the budget** — and those trajectories are essentially
never correct: **accuracy 0.004 (gemma-4, n=246) and 0.036 (gpt-oss, n=138)**.

Why they fail is unambiguous:

| | budget-exhausted Arm B | Arm A with ≥2 eval calls |
|---|---|---|
| gemma-4: **never changes its answer** | **0.866** | 0.037 |
| gemma-4: median distinct answers | **1** | 2 |
| gpt-oss: never changes its answer | 0.355 | 0.048 |
| gpt-oss: median distinct answers | 2 | **5** |

**86.6% of gemma-4's exhausted role-free trajectories emit exactly one distinct
answer across the entire trajectory** — six rounds of ground-truth-informed
"this is wrong" feedback, and the team restates the same answer every time.
Arm A does this 3.7% of the time.

## 4. The restated mechanism

> Role removal does not stop the system from getting another chance, and does
> not make it worse per attempt. It makes the team **unable to use the chances
> it gets**: a role-free team that is wrong converges on one answer and cannot
> move off it, burning the entire repair budget restating it.

This is *diversity*, but specifically **diversity of revision**, not diversity
of initial reasoning. What roles preserve is the capacity to *change your mind*
after being told you are wrong.

## 5. Consequence for the paper

- The premature-consensus/stopping framing in Bella's §5 must **not** be used —
  the data refutes it.
- The §9 fixed-opportunity control experiment (B-no-early-stop) is
  **unnecessary and would be uninformative**: Arm B already receives *more*
  opportunities than Arm A. Forcing still more rounds cannot rescue a team that
  restates one answer across six. **Dropping it saves a campaign and the
  writing window.**
- "Roles buy recovery, not first-pass accuracy" survives and is now mechanised.
- The honest causal language remains associational: answer lock-in is measured
  conditional on failing, which is post-treatment.

## 6. Caveats
- Recovery is oracle-gated throughout (the evaluator sees gold), so "recovery"
  means recovery *with* an oracle signal.
- The matched-opportunity table is only well-powered for gpt-oss.
- Llama-3.3's n is small (148/144/146 per arm at this cut).
