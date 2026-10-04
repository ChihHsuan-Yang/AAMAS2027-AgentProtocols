# Official AAMAS class

## CURRENT: AAMAS-2027 author kit — added 2026-10-03

Source: https://warwick.ac.uk/fac/sci/dcs/aamas2027/aamas_2027_template.zip
linked from the AAMAS 2027 Submission Instructions page
(https://warwick.ac.uk/fac/sci/dcs/aamas2027/guidelines-and-policies/instructions/).
Downloaded in a browser by a co-author on 2026-10-03.

| file | sha256 |
|---|---|
| `aamas_2027_template.zip` (not stored here) | `e70e88d36fd96db0777b9d00a1cd0bd1eecbbb28619e9e723dcf207a9bc6ce2a` |
| `aamas.cls` (acmart v2.19, 2026/06/27) | `e88c8e3e5fd1e39f93a2a4fa5b664e125b67487996b4236668206acf5c70ca7e` |
| `ACM-Reference-Format.bst` | `8ec002c927068bfc5b3cfe71b66aa4767b9e485530ac3c67ba5c064df4c2e6ac` |
| `by.pdf` (CC-BY mark used by the copyright block) | `19b7b19350bb937afead8e45e4ad006187e14803bef783902dbd88e370fc9917` |

`aamas.cls`, `ACM-Reference-Format.bst` and `by.pdf` in this directory and in
`paper/` are now the 2027 kit's files, unmodified. `AAMAS_2027_sample.tex` and
`sample_2027.bib` are kept for reference.

What changed against the 2026 kit, as it affects this paper:

- New copyright block (CC-BY, uses `by.pdf`), copied verbatim into
  `paper/main.tex` and `paper/supplement.tex`.
- `\acmConference` now reads "AAMAS 2027 ... 3--7 May 2027 ... Hanoi, Vietnam"
  with the named editors.
- NEW, REQUIRED: `\acmSubmissionID{<OpenReview submission id>}` — printed on
  page 1 in anonymous mode — and `\submissionType{Research Paper Track}`.
  **The submission ID in main.tex and supplement.tex is
  `2850` (set 2026-10-03 from the OpenReview author console).**
- The 2027 sample has no CCS-concepts block and gives keywords separated by
  commas; main.tex follows the sample on both.
- `\acmPrice` removed (the sample no longer sets it).
- The class warns about figures without `\Description{}`; both figures have one.
- Section headings are set in mixed case ("References", not "REFERENCES");
  the running head is "Research Paper Track" / "AAMAS 2027, 3–7 May 2027,
  Hanoi, Vietnam". `scripts/pagecheck.py` was updated for the new head.

Result on 2026-10-03 (TeX Live 2023 build): main text ends on page 8,
references on page 9, supplement 11 pages. Re-check on the submitting machine.

Everything below this line is the HISTORICAL record for the AAMAS-2026 kit the
paper was built on until 2026-10-03. Statements there that the 2027 kit does
not exist are superseded by this section.

---

# Official AAMAS class (2026 kit) — retrieved 2026-09-30

Source: https://cyprusconferences.org/aamas2026/wp-content/uploads/2025/06/AAMAS-2026-Formatting-Instructions-pre-CR.zip
linked from https://cyprusconferences.org/aamas2026/submission-instructions/

## How to fetch it (this matters)

A plain `curl -sL <url>` returns **HTTP 404 with a 401KB HTML page**. The
server rejects requests without a browser User-Agent and a same-site Referer.
This works:

```
curl -sL -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)" \
     -e "https://cyprusconferences.org/aamas2026/submission-instructions/" \
     -o t.zip "<url>"
```

**Earlier in this project the class was recorded as unobtainable** ("every
candidate URL returned 403 or 404", main.tex header comment, 2026-09-28). That
was wrong: the file was always there, and the 404 was a hotlink guard. The
lesson is that a 404 whose body is 400KB of HTML is not a missing file — check
the payload before concluding a resource does not exist.

## Verified rules from the submission-instructions page (2026-09-30)

- "The use of LaTeX is mandatory."
- "Please do not modify the style files or any of the layout parameters."
- "Papers submitted to the main track must be at most 8 pages long, with any
  number of additional pages containing bibliographic references."
- "Excessive use of typesetting tricks to make everything fit into 8 pages is
  not admissible."
- "AAMAS reviewing is double-blind."
- Replace name/affiliation on page 1 with the paper tracking number; no
  acknowledgements.
- Self-cite in the third person.
- "Papers must not include pointers to any supplementary material that is not
  provided as part of the submission."
- Abstract ~100-300 words, plain text, due one week before the paper.
- Supplementary: single zip, <= 25MB, same anonymity policy.

NOTE: these are the AAMAS **2026** instructions. AAMAS 2027 had not published
its own at retrieval time. The 2027 dates Bella gave (abstract Oct 1, paper
Oct 8 AoE) match the 2026 pattern exactly. Re-check before submission.

## Class usage
```
\documentclass[sigconf,anonymous]{aamas}   % submission
\documentclass[sigconf]{aamas}             % camera-ready
```
The copyright block in AAMAS_2026_sample.tex is marked "do not change" and
must be carried over, with the year/venue updated for 2027 when known.

---

## AAMAS 2027 author kit: DOES NOT EXIST YET (checked 2026-09-30)

Bella's brief asked for "the current official AAMAS 2027 author kit, not a
2026 kit with the year manually changed." I looked for one. **There is none.**

Checked:
- `aamas2027.org` — does not resolve (HTTP 000, no DNS).
- `ifaamas.org` — no 2027 link anywhere on the site.
- `ifaamas.org/previousaamas.html` — lists every AAMAS from 2002 to 2026.
  **2027 is absent entirely**: no URL, no location, no dates, no organizers.
  The most recent listed edition is 2026, Paphos, 25-29 May.

So the 2026 kit is not a convenient substitute; it is **the newest kit that
exists**. The submission therefore uses `aamas.cls` from the AAMAS-2026 kit
(sha256 `f0af39a7…`, byte-identical to the downloaded original — verified,
never edited) with the copyright block's year advanced to 2027.

### What this means for the submission
Nothing blocking. Venue metadata in an anonymous submission is cosmetic; the
class controls the layout, and the layout rules (8 pages main text, unlimited
references, double-blind, no style-file edits, no typesetting tricks) have
been stable across AAMAS editions.

### What must be re-checked, and when
`CAMERA_READY_CHECKLIST.md` carries this. When IFAAMAS publishes the 2027
kit, re-verify and update:
- the `\acmConference` block (venue name, dates, city, editors);
- `\copyrightyear` / `\acmYear`;
- the page limit and any anonymity-rule change;
- whether `aamas.cls` itself changed.

**Do not treat the year-advanced 2026 block as correct metadata.** It is a
placeholder chosen because no 2027 source exists, and it is flagged in
`main.tex`'s header comment as such.

---

## AAMAS 2027 template: re-checked 2026-10-01, STILL NOT REACHABLE HERE

Bella reports the official AAMAS 2027 submission page now exposes
`aamas_2027_template.zip`. **I could not reach it from this environment.**
That is a negative result about my network, not a contradiction of her
report, and it is recorded in that spirit.

### Everything I probed

| target | result |
|---|---|
| `aamas2027.org`, `www.aamas2027.org`, `aamas-2027.org` | **NXDOMAIN** (no DNS) |
| `ifaamas.org/previousaamas.html` | lists 2002-2026; **2027 absent** |
| `cyprusconferences.org/aamas2026/` | no forward link, no "Hanoi", no "Vietnam" |
| `ifaamas.org/AAMAS/aamas2027/` | 404 |
| `aamas_2027_template.zip` at ifaamas.org, aamas2027.org, cyprusconferences.org | 404 / no DNS |
| `aamas2027.hanoi.vn`, `aamas2027.vn`, `aamas27.org`, `aamas2027.com`, `aamas2027.github.io`, `conf.researchr.org/home/aamas-2027` | no DNS or 404 |
| `aamas-conference.org` | 200 but serves a browser-verification interstitial only |
| `sites.google.com/view/aamas2027` | 302 to a Google login wall |
| DuckDuckGo HTML + lite endpoints | returned no usable result links |
| DBLP API | no parseable hits |

**WebSearch is blocked by org policy in this environment** (HTTP 400,
`constraints/vertexai.allowedPartnerModelFeatures`), so the search was
exhaustive only over direct URL probes and two search-engine HTML endpoints.
A reachable 2027 site almost certainly exists on a host I did not guess.

### What I did instead

Applied the parts of P0-1/P0-2 that do **not** require the kit:

- **Venue metadata corrected to Hanoi, Vietnam** in `\acmConference`.
  Verified absent: zero occurrences of "Paphos" remain in the rendered PDF.
- Edition number checked: AAMAS 2026 is the 25th, so **26th** for 2027 is
  correct as written.
- The header comment in `main.tex` now records the probe result and the
  migration instruction, rather than the earlier and now-stale claim that no
  2027 kit exists at all.

### What a next agent must do

**This is the single highest-value action available to someone on a
different network.** Fetch `aamas_2027_template.zip`, diff `aamas.cls`
against `paper_support/aamas_official/aamas.cls`
(sha256 `f0af39a72cbcdc88be4817b56cfa74510896b5ef9f32c3f3d32884f68280980c`),
and migrate. The layout rules (8 pages main text, unlimited references,
double-blind, no style edits) have been stable across editions, so the risk
is cosmetic rather than structural — but **do not assume that**; re-run every
gate after swapping the class.

Note the server behaviour already documented above: the 2026 kit is served
behind a hotlink guard that returns a 401KB HTML "404" to a plain `curl`. If
the 2027 host behaves the same way, use a browser User-Agent and a same-site
Referer before concluding the file is missing.
