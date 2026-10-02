# Invalid and superseded — what not to use, and why

Back to [the project README](../README.md) ·
[artifact map](PAPER_ARTIFACT_MAP.md) ·
[trace availability](TRACE_AVAILABILITY.md) ·
[data provenance](DATA_PROVENANCE.md)

**Retraction here is labelling, not deletion.** Every number below is left
readable on purpose. A retracted value that has been deleted cannot be
recognised when it resurfaces in a stale note, an old figure, or a worker's
summary — and in this project retracted numbers *have* resurfaced. If you
meet one of the values in the right-hand columns, you are looking at
something stale.

Last verified **2026-10-02** against the live canonical output.

---

## Superseded runs — present on disk, never pooled

| run | path | why it is void | status |
|---|---|---|---|
| `campaign_v1` | `experiments/results/main/campaign_v1_TRUNCATION_BUG.jsonl` | a truncation defect in the runner; the rows are not comparable with v2 | **QUARANTINED** — never pooled, never analysed, retained as evidence |
| `smoke_v1` | `experiments/results/smoke/smoke_v1_prefix_PREFIX_BUG.jsonl` | produced before the validators were fixed | **QUARANTINED** |

Both are kept deliberately. Neither is released, and neither contributes a
single row to any reported number. The canonical campaign is
`experiments/results/FROZEN/`, whose manifest names exactly three Omni-MATH
traces.

## Superseded numbers — if you see these, the artifact is stale

| quantity | **stale value** | **current value** | what happened |
|---|---|---|---|
| enforced-condition recovery, 3 actors | 0.412 / 0.461 / 0.150 | **0.314 / 0.395 / 0.139** | the recovery denominator dropped 173 trajectories that received a first incorrect verdict and then died in regeneration. Repaired; two of three paired enforcement $p$-values did not survive |
| enforced-condition first pass | 0.822 | **0.779** | the same survivorship defect, one column to the left |
| grader noise floor | 0.0395, then 0.0023, then 0.0086 | **0.0072** (group-level, conservative) | four successive measurements of the same quantity: a wrong key, then clustered pairs, then group-level, then exact candidate bytes. Only the last is correct |
| "effect ÷ noise floor = 3.9×" | *any* such ratio | **withdrawn entirely** | dividing an effect size by a grader-disagreement rate is not a valid operation, and the noise largely cancels in a paired contrast. `[T27]` now resamples the paired difference with the per-call flip probability instead — and its own header says the ratio is withdrawn |
| authorship-axis rates | 0.014 / 0.084 / 0.042 | **0.986 / 0.916 / 0.958** | the column was `authored-free`, i.e. *not* authored. The axis was inverted in the prose |
| significance of several contrasts | read off a bootstrap CI bound | **exact McNemar on discordant pairs** | the CI-bound reading was seed-dependent — one contrast read significant in 62% of seeds. The defect appeared at four separate sites |
| "9.35% noise floor" | — | **not ours at all** | imported from an unrelated project's memory file. Ours is 0.0072 |

Full audit trail with dates and commits: [`../STATISTICAL_AUDIT.md`](../STATISTICAL_AUDIT.md).

## Dead claims

[`../APPROVED_CLAIMS.md`](../APPROVED_CLAIMS.md) carries a **DEAD** table of
claims that were asserted and then falsified. It is binding: a claim on that
list must not reappear in any artifact, including a figure caption or a
README. Three that recur most often:

- enforcement "restores both organization and recovery" — it un-freezes the
  answer; it does not become end-to-end accuracy;
- Llama-3.3's null as "a floor effect" — falsified by our own enforced
  condition, which moves that same actor to 0.139;
- the adjudication as "blinded" — it is outcome-blind and **not**
  condition-blind.

## Superseded figures

| file | status |
|---|---|
| `figures/fig1_v1_grouped.pdf` | **SUPERSEDED** by `fig1_v1_story`. Deleted from `paper/figures/` on 2026-10-02: the copy there was the *uncorrected* one, still printing bare condition codes, and it sat in the Overleaf-bound directory while the terminology gate — reading `figures/` — reported clean |
| `figures/fig1_v2_story.pdf`, `fig1_v2_slopes`, `fig1_v3_dumbbell`, `fig2_v1_xdomain`, `fig2_v1_budget`, `fig2_v2_panels`, `fig2_v3_funnel`, `fig3_*`, `fig4_*`, `figS1_conditions` | **ALTERNATES** — design variants kept for reference under `figures/`. None is shipped. `paper/figures/` contains exactly what the documents include, and a gate fails if that stops being true |

## Why the stale values keep coming back

Three mechanisms, all observed in this project:

1. **A number typed into a second file stops tracking the first.** This is
   why `SOURCE_OF_TRUTH.md` forbids hand-maintained numbers and why every
   table and figure is generated.
2. **A retracted analysis resurfaces in a later summary** written by someone
   reading an older note. Instrument beats timestamp: check the value against
   `analysis/out/FINAL_TABLES_OUTPUT.txt`, not against which document looks
   more recent.
3. **A derived artifact goes stale behind its source.** After any change to
   `FINAL_TABLES.py`, re-derive `APPROVED_CLAIMS.md` too — it has fallen
   behind the manuscript twice.
