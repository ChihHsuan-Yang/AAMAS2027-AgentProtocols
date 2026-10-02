# TODO — AAMAS 2027 (authoritative task board)

**Rewritten 2026-09-30 17:0x from VERIFIED state, not from worker reports.**
The previous board listed eight P0 items as OPEN; I checked each against the
artifact and **all eight were in fact closed**. A board that lags reality is
worse than no board — a new agent would have re-done finished work. Every
status below was re-verified by running the check named in its validation
column, today.

DONE = artifact exists **and** the validation command passes **and** Master
Agent reviewed it.

Deadlines: **abstract Oct 1 AoE** · **paper Oct 8 AoE**.

---

## P0 — submission-threatening

| id | task | owner | status | validation (run this) |
|---|---|---|---|---|
| P0-A | Close `STATISTICAL_AUDIT.md`: 1 FATAL + 5 SERIOUS | M | **DONE** | all 6 verified in rendered PDF; see breakout |
| P0-B | Main text ≤ 8 pages | M | **DONE** | `python3 scripts/pagecheck.py paper/main.pdf` → exit 0 |
| P0-C | Frozen snapshot backed up off-laptop | M | **DONE** | iCloud copy, 3/3 sha256 re-verified **at the destination** |
| P0-D | Push all commits | M | **DONE** | `git status -sb` → `## main...origin/main` |
| P0-E | Overleaf synced | M | **DONE** | remote at `ef400b20`; fresh clone builds standalone, 0 undef |
| P0-F | Abstract carries no dead claim | M | **DONE** | 0 hits for floor-effect / highest-of-any-arm / blinded-confirms |
| P0-G | Anonymity audit on final PDF | M | **DONE** | 0 hits for institution / HF / GitHub / author |
| P0-H | OpenReview profiles, author list, reciprocal reviewer | **BELLA** | **BELLA-ONLY** | not a project blocker; see `SUBMISSION_PACKAGE.md` |
| **P0-I** | **Second fresh mock review on the revised PDF** | M | **TODO** | reviewer #1 said weak-accept if blockers cleared; they are |
| **P0-J** | **Second independent number audit vs current output** | M | **TODO** | the last one predates 4 script fixes |

### P0-A breakout — all six verified in the rendered PDF today

| id | finding | status |
|---|---|---|
| F1 | Arm C recovery denominator dropped 173 rows | **DONE** — 0.314/0.395/0.139; Llama-only claim; "all three actors" gone |
| S1 | Holm asserted but never run | **DONE** — T29 runs it; P3 gemma Holm p=0.0120, P4 all retain |
| S2 | Llama "floor effect" falsified by our own Arm C | **DONE** — now "a genuine null specific to the role manipulation" |
| S3 | Context quartiles cut on the pooled distribution (n=12 cell) | **DONE** — re-cut within arm, n=12 figure gone |
| S4 | effect ÷ disagreement-rate is not a valid operation | **DONE** — replaced by noise-propagated bootstrap CIs |
| S5 | 2 of 3 P4 DiDs cannot detect any plausible interaction | **DONE** — only the gpt-oss−gemma DiD called informative |

---

## P1 — materially improves acceptance

| id | task | owner | status | note |
|---|---|---|---|---|
| P1-1 | SciBench A/B cross-domain replication | XDOM worker | **ACTIVE** | 919/2,296, zero failures, ETA ~55 min |
| P1-2 | SciBench freeze + manifest | XDOM worker | TODO | freeze script pre-validated on a partial copy |
| P1-3 | **SciBench integration decision** | M | TODO | rules fixed in advance: `notes/XDOMAIN-POWER-PREREG.md` |
| P1-4 | Figure selection final | M | **DONE** | fig1_v1_grouped in as Figure 1; 2 and 3 held for space |
| P1-5 | HF normalized parquet layer | steward | **DONE** | 5 tables, 181/181 values re-derived |
| P1-6 | Supplementary ZIP (≤25MB, anonymous) | M | TODO | prompts, rubric, prereg, extra tables |

---

## P2 — only if P0/P1 secure

| id | task | status |
|---|---|---|
| P2-1 | SciBench Arm C | **conditional** — only if A/B is informative |
| P2-2 | JEEBench third domain | TODO — 515 problems, free-response, MIT |
| P2-3 | Public HF release after acceptance | blocked on acceptance; `preflight_public.py` gates it |

---

## Standing rules a new agent must not violate

1. **`APPROVED_CLAIMS.md` governs every claim.** Its DEAD table is binding.
   After ANY change to `FINAL_TABLES.py`, re-derive that file too — it went
   stale behind the paper once already.
2. **No number is hand-maintained.** Every literal traces to
   `FINAL_TABLES.py` against `experiments/results/FROZEN/`.
3. **`scripts/pagecheck.py` is the only valid page check.** Two earlier
   versions passed a 10-page paper; both failure modes are in its docstring.
   Run it without a pipe — `| tail` makes `$?` report tail.
4. **HF stays PRIVATE until acceptance.** `hf_artifact/raw/` is gitignored
   (283MB; GitHub rejects it) and 14 rows still name the institution;
   `hf_artifact/scripts/preflight_public.py` fails by design until fixed.
5. **No underpowered null may be reported as absence.** This project has made
   that error twice.
