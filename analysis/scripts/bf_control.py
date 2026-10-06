#!/usr/bin/env python3
"""bf_control -- analysis of the Arm Bf control (role-free + evaluator feedback
delivered) against the frozen Arm A and Arm B cells, one actor, one domain.

WHY THIS EXISTS
---------------
Arm B agents never received the evaluator's FAIL verdict or repair hint (the
Arm B template has no ${advice} slot; see experiments/BF_CONTROL.md). The
headline recovery contrast A-vs-B is therefore confounded with feedback
delivery. Arm Bf delivers the same feedback string Arm A receives, with the
Arm B prompt otherwise unchanged. This script reads the three cells on the
same problems and prints what the paper needs.

DEFINITIONS -- identical to analysis/scripts/x4_recovery.py and x5_lockin.py
----------------------------------------------------------------------------
first_pass_wrong : the FIRST evaluator verdict on the trajectory is incorrect.
recovered        : first_pass_wrong AND the trajectory's final grade is correct.
recovery rate    : recovered / first_pass_wrong (denominator always printed).
final correct    : `correct` == 1; a trajectory that never produced a graded
                   answer counts as incorrect (the pre-registered rule).
one answer       : the whole message stream asserts exactly one distinct
                   normalised \\boxed answer (x5's "frozen" measure).
never declines   : every Reviewer-slot route in the trajectory is "agree".

USAGE
-----
  python3 analysis/scripts/bf_control.py \\
      --frozen experiments/results/FROZEN/campaign_v2.jsonl \\
      --bf     experiments/results/bf/bf_omnimath_gemma4.jsonl \\
      --actor  gemma-4-31B-it

--frozen and --bf each accept several files. Run once per domain.
The A-vs-B block must reproduce the paper (Omni-MATH gemma-4: recovery 70/316
vs 16/316; paired 37 vs 3 on n=237). If it does not, stop: the wrong frozen
file was loaded and nothing below it means anything.
"""
import argparse, json, re, sys
from math import comb

BOXED = re.compile(r"\\boxed\s*\{")


def load(paths):
    rows = []
    for p in paths:
        with open(p) as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rows.append(json.loads(line))
                except Exception:
                    pass
    return rows


def actor(r):
    return r["actor_model"].split("/")[-1]


def evals(r):
    return r.get("evaluator_history") or []


def first_pass(r):
    """1 / 0 on the first evaluator verdict; None if never judged."""
    e = evals(r)
    if not e:
        return None
    return int(e[0].get("correctness") or 0)


def fp_wrong(r):
    return first_pass(r) == 0


def final_correct(r):
    return int(r.get("correct") or 0)


def norm(s):
    if s is None:
        return None
    s = re.sub(r"\s+", "", str(s)).strip("$").strip()
    return s or None


def boxed_all(t):
    out = []
    for m in BOXED.finditer(t or ""):
        i = m.end() - 1
        d = 0
        for j in range(i, min(len(t), i + 4000)):
            if t[j] == "{":
                d += 1
            elif t[j] == "}":
                d -= 1
                if d == 0:
                    out.append(t[i + 1:j])
                    break
    return out


def answer_sequence(r):
    seq = []
    for m in (r.get("messages") or []):
        if m.get("role") not in ("planner", "executor", "reviewer"):
            continue
        for b in boxed_all(m.get("text") or ""):
            a = norm(b)
            if a and (not seq or seq[-1] != a):
                seq.append(a)
    return seq


def routes(r):
    return [m.get("route") for m in (r.get("messages") or [])
            if m.get("role") == "reviewer" and m.get("route")]


