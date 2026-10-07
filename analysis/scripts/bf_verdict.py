#!/usr/bin/env python3
"""The §20 verdict rule, isolated so it can be positive-controlled.

Inputs are the three PAIRED recovery contrasts bf_control.py already prints.
Output is exactly one of the four labels §20 permits.

HOW TO READ NUMBERS OFF bf_control.py's OUTPUT. That script prints, for each
pair (x, y): "recovered only under x: B, only under y: C". Pass b=B and c=C.
Do NOT pass its printed `delta`: bf_control prints delta as (c-b)/n, i.e.
y-minus-x, whereas this module's internal margin is (b-c)/n, i.e. x-minus-y.
The two have OPPOSITE SIGNS by design; transcribing the delta instead of the
counts silently inverts every verdict.

THRESHOLDS ARE FIXED HERE, BEFORE ANY Bf RESULT IS READ. A "role effect
survives" verdict requires A to still beat Bf by a margin that is BOTH
statistically resolved and a non-trivial share of the frozen A-vs-B recovery
gap that the control exists to test.

That reference gap is DOMAIN-SPECIFIC and must be passed explicitly; there is
no default, because silently reusing one domain's gap for the other moves the
materiality floor by ~19%. Measured from the frozen files, gemma-4, marginal
recovery (each arm over its own first-pass-wrong set):

  REF_GAP_OMNI     = 0.1709   (A 70/316 = 0.2215 vs B 16/316 = 0.0506)
  REF_GAP_SCIBENCH = 0.2034   (A 30/118 = 0.2542 vs B  6/118 = 0.0508)

SENSITIVITY (measured, not asserted; see BF_VERDICT_CONTROLS.md). Varying
SURVIVE_FRAC over 1/5 .. 1/2 leaves the SURVIVES, FEEDBACK-EXPLAINS and
INCONCLUSIVE verdicts unchanged. The BOTH-CONTRIBUTE world is NOT merely
threshold-sensitive at the top of that range -- it crosses THREE labels:
for a world with A-Bf +0.070 and Bf-B +0.064 it reads BOTH at frac<=1/3,
ROLE EFFECT SURVIVES at frac~0.375-0.40, and INCONCLUSIVE at frac>=0.42.
So if the realized result lands in the BOTH region, the report must state the
margin relative to the floor and must NOT present BOTH as threshold-
independent. The other three labels are robust across that range.
"""
ALPHA = 0.05
# A-vs-Bf must retain at least a third of the original A-vs-B gap to count as
# a surviving role effect rather than a residue.
SURVIVE_FRAC = 1.0 / 3.0

# Frozen A-vs-B marginal recovery gaps, gemma-4, measured from the frozen
# files while blind to every Bf result. Pass the one matching the domain.
REF_GAP_OMNI = 0.1709
REF_GAP_SCIBENCH = 0.2034


