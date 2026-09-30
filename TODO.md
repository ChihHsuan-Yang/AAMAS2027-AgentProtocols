# TODO — AAMAS 2027 (authoritative task board)

**Rewritten 2026-09-30.** 8 days to the full-paper deadline. The campaign is
**complete and frozen**; everything below is write-up, correction, and
packaging. **No experiment is in flight and no new campaign is planned** — a
new one would need Bella's approval and there is no time for it.

DONE = artifact exists **and** it was reviewed **and** validation passed.

---

## P0 — submission-threatening

| id | task | owner | status | validation |
|---|---|---|---|---|
| **P0-A** | **Close out `STATISTICAL_AUDIT.md`** — 1 FATAL (tables fixed, prose open) + 5 SERIOUS, see the breakout below | paper + analysis | **OPEN** | each required change made, or explicitly declined with a reason |
| **P0-B** | **Page budget 9 → 8** by cutting content (typesetting tricks are inadmissible) | paper | **OPEN** | `pdfinfo main.pdf \| grep Pages` shows 8 |
| **P0-C** | **Back up `experiments/results/FROZEN/`** off this laptop | any | **OPEN** | a second copy exists, hashes re-verified there |
| **P0-D** | **Push the 16 local commits** to `origin/main` | any | **OPEN** | `git status` says up to date |
| **P0-E** | **Sync `paper/` → Overleaf** (clone is at `128771e`, missing the class and later rewrites) | paper | **OPEN** | Overleaf builds and matches `paper/` |
| **P0-F** | **Abstract pass against the audit** — it still asserts two now-dead claims | paper | **OPEN** | no dead claim in `main.tex`'s abstract |
| **P0-G** | **Re-run the anonymity audit after the final trim** | any | **OPEN** | 8/8 counts zero on the rendered PDF, metadata clean |
| P0-H | OpenReview profiles / reciprocal reviewer / author list | **BELLA** | **BLOCKED — not a project blocker** | manual; API 403s on every call, CFP host does not resolve |

### P0-A breakout — the audit findings

| id | finding | required change | where |
|---|---|---|---|
| **F1** | **FATAL.** Arm C's recovery denominator dropped 173 trajectories with a recorded first *incorrect* verdict that then died in regeneration. Corrected 0.314/0.395/0.139; 2 of 3 paired p-values lost. | Delete "recovery … above Arm A in all three actors (p ≤ 1.6e-3)". Claim Arm C recovery for **Llama-3.3 only**; report the other two as directionally consistent, not resolvable against attrition. | `APPROVED_CLAIMS.md` A6 ✅ · `FINAL_TABLES.py` T1 ✅ (commit `ba28977`) · `results.tex` §R5 ❌ |
| **S1** | **A false statement about the methods.** `method.tex:63` and `results.tex:6` assert a Holm correction; `holm` appears **0 times** in `FINAL_TABLES.py` and 0 times in its output. **A reviewer verifies this with one grep.** | **Run it** (preferred — the preregistration committed to it; numbers in `stat_audit_a3_multiplicity.py` §3.3). It changes no verdict: gemma C−A survives at Holm p=0.042, P4 still null. | `FINAL_TABLES.py` ❌ · `method.tex` ❌ · `results.tex` ❌ |
| **S2** | "Floor effect" for Llama-3.3 is falsified by our own Arm C — a channel that does not exist cannot be restored, and Arm C restores it (p=3.8e-06). | Replace with "a genuine null, specific to the role manipulation," plus the power statement (~80% at 0.04–0.05 vs a gemma effect of 0.171). `limitations.tex` has it exactly backwards. | `APPROVED_CLAIMS.md` A3 ✅ · `results.tex` §R3 ❌ · `limitations.tex` ❌ |
| **S3** | T22's quartiles are cut on the **pooled** A+B context distribution, making them arm indicators (gpt-oss Q1 = 12 Arm A vs 198 Arm B). An n=12 cell is quoted. The context measure is additionally distorted by the F13 logging defect. | Re-cut within arm; state why; drop the n=12 figure and the "All three statements stand" sentence. The reversal itself survives. | `results.tex` §R4 ❌ |
| **S4** | Effect-size ÷ grader-disagreement-rate is not a valid operation, and the noise largely cancels in a paired contrast. | Delete every "3.9×" style ratio. Propagate the per-call rate into the bootstrap instead — same three verdicts. | `APPROVED_CLAIMS.md` A8 ✅ · `FINAL_TABLES.py` T27 ❌ · `results.tex`, `limitations.tex` ❌ |
| **S5** | Two of three P4 DiDs have MDE 0.069/0.075 against plausible effects ≤ 0.040 — they cannot detect any plausible interaction. | Say which DiD is an informative null (only gpt-oss−gemma, MDE 0.033) and which are not. | `APPROVED_CLAIMS.md` A10 ✅ · `experiments.tex` ❌ |

