#!/usr/bin/env python3
"""bf_drift -- S.16 endpoint-drift bridge.

Question it answers, and the ONLY one: has the live endpoint drifted since the
frozen campaign, enough to change how a fresh Bf row should be read against
frozen A/B rows?

Design: a FRESH Arm A run (n=400) against the FROZEN Arm A rows on the SAME
problems. Both arms are A -- same prompts, same models, same budget -- so any
systematic difference is endpoint/serving drift. The bridge is NEVER pooled
into any results table (directive S.16); its sole output is a verdict.

POWER NOTE, fixed before the run and the reason the verdict is not driven by
raw rate deltas: first-pass and final accuracy are measured on all 400 paired
problems and are well powered. The recovery rate is measured only on the
first-pass-wrong subset (n ~ 75-90), where the standard error of a difference
of two such rates is ~0.07. A +-0.05 threshold on recovery is INSIDE noise and
will fire on a null. Recovery is therefore reported with a confidence interval
and can only drive the verdict when that interval excludes zero.
"""
import argparse, json, sys
from math import comb, sqrt


def load(paths):
    rows = []
    for p in paths:
        with open(p) as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except Exception:
                        pass
    return rows


def first_pass(r):
    eh = r.get("evaluator_history") or []
    if not eh:
        return None
    c = eh[0].get("correctness")
    return None if c is None else int(c)


def final_correct(r):
    return 1 if r.get("correct") == 1 else 0


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def wilson(k, n, z=1.959964):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def newcombe(k1, n1, k2, n2):
    """95% CI on p2 - p1 (independent proportions, Newcombe method 10)."""
    if n1 == 0 or n2 == 0:
        return (-1.0, 1.0)
    l1, u1 = wilson(k1, n1)
    l2, u2 = wilson(k2, n2)
    d = k2 / n2 - k1 / n1
    lo = d - sqrt((k2 / n2 - l2) ** 2 + (u1 - k1 / n1) ** 2)
    hi = d + sqrt((u2 - k2 / n2) ** 2 + (k1 / n1 - l1) ** 2)
    return (lo, hi)


def paired_ci(b, c, n, z=1.959964):
    """95% CI on the paired difference (c - b)/n, by the Wald method on
    discordant pairs. b = frozen-only successes, c = bridge-only successes."""
    if n == 0:
        return (0.0, 0.0)
    d = (c - b) / n
    se = sqrt(max(b + c - (c - b) ** 2 / n, 0.0)) / n
    return (d - z * se, d + z * se)


