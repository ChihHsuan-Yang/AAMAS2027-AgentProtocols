# Power analysis — paired arm comparison

**Correction to my own first output:** I printed "n=200 gives >0.9 power for
moderate effects" directly beneath a table showing **0.28**. The table is right,
the sentence was wrong. Corrected below.

## Design

Arms run on the SAME problems, so the test is paired (McNemar on discordant
items). Two parameters, both estimated from observed PER-vs-broadcast data on
omnimath2:
- discordance rate: gemma3 0.203, gpt_oss 0.149
- net asymmetry among discordant: gemma3 0.680, gpt_oss 0.387

## Power, two-sided α=0.05, 4,000 sims

| effect | n=150 | n=200 | n=300 | n=400 | n=600 |
|---|---|---|---|---|---|
| large (gemma3-like, disc .20, asym .40) | 0.61 | 0.73 | 0.88 | **0.96** | 0.99 |
| moderate (gpt_oss-like, disc .15, asym .25) | 0.23 | 0.28 | 0.40 | 0.49 | 0.65 |
| small (disc .15, asym .15) | 0.11 | 0.13 | 0.17 | 0.22 | 0.30 |
| very small (disc .15, asym .10) | 0.08 | 0.09 | 0.10 | 0.12 | 0.15 |

## What this means for sizing

- **n=200/cell is adequate ONLY for large effects** (0.73), and underpowered for
  everything else. Bella's suggested pilot size is a *screen*, not a test.
- **n=400/cell** reaches 0.96 for large effects but still only **0.49** for
  moderate ones.
- Detecting a *moderate* arm difference at 0.8 power needs **n ≈ 800+/cell**.

## Consequence

Do not promise to detect moderate effects at pilot scale. The honest framing:
- **Pilot (n=200)** answers "is there a large arm effect?" and returns
  fidelity-metric estimates with tight CIs (fidelity is measured per *message*,
  so n=200 trajectories still yields thousands of messages — the *measurement*
  half of the paper is well-powered even when the *outcome* half is not).
- **Confirmatory (n=400-600)** for the outcome comparison.
- A null at n=200 must be reported as "no large effect detected", never as
  "no effect".

**This asymmetry is itself a design insight:** the role-realization measurements
(Claim 1 and 2 on the ladder) are cheap and well-powered; the outcome claims
(Claim 3 and 4) are expensive. Prioritise accordingly.