def verdict(ab, abf, bfb, ab_gap_ref):
    """ab, abf, bfb: dicts {b, c, n, p} for A-vs-B, A-vs-Bf, Bf-vs-B.
    b = recovered only under the FIRST arm, c = only under the SECOND.
    ab_gap_ref: the frozen marginal A-vs-B recovery gap for THIS domain
    (REF_GAP_OMNI or REF_GAP_SCIBENCH). Required -- no default.

    `ab` is the frozen A-vs-B contrast. It is the premise of the whole
    control: if A did not actually beat B on recovery in the frozen data,
    there is no gap for feedback delivery to explain and no verdict here is
    meaningful. It is checked rather than assumed."""
    need = SURVIVE_FRAC * ab_gap_ref
    ab_margin = (ab["b"] - ab["c"]) / ab["n"] if ab["n"] else 0.0
    if not (ab["p"] < ALPHA and ab_margin > 0):
        return ("INCONCLUSIVE",
                "PREMISE FAILS: the frozen A-vs-B recovery contrast does not "
                "favour A at alpha={} (A-B {:+.3f}, p={:.3g}). The control "
                "tests an effect that is not present in the frozen data; no "
                "Bf verdict is interpretable.".format(ALPHA, ab_margin, ab["p"]))
    a_over_bf = (abf["b"] - abf["c"]) / abf["n"] if abf["n"] else 0.0
    bf_over_b = (bfb["b"] - bfb["c"]) / bfb["n"] if bfb["n"] else 0.0
    a_wins  = abf["p"] < ALPHA and a_over_bf >= need
    bf_wins = bfb["p"] < ALPHA and bf_over_b >= need
    a_null  = abf["p"] >= ALPHA
    # Bf OVERTAKING A is a real possible world: delivering feedback might not
    # merely close the A-vs-B gap but reverse it. It is not "inconclusive",
    # and it must never be reported with a materiality-floor reason, which
    # would be false -- the effect is large, just signed the other way.
    bf_beats_a = abf["p"] < ALPHA and a_over_bf <= -need

    if bf_beats_a:
        return ("FEEDBACK DELIVERY EXPLAINS ORIGINAL GAP",
                "feedback delivery OVERSHOOTS: Bf beats A by {:+.3f} "
                "(p={:.3g}){}. The A-vs-B recovery gap cannot be a role "
                "effect. FLAG FOR REVIEW: this reverses the original "
                "direction and is not a case the paper anticipates.".format(
                    -a_over_bf, abf["p"],
                    " and Bf beats B by {:+.3f}".format(bf_over_b)
                    if bf_wins else ""))

    if a_wins and not bf_wins:
        return ("ROLE EFFECT SURVIVES FEEDBACK MATCHING",
                "A still beats Bf by {:+.3f} (p={:.3g}), and Bf is not "
                "distinguishable from B".format(a_over_bf, abf["p"]))
    if bf_wins and a_null:
        return ("FEEDBACK DELIVERY EXPLAINS ORIGINAL GAP",
                "Bf beats B by {:+.3f} (p={:.3g}) while A vs Bf is unresolved "
                "(p={:.3g})".format(bf_over_b, bfb["p"], abf["p"]))
    if a_wins and bf_wins:
        return ("BOTH CONTRIBUTE",
                "Bf beats B by {:+.3f} AND A still beats Bf by {:+.3f}".format(
                    bf_over_b, a_over_bf))
    if a_null and bfb["p"] >= ALPHA:
        return ("INCONCLUSIVE",
                "neither A vs Bf (p={:.3g}) nor Bf vs B (p={:.3g}) is "
                "resolved".format(abf["p"], bfb["p"]))
    return ("INCONCLUSIVE",
            "a contrast is significant but below the {:.3f} materiality "
            "floor (A-Bf {:+.3f}, Bf-B {:+.3f})".format(need, a_over_bf, bf_over_b))


if __name__ == "__main__":
    import itertools
    # Four worlds with KNOWN right answers. n and p chosen to be realistic.
    worlds = {
      "role effect survives": (
         dict(b=37,c=3,n=237,p=1.9e-8),   # A vs B  (frozen, unchanged)
         dict(b=30,c=5,n=230,p=1e-5),     # A vs Bf (A still far ahead)
         dict(b=6, c=4, n=235,p=0.75)),   # Bf vs B (Bf ~ B)
      "feedback explains gap": (
         dict(b=37,c=3,n=237,p=1.9e-8),
         dict(b=8, c=7, n=230,p=1.0),     # A vs Bf unresolved
         dict(b=28,c=3,n=235,p=1e-5)),    # Bf vs B: Bf jumped to A
      "both contribute": (
         dict(b=37,c=3,n=237,p=1.9e-8),
         dict(b=20,c=4,n=230,p=1e-3),     # A still ahead of Bf
         dict(b=18,c=3,n=235,p=2e-3)),    # and Bf ahead of B
      "inconclusive": (
         dict(b=37,c=3,n=237,p=1.9e-8),
         dict(b=9, c=7, n=60, p=0.80),    # small n, nothing resolved
         dict(b=8, c=6, n=60, p=0.79)),
    }
    worlds["premise fails (A never beat B)"] = (
         dict(b=5,c=6,n=237,p=0.90),      # frozen A-vs-B: no effect to explain
         dict(b=30,c=5,n=230,p=1e-5),
         dict(b=6, c=4, n=235,p=0.75))
    for name,(ab,abf,bfb) in worlds.items():
        v,why = verdict(ab,abf,bfb,REF_GAP_OMNI)
        print("{:<34} -> {:<42} ({})".format(name, v, why))
