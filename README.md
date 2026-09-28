# AAMAS 2027 — Agent Protocols (working title)

**Target:** AAMAS 2027. Abstract **2026-10-01**, full paper **2026-10-08**, both AoE.
8 pages main text + unlimited references. Double-blind. LaTeX mandatory.
**Likely area:** GAAI (Generative and Agentic AI). Not LEARN — no learning
contribution is currently justified (see CLAIM-STATUS.md).

**This is NOT the IEEE BigData SciAgentTrace dataset paper.** See `OVERLAP_AUDIT.md`.

## Start here

| file | what it is |
|---|---|
| `notes/CLAIM-STATUS.md` | **read first** — what survives, what does not, and why |
| `notes/FINDING-0*.md` | the six findings, each with its own caveats and corrections |
| `notes/EXPERIMENT_PROPOSALS.md` | costed proposals; **nothing has been run** |
| `OVERLAP_AUDIT.md` | BigData separation, incl. ideas self-rejected |
| `AI_ASSISTANCE_LOG.md` | AAMAS-mandated disclosure, incl. the AI's own corrections |

## Findings at a glance

- **F01** confidence-argmax speaker selection ≈ random (replicated, 2 actors)
- **F02** protocol ladder is ~50% oracle-feedback artifact; single-agent is ~100%
- **F03** peer approval signal — **downgraded**, see its own CORRECTION section
- **F04** effect-size reality check + held-out confirmation; P2 prediction failed
- **F05** PER role separation instructed but not obeyed (+ a Simpson's reversal)
- **F06** which organization wins flips sign by actor model

## Data

Read-only from the public release cached at
`../IEEE-BigData-SciAgentTrace/analysis/hf_cache/release` (68,892 trajectories,
1.89M messages, 439 MB). Nothing in this project writes to the BigData or SC26
projects.

## Reproduce

```bash
cd analysis/scripts
python3 d1_oracle_decomposition.py      # oracle vs structure decomposition
python3 d2_extract_polls.py             # build the confidence-poll panel
python3 d3_grader.py                    # grader + CALIBRATION (run before d4)
python3 d4_counterfactual_selection.py
python3 d5_selection_vs_random.py       # the null
python3 d6_confidence_decomposition.py  # the mechanism
python3 d7_within_turn_signal.py        # feature sweep
python3 d8_budget_matched.py
python3 d9_blind_approval.py
python3 d10_peer_within_item.py         # like-for-like correction to d9
python3 d11_holdout_confirmation.py     # held-out actor model
python3 d12_role_compliance.py
```

`d2` and `d12` scan all 10 message shards and take a few minutes; the rest are fast.

## Standing rules for this project

1. **Calibrate every grader against recorded labels before using it** (`d3`).
2. **Hold out `gemma_4_31b` / jeebench / mascqa** for confirmation; discovery ran
   on labbench + gpt_oss_120b.
3. **Stratify before pooling** — two Simpson's reversals found so far (F05, F06).
4. **No HPC campaign without Bella's sign-off** (her instruction §21/§33).
5. Record corrections in place rather than deleting the wrong version.
