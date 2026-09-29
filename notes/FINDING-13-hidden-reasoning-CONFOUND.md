# Finding 13 — A LOGGING DEFECT INFLATES THE HEADLINE. Verified by the Master.

**2026-09-29. This is the most serious defect found in the project and it
changes the headline number. Found by the functional-metrics worker; I verified
it independently against the live endpoint before accepting it.**

## The defect, in the code

`runner.py:289-300` logs `message.content`, and falls back to
`message.reasoning` **only when content is empty**:

```python
txt = (msg.get("content") or "")
if not txt.strip():                     # <-- only when EMPTY
    txt = (msg.get("reasoning") or msg.get("reasoning_content") or "")
```

A response with **short content and a long hidden reasoning trace** is logged as
the short content. The reasoning is discarded, and `used_reasoning_fallback`
stays False, so the loss is undocumented.

## Live confirmation (Master, direct endpoint call)

One generic-prompt math request to `openai/gpt-oss-120b`, max_tokens 8192:

| field | size |
|---|---|
| `content` | **17 chars** — `\boxed{8}\n[Agree]` |
| `reasoning` | **546 chars** of real derivation (Euler's theorem, 7^2025 ≡ 7^9, ...) |
| completion_tokens | 303 |

Our logger would have recorded the 17 characters and thrown away the work.

## Exposure, measured per cell (visible chars per second of latency)

| arm / actor | <20 ch/s | documented flag | <200 chars |
|---|---|---|---|
| **gpt-oss / B** | **0.818** | 0.057 | **0.824** |
| gpt-oss / A | 0.128 | 0.025 | 0.056 |
| gpt-oss / C | 0.121 | 0.000 | 0.043 |
| gemma-4 / all | 0.005-0.011 | 0.000 | 0.000-0.049 |

**82% of gpt-oss Arm B messages are affected; the documented flag catches 5.7%.**
gemma-4 is essentially unaffected — so the artifact is concentrated in exactly
the cell carrying the headline.

## Is the finding therefore an artifact? NO — but it is INFLATED

Cross-tabulating, on gpt-oss Arm B first-pass cycles (n=1,287):

| cycle type | n | first-pass collapse |
|---|---|---|
| hidden-reasoning (all 3 msgs <20 ch/s) | 845 | **0.863** |
| **fully logged** | **442** | **0.367** |
| pooled | 1,287 | 0.692 |

**Collapse is 0.367 among cycles where we can see the whole output.** That is
far from zero, and still infinitely larger than gemma-4's first-pass 0.000. So:

- **The phenomenon is real.** Fully-logged gpt-oss cycles collapse at 36.7%
  while gemma-4 collapses at 0.0% under the same rule.
- **The headline number is not defensible as stated.** "~70% collapse" pools
  logged and unlogged cycles; the defensible figure on visible evidence is
  **0.367**, with 0.692 as an upper bound that assumes hidden reasoning is
  redundant — which we cannot show.

## Ruling (Master)

1. **The headline becomes 0.367, not 0.698 or 0.846.** Report it on the
   fully-logged subset, and state the pooled figure as an upper bound with the
   artifact disclosed.
2. **"Byte-identical outputs" may NOT be glossed as "the agents did the same
   work."** With reasoning discarded we cannot claim the hidden computation was
   redundant. The honest statement is about *emitted* output.
3. The **accuracy** results are unaffected — grading uses `final_answer`, which
   is parsed from content that was present. F10/F11 accuracy numbers stand.
4. The **mechanism** (F11: gemma-4's recovery collapsing 0.490 → 0.045) is on
   gemma-4, the unaffected actor, so it stands.
5. Fix the logger for any future run (capture `reasoning` always, as a separate
   field). **Not** re-running the campaign: 8 days out, and the fully-logged
   subset already supports the claim at n=442.

## Why this was catchable and nearly missed
The documented `used_reasoning_fallback` flag reports 5.7% and looked benign.
The real rate is 82%. A flag that only fires on the *empty-content* case cannot
measure the *short-content* case — the same error class as this project's
earlier retractions: an instrument that cannot observe the failure it is
supposed to detect.
