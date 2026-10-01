# Release procedure — how to flip this dataset public after acceptance

**Current status: PUBLISHED, PRIVATE — now at v1.1.0 (two domains).**
`AgentsSci/AAMAS2027-Roles` — private, verified three ways before and after
every upload: the authenticated API reports `private=True`, an anonymous fetch
of a raw file returns **401**, and a positive control on a known-public dataset
returns **200 in the same run** (so a 401 cannot be a network artifact).

Nothing here should be run before the paper is accepted.

---

## Why it is held back

AAMAS 2027 reviewing is **double-blind**, and the hosting organization
`AgentsSci` **identifies the research group**. That alone deanonymizes the
submission to anyone who finds the repository.

The risk does not require a pointer from the paper. The dataset reproduces the
paper's tables exactly — 11,600 trajectories, the same three actor models, the
same 0.222 → 0.051 recovery drop. A reviewer or competitor who encounters a
public dataset whose numbers match the submission under review has
deanonymized it, whether or not the PDF ever links here.

So two rules hold for the whole review period:

1. **The repository stays private.**
2. **The HF URL never appears in the anonymous PDF** — not in the abstract, not
   in a data-availability statement, not in a footnote, not in the
   supplementary. It belongs only in the private GitHub handoff docs.

An accidental public dataset matching the paper's numbers is a deanonymization
path that **cannot be undone**: it is indexed, mirrored and cached within
minutes, and making it private again does not retract it.

### A second, independent reason this repo cannot be flipped as-is

`raw/` ships the frozen traces as **exact bytes** so their sha256 verifies
against `MANIFEST.json`. Those bytes include upstream HTTP error bodies, and
**14 rows name the operating institution** — a CDN block page carrying the
institution's name in its `<title>`, and a service traceback carrying an
absolute path under a service account's home directory. (The literal strings
are deliberately not reproduced in this file; `scripts/preflight_public.py`
locates them.) The derived parquet layer was sanitized; the raw layer
deliberately was not, because redacting it would break the hash chain.

This is harmless while the repo is private and disqualifying the moment it is
not. It is enforced by a gate, not by memory — see step 1.

---

## The flip, after acceptance

### 1. Clear the anonymity gate — this is a hard blocker

```bash
python3 scripts/preflight_public.py          # must exit 0
```

It currently **FAILS**, listing **15** matching rows. Do not flip public on a
FAIL, and do not delete the check to get past it.

**Read the 15 before acting — they are not all the same thing.**

- **14 are genuine** (v1.0.0 Omni traces): an upstream HTTP error body in the
  `error` field naming the operating institution. These are the reason this
  repository cannot be public.
- **1 is a FALSE POSITIVE** (v1.1.0, `scibench_AB.jsonl` line 1482, row uid
  `scibench:matter:40.3`, `messages` field): a **navigational star**, named in
  a physics problem about photon flux, whose name is also an HPC hostname —
  the same collision class as "crux". **SciBench introduces no new genuine
  instance.** Run the gate to see the literal; it is deliberately not written
  in this file, because a document that prints a hostname next to the phrase
  "operating institution" is a worse disclosure than the trace row it
  describes.

It is deliberately **not** allowlisted. An allowlist keyed on the word would
also exempt a real hostname, and this hit sits in `messages` rather than
`error`, so `--fix` correctly refuses to touch it. When clearing the gate for
release, handle this one **by hand** and record the decision.

To clear the genuine 14:

```bash
python3 scripts/preflight_public.py --fix    # redacts ONLY the `error` field
python3 scripts/emit_release_metadata.py     # re-stamp hashes after redaction
python3 scripts/preflight_public.py          # re-verify: must now PASS
```

`--fix` replaces the captured upstream response body with a marker and leaves
every other byte untouched (the failure *class* is preserved). It then rewrites
each trace's manifest (`raw/MANIFEST.json`, `raw/MANIFEST_SCIBENCH.json`) for
the new hashes.

**`--fix` will refuse while the SciBench false positive is present**, because
that hit is outside the `error` field. It refuses **having written nothing** —
v1.1.0 made the redaction two-phase (plan every trace, then write only if all
are safe). The previous single-phase version would rewrite earlier traces and
*then* abort, leaving manifests that no longer described the bytes on disk. It
could not fire while every known hit was in an `error` field; the SciBench row
made it reachable, and it was fixed rather than worked around. **The pre-redaction hashes stay in
`VERSION.release_history`**, so anything published against v1.0.0 remains
checkable, and the card must then say the raw traces are byte-exact *except for
a documented redaction of 14 `error` fields*.

