# Second domain (SciBench) — **SLOT FILLED in v1.1.0**

> **STATUS: FILLED.** As of **v1.1.0** this release contains SciBench data:
> 2,296 trajectories, 574 problems, 2 actors, Arms A and B only.
> This file is kept as the record of what was promised, so the promises can be
> checked against what was actually done. Each numbered step below is marked
> with its outcome.
>
> | promised | done? |
> |---|---|
> | arrives as v1.1.0, never an edit to v1.0.0 | **yes** — build and emitter both assert every v1.0.0 file is byte-unchanged |
> | new rows carry `benchmark_id='scibench'`, `domain='science'`, own `config_version` | **yes** — `aed89f28ab338bdb`, asserted single-valued over all 2,296 rows |
> | new trace gets its own sha256/rows/bytes; existing three keep theirs | **yes** — `raw/MANIFEST_SCIBENCH.json`; the v1.0.0 digests are re-listed in `VERSION.release_history` |
> | `CHECKSUMS.txt` / `VERSION` regenerated, history gains an entry, v1.0.0 hashes stay listed | **yes** |
> | per-domain results split in the card | **yes** — *Cross-domain (v1.1.0)* |
> | SciBench gets its own MIT entry; NOT absorbed into Apache-2.0 | **yes** — plus `LICENSES/MIT-SciBench.txt` verbatim, verified three ways |
>
> **One thing this file did not anticipate:** the Arm A prompt had to be
> **domain-adapted**, so Arm A is *not* the same contract in the two domains
> (Arm B is byte-identical). That is stated in the card, in
> `config/run_config_scibench.json`, and in a per-prompt diff table in
> `config/prompts_scibench.json`. It is why no cross-domain P1a or
> clause-specific fidelity metric is computed.

---

## The original text, as written before the slot was filled

**Status in v1.0.0: NOT PRESENT. Nothing in this release is SciBench data.**

A second-domain campaign on **SciBench** was running while v1.0.0 was packaged.
It is deliberately not blocked on: v1.0.0 is complete and self-consistent as a
single-domain (competition math, Omni-MATH-2) release.

## Why this file exists

So that a later freeze is **added**, never silently folded into these numbers.
Every row in v1.0.0 carries `benchmark_id = "omnimath2"` and `domain = "math"`
— verified over all 11,600 rows, one distinct value each. A consumer can
therefore always separate domains by filtering, including after v1.1.0 lands.

## How the second domain will be added

1. It arrives as **v1.1.0**, a new minor version — never as an edit to v1.0.0.
   v1.0.0's files keep their bytes and their sha256s.
2. New rows carry `benchmark_id = "scibench"`, `domain = "science"`, and their
   own `config_version`. Existing rows are untouched.
3. `manifests/FROZEN_MANIFEST.json` gains the new trace file with its own
   sha256/rows/bytes; the three existing entries keep their current hashes.
4. `CHECKSUMS.txt` and `VERSION` are regenerated; `VERSION.release_history`
   gains an entry. The v1.0.0 hashes stay listed so anything published against
   v1.0.0 remains checkable.
5. The card gains a per-domain results split. **Any cross-domain claim is new
   and must clear `APPROVED_CLAIMS.md` first** — a second domain does not
   inherit the math findings.

## Licensing consequence — do not skip this

SciBench is **MIT**, not Apache-2.0, and the upstream registry marks it
`evaluation_only_recommended`. It is a *different licence from the Omni-MATH-2
material already here.* Adding it means:

- adding a SciBench row to `LICENSES/registry.json` (its `license_id`,
  `training_use_policy`, and what is actually redistributed), and
- **not** extending this release's Apache-2.0 statement over it.

See `LICENSES/README.md`, which already records the per-source position rather
than a single blanket licence, precisely so this slot can be filled without
rewriting the licensing story.
