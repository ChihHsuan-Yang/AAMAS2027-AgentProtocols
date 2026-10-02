# HANDOFF_CURRENT — live pointer to the Overleaf-ready submission

**Updated 2026-10-02. Read this first if you are picking the project up, or
if Overleaf access has just been restored.**

**GitHub HEAD: `c7716f1ee05e`** on `main`. Everything below is at that commit.

---

## The one-line state

The submission is **gate-complete**: main paper 8 pages + references,
supplement assembled and building, all gates passing, data artifact verified
private. Overleaf is blocked for an account reason and **nothing depends on
it** — `paper/` reconstructs the project exactly.

```
python3 scripts/final_freeze.py        # every gate, writes FINAL_FREEZE.json
```
Last run: **ALL_GATES_PASS true, FAILED_GATES []**.

---

## Overleaf is BLOCKED, and it is not a project defect

```
fatal: remote error: no git access
```

The bare HTTPS endpoint returns **401** while `overleaf.com` returns 200, so
the service is up and this project's git access is off. **Cause: Bella's
Argonne Premium affiliation is not yet linked.** She will say when it is
restored.

**Do not** create a replacement Overleaf project, change the remote, or
treat this as a blocker.

Last successful Overleaf push: `19f5d6e53c81` (2026-10-01, pre-rewrite). The
Overleaf project is therefore **two rewrites stale** — it still carries the
old title and the pre-narrative sections. Do not read it as current.

---

## WHAT IS WAITING TO PUSH

| | |
|---|---|
| staging clone | `/tmp/aamas_ol` — the real Overleaf clone, remote intact |
| commit sitting there, unpushed | `1d5883811cfc` — **now itself stale**; it predates the supplement, the regenerated figures and the current tables |
| canonical copy | **`paper/` at GitHub HEAD** |

**Rebuild the staging commit from `paper/` rather than pushing the one in
`/tmp`.** The procedure at the bottom does that from scratch; it is the
supported path and `/tmp` is not durable.

---

## What changed since the last handoff

- **Supplement assembled** — `paper/supplement.tex`, a second document in
  the same project sharing `aamas.cls`, `refs.bib` and `tables/`. 11 pages,
  builds clean. The paper promised a supplement in five places and there
  was none.
- **New generated table** `tables/context_quartiles.tex` supplies the
  context panel the main text promised and nothing produced.
- **Table disposition is now generated**, declared beside the registry in
  `mk_tables.py`, with the "which document inputs this" column read off
  both documents' sources. A table inputted by neither is reported as an
  orphan.
- **`scripts/final_freeze.py` rewritten** — it gated only `main.pdf`, its
  TODO gate counted its own macro definition (so it read 1 forever), and
  its title was two rewrites stale because it was hand-typed. Title and
  figure list are now parsed from the sources, and the supplement is gated
  as hard as the main paper.
- **A stale figure was shipping.** `paper/figures/` held an uncorrected
  `fig1_v1_grouped.pdf` still printing bare condition codes, while the
  terminology gate — reading `figures/`, one directory up — reported clean.
  Deleted; the gate now reads both directories and compares them; and
  `mk_figstyle.save()` syncs the copy LaTeX actually uses.
- **Figure PDFs are byte-reproducible** — `savefig` was embedding a
  wall-clock `CreationDate`, so the hash recorded at freeze could not
  distinguish *changed* from *regenerated*.
- **`freeze_commit` no longer follows HEAD** — it was `git rev-parse HEAD`,
  so a docs-only re-stamp re-dated the data freeze to a prose commit. Now
  derived from the frozen-data descriptors.
- **Anonymous AI-assistance disclosure** written at
  `paper/AI_ASSISTANCE_DISCLOSURE.md` (the internal `AI_ASSISTANCE_LOG.md`
  stays internal; it carries identifying content).

---

## Where to look

| question | file |
|---|---|
| what is the paper, in 30 seconds | `README.md` |
| how do I rebuild the Overleaf project | `paper/README.md` |
| what may I assert | `APPROVED_CLAIMS.md` (incl. a DEAD list) |
| where did this figure come from | `paper/figures/README.md` |
| where did this table come from, and where does it go | `paper/tables/README.md` |
| what do the condition codes mean | `paper/TERMINOLOGY.md` |
| what is in the data artifact | `paper/README.md`, HF section |

---

## HOW TO PUSH WHEN ACCESS RETURNS

Rebuild the staging clone from `paper/` rather than pushing whatever sits in
`/tmp` — that commit predates the supplement and the regenerated figures.

**Two traps in this copy, both hit while writing the procedure.** Excluding
`*.pdf` to drop build products also drops the *figures*, and the build then
succeeds with missing images. And a grep for `github|huggingface` over the
source fires on `aamas.cls` (upstream, two issue links in comments) and on
`refs.bib` comments that exist precisely to warn against those URLs — so a
source grep must name the actual private identifiers, while the real
anonymity test is run on the **compiled PDF**.

