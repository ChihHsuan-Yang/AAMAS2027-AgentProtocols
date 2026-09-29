# Blinded frontier-model adjudication — reproducible protocol

**Not human annotation.** This validates whether the automated collapse metric
corresponds to judged semantic/functional redundancy. It is model-based
adjudication and is described as such everywhere.

## Judge
- primary: **Opus 5** (`claude-opus-5`), reached via the local argo-shim proxy
  (`ANTHROPIC_BASE_URL` + `apiKeyHelper`). No credential is logged or committed.
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
