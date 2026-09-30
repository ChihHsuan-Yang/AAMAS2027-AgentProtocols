# Blinded frontier-model adjudication — reproducible protocol

**Not human annotation.** This validates whether the automated collapse metric
corresponds to judged semantic/functional redundancy. It is model-based
adjudication and is described as such everywhere.

## Judge
- primary: **Opus 5** (`claude-opus-5`), reached through an institutional
  API gateway. [Endpoint and credential mechanism redacted for review; no
  credential was ever logged or committed.]
- **decoding:** the endpoint **rejects `temperature`** ("deprecated"), so the
  served default is used and recorded as `temperature: null`. Judge stability
  is therefore estimated **empirically** from repeated independent calls, which
  is a stronger check than asserting temperature 0.
- **reps: 3 independent calls per item**, presentation order randomized
  (seed 20260929). Disagreements are recorded, never averaged away.

## Blinding — verified, not assumed
The judge sees only `=== Agent 1/2/3 ===` transcripts. Withheld: actor, arm,
automated collapse label, correctness, the hypothesis, the expected direction.

**A leak was found and fixed before running.** 45 items contained literal role
names ("Planner"/"Executor"/"Reviewer") in the message text, and they were
concentrated **42 in Arm A vs 3 in Arm B** — a near-perfect arm signal, because
Arm B's prompts omit role words. All role tokens were neutralized to
`Agent-P/E/R` **uniformly across every item**, so their presence carries no
information. Post-fix residual leaks: **0**. Actor-name leaks: **0** before and
after. Recorded in `SAMPLING_MANIFEST.json`.

## Rubric
`RUBRIC_v1.md`, sha `4f624de5b1073940`, **frozen before the first judgement**,
with four worked examples and a pre-declared borderline (a reviewer that checks
without adding content). Amendments require a dated entry and reporting of
pre-amendment numbers.

## Sample
171 items, stratified over actor × arm × automated-collapse across 14 non-empty
strata, seed 20260929, ≤14 per stratum. Manifest and per-item key in
`SAMPLING_MANIFEST.json` / `KEY.jsonl` (key withheld from the judge).

## Artifacts (all committed; no secrets)
`RUBRIC_v1.md` · `build_sample.py` · `ITEMS_blinded.jsonl` · `KEY.jsonl` ·
`SAMPLING_MANIFEST.json` · `adjudicate.py` · `VERDICTS.jsonl` (raw + parsed,
per call: model, rubric sha, prompt sha, UTC timestamp) · `adjudicate.log`.

## Reporting contract
agreement · precision · recall · confusion matrix · **per-actor** and
**per-arm** breakdowns · judge stability across the 3 reps · inspection of
disagreement cases. Never one aggregate number alone.

## What this establishes, and what it does not
It can support that the automated metric corresponds to *judged* semantic and
functional redundancy. It is **not ground truth**. The paper will state the
judge, the blinded protocol, the rubric, the stability, and the limitations of
model-based adjudication, and will not present it as equivalent to human
labelling.

## What it cannot do
It cannot reinstate the withdrawn scope claim. The byte metric's failure was
**recall** (it misses gemma-4's collapse entirely), and a better judge can only
raise gemma-4's measured collapse — pushing the actors closer together, never
apart. See `ADJUDICATION-SCOPE-NOTE.md`.

---

## Coverage limitation, found before analysis (2026-09-29)

The automated flag's positive stratum is **extremely unbalanced across actors**,
because collapse positives only exist where the metric fires:

| actor | auto_collapse = True | = False |
|---|---|---|
| gpt-oss-120b | **14** | 56 |
| gemma-4-31B | **3** | 56 |
| Llama-3.3-70B | **0** | 42 |

**Consequence, stated before any result is read:**
- **Precision** (of the flagged cases) is estimable only for **gpt-oss-120b**.
  gemma-4 has n=3; Llama-3.3 has none.
- **Recall** is estimable for all three, and recall is the quantity that
  withdrew the scope claim, so the design still answers the load-bearing
  question.

This is not fixable by sampling harder: Llama-3.3 has **zero** count-matched
collapse positives in its entire run (A 0/79, B 0/81, C 0/81). That zero was
verified as real rather than an instrument fault — **3,235/3,235 response
hashes recomputed from the raw text match exactly**, so its roles genuinely
emit different strings.

The paper must therefore report precision **per actor**, name the n, and not
present a pooled precision as if it generalized.

---

## Defect found and fixed mid-run (2026-09-29)

**31 of the first 125 verdicts (25%) returned EMPTY content** with no error —
`stop_reason: end_turn`, zero text. Diagnosis: at `max_tokens: 400` the judge
spent its budget reasoning on harder transcripts and emitted nothing.
Transcript length was **not** the driver (median 4,486 vs 4,192 chars overall),
so it is reasoning depth, not input size.

**This is the same error class as F13** — a budget exhausted on hidden
reasoning, producing an empty visible field. Discarding those items would have
biased coverage toward transcripts the judge found *easy*, i.e. exactly the
clear-cut cases, inflating apparent agreement.

**Fix:** `max_tokens` 400 → 1200, plus a salvage parser that recovers labels
from a verdict truncated mid-JSON. The 34 affected calls were **deleted and
re-queued**, not patched, so every verdict in the final file was produced under
one configuration. Post-fix: **131/131 parsed, 0 empty.**

**Judge stability so far:** among items with ≥2 completed reps, Q5 agreement is
**20/20 (1.000)**. Final stability is reported over all 3 reps at completion.
