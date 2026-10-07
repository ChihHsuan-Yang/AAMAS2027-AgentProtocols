# Sec.12 — freeze script controls (run before the cells finish)

`experiments/bf_freeze.py`, exercised on a fixture of 40 **real** runner rows
(a synthetic fixture previously crashed on a missing optional field and made
three controls report FAIL for the wrong reason).

Exit codes captured directly, not through a pipe — see the note below.

| # | control | expected | result |
|---|---|---|---|
| 1 | freeze a real-row source | writes manifest, exit 0 | PASS (sha e5b2ca5ba6723ff5) |
| 2 | verify what was just frozen | PASS, exit 0 | PASS |
| 3 | flip ONE byte in the source | FAIL, exit 1 | **FAIL** (manifest e5b2… vs disk 265d…) |
| 4 | restore the byte, verify again | PASS, exit 0 | **PASS** — tracks bytes, does not latch |
| 5 | verify clean | PASS, exit 0 | PASS |
| 6 | flag typo `--src DIR` | refuse, exit 1, create nothing | refused; no stray `--src` dir |
| 7 | nonexistent source | refuse, exit 1 | refused |
| 8 | empty source dir | refuse, exit 1, write nothing | refused; dir left with 0 entries |
| 9 | two positional args | refuse, exit 1 | refused |
| 10 | manifest with no sha-bearing entries | refuse, exit 1 | refused (no vacuous PASS) |

Control 4 is the one that matters most: a checker that reports FAIL forever
after one bad run is indistinguishable from a working one on a single test.
Verify recovers, so it is reading bytes each time.

## A measurement error worth recording

I first reported "VERIFY: FAIL exits 0" — a real defect if true, since a CI
step or `&&` chain would read failure as success. It was wrong. I had written
`... | tail -4; echo "exit=$?"`, which captures the exit status of `tail`, not
of the script. Run directly, the script exits **1** on FAIL, as it should.

Same shape as two other errors this session (a b/c inversion in my drift
control harness; a leak pattern satisfied by whitespace): the instrument was
pointed at the wrong subject and returned a confident, wrong answer. The script
was correct in all three cases.

## Pre-existing frozen data (Sec.12: must not be disturbed)

Re-verified after all of the above, both still byte-identical to their own
manifests:

- `/tmp/frozen_omni` — actor3.jsonl (1200), armCp.jsonl (800), campaign_v2.jsonl (9600) → **VERIFY: PASS**
- `/tmp/frozen_sci` — scibench_AB.jsonl (2296) → **VERIFY: PASS**

Bf will be frozen into its own separate directory and never merged into these.

## Freeze timing — why the freeze has NOT been run yet (2026-10-06 ~15:50)

Both Bf cells are complete:

```
bf_omnimath_gemma4.jsonl   1600/1600   COMPLETE, 0 infra failures
bf_scibench_gemma4.jsonl    574/574    COMPLETE, 0 infra failures (bf_status exit 0)
```

but `bf_freeze.py` freezes **every** `.jsonl` in its source directory:

```python
for f in sorted(os.listdir(SRC)):
    if f.endswith(".jsonl") and not f.endswith(".infra_failed.jsonl"):
        cells[f] = cell(os.path.join(SRC, f))
```

and `experiments/results/bf/` now also contains
`bridgeA_omnimath_gemma4_n400.jsonl`, which the orchestrator started writing at
15:42:35 and is still growing. Freezing now would record a sha256 for a file
that changes seconds later — a manifest that fails its own `--verify` through
no fault of the tool, and worse, a frozen record of a partial bridge.

The freeze therefore runs **after** the bridge cell completes, so one manifest
covers three settled files. This is a sequencing decision, not a design change:
`n` is unchanged, no cell is dropped, nothing is re-scoped.

Note also that the bridge lands in the same directory and will be captured by
the same manifest. That is acceptable for *provenance* (it records what was
produced) and is not pooling: S.16 forbids pooling the bridge into any results
table, which is a property of the analysis scripts, not of the freeze. The
manifest keeps each cell as a separate entry with its own `config_version`, and
those differ by construction:

| cell | arm | config_version |
|---|---|---|
| bf_omnimath_gemma4.jsonl | Bf | `25a04a554afcd006` |
| bf_scibench_gemma4.jsonl | Bf | `d311904cee36c21b` |
| frozen omni campaign_v2 | A/B/C | `e3afa39849c1b980` |
| frozen scibench_AB | A/B | `aed89f28ab338bdb` |

Four distinct values; no two cells can be silently merged on a shared key.

## Pre-existing frozen data re-verified (again, after both cells finished)

```
/tmp/frozen_omni   actor3.jsonl, armCp.jsonl, campaign_v2.jsonl   -> VERIFY PASS
/tmp/frozen_sci    scibench_AB.jsonl                              -> VERIFY PASS
```

Still byte-identical to their own manifests. Nothing in this work has modified
the frozen A/B campaign.
