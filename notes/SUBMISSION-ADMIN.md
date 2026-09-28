# Submission administration — AAMAS 2027 (updated 2026-09-28)

## Deadlines (as given by Bella; I could not independently verify — see below)
- **Abstract: 2026-10-01 AoE** — 3 days out
- **Full paper: 2026-10-08 AoE**
- 8 pages main + unlimited references · double-blind · LaTeX mandatory

## What I could NOT verify, and why — do not treat any of this as checked

| item | attempted | result |
|---|---|---|
| OpenReview profiles for each author | `api.openreview.net` and `api2.openreview.net`, profile + notes endpoints, 4 author IDs | **HTTP 403 on every call.** A 403 is the API refusing me. It is **not** evidence that a profile is missing or present. |
| AAMAS 2027 CFP / submission interface | `aamas2027.org`, `www.aamas2027.org`, `aamas2027.com` | **connection failed (000)** on all three |
| Reciprocal-reviewer requirement | needs the CFP | **unverified** |
| Author-list lock at abstract deadline | needs the submission interface | **unverified — I am explicitly NOT inferring this**, per your instruction |

**Everything in this section requires a human with a browser.** I am reporting
access failures as access failures.

## Intended authors — needs your confirmation

Derived from the two group arXiv papers on this corpus (both verified by
fetching their abs pages), not from any project decision record:

| author | source | OpenReview profile? | affiliation current? |
|---|---|---|---|
| Chih-Hsuan Yang | 2609.27822, 2608.14927 | ☐ unverified | ☐ |
| Jingyan Jiang | 2609.27822, 2608.14927 | ☐ unverified | ☐ |
| Huihuo Zheng | 2609.27822, 2608.14927 | ☐ unverified | ☐ |
| Rajeev Thakur | 2609.27822 | ☐ unverified | ☐ |
| Cheng-Hau Yang | 2608.14927 | ☐ unverified | ☐ |
| Vikram Vasudevan | 2608.14927 | ☐ unverified | ☐ |
| Venkatram Vishwanath | 2608.14927 | ☐ unverified | ☐ |

The BigData project's MASTER_TODO records authors as **"interim ... Final list
on hold"** (decision 0.4), so the list is genuinely unsettled.

## Actions for you, today

1. **Log in to openreview.net** and confirm a profile with a current affiliation
   exists for every intended author. New profiles can face multi-day moderation;
   with the abstract due Oct 1 that is a hard blocker, not a formality.
2. **Settle the author list** before Oct 1 if the interface locks it (I could not
   verify whether it does — check the submission form itself).
3. **Check the CFP** for a reciprocal-reviewing commitment; several recent AAMAS
   cycles have required submitting authors to serve as reviewers.

## Double-blind hazards specific to us
- Two public arXiv papers by this group on this corpus (2609.27822, 2608.14927).
  Cite in third person only; never "our prior work".
- Do not name the HF org `AgentsSci` or the GitHub account in submitted text.
- The LaTeX template is not yet set up in `paper/`.
