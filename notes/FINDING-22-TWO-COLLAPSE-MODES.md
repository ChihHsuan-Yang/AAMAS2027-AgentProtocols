# Finding 22 — "Collapse" is two mechanisms, and the one we built the
# headline on is a logging artifact in disguise

**2026-09-29. Confirms and then substantially sharpens D19. This is the most
consequential finding since the pivot, and it retires a claim that is
currently in the manuscript.**

## 1. D19's core claim is CONFIRMED

Decomposing functional collapse by role, Arm B first pass:

| actor | n | planner asserts | executor | reviewer |
|---|---|---|---|---|
| Llama-3.3 | 310 | 0.897 | 0.981 | 0.965 |
| gemma-4 | 1,440 | 0.978 | 0.992 | 0.998 |
| gpt-oss | 1,434 | 0.902 | 0.953 | 0.964 |

vs Arm A, where the planner abstains almost perfectly (0.000 / 0.000 / 0.186).
**The executor is at ceiling in both arms; the planner carries the entire
signal.** The proxy measures planner abstention — the project's existing P1a,
inverted. The worker is right that it should have found this before naming a
new metric, and right that it does not inherit P1a's length confound.

Planner length in Arm B splits the actors cleanly:

| actor | median planner chars | frac < 500 |
|---|---|---|
| **gpt-oss** | **37** | **0.743** |
| gemma-4 | 2,288 | 0.025 |
| Llama-3.3 | 2,914 | 0.010 |

## 2. But the interpretation is wrong, and it is our own defect

D19 reads gpt-oss's 37-character planner as a behaviour: *"the planner stops
working and rubber-stamps (degenerate)."* **gpt-oss is exactly the actor with
the F13 hidden-reasoning logging defect** — 84.7% of its Arm B messages carry
a short visible content string alongside a long discarded reasoning trace. A
median of 37 visible characters is precisely what that defect manufactures.

The characters-per-second test separates the two readings. A model that really
emitted 37 characters is fast; a model whose reasoning was discarded is slow
but logs as short.

| actor / arm | median chars | median latency | **median ch/s** |
|---|---|---|---|
| gpt-oss / A | 4,072 | 22.6 s | 178.1 |
| **gpt-oss / B** | **37** | **28.0 s** | **3.28** |
| gemma-4 / B | 2,288 | 15.0 s | 150.8 |
| Llama-3.3 / B | 2,914 | 31.5 s | 89.1 |

**gpt-oss's Arm B planner is 54x slower per visible character than its own
Arm A planner, and 46x slower than gemma-4's Arm B planner.** It spends 28
seconds to emit 37 characters. It is not abstaining from work — **the work is
being done and thrown away by our logger.**

Two further confirmations:
- `used_reasoning_fallback` is **False in 959/959** of the sub-100-character
  messages. The flag meant to record exactly this substitution never fired —
  the original F13 defect.
- The visible payload is uniformly `\boxed{...}\n\n[Agree]`, i.e. only the
  protocol-mandated tokens survived. Latency on these runs to 213 s.

## 3. What this retires

**The two-mechanism story is real, but it is not "degenerate vs redundant."**
It is:

- **gemma-4, Llama-3.3 (2 of 3 actors):** the planner visibly writes a full
  independent solution, then boxes an answer. Genuine redundant duplication.
- **gpt-oss (1 of 3):** the planner *also* does substantial work — 28 seconds
  of it — but our instrument recorded only the answer. **We cannot say what it
  did.** It may be duplication too.

So the honest split is **"observed duplication" vs "unobservable, instrument
failed here,"** not two model behaviours. Reporting gpt-oss as a distinct
*behavioural* mode would be attributing our logging defect to the model.

**This closes the loop on the withdrawn byte-identity metric.** Byte-identity
fired at 0.846 for gpt-oss and ~0.000 for the other two not because gpt-oss
rubber-stamps, but because gpt-oss is the actor whose visible output was
reduced to a boxed answer — and identical boxed answers are byte-identical.
The metric was measuring our logger. Same for the adjudication's low recall.

## 4. D19's genuinely valuable part survives

The third actor's contribution stands and is strengthened: **Llama-3.3 lands
with gemma-4 on visible duplication, making gpt-oss's pattern 1 of 3 rather
than the norm.** The manuscript currently generalizes from the gpt-oss shape.
It should instead say: two of three actors show planners that write full
solutions; the third is uninstrumented.

## 5. Actions

- Any collapse-rate table must split observed-duplication from
  instrument-failed, and must NOT present gpt-oss's short planner as a
  behaviour.
- `results.tex` §\ref{subsec:collapse} and the conclusion's
  "$0.846$--$0.975$ ... become three independent solvers" both need the
  planner decomposition and the ch/s caveat.
- The existing logging-defect subsection already discloses F13 but frames it
  as bounding *duplication*. It also bounds **collapse-mode interpretation**,
  which is a second consequence and is not currently stated.
- P1a-vs-proxy relationship must be stated: the proxy is inverted P1a, made
  length-robust. Not a new construct.