# Decision thresholds, fixed here BEFORE the bridge is run.
# MATERIAL_DELTA is referenced to the effect the bridge exists to protect:
# the frozen Omni A-vs-B recovery gap is 0.2215 - 0.0506 = 0.171. Drift that
# could move a rate by >= 0.05 is a meaningful fraction of that gap; drift
# bounded below 0.05 cannot overturn it.
MATERIAL_DELTA = 0.05
ALPHA = 0.05


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frozen", nargs="+", required=True)
    ap.add_argument("--bridge", nargs="+", required=True)
    ap.add_argument("--actor", default="gemma-4-31B-it")
    a = ap.parse_args()

    F, Bg = {}, {}
    for r in load(a.frozen):
        if r.get("arm") == "A" and str(r.get("actor_model", "")).endswith(a.actor):
            F[r["problem_uid"]] = r
    for r in load(a.bridge):
        if r.get("arm") == "A" and str(r.get("actor_model", "")).endswith(a.actor):
            if r.get("stopping_condition") == "model_unavailable":
                continue
            Bg[r["problem_uid"]] = r
    common = sorted(set(F) & set(Bg))
    if not common:
        sys.exit("no common problems: wrong files?")
    n = len(common)

    print("=" * 76)
    print("S.16 endpoint-drift bridge   Arm A frozen vs Arm A re-run, same problems")
    print("=" * 76)
    print("frozen A rows {}   bridge A rows {}   paired problems {}".format(
        len(F), len(Bg), n))
    print("NOT POOLED into any results table. Diagnostic only.\n")

    stats = {}
    for lab, D in (("frozen", F), ("bridge", Bg)):
        fp = sum(1 for u in common if first_pass(D[u]) == 1)
        fc = sum(final_correct(D[u]) for u in common)
        w = [D[u] for u in common if first_pass(D[u]) == 0]
        rec = sum(final_correct(r) for r in w)
        stats[lab] = dict(fp=fp, fc=fc, rec=rec, nw=len(w))
        print("  {:<7} first-pass {:>4}/{} = {:.4f}   final {:>4}/{} = {:.4f}   "
              "recovery {:>3}/{:<4} = {:.4f}".format(
                  lab, fp, n, fp / n, fc, n, fc / n,
                  rec, len(w), rec / max(len(w), 1)))

    print("\n  PAIRED on the same problems -- the powered comparison (n = {}):".format(n))
    verdict_sig = {}
    for name, fn in (("first-pass", lambda r: 1 if first_pass(r) == 1 else 0),
                     ("final", final_correct)):
        b = sum(1 for u in common if fn(F[u]) == 1 and fn(Bg[u]) == 0)
        c = sum(1 for u in common if fn(F[u]) == 0 and fn(Bg[u]) == 1)
        p = mcnemar_exact(b, c)
        lo, hi = paired_ci(b, c, n)
        verdict_sig[name] = (p, (c - b) / n, lo, hi)
        print("    {:<11} frozen-only {:>3}  bridge-only {:>3}  delta {:+.4f}  "
              "95% CI [{:+.4f}, {:+.4f}]  p = {:.3g}".format(
                  name, b, c, (c - b) / n, lo, hi, p))

    f, g = stats["frozen"], stats["bridge"]
    rlo, rhi = newcombe(f["rec"], f["nw"], g["rec"], g["nw"])
    rd = g["rec"] / max(g["nw"], 1) - f["rec"] / max(f["nw"], 1)
    print("\n  UNPAIRED, UNDERPOWERED -- recovery rate (denominators {} vs {}):".format(
        f["nw"], g["nw"]))
    print("    recovery   delta {:+.4f}  95% CI [{:+.4f}, {:+.4f}]  "
          "{}".format(rd, rlo, rhi,
                      "excludes 0" if (rlo > 0 or rhi < 0) else "includes 0"))
    print("    (the first-pass-wrong subset is small by construction; a delta "
          "of\n     this size is not evidence of drift unless the CI excludes zero)")

    # ---- verdict -------------------------------------------------------
    fp_p, fp_d, fp_lo, fp_hi = verdict_sig["first-pass"]
    fi_p, fi_d, fi_lo, fi_hi = verdict_sig["final"]
    sig = [(nm, s) for nm, s in verdict_sig.items() if s[0] < ALPHA]
    big = [(nm, s) for nm, s in sig if abs(s[1]) >= MATERIAL_DELTA]
    rec_sig = (rlo > 0 or rhi < 0)
    rec_big = rec_sig and abs(rd) >= MATERIAL_DELTA
    bounded = (abs(fp_lo) < MATERIAL_DELTA and abs(fp_hi) < MATERIAL_DELTA
               and abs(fi_lo) < MATERIAL_DELTA and abs(fi_hi) < MATERIAL_DELTA)

    if big or rec_big:
        v, why = "MATERIAL", "a powered comparison is both significant and >= {:.2f}".format(MATERIAL_DELTA)
    elif sig or rec_sig:
        v, why = "SMALL", "drift is detectable but bounded below {:.2f}".format(MATERIAL_DELTA)
    elif bounded:
        v, why = "NONE", "no detectable drift, and the CIs exclude drift >= {:.2f}".format(MATERIAL_DELTA)
    else:
        v, why = "SMALL", "no detectable drift, but the CIs do not exclude drift >= {:.2f} (underpowered)".format(MATERIAL_DELTA)

    print("\n  decision rule, fixed before the run: MATERIAL if a paired test is")
    print("  significant at {:.2f} AND |delta| >= {:.2f} (or recovery CI excludes 0".format(ALPHA, MATERIAL_DELTA))
    print("  with |delta| >= {:.2f}); NONE if nothing is significant AND the paired".format(MATERIAL_DELTA))
    print("  CIs rule out drift >= {:.2f}; SMALL otherwise.".format(MATERIAL_DELTA))
    print("\n  DRIFT VERDICT: {}  ({})".format(v, why))


if __name__ == "__main__":
    main()
