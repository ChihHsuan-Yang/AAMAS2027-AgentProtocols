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

## Two manifests describe these filenames — read this before citing a hash

The branch carries **two** manifests naming the same three files with
**different** sha256, byte counts and timestamps:

| | written by | records |
|---|---|---|
| `experiments/results/bf/MANIFEST_BF.json` | the parallel gpt-oss/Llama session, commit `4e50b4c` | **chain 1** |
| `experiments/results/bf/FROZEN_BF/MANIFEST.json` | `bf_freeze.py`, this session | **chain 2** = the bytes on disk |

This is not corruption and neither manifest is wrong. `run_bf.sh` defaults to
`TAG=${TAG:-gemma4}` and writes `$D/bf_omnimath_${TAG}.jsonl`, so a second
invocation with the default tag **rewrites the same three filenames in place**.
It was run twice, about 13 h apart. Each chain is internally contiguous — one
sequential pass of omni → scibench → bridge — per the per-cell `.log` files:

| cell | chain 1 (manifest only) | chain 2 (bytes on disk) |
|---|---|---|
| `bf_omnimath_gemma4.jsonl` | 05:41:19 → 09:19:29 UTC | 18:33:39 → 21:55:43 UTC |
| `bf_scibench_gemma4.jsonl` | 09:19:31 → 10:41:46 UTC | 21:55:45 → 22:42:34 UTC |
| `bridgeA_omnimath_gemma4_n400.jsonl` | 10:41:47 → 11:39:48 UTC | 22:42:35 → 23:43:22 UTC |

Both chains report the same `config_version` per domain
(`25a04a554afcd006`, `d311904cee36c21b`), the same row counts, and the same
`run_id`s (`bf-gemma4-n1600`, `bf-gemma4-scibench`, `bridgeA-gemma4-n400`) —
all four verified against the chain-2 rows directly. They differ only in
sampled content.

The two chains are pinned to commit `0450ac0` by **different standards of
evidence**, which matters if you are deciding how much to trust them. Chain 2
is hash-pinned: `FROZEN_BF/MANIFEST.json` records `runner_sha256` for
`prompts.py`, `runner.py` and `runner_xdomain.py`, and all three are
byte-identical to their contents at `0450ac0`. Chain 1's `0450ac0` is a
self-reported string in `MANIFEST_BF.json` with no accompanying source hashes,
and its bytes are gone, so it cannot now be checked. The trajectory rows
themselves carry **no** `code_commit` field in either chain — the commit is
never stamped per row, only per manifest. (`git_status_dirty` is `true` in the
freeze manifest: the tree held uncommitted report files at freeze time, but the
three hashed runner sources were clean.)

**Every number in `BF_FINAL_REPORT.md` was computed from chain 2**, the bytes
currently on disk — sha `be3469f720048ca9` / `965ed061ebb107d5` /
`0ec97d88048e84e3`, matching `FROZEN_BF/MANIFEST.json` and the durable copy in
`hf_artifact/raw/bf/`. This was confirmed by re-running `bf_control.py` at
handoff and reproducing the reported figures exactly (`Bf 177/302 = 0.5861`,
`Bf 54/124 = 0.4355`, `A vs Bf p = 2.39e-24`, `Bf vs B p = 7.29e-43`). The
freeze, the hashes above, the gate audits and the drift analysis all read the
same bytes.

**The chain-1 bytes no longer exist** — not on disk, not in the durable copy,
not in git (raw `.jsonl` is gitignored and was never committed). They were
overwritten in place. `MANIFEST_BF.json` is therefore a record of a run that
cannot be re-verified or re-analysed; it should be read as provenance for a
superseded pass, not as a checksum for anything now present. **Do not "fix" the
discrepancy by editing or deleting either manifest** — the conflict is the
evidence that two passes happened.

### What this costs, stated plainly

The two chains are not interchangeable. Mapping stopping conditions to
final-correct (validated against per-row truth and the runner logs on chain 2,
exact in 3/3 cells):

| cell | chain 1 | chain 2 |
|---|---|---|
| `bf_omnimath_gemma4.jsonl` | 1474/1600 | 1475/1600 |
| `bf_scibench_gemma4.jsonl` | 505/574 | 504/574 |
| `bridgeA_omnimath_gemma4_n400.jsonl` | **327/400** | **338/400** |

The two Bf cells move by ≤1 trajectory, so the headline Bf-vs-A and Bf-vs-B
contrasts are insensitive to which chain is used. **The bridge is not.** Section
H's drift test compares the bridge against the frozen arm-A reference of
330/400; chain 2 gives 338/400 (delta **+0.0200**), chain 1 would give 327/400
(delta **−0.0075**). The point estimate changes sign. Both are small and both
sit inside the CI reported in §H, so the `NONE` verdict is unlikely to change —
but the drift estimate is demonstrably re-run-sensitive at this n, which is an
additional reason to read §H's `NONE` as weak evidence rather than as a
certificate. This compounds the defect already recorded in §H and §I: `NONE` is
emitted by a `bounded` predicate that reads first-pass and final only and never
consults the recovery CI, so recovery drift was already unresolved at n = 400.

Chain 1 cannot be used to check this, because its rows are gone. Re-running the
bridge would produce a *third* chain, not a reconciliation — and the user has
directed that no further Bf runs be launched. Recorded here for the human
authors rather than resolved.