The audit also **reproduced T1/T2/T4/T7 exactly** and found **no arithmetic
error anywhere in the headline pipeline**, and it attacked the gemma-4 headline
six ways without breaking it (raw p=1.9e-08; Bonferroni over all 38 contrasts
= 7.4e-07). Every finding above is about *what was computed*, not whether it
was computed correctly.

---

## P1 — strengthening

| id | task | owner | status | note |
|---|---|---|---|---|
| P1-1 | Choose which Figure 1 variant ships and `\includegraphics` it | figures | OPEN | three exist (`fig1_v1_grouped`, `v2_slopes`, `v3_dumbbell`), all frozen-snapshot-sourced via `FIGDATA.json`; **none is in `main.tex`** |
| P1-2 | Decide supplementary material | paper | OPEN | must ship **inside** the submission zip (≤ 25 MB), never behind a link |
| P1-3 | Author-independent submission metadata to paste | paper | OPEN | — |
| P1-4 | R-10 evaluator independence — gpt-oss grades itself | — | **UNTESTED, likely won't happen** | the identical-prompt control rules out bias *on the answer string* only and **does not upgrade this**. Report as a limitation. |
| P1-5 | Confirm `results.tex` §p4null uses **prereg** scoring with as-graded as a disclosed sensitivity and attrition beside it | paper | OPEN | F24 §6 |

---

## P2

| id | task | status |
|---|---|---|
| P2-1 | Internal mock review of the final draft | OPEN — the last one produced 20 confirmed defects; worth repeating if time allows |
| P2-2 | Reviewer-annotation work (R4 / N-14) | **DECIDED: narrow the claim** rather than annotate. `notes/R4-DECISION.md`. |

---

## Closed — do not reopen

| id | task | outcome |
|---|---|---|
| Main campaign (3 arms × 3 actors + C′) | **DONE** — 11,600/11,600, frozen, hashed, verified |
| Third-actor decision | **DONE** — gemma-3-27b was 503 throughout; substituted Llama-3.3-70B, verified live |
| Preregistration committed before confirmatory results | **DONE** — prereg 22:52:33Z < launch 23:00:42Z |
| Smoke run + 15 launch gates | **DONE** — 15/15 pass, re-verified 2026-09-30 |
| Blinded frontier-model adjudication | **DONE** — 171 items × 3 reps, rubric frozen, 3 defects found and fixed mid-run |
| Official AAMAS class | **DONE** — the earlier "unobtainable" finding was wrong; the 404 was a hotlink guard |
| Pre-declared NOT-SUBMIT condition | **EVALUATED, NOT TRIGGERED** — narrowly; see `SUBMISSION_CHECKLIST.md` |
| Collapse measurement audit, count-matched rule, difficulty stratification, stability-as-n-grows, mechanism, single-agent fairness, novelty audit | **DONE** |
| Verified bibliography | **DONE** — 24 entries |
| Result provenance for every number | **DONE** — replaced by a single rule: `FROZEN/` + `FINAL_TABLES.py`, no duplicate numbers |

## Dropped with reason

| item | reason |
|---|---|
| Arm D (role shuffle) | tests a different question; would halve power on the A/B/C contrast |
| C2 strict-computation arm | no defensible validator buildable before the deadline without risking P0s |
| Second domain | the runner pins omnimath2; lab-bench's Planner contract has no computation clause |
| Full n=4181 stretch | marginal power not worth risking C′ and the noise floor |
| Second organization / topology | out of scope for the claim |
| Releasing the poll panel as a sub-dataset | would make the dataset the contribution again — `OVERLAP_AUDIT.md` |
| DHD | core asset of a third, already-public paper |
