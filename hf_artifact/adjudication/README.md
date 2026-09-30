# Blinded adjudication files

Model-based adjudication (Opus 5) validating the automated functional-collapse
metric. **Not human annotation. Not ground truth.** See `PROTOCOL.md`.

| file | contents |
|---|---|
| `ITEMS_blinded.jsonl` | 171 blinded transcripts (`=== Agent 1/2/3 ===` only) |
| `KEY.jsonl` | unblinding key (actor, arm, auto_collapse, correctness) — withheld from the judge |
| `VERDICTS.jsonl` | 513 verdicts = 171 items x 3 reps, raw + parsed |
| `RUBRIC_v1.md` | frozen before the first judgement, sha `4f624de5b1073940` |
| `SAMPLING_MANIFEST.json` | seed, strata, pre/post-neutralization item hashes |
| `PROTOCOL.md` | method and mid-run defects |
| `build_sample.py`, `analyze.py` | sampling and analysis |

## Two modifications made for release

1. **`build_sample.py`** — a hardcoded absolute home-directory path was replaced
   with `os.environ.get("PROJECT_ROOT", ".")`. It was deanonymizing.
2. **`PROTOCOL.md`** — the judge endpoint and its credential-helper mechanism
   were redacted. No credential was present in any file; the names of the
   internal proxy and env var were.

`adjudicate.py` is **not included**: it resolves an endpoint and a credential
helper, and is transport rather than method. Everything needed to audit the
study — protocol, rubric, items, key, verdicts, analysis — is here.

## Read the residual blinding leak first

`PROTOCOL.md` states "post-fix residual leaks: **0**". That is true of the
literal role-name strings and **false of the signal**. The role tokens were
*renamed* to `Agent-P`/`Agent-E`, not removed, and their presence retains the
original near-perfect arm signal: 42/42 of Arm A items contain one, versus
3/56 of Arm B (Fisher exact p = 1.5e-24).

Arm-contrastive adjudication numbers are therefore **not** protected by the
blinding the protocol claims. `../SCHEMA.md` documents what this does and does
not threaten.
