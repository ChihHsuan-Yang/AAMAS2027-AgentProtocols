# Release procedure — DO NOT RUN BEFORE ACCEPTANCE

This artifact is **complete and ready to upload**. It has deliberately **not**
been pushed anywhere. Read the anonymity reasoning before running anything
below.

Status: **HELD. No HuggingFace repo has been created — not public, not private,
not gated.**

---

## 1. Why it is held

AAMAS reviewing is **double-blind**. Two rules from the official submission
instructions (verified in `paper_support/aamas_official/PROVENANCE.md`) govern
this artifact:

> "AAMAS reviewing is double-blind."
>
> "Papers must not include pointers to any supplementary material that is not
> provided as part of the submission."

A public HuggingFace dataset, created now, under an identifiable account, whose
numbers match the paper exactly, is a **deanonymization path**. It does not
require the paper to link to it. A reviewer who searches a distinctive
figure — `24/2791`, `0.222 → 0.051`, "11,600 trajectories", the F13 chars/sec
table — lands on the dataset card, and the card's owner is the author. The
paper does not have to point at the artifact for the artifact to point back at
the paper.

The upload is also **one command**, and everything it needs is already built.
There is no schedule pressure that justifies taking the risk early.

### On a private or gated repo — my recommendation, your decision

You asked me to flag this rather than act on it. **My recommendation is to
create nothing at all until acceptance.** The reasoning:

- A **private** repo is genuinely invisible to reviewers, so the
  deanonymization risk is near zero *while it stays private*. The real risk is
  operational: a private repo that must later be flipped public is exactly the
  kind of state that gets flipped early by accident, and the failure is
  irreversible — you cannot un-disclose. Holding zero repos has no such failure
  mode.
- A **gated** repo is *not* safe. Gated repos are publicly listed and
  publicly searchable: the card, title, and description are visible before any
  access request. That is precisely the searchable surface that deanonymizes.
  **Do not use gating as a substitute for privacy.**
- A private repo buys essentially nothing the local directory does not already
  provide. The artifact is built, validated, checksummed, and reproducible on
  disk. Uploading early only moves the bytes; it does not de-risk the release.
- One narrow exception, if you want it: AAMAS permits supplementary material as
  a **single zip ≤ 25 MB**, submitted with the paper and under the same
  anonymity policy. This artifact is ~39 MB, so it does not fit as-is. A
  reduced zip (drop `role_messages.parquet`, keep trajectories + evaluator
  calls + manifests + docs ≈ 2 MB) would fit and is the *anonymity-safe* way to
  give reviewers the data, because it travels inside the submission rather than
  sitting on a public host. See §5.

If you decide a private repo is worth it anyway, the commands in §3 work
unchanged with `--private`; just do not remove that flag until §2 is satisfied.

---

## 2. Preconditions — all must be true before §3

- [ ] Paper **accepted** (not "probably", not "conditionally pending
      camera-ready"). A rejected or withdrawn paper may be resubmitted to
      another double-blind venue, and a public artifact deanonymizes that
      submission too.
- [ ] Decision is final and you are not resubmitting this work elsewhere blind.
- [ ] Camera-ready author list settled — the card names the same authors.
- [ ] Co-authors have agreed to publish the data.
- [ ] Any institutional data-release or export review completed.
- [ ] `python3 scripts/validate_artifact.py` passes (181/181).
- [ ] `python3 scripts/secret_scan.py` exits CLEAN.
- [ ] `shasum -c CHECKSUMS.txt` passes.

---

## 3. The upload — one command after the card edits in §4

```bash
# 0. verify, every time, immediately before upload
cd hf_artifact
python3 scripts/validate_artifact.py            # expect: ALL 181 CHECKS PASSED
python3 scripts/secret_scan.py                  # expect: CLEAN
shasum -c CHECKSUMS.txt                         # expect: all OK

# 1. authenticate (interactive; never paste a token into a file in this repo)
huggingface-cli login

# 2. create the repo — PUBLIC, and only after §2 and §4 are done
huggingface-cli repo create <ORG>/<DATASET-NAME> --type dataset

# 3. upload the whole directory, excluding this file
huggingface-cli upload <ORG>/<DATASET-NAME> . . \
    --repo-type dataset \
    --exclude "RELEASE_PROCEDURE.md" "**/__pycache__/**" ".DS_Store"
```

`RELEASE_PROCEDURE.md` is excluded because it is an internal process document
that discusses the review timeline; it is not part of the published dataset.

Then, in the HF web UI: confirm the dataset viewer renders all three configs,
and confirm the license shows `apache-2.0`.

---

## 4. What to change in the dataset card at release

Edit `README.md` before uploading:

1. **Delete the anonymization banner** — the HTML comment block and the line
   "**Anonymous during review.** Author, institution, and code repository are
   withheld. They will be added on acceptance."
2. **Add authors and affiliations** to the YAML front matter and the card body.
3. **Add the citation block** — the accepted AAMAS 2027 reference, with DOI once
   the ACM DL assigns one:
   ```bibtex
   @inproceedings{<key>,
     title     = {<title>},
     author    = {<authors>},
     booktitle = {Proceedings of the 26th International Conference on
                  Autonomous Agents and Multiagent Systems (AAMAS 2027)},
     year      = {2027},
   }
   ```
4. **Add the code repository link** (withheld during review).
5. **Add funding and acknowledgements** — omitted during review per the
   anonymity rules.
6. **Add a "Paper" section** linking to the camera-ready PDF / ACM DL page.
7. **Keep unchanged**: the F13 and F18 defect disclosures, the adjudication
   blinding-leak note, the scope and limitations section, and the licensing
   section. These are the substance of the card. Do not soften them for
   publication — a consumer who does not read them will draw wrong conclusions,
   which is the whole reason they are there.

Also update `VERSION`: set `release_status` from `HELD_PENDING_ACCEPTANCE` to
`PUBLIC`, and record the release date and the HF repo id.

---

## 5. Optional: anonymous supplementary zip for the submission itself

If you want reviewers to have the data *during* review, this is the safe route —
it travels inside the submission and is covered by the same anonymity policy,
so nothing is publicly searchable.

AAMAS allows a single zip, **≤ 25 MB**. The full artifact is ~39 MB, so drop the
message text:

```bash
cd hf_artifact
zip -r ../supplementary.zip . \
    -x "data/role_messages.parquet" "RELEASE_PROCEDURE.md" \
       "**/__pycache__/*" ".DS_Store"
ls -lh ../supplementary.zip          # confirm <= 25MB
```

Before attaching it, confirm the zip is anonymous:

```bash
unzip -l ../supplementary.zip                  # no unexpected files
python3 scripts/secret_scan.py                 # run on the directory first
```

Note in the paper that the supplement omits `role_messages.parquet` for size,
and that the collapse, duplication, and frozen-answer analyses need it — **do
not** point to an external host for the omitted file, as that is exactly the
"pointer to supplementary material not provided as part of the submission" the
instructions forbid.

---

## 6. If the paper is rejected

**Do not publish.** Return to step 1: the work will most likely go to another
double-blind venue, and the same reasoning applies unchanged. The artifact
stays on disk, still valid, still reproducible from the frozen snapshot.

If the snapshot is re-frozen in the meantime, re-run
`scripts/build_artifact.py` (it will refuse to build if the recorded hashes no
longer match) and regenerate `CHECKSUMS.txt` and `VERSION`.
