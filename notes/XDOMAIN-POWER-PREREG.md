# SciBench cross-domain replication — interpretation rules, fixed BEFORE
# the recovery numbers are looked at

**2026-09-30, written while the run is at 761/2,296 and no recovery
contrast has been computed. This exists so the reading of the result is not
chosen after seeing it.**

## The power situation, measured not assumed

SciBench is much easier than Omni-MATH for these actors. First-pass accuracy
on the rows landed so far is 0.822-0.847 against 0.710-0.802 on Omni-MATH, so
the first-pass-wrong denominator — which IS the recovery denominator —
shrinks by roughly a factor of three:

| | Omni-MATH fpw/cell | SciBench projected fpw/cell |
|---|---|---|
| gemma-4 | 316 | ~95 |
| gpt-oss | 463 | ~95 |

Simulated power at n=95 per cell, two-sided alpha=0.05:

| effect | power @95 | power @316 |
|---|---|---|
| gemma-sized (0.222 -> 0.051) | **0.95** | 1.00 |
| gpt-oss-sized (0.324 -> 0.247) | **0.21** | 0.57 |
| half a gemma effect (0.222 -> 0.136) | 0.34 | 0.81 |

## The rules, fixed now

1. **A gemma-4 null on SciBench IS informative.** Power 0.95 against the
   effect we found in Omni-MATH. If it comes back null, that is a real
   boundary condition and we report it as one.

2. **A gpt-oss null on SciBench is NOT informative.** Power 0.21. It must be
   reported as "cannot detect an effect of the size we observed in
   Omni-MATH", never as a non-replication, and never counted as one of two
   actors failing to replicate.

3. **We do not pool the two actors** to manufacture power. The Omni-MATH
   effects differ by a factor of two between them; pooling would average a
   detectable effect with an undetectable one.

4. **No P1a or clause-specific fidelity metric crosses domains.** The Arm A
   contract was adapted (option b), so scoring against Omni-MATH's clauses
   would score agents against instructions they never received.

5. **Integration decision, per Bella's 35:** SciBench goes in the main paper
   only if it gives a clear independent-domain replication or an
   interpretable boundary condition. A mixed result — gemma replicates,
   gpt-oss underpowered — is **supplement or rebuttal material**, not a
   second headline. It must not weaken a clear 8-page story to say "two
   benchmarks".

## Why this is written down in advance

This project has already been bitten twice by underpowered nulls read as
evidence of absence: the Llama P4 DiDs (MDE 0.069/0.075 against plausible
effects <=0.040) and the Llama "floor effect" that Arm C then refuted. The
difference between an informative null and an underpowered one is not
visible in the number itself, and it is very easy to decide afterwards which
kind you are looking at.

## Worker's independent finding, recorded
The upstream released corpus already ran this exact slice with both actors
(8 runs, `target_complete`): PER accuracy 0.913 gemma / 0.875 gpt-oss. That
corroborates the easiness from a completely separate source, and it was
found by the worker, not assumed by me.
