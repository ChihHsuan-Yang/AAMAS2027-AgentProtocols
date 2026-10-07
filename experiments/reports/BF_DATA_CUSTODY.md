# Bf control — where the data lives

Written at handoff, 2026-10-06. The raw Bf trajectories are **not in git** (the
repo's `.gitignore` excludes `experiments/results/**/*.jsonl`; raw rows are
~42MB and follow the same convention as the original campaign). This file
records where they are and how to prove a copy is intact.

## Control branch SHA

| | |
|---|---|
| branch | `control-rolefree-feedback` |
| SHA at which every Bf cell was collected | `0450ac0635008da899861170c4e7921b4ecd11dd` |
| remote | `github.com/ChihHsuan-Yang/AAMAS2027-AgentProtocols` |

The freeze manifest also records this SHA, the per-runner source hashes
(`runner.py`, `runner_xdomain.py`, `prompts.py`) and `git_status_dirty`.

## Durable location of the raw rows

```
AAMAS2027-AgentProtocols/hf_artifact/raw/bf/
    bf_omnimath_gemma4.jsonl              1600 rows   sha be3469f720048ca9...
    bf_scibench_gemma4.jsonl               574 rows   sha 965ed061ebb107d5...
    bridgeA_omnimath_gemma4_n400.jsonl     400 rows   sha 0ec97d88048e84e3...
    + per-cell .log files
    FROZEN_BF/MANIFEST.json                (copy of the tracked manifest)
```

This sits beside the original campaign's raw rows (`campaign_v2.jsonl`,
`scibench_AB.jsonl`) in the same `hf_artifact/raw/` staging tree, which is
gitignored by design. The working copy under `/tmp/aamas_bf` is **scratch and
should not be relied on** — `/tmp` is cleared on reboot.

`hf_artifact/` is the staging tree for `AgentsSci/AAMAS2027-Roles`, which is
**PRIVATE** and must stay private during double-blind review. Nothing here has
been published.

## Verifying any copy

The manifest is content-addressed, so it verifies a copy anywhere:

```bash
python experiments/bf_freeze.py --verify <dir>/FROZEN_BF <dir>
```

Confirmed PASS at handoff against **both** the `/tmp` working copy and the
durable `hf_artifact/raw/bf/` copy. The verifier was positive-controlled by
flipping one grade in a throwaway copy: it reported MISMATCH and exited 1.

## The original frozen campaign is untouched

Re-verified at handoff, unchanged from the digests recorded before the Bf
freeze ran:

| dir | digest (first 16) |
|---|---|
| `experiments/results/FROZEN` | `8e7b191d8c52f13f` |
| `experiments/results/xdomain/FROZEN_SCIBENCH` | `c35afcf862c709bd` |

`bf_freeze.py` writes only to `<SRC>/FROZEN_BF` and structurally cannot touch
those directories. Bf is frozen **separately** and is never pooled (S.12/S.16);
each manifest cell records its own `arms`, so the bridge self-labels `["A"]`
and the Bf cells `["Bf"]`.
