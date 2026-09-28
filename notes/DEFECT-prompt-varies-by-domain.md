# Measurement defect — the PER role contract is NOT the same across domains

**Found 2026-09-28, before any claim was written. This invalidates part of r6.**

## What happened

I built the fidelity suite (r1/r3/r5) from `configs/paper/per_hint_llm/config.yaml`
— which is the **Omni-MATH** PER config — and then scored Planner/Executor/
Reviewer messages from **all five domains** against it.

The prompts are domain-specific. Marker counts in the per-domain presets
(`configs/paper/prompt_presets/<domain>/per_hint_llm.yaml`):

| clause | omni_math | lab_bench_mc | science_qa |
|---|---|---|---|
| `MUST NOT` (computation prohibition) | 3 | **0** | **0** |
| `Target quantity` / answer form | 2 | **0** | **0** |
| `DELTA:` | 2 | **0** | **0** |
| `Diagnosis:` | 2 | **0** | **0** |
| `[Route:Planner]` | 3 | 2 | 2 |

The lab_bench Planner prompt in full is only: *"Identify what evidence in the
prompt matters. State which option letters are plausible or implausible and why.
If feedback exists, address it explicitly. Do not provide the final evaluator
submission yourself."* **There is no computation prohibition to violate.**

## What this invalidates

The r6 tables read as dramatic actor × domain variation. Much of that is the
prompt, not the agent:

- `R2_diagnoses` = **0.000** in every non-omnimath cell, for both actors. Not a
  behavioural collapse — the word "Diagnosis:" is never requested there.
- `P4_declares_form` ≈ 0.000 outside omnimath2 for the same reason.
- `P1a_no_computation` = 0.925/0.947 on labbench vs 0.111/0.042 on omnimath2.
  Labbench is multiple-choice biology: there is nothing to compute. The domain
  difference is **task content**, not role realization.

Reporting any of these as "role fidelity varies by domain" would be scoring
agents against a contract they were never given — the same error class as
[[verification-instrument-defect-class]]: a check inspecting the wrong subject.

## What survives

**Only within-domain, cross-actor comparisons are valid**, because within a
domain both actors receive an identical prompt. The actor contrast on
**omnimath2** is the sound one: it is the only domain whose contract contains the
"MUST NOT compute" clause, both actors ran it, and n is large
(gpt_oss 10,707 / gemma_4 8,050 / gemma3 3,501 Planner messages).

Cross-domain fidelity comparisons must be **dropped**, not caveated.

## Corrected analysis plan

1. Score each domain against **its own** prompt contract (r7).
2. Make the headline contrast **actor × actor within omnimath2**.
3. Use labbench only for clauses its prompt actually imposes
   (answer abstention, routing).
4. Never average fidelity across domains.