Bump to **1.0.1** when you do this: the released bytes changed.

### 2. Re-run the full verification chain

```bash
python3 scripts/secret_scan.py               # must print CLEAN (positive control must fire)
python3 scripts/validate_artifact.py         # must print 181/181
shasum -c CHECKSUMS.txt                      # every file OK
```

`secret_scan.py` plants a known secret and a known leak and **exits non-zero if
its own patterns fail to catch them** — a clean run therefore means the scanner
works and found nothing, not merely that it found nothing.

### 3. Flip the repository

```bash
hf repo settings AgentsSci/AAMAS2027-Roles --repo-type=dataset --private=false
```

Then confirm anonymously, not from an authenticated session:

```bash
curl -s -o /dev/null -w '%{http_code}\n' \
  https://huggingface.co/api/datasets/AgentsSci/AAMAS2027-Roles   # expect 200
```

### 4. What to change in the dataset card

Only after the flip:

- **Remove** the `ANONYMIZED FOR DOUBLE-BLIND REVIEW` HTML comment at the top.
- **Remove** "Anonymous during review. Author, institution, and code repository
  are withheld."
- **Add** author list, affiliation, funding/grant acknowledgement, and a
  **BibTeX citation block** for the accepted paper.
- **Add** the code repository link and the paper DOI / proceedings link.
- **Un-redact** `config/run_config.json`: `backend.base_url` and
  `corpus.problems_source` are currently `<REDACTED …>` because they name the
  institution. Restore them — they are genuinely useful for reproduction. Do
  **not** restore any credential or auth-helper path; `adjudication/adjudicate.py`
  stays excluded.
- **Update** `VERSION.release_status` from
  `PUBLISHED_PRIVATE_PENDING_ACCEPTANCE` to `PUBLIC`, and clear
  `public_release_gate`.
- **Keep everything else exactly as it is.** In particular keep the entire
  *Known instrumentation defects* section, the superseded-analyses list, and
  the licensing section. Those are not review-period hedges; they are what makes
  the data usable.

### 5. Re-verify after the flip

Fresh-download in a clean directory as an anonymous user and re-check hashes
against `CHECKSUMS.txt`, including one large trace. A CLI exit 0 is not
evidence that the bytes on the hub are the bytes you built.

---

## If it is published publicly by mistake, before acceptance

1. Make it private immediately — `--private=true`.
2. **Assume it was seen.** Do not assume the window was too short.
3. Tell the authors at once so they can decide whether to notify the PC. A
   self-reported anonymity break is recoverable; a discovered one is usually
   not.
4. Do not delete the repo and re-create it under a new name as a cover — the
   deletion does not retract mirrors and the new repo is trivially linked.

## The second domain — DONE (v1.1.0)

The SciBench campaign landed **additively** as v1.1.0. Every v1.0.0 file keeps
its bytes and sha256; both `scripts/build_scibench.py` and
`scripts/emit_release_metadata.py` **assert** this and refuse to proceed
otherwise. SciBench is **MIT** — a different licence from the Apache-2.0
material — and has its own `LICENSES/registry.json` entry plus the verbatim
`LICENSES/MIT-SciBench.txt`, rather than being absorbed. See
`config/SECOND_DOMAIN_SLOT.md` for promise-by-promise outcomes.

### If a THIRD domain is ever added, these are the two things that bit us

1. **The public-release gate does not scan what it is not told about.**
   `TRACES` in `scripts/preflight_public.py` is an explicit tuple. A trace
   absent from it is **unchecked**, not clean — and it would have reported PASS
   while saying nothing. The gate now prints which traces it scanned, and
   `emit_release_metadata.py` refuses if `raw/` holds a `.jsonl` it has no
   provenance entry for. Add the new trace to **both**.
2. **Benchmark-specific vocabulary trips the deanonymization patterns.** HPC
   hostnames collide with ordinary nouns and proper names: `crux` (already
   known), and now a **star name** in a physics corpus. Expect a chemistry or
   astronomy corpus to produce more. Triage each hit by reading its context;
   never allowlist the bare word — and when you write the triage up, do not
   reproduce the literal in a file the scanner also reads.