```bash
cd ~/Documents/note/projects/AAMAS2027-AgentProtocols

# 0. Refuse to push a tree that does not pass its own gates.
python3 scripts/final_freeze.py || { echo "GATES FAIL -- do not push"; exit 1; }

# 1. Fresh clone of the REAL project. Never create a new one.
rm -rf /tmp/aamas_ol
git clone https://git@git.overleaf.com/6abae70ebd16e2dc9cdecee6 /tmp/aamas_ol

# 2. Mirror paper/ into it. Build products out, FIGURES IN -- the figures
#    are PDFs and a naive --exclude '*.pdf' silently drops them.
rsync -a --delete --exclude '.git' \
      --exclude '*.aux' --exclude '*.log' --exclude '*.out' \
      --exclude '*.fls' --exclude '*.fdb_latexmk' --exclude '*.bbl' \
      --exclude '*.blg' --exclude '*.synctex.gz' \
      --exclude 'main.pdf' --exclude 'supplement.pdf' \
      paper/ /tmp/aamas_ol/

# 3. Remove what is OURS, not the manuscript's. paper/README.md carries the
#    private GitHub/Overleaf/HF links and must not be copied anywhere.
rm -f /tmp/aamas_ol/README.md \
      /tmp/aamas_ol/TERMINOLOGY.md \
      /tmp/aamas_ol/AI_ASSISTANCE_DISCLOSURE.md \
      /tmp/aamas_ol/ABSTRACT_provisional.md \
      /tmp/aamas_ol/figures/README.md \
      /tmp/aamas_ol/tables/README.md

# 4. Prove the figures arrived and the private identifiers did not.
ls /tmp/aamas_ol/figures/*.pdf                    # must list the figures
grep -rniE "ChihHsuan-Yang|AgentsSci|6abae70ebd16e2dc9cdecee6|argonne|alcf" \
     /tmp/aamas_ol --exclude-dir=.git \
  && { echo "PRIVATE IDENTIFIER IN THE TREE -- stop"; exit 1; } \
  || echo "source clean"

cd /tmp/aamas_ol && git add -A
git commit -m "Narrative rewrite: title, five-step story, supplement, regenerated figures"
git push origin main
```

**Then verify. A push exiting 0 is not evidence the remote builds:**

```bash
git ls-remote origin | head -1                     # must equal local HEAD
rm -rf /tmp/olverify
git clone https://git@git.overleaf.com/6abae70ebd16e2dc9cdecee6 /tmp/olverify
cd /tmp/olverify
for d in main supplement; do
  pdflatex -interaction=nonstopmode $d.tex >/dev/null 2>&1
  bibtex $d >/dev/null 2>&1
  pdflatex -interaction=nonstopmode $d.tex >/dev/null 2>&1
  pdflatex -interaction=nonstopmode $d.tex >/dev/null 2>&1
done
python3 ~/Documents/note/projects/AAMAS2027-AgentProtocols/scripts/pagecheck.py main.pdf
grep -a -c "Undefined citation" main.log           # 0

# Anonymity, on the RENDERED text of both PDFs -- the only check that matters.
pdftotext main.pdf - | grep -icE "argonne|alcf|github|huggingface|overleaf"
pdftotext supplement.pdf - | grep -icE "argonne|alcf|github|huggingface|overleaf"

# The real test: does the clone produce the SAME PAPER?
pdftotext main.pdf - | shasum -a 256
pdftotext ~/Documents/note/projects/AAMAS2027-AgentProtocols/paper/main.pdf - | shasum -a 256
# These two must match. Equal page counts are not the same claim.
```

---

## STATE OF THE MANUSCRIPT RIGHT NOW

**This draft is at the page limit and passes every submission gate.**

| | |
|---|---|
| title | From Feedback to Revision: When Multi-Agent Roles Become Load-Bearing |
| pages | **8 main text + references on 9** — compression COMPLETE |
| `pagecheck` | EXIT 0, positive-controlled on this build |
| `latexmk` | exit 0, 0 undefined citations, 0 duplicate labels |
| arm labels in prose / figures | **0 / 0** |
| venue | Hanoi, Vietnam |
| `aamas.cls` | byte-identical to the official kit |

Bella's instruction was that story quality precedes compression. The
expansion pass deliberately overshot (11 pages) so the argument could be
written properly; the compression pass then cut it to 8 using the writing
agent's own ranked cut list, ending with one decisive 165-word condensation
once I measured that small cuts were not moving a Conclusion that reflows as
one block.

---

## KNOWN OPEN ITEM BEFORE THE NEXT FREEZE

**RESOLVED 2026-10-02.** The inline `tab:collapse` is replaced by
`\input{tables/main_role_collapse}`; duplicate-label warnings are 0 and the
table in the paper is generated, so its numbers carry provenance. The other
two inline tables had already been removed by the compression pass.

**Still open:** the remaining five generated tables in `paper/tables/` are
not yet `\input` anywhere — they are destined for the supplement, which is
not yet built. See `paper/tables/README.md` for which goes where.

---

## WHERE EVERYTHING IS

| what | path |
|---|---|
| canonical manuscript | `paper/` (GitHub, authoritative) |
| generated tables + index | `paper/tables/` |
| terminology map (internal, never compiled) | `paper/TERMINOLOGY.md` |
| figures | `figures/`, generated by `analysis/scripts/mk_fig*.py` |
| the only source of a number | `analysis/scripts/FINAL_TABLES.py` -> `analysis/out/FINAL_TABLES_OUTPUT.txt` |
| what may be claimed | `APPROVED_CLAIMS.md` (DEAD table binding) |
| frozen data | `experiments/results/FROZEN/` + `experiments/results/xdomain/FROZEN_SCIBENCH/` |
| private data artifact | HF `AgentsSci/AAMAS2027-Roles` v1.1.0 (PRIVATE) |
| update chain, mandatory | `SOURCE_OF_TRUTH.md` |
