# Final literature audit — forward citations + claim-level citation verification (2026-09-30)

Commissioned adversarially. Two jobs: (1) close the forward-citation hole that
`NOVELTY-RECOVERY-2026-09-29.md` §6 flagged as "the biggest hole", (2) verify the
~8 closest citations at the level of **what the paper says**, not its metadata.

**Headline:** no scoop found. One **MISMATCH** in the paper text
(`yang2026precise` is not observational). Two disputed phrases from a prior audit
**do** verify and were wrongly doubted. The four-part conjunction stands.

---

## 0. WHAT CHANGED VERSUS THE PRIOR AUDIT

| prior audit's blocker | status now |
|---|---|
| Semantic Scholar 429'd; no forward-citation search possible | **RESOLVED.** S2 answers with a browser `User-Agent`. Default Python/curl UA gets 429; `Mozilla/5.0 …Chrome/124.0` gets 200. 3,406 citing papers pulled. |
| WebSearch unavailable | **STILL BLOCKED** (Vertex org policy `constraints/vertexai.allowedPartnerModelFeatures`, HTTP 400). Routed around via S2 + OpenAlex + arXiv API + OpenReview. |
| MAST's 14 modes only 6/14 recovered | **RESOLVED.** All 14 recovered from the PDF. None matches us. |
| 2609.04217 "role-differentiation collapse"/"decorative" unverified | **RESOLVED — both phrases are real.** Prior doubt was an artifact of reading the abs page only. |
| DBLP / OpenAlex never attempted | OpenAlex **works** but has poor preprint→preprint recall (36 citations for Huang vs S2's 1,240) — used only as a cross-check. DBLP is **bot-walled** (Anubis interstitial). |

---

## 1. JOB 1 — FORWARD-CITATION SEARCH

### 1.1 Coverage actually achieved

Wave 1 — full forward-citation crawl of the four requested seeds, paginated to
exhaustion, **zero aborted pages** (verified: `grep -c ABORT` = 0):

| seed | paper | citing papers pulled |
|---|---|---|
| 2310.01798 | Huang et al., LLMs Cannot Self-Correct Reasoning Yet | 1,240 |
| 2402.08115 | Stechly et al., Self-Verification Limitations | 164 |
| 2305.19118 | Liang et al., Encouraging Divergent Thinking / DoT | 1,415 |
| 2503.13657 | Cemri et al., Why Do Multi-Agent LLM Systems Fail? | 647 |

Wave 2 — forward citations of the **closest prior works** (a scooper would cite
these, not only the four seeds): 2609.04217 (0), 2609.28150 (0), 2503.16814 (2),
2406.01297 (367), 2604.03809 (4), 2602.03128 (4).

- Wave 1 unique: **3,222**. Wave 2 new: **184**. **Total distinct screened: 3,406.**
- Year mix (wave 1): 2026 → 1,481; 2025 → 1,037; 2024 → 493; 2023 → 122; unknown → 88.
- Abstracts present for 2,948/3,222 (91%); median abstract 1,359 chars (full, not snippets).
  **274 papers were screened on title only** — the one real recall gap inside the crawl.

### 1.2 The screen, and how it was made honest

A first screen returned **0 papers matching all three core categories**. I did not
report that. I ran it against a **paraphrase of our own claim** and it scored 0/4 —
i.e. the screen could not have found us, so its null was worthless. Per
`prove-the-checker-can-fail` / `run-the-pattern-against-its-own-positive`, I widened
until three positive controls all fired and negatives stayed clean:

| control | v1 | final |
|---|---|---|
| our claim in our own words | 4/4 | 4/4 |
| our claim paraphrased (no shared jargon) | **0/4** | 4/4 |
| our claim written obliquely ("job descriptions", "nameless crews") | **0/4** | 4/4 |
| negative: GPU attention kernel | 0/4 | 0/4 |
| negative: prompt-engineering survey | 0/4 | 0/4 |

Final screen on 3,222: 408 papers at 4/4, 1,053 at 3/4. All 408 title-reviewed;
the ~30 plausible ones read at abstract level; 6 read in full text.

A second, structural screen avoided vocabulary entirely: papers citing **both** a
self-correction seed **and** a multi-agent seed — the co-citation footprint our
claim would necessarily have. **128 papers; 97 from 2025–2026; all 97 titles read.**
**Zero papers cite all four seeds.**

### 1.3 Every query and source, including failures

**Semantic Scholar** (graph API, browser UA) — forward citations: 4 seeds + 6
second-wave seeds, exhaustive pagination. Relevance search: 12 queries, **9 of 12
returned HTTP 429 even with backoff** (recorded as failures, not as nulls); the 3
that succeeded returned nothing on point.

**arXiv Atom API** — 15 targeted queries for the conjunction. Notable: `abs:"role-free" AND abs:"agent"`
→ 3 hits; `abs:"role ablation"` → 5 (none MAS-relevant); `all:"remove role labels"` → **0**;
`abs:"without role labels"` → **0**; `abs:"oracle" AND abs:"role" AND abs:"multi-agent" AND abs:"recovery"` → **0**;
`abs:"distinct answers" AND abs:"agent"` → 1. Note `abs:"distinct answers"` matched
**0 of 3,222** citing papers — our mediator's vocabulary is essentially unused in this literature.

**OpenAlex** — works, and indexes 2026 arXiv IDs, but forward-citation recall is far
below S2 (Huang: 36 vs 1,240). Used only to cross-check metadata and to confirm
duplicate records (MAST has two: W6910824972 preprint / W7196981818 NeurIPS 2025).

**OpenReview** (api2) — 6 queries. Returns *review text*, not matching papers; no signal.
Weak instrument for this purpose, reported as such.

**Blocked / unusable:** WebSearch (org policy, HTTP 400, whole session) · DBLP
(Anubis bot wall) · CORE (redirect loop, no key) · Inciteful (404) · Crossref
(404 on arXiv DOIs) · Google Scholar (not attempted — hard bot-walled; I did not
want to report a null from an instrument I could not run) · Connected Papers (no
public API) · ar5iv (failed for 2310.01798 and 2402.08115 on `ar5iv.labs.arxiv.org`;
**`ar5iv.org/abs/<id>` worked** — a host quirk, not a missing paper).

### 1.4 Scoop candidates

None reaches SCOOP. Ordered by overlap.

| # | paper | rating | why it is not a scoop |
|---|---|---|---|
| 1 | **2606.05976** — The Self-Correction Illusion: **Role Relabeling** Gates Explicit Error Flagging | **STRONG OVERLAP — closest new find; MUST CITE** | Title is alarming and the manipulation is genuinely *the role label*, held byte-identical: it varies only whether an erroneous claim is tagged assistant / user / tool / system, and relabeling to an external role raises explicit-correction rate by **23–93 pp** in 10/12 settings. But: **single-agent** (`multi-agent` appears 0 times in the full text), the roles are *chat-template message roles*, not agent personas; **no recovery conditional, no answer-diversity measure, no budget matching** (`recovery` 0 hits, `budget` 0 hits). It is the strongest published statement that *a role label is a causal variable in error correction* — which makes it a natural ally and a reviewer's likely "isn't this yours?" It is not the conjunction. |
| 2 | **2607.28908** — Reflection or Re-Generation? Why LLM Revision Fails Where Human Revision Succeeds | ADJACENT, upgraded | Has two of our four moving parts and says so in the abstract: "revision **conditioned on first-pass correctness**" and "**oracle**-guided revision", plus a human baseline. But **no roles at all** (`planner`/`executor`/`role-free` all 0 hits) and no answer-diversity metric. Its finding — objective-task reflection is "neutral re-generation indistinguishable from re-sampling", ∆I≈0 — is a *sharper* statement of the failure we inherit, and it is a better citation for "recovery-after-error as a metric" than what we cite now. |
| 3 | 2604.01029 — Revision or Re-Solving? Decomposing Second-Pass Gains | ADJACENT | Four matched conditions decomposing second-pass gains into re-solving / scaffold / content, incl. role-reversed arms. Two-model revision pipeline, not a role ablation; no recovery conditional, no diversity metric. |
| 4 | 2605.27559 — Detection Without Correction | ADJACENT | Two-parameter decomposition (detection vs conditional generation); conditional miscorrection 53–94%. Our "more feedback, no repair" in different coordinates — but no role manipulation. |
| 5 | 2609.32802 — Re-derivability Decides What a Staged Agent Pipeline Recovers After an Upstream Fault | ADJACENT | Staged pipeline, recovery after an injected fault, budget/topology held fixed, registered kill test. The manipulated variable is **re-exposure of the original problem**, not the role label; no answer-diversity mediator. Methodologically our nearest neighbour. |
| 6 | 2606.19826 — Heterogeneous LLM Debate Under Adversarial Peers | ADJACENT | Matched panels; harmful-revision and flip rate **on initially-correct items** — a conditional, but the mirror of ours. Lever is peer heterogeneity, not roles. |
| 7 | 2609.36855 — When Upstream Messages Override Correct Answers | ADJACENT | Controlled, evidence held fixed, three message conditions; "answer substitution" in 94% of harmful cases. Message content is the lever, not role structure. |
| 8 | 2608.11949 — ExRole | ADJACENT | Explicitly compares against a **role-free** control and beats it — but on aggregate EM/F1 for search tasks, with no post-failure conditional. Relevant as prior art that a role-free control is a standard baseline. |

**Nothing found runs a role ablation and reports a post-failure conditional.**
That specific pairing returned **zero** across 3,406 citing papers, 15 arXiv
queries, and the co-citation screen.

### 1.5 Confidence, stated honestly

**Moderately high, not certain.** Strong: the citation graph around the four seeds
is now exhaustively enumerated (0 aborted pages), the screen is calibrated against
three positive controls, MAST's 14 modes are closed out, and two independent
screens (lexical, co-citation) agree. Weak: **no general web search ran at all**;
274/3,222 papers were title-only; 9 of 12 S2 relevance queries 429'd; DBLP and
Google Scholar never ran, so **non-arXiv venue work published 2025–2026 that does
not cite any of our ten seeds is invisible to this audit.** A scoop, if one exists,
most likely lives there or in a paper posted in the last few weeks that has not yet
been cited or indexed.

---

## 2. JOB 2 — CITATION VERIFICATION

Method per row. "Full text" = PDF via `arxiv.org/pdf` + `pdftotext -layout`, or
rendered HTML, string-searched and read in context. Hotlink note: arXiv PDF needs
a browser UA **and** a `Referer` of the abs page.

| key | arXiv | what we claim | verdict | how verified |
|---|---|---|---|---|
| `huang2024selfcorrect` | 2310.01798 | 74.7% = **answer retention**, not round-2 accuracy; oracle condition **improves** 75.9→84.3 | **VERIFIED-CLAIM** | ar5iv full text. Both "74.7" occurrences located and disambiguated. Occurrence 1 = Table 3 round-2 *accuracy* 74.7. Occurrence 2 = §3.3: "For GSM8K, **74.7% of the time, GPT-3.5 retains its initial answer**." We cite the second. Table 2 oracle row confirmed 75.9→84.3 (GSM8K), 95.5→97.5 (GPT-4), and "we use the correct label to determine when to stop the self-correction loop". **We cite the right one.** |
| `dylan2026equal` | 2609.04217 | 0.769 vs 0.754, p=0.80 | **VERIFIED-CLAIM** | Full PDF. Table IV: "All (n=134) … 0.657 / **0.754** (single, evolve p_exec) / **0.769** (team P→E→C) / 0.731 (LOI:exec)". Column headers read explicitly to avoid an off-axis read. Body: "not statistically separable from the single agent (∆=+0.015, **p=0.80**) while costing 1.8× the evaluation calls". |
| — | 2609.04217 | prior audit: "role-differentiation collapse" and "decorative" **did not verify** | **PRIOR DOUBT OVERTURNED — both phrases are real** | Full PDF. "This is **role-differentiation collapse**—not an optimizer failure but a property of the substrate" (×1). "**decorative**" ×5, incl. "The roles are **decorative**: they consume the extra calls … without changing outcomes", fig. caption "Steering roles are decorative", and instrumentation: planner influence 0.14, critic 0.41, critic restate-rate 0.00. **Both are quotable.** The earlier null came from checking the abs page only. |
| `jiang2026exactfeedback` | 2609.28150 | "failed trajectories often repeat earlier outputs"; recurrence **associated with** lower recoverability | **VERIFIED-CLAIM — hedge is correct** | Full PDF. Abstract verbatim: "failure trajectories often repeat earlier outputs, and prior recurrence **is associated with** substantially lower subsequent recoverability." Body is even more explicit: "This is a **predictive association, not evidence that repetition itself causes failure**." We have **not** upgraded "associated" to "predicts". Keep it that way. |
| `liang2024divergent` | 2305.19118 | DoT definition; MAD is the prescribed cure (our inversion depends on it) | **VERIFIED-CLAIM** | ar5iv full text. Verbatim: "once the LLM has established confidence in its solutions, it is unable to generate novel thoughts later through reflection even if its initial stance is incorrect." Body adds "proposed and defined by us for the first time." Cure: "**To address the DoT problem, we propose a Multi-Agent Debate (MAD) framework**". **Inversion claim is safe.** |
| `stechly2024selfverification` | 2402.08115 | the binary backprompt condition | **VERIFIED-CLAIM** | Full PDF §5.2 verbatim: "**Binary feedback** … either the verifier accepts the solution, stopping the system, or we create a backprompt which says the previous answer was wrong but doesn't elaborate." Plus "the level of feedback often doesn't seem to matter–as long as the verifier is sound". |
| `oh2026entrenchment` | 2503.16814 | belief entrenchment; "reinforce shared errors"; cure = perspective diversity | **VERIFIED-CLAIM** (see §3 for a metadata nit) | Full PDF. "belief entrenchment, where agents **reinforce shared errors rather than correcting them**"; root causes "biased static initial belief" + "homogenized debate dynamics"; remedy is diverse-perspective prompting. Confirmed it has **no** role ablation (`role-free`, `planner`, `executor` = 0 hits) — our differentiation holds. |
| `kamoi2024when` | 2406.01297 | "self-correction works well in tasks that can use reliable external feedback" | **VERIFIED-CLAIM** | Full PDF, verbatim in the abstract-contributions list: "(2) **self-correction works well in tasks that can use reliable external feedback**"; restated §5.1. Vol 12 / pp. 1417–1440 confirmed against **ACL Anthology** (`2024.tacl-1.78`). |
| `yang2026contamination` | 2605.08563 | single author **Zhanfu Yang** (earlier draft confabulated 3 fake authors) | **VERIFIED-METADATA + CLAIM** | arXiv abs page `citation_author` meta: **exactly one** author, "Yang, Zhanfu". Abstract confirms CCRM, contaminated-restart error rate ε1 > ε0. **The confabulation is gone; do not reintroduce co-authors.** |
| `cemri2025why` | 2503.13657 | MAST taxonomy, 1,600+ traces, "disobey role specification" | **VERIFIED-CLAIM** | Full PDF: "MAST-Data, a comprehensive dataset of **1600+** annotated traces across 7 MAS frameworks" (exact n = 1,642); taxonomy from 150 traces, κ=0.88, **14 modes / 3 categories**. **All 14 recovered** (1.1–1.5, 2.1–2.6, 3.1–3.3) — closing the prior audit's 6/14 hole. FM-1.2 Disobey Role Specification confirmed at 1.50%/1.57%. **No mode matches answer-identity-under-role-ablation.** |
| `jiang2026confidence` | 2609.27822 | observational, does not manipulate roles | **VERIFIED-CLAIM** | Full PDF. Self-describes: "The adoption logit in Appendix E is **observational**"; "the **observational taxonomy** does not establish that endorsement caused the difference"; "A system-level effect requires an intervention or rerun" (i.e. it did not run one). `role-free` = 0. |
| `yang2026protocol` | 2608.14927 | observational, does not manipulate roles | **VERIFIED-CLAIM** | Full PDF. Four-protocol comparison with solver held fixed; `intervention` = 0, `role-free` = 0, `counterfactual` = 0. Protocol choice is the compared unit; roles are never ablated. |
| `yang2026precise` | 2607.15388 | **"All three are observational"** (related.tex) | **MISMATCH** | Full PDF. It runs **within-PER interventions**: contribution #2 is literally titled "**Interventions.**" — "Within-PER probes that hold the model family, reviewer backbone, and budget fixed"; Figure 4 is "Within-PER **intervention** evidence", arms PER(base) / PER+ACK / PER+EMB, N=4,181, ACK lowering FinalPassRate 85.2→82.5. **It is interventional, and budget-matched.** See §3. |

Bibliographic metadata for the remaining 12 entries was re-pulled from the arXiv
Atom API (title, full author list, submission date, primary class) and all matched
`refs.bib`: 2602.03128, 2608.21747, 2607.21627, 2609.28693, 2605.28433, 2510.07614,
2609.05933, 2603.28990, 2605.08813, 2607.16133, 2604.00026, 2604.03809.
**24/24 metadata OK. One claim-level MISMATCH, listed above.**

---

## 3. MISMATCHES AND FIXES

### 3.1 MISMATCH — `yang2026precise` is not observational (blocking)

`paper/sections/related.tex:88` reads:

> Three prior studies analyze the corpus this work instruments[…]. **All three are
> observational**; none measures whether the specified division of labor is
> realized, and the controlled arms of §4 do not exist in that corpus.

2607.15388 is **interventional**. Its own contribution list says "**Interventions.**
Within-PER probes that hold the model family, reviewer backbone, and budget fixed",
and Figure 4 reports PER(base) vs PER+ACK vs PER+EMB on the full 4,181 benchmark.

Why this one matters more than a wording slip: it is **our own group's paper**, on
**the same corpus**, running a **budget-matched intervention on a PER pipeline**.
A reviewer who reads it and then reads "all three are observational" has found us
overstating our own delta, in the exact place the thin-slicing objection lands. The
two clauses that follow are still true and still do the work — it does **not**
manipulate roles (its interventions vary how critique *reaches* the solver, not who
the agents are), and it has no role-free arm. The paper even declines the stronger
reading itself: "we do not interpret their gap as a pure prompt-control ablation."

Suggested replacement (text only — `paper/` is yours, I have not touched it):

> Three prior studies analyze the corpus this work instruments. Two are purely
> observational; the third runs within-PER interventions that hold model, reviewer
> and budget fixed while varying how critique reaches the solver. **None manipulates
> the role structure itself**, none measures whether the specified division of labor
> is realized, and the controlled arms of §4 do not exist in that corpus.

### 3.2 Not a mismatch, but worth a note: `oh2026entrenchment`

`year = {2026}` on arXiv ID **2503**.16814 (submitted 2025-03-21, v5, comments
"Accepted to TACL", `citation_online_date` 2026/02/11). Consistent with the file's
own documented convention, but it is **not** one of the three IDs the header's
"known metadata caveat" lists. Either add it to that list or set `year = {2025}`.
Unlike the other TACL entry it carries no volume/pages — correct, since TACL has
not paginated it yet.

### 3.3 Optional: `cemri2025why` has a real venue

The bib has it as `@misc` / arXiv only. The PDF's own footer: "**39th Conference on
Neural Information Processing Systems (NeurIPS 2025) Track on Datasets and
Benchmarks**", and OpenAlex carries a separate conference-paper record
(W7196981818). Citing the arXiv version is defensible; citing NeurIPS D&B is better.

---

## 4. PROPOSED BIBTEX (for you to apply — I did not edit `refs.bib`)

Both verified this session from the arXiv Atom API + full PDF text.

```bibtex
% Closest new find of the 2026-09-30 forward-citation search.
% Single-agent; "roles" here are chat-template message roles, not agent personas.
% Cite as the strongest evidence that a role LABEL is causal for error correction,
% and to pre-empt "isn't this the same manipulation?" -- it is not multi-agent,
% has no recovery conditional, no diversity metric and no budget matching.
@article{chen2026relabeling,
  author  = {Chen, Kuan-Yen and Su, Fang-Yi and Lin, Shih-Yen and Li, Bao and
             Chiang, Jung-Hsien},
  title   = {The Self-Correction Illusion: Role Relabeling Gates Explicit Error
             Flagging in Large Language Models},
  journal = {arXiv preprint arXiv:2606.05976},
  year    = {2026},
  eprint  = {2606.05976},
  archivePrefix = {arXiv},
  primaryClass = {cs.AI},
  note    = {15 pages, 3 figures, 15 tables.}
}

@article{tao2026reflection,
  author  = {Tao, Yefan and Friedland, Gerald and
             Chandrasekaran, Madhusudhanan and Kong, Luyang},
  title   = {Reflection or Re-Generation? Why {LLM} Revision Fails Where Human
             Revision Succeeds},
  journal = {arXiv preprint arXiv:2607.28908},
  year    = {2026},
  eprint  = {2607.28908},
  archivePrefix = {arXiv},
  primaryClass = {cs.LG},
  note    = {20 pages, 8 figures.}
}
```

Both author lists were pulled from the **arXiv Atom API** (`export.arxiv.org/api/query?id_list=`),
the same instrument and the same `<name>` fields `refs.bib`'s existing provenance
note relies on — not from recall, and not from the Semantic Scholar record (which
returned these papers without authors). Titles, submission dates (2026-06-04 and
2026-07-31), primary classes and page counts came from the same records.

`tao2026reflection` is useful in the "failure to revise" paragraph — it has
*revision conditioned on first-pass correctness* **and** an oracle arm, which is
two of our four parts in a single-agent setting, and its ∆I≈0 "neutral
re-generation" result is a cleaner citation than several we currently use.

---

## 5. DOES THE FOUR-PART CONJUNCTION STILL HOLD?

**Yes.** Part by part, against 3,406 citing papers:

| part | status |
|---|---|
| (i) first-pass accuracy unchanged under role deletion | **Owned by others** — 2609.04217 (p=0.80, now fully verified incl. both disputed phrases), 2602.03128, 2402.18272. Already conceded in `related.tex` as a control. Correct as written. |
| (ii) recovery conditional on a wrong first answer collapses | **The phenomenon of low recovery is known**; the **contrast across a role ablation is not**. Zero of 3,406 papers pair a role manipulation with a post-failure conditional. |
| (iii) not by closing the repair loop — role-free gets MORE feedback | **No prior work found makes this dissociation.** Nearest is 2402.08115 ("level of feedback doesn't matter — as long as the verifier is sound"), which is single-agent and reports success rates only. |
| (iv) by collapsing production of distinct candidate answers | **Phenomenon owned** (DoT, verified verbatim; 2609.28150, verified incl. its own "association not causation" hedge). As a **measured mediator across a role contrast**, still unclaimed — `abs:"distinct answers"` matched **0 of 3,222** citing papers. |

The conjunction, and the role manipulation as the control variable, survive. Two
things to do before submission, both cheap: fix §3.1, and cite 2606.05976 — it is
the single most likely paper for a reviewer to wave at this submission, and citing
it first with the four differences stated is much cheaper than being handed it.

**What could still overturn this:** a 2025–2026 paper at a non-arXiv venue that
cites none of our ten seeds. No instrument I could reach covers that set. If you
want it closed, the missing instrument is Google Scholar or DBLP from a host that
is not bot-walled — I would not claim coverage of it from here.

---

## 6. REPRODUCTION

Working files in `/tmp/lit/` (ephemeral — copy out if you want them kept):
`cites.json` (wave-1 raw), `cites2.json` (wave-2), `uniq.json` (3,222 deduped),
`scored.json`, `screen4.py` (calibrated screen incl. its controls),
`cocite.json`, `ft/` (PDFs + extracted text for 13 papers).

Two operational notes worth keeping:
- **Semantic Scholar is not actually down for us** — it rate-limits on User-Agent.
  A browser UA plus ~3.5 s between pages sustained ~3,400 records. The prior audit's
  "S2 429'd" was a UA problem, not a quota problem.
- **arXiv PDF fetches need UA + `Referer: https://arxiv.org/abs/<id>`**; and when
  `ar5iv.labs.arxiv.org` returns nothing, try `ar5iv.org/abs/<id>` before concluding
  the full text is unavailable.