def mcnemar_exact(b, c):
    """Two-sided exact McNemar on discordant counts b, c."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    return min(1.0, 2 * sum(comb(n, i) for i in range(k + 1)) / 2 ** n)


def frac(a, b):
    return "{}/{} = {:.4f}".format(a, b, a / b) if b else "{}/0".format(a)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--frozen", nargs="+", required=True,
                    help="frozen JSONL file(s) holding the Arm A and Arm B cells")
    ap.add_argument("--bf", nargs="+", required=True,
                    help="JSONL file(s) holding the Arm Bf cell")
    ap.add_argument("--actor", default="gemma-4-31B-it")
    args = ap.parse_args()

    cells = {}
    for r in load(args.frozen):
        if actor(r) == args.actor and r.get("arm") in ("A", "B"):
            cells.setdefault(r["arm"], {})[r["problem_uid"]] = r
    for r in load(args.bf):
        if actor(r) == args.actor and r.get("arm") == "Bf":
            if r.get("stopping_condition") == "model_unavailable":
                continue
            cells.setdefault("Bf", {})[r["problem_uid"]] = r

    for a in ("A", "B", "Bf"):
        if a not in cells:
            sys.exit("no rows for arm {} / actor {}".format(a, args.actor))

    common = sorted(set(cells["A"]) & set(cells["B"]) & set(cells["Bf"]))
    print("=" * 78)
    print("Arm Bf control   actor={}".format(args.actor))
    print("=" * 78)
    print("problems per arm: A={} B={} Bf={}   common to all three: {}".format(
        len(cells["A"]), len(cells["B"]), len(cells["Bf"]), len(common)))
    if len(common) < len(cells["A"]):
        print("NOTE: every statistic below is on the {} common problems. If "
              "the Bf run is complete this must equal the A/B cell size.".format(len(common)))
    R = {a: {u: cells[a][u] for u in common} for a in cells}
    n = len(common)

    # ---------------------------------------------------------------- 0
    print("\n[0] Bf run health")
    stops = {}
    for r in R["Bf"].values():
        stops[r.get("stopping_condition")] = stops.get(r.get("stopping_condition"), 0) + 1
    print("    stopping conditions: {}".format(dict(sorted(stops.items(), key=lambda kv: -kv[1]))))
    print("    config_version(s): {}".format(sorted({r.get("config_version") for r in R["Bf"].values()})))
    post = [m for r in R["Bf"].values() for m in (r.get("messages") or [])
            if m.get("role") in ("planner", "executor", "reviewer")
            and "evaluator_feedback_in_prompt" in m]
    with_fb = sum(1 for m in post if m["evaluator_feedback_in_prompt"])
    print("    actor messages whose prompt carried evaluator feedback: {}".format(frac(with_fb, len(post))))
    fpw_bf = [r for r in R["Bf"].values() if fp_wrong(r)]
    delivered = sum(1 for r in fpw_bf if any(
        m.get("evaluator_feedback_in_prompt") for m in (r.get("messages") or [])))
    print("    first-pass-wrong Bf trajectories in which feedback reached an agent: {}".format(
        frac(delivered, len(fpw_bf))))
    print("    (a first-pass-wrong trajectory with NO delivery can only be one whose "
          "first verdict came in the last cycle)")

    # ---------------------------------------------------------------- 1
    print("\n[1] First pass and final accuracy (never-judged counts as incorrect)")
    print("    {:<4}{:>8}{:>14}{:>22}{:>22}".format("arm", "n", "never judged", "first-pass correct", "final correct"))
    for a in ("A", "B", "Bf"):
        rs = list(R[a].values())
        nj = sum(1 for r in rs if first_pass(r) is None)
        fp = sum(1 for r in rs if first_pass(r) == 1)
        fc = sum(final_correct(r) for r in rs)
        print("    {:<4}{:>8}{:>14}{:>22}{:>22}".format(a, n, nj, frac(fp, n), frac(fc, n)))

    def paired_final(x, y):
        b = sum(1 for u in common if final_correct(R[x][u]) == 1 and final_correct(R[y][u]) == 0)
        c = sum(1 for u in common if final_correct(R[x][u]) == 0 and final_correct(R[y][u]) == 1)
        return b, c

    print("\n    Final accuracy, paired on all {} problems (no conditioning):".format(n))
    for x, y in (("A", "B"), ("A", "Bf"), ("Bf", "B")):
        b, c = paired_final(x, y)
        print("    {:>2} vs {:<2}: correct only under {}: {:>4}   only under {}: {:>4}   "
              "delta({}-{}) = {:+.4f}   exact McNemar p = {:.3g}".format(
                  x, y, x, b, y, c, y, x, (c - b) / n, mcnemar_exact(b, c)))

    # ---------------------------------------------------------------- 2
    print("\n[2] Recovery after a wrong first verdict")
    print("    marginal (each arm over its own first-pass-wrong set):")
    for a in ("A", "B", "Bf"):
        fpw = [r for r in R[a].values() if fp_wrong(r)]
        rec = sum(final_correct(r) for r in fpw)
        print("    {:<4} {}".format(a, frac(rec, len(fpw))))

    print("\n    paired (problems first-pass-wrong under BOTH arms of the pair):")
    for x, y in (("A", "B"), ("A", "Bf"), ("Bf", "B")):
        both = [u for u in common if fp_wrong(R[x][u]) and fp_wrong(R[y][u])]
        rx = sum(final_correct(R[x][u]) for u in both)
        ry = sum(final_correct(R[y][u]) for u in both)
        b = sum(1 for u in both if final_correct(R[x][u]) == 1 and final_correct(R[y][u]) == 0)
        c = sum(1 for u in both if final_correct(R[x][u]) == 0 and final_correct(R[y][u]) == 1)
        print("    {:>2} vs {:<2}: n={:<4} {}: {:<18} {}: {:<18} recovered only under {}: {:>3}, "
              "only under {}: {:>3}   exact McNemar p = {:.3g}".format(
                  x, y, len(both), x, frac(rx, len(both)), y, frac(ry, len(both)),
                  x, b, y, c, mcnemar_exact(b, c)))

    # ---------------------------------------------------------------- 3
    print("\n[3] What a first-pass-wrong trajectory spends its cycles on")
    print("    {:<4}{:>7}{:>9}{:>13}{:>11}{:>18}{:>15}".format(
        "arm", "n_fpw", "cycles", "submissions", "revisions", "never declines", "one answer"))
    for a in ("A", "B", "Bf"):
        fpw = [r for r in R[a].values() if fp_wrong(r)]
        if not fpw:
            continue
        cyc = sum((r.get("inner_used") or 0) for r in fpw) / len(fpw)
        sub = sum(len(evals(r)) for r in fpw) / len(fpw)
        nd = sum(1 for r in fpw if routes(r) and all(x == "agree" for x in routes(r))) / len(fpw)
        one = sum(1 for r in fpw if len(answer_sequence(r)) == 1) / len(fpw)
        print("    {:<4}{:>7}{:>9.2f}{:>13.2f}{:>11.2f}{:>18.3f}{:>15.3f}".format(
            a, len(fpw), cyc, sub, cyc - sub, nd, one))

    # ---------------------------------------------------------------- 4
    print("\n[4] Reading, fixed before the run (experiments/BF_CONTROL.md):")
    print("    * A vs Bf paired recovery still clearly favours A, and Bf is close to B")
    print("        -> the role contrast survives feedback delivery; report Bf as the")
    print("           role-free condition (or beside B).")
    print("    * Bf recovery close to A, A vs Bf paired not resolved")
    print("        -> the A-vs-B recovery gap was feedback delivery, not roles.")
    print("    * in between -> both contribute; report the decomposition B -> Bf -> A.")


if __name__ == "__main__":
    main()
