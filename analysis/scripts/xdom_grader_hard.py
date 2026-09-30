#!/usr/bin/env python3
"""HARD grading probe: equivalence cases the evaluator must NOT reject.

The first grader check scored 40/40, which is weak evidence: the positives
were upstream answers already written in gold's unit, so the unit-equivalence
machinery was never actually exercised.  A check run only on its home case is
not known to discriminate.

The hazard that would actually corrupt this experiment is the FALSE NEGATIVE:
a scientifically correct answer expressed differently from gold -- other unit,
other notation, more or fewer significant figures -- graded WRONG.  That would
depress measured accuracy, inflate the first-pass-wrong denominator, and could
differ between arms if the arms write answers in systematically different
styles.  So it must be measured, not assumed.

Each case below is a MACHINE-GENERATED restatement of the gold answer that a
chemist would accept: exact unit conversions, notation changes, and rounding
inside the reference's own precision.  Every one SHOULD grade correct.
I also keep a small set of near-miss NEGATIVES (just outside tolerance) so the
probe cannot pass by the evaluator simply saying PASS to everything -- a
grader that accepts all restatements AND all near-misses is not lenient, it is
broken, and only the negatives can tell those apart.
"""
from __future__ import annotations
import argparse, asyncio, importlib.util, json, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent.parent / "experiments"
sys.path.insert(0, str(EXP))
spec = importlib.util.spec_from_file_location("rx", str(EXP / "runner_xdomain.py"))
RX = importlib.util.module_from_spec(spec)
sys.modules["rx"] = RX
sys.argv = ["xdom_grader_hard"]
spec.loader.exec_module(RX)


def parse_gold(ans: str):
    m = re.match(r"\s*(-?[0-9]*\.?[0-9]+)\s*(.*)", ans.strip())
    if not m:
        return None, None
    try:
        return float(m.group(1)), m.group(2)
    except ValueError:
        return None, None


def unit_words(u: str):
    """Strip LaTeX to a rough plain-text unit."""
    u = re.sub(r"\\(mathrm|text|mathdegree)\s*", "", u)
    u = u.replace("$", "").replace("{", "").replace("}", "")
    u = u.replace("\\,", " ").replace("\\;", " ").replace("~", " ")
    return re.sub(r"\s+", " ", u).strip()


# exact conversion factors: gold unit -> (new value multiplier, new unit)
CONV = [
    ("atm",   101.325, "kPa"),
    ("atm",   1.01325e5, "Pa"),
    ("kJ",    1000.0,  "J"),
    ("J",     0.001,   "kJ"),
    ("dm^3",  1e-3,    "m^3"),
    ("g",     1e-3,    "kg"),
]


def build_cases(probs, want_pos=22, want_neg=8):
    pos, neg = [], []
    for uid in sorted(probs):
        gold = probs[uid]["answer"]
        v, u = parse_gold(gold)
        if v is None or v == 0:
            continue
        pu = unit_words(u)

        # --- POSITIVES: must grade CORRECT ---
        if len(pos) < want_pos:
            # (1) exact unit conversion
            done = False
            for gu, f, nu in CONV:
                if re.search(r"(?<![A-Za-z])" + re.escape(gu) + r"(?![A-Za-z])", pu):
                    nv = v * f
                    pos.append({"uid": uid, "gold": gold,
                                "candidate": "{:.6g} {}".format(nv, pu.replace(gu, nu)),
                                "expect": 1, "kind": "unit_conversion"})
                    done = True
                    break
            if not done:
                # (2) scientific-notation restatement of the same value
                if abs(v) >= 1000 or (abs(v) < 0.01):
                    pos.append({"uid": uid, "gold": gold,
                                "candidate": "{:.4e} {}".format(v, pu).strip(),
                                "expect": 1, "kind": "sci_notation"})
                else:
                    # (3) extra trailing precision, same value
                    pos.append({"uid": uid, "gold": gold,
                                "candidate": "{:.4f} {}".format(v, pu).strip(),
                                "expect": 1, "kind": "extra_precision"})

        # --- NEGATIVES: near-miss, must grade WRONG ---
        elif len(neg) < want_neg:
            neg.append({"uid": uid, "gold": gold,
                        "candidate": "{:.6g} {}".format(v * 1.25, pu).strip(),
                        "expect": 0, "kind": "near_miss_25pct"})
        if len(pos) >= want_pos and len(neg) >= want_neg:
            break
    return pos + neg


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(HERE.parent.parent /
                                         "experiments/results/xdomain/grader_hard.json"))
    args = ap.parse_args()

    probs = {p["problem_uid"]: p for p in RX.load_problems(574, 20270101)}
    cases = build_cases(probs)
    print("hard cases: {} positive (equivalent restatements), {} negative (near-miss)".format(
        sum(1 for c in cases if c["expect"] == 1),
        sum(1 for c in cases if c["expect"] == 0)))
    kinds = {}
    for c in cases:
        kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
    print("kinds:", kinds, "\n")

    tokens = RX.TokenProvider()
    backend = RX.Backend(tokens)
    sem = asyncio.Semaphore(8)

    async def judge(c):
        async with sem:
            p = probs[c["uid"]]
            pre = RX.fill(RX.P.EVALUATOR_PREPEND,
                          task_description=p["problem_text"],
                          solution=c["candidate"], result=p["reference"])
            r = await backend.chat(RX.EVALUATOR_MODEL,
                                   [{"role": "user",
                                     "content": pre + "\n\n" + RX.P.EVALUATOR_APPEND}],
                                   tag="hard")
            if not r.ok:
                c["got"], c["hint"] = None, "CALL FAILED"
                return c
            got, hint = RX.parse_evaluator(r.text)
            c["got"], c["hint"] = got, (hint or "")[:200]
            return c

    done = await asyncio.gather(*(judge(c) for c in cases))
    await backend.aclose()

    tp = sum(1 for c in done if c["expect"] == 1 and c["got"] == 1)
    fn = sum(1 for c in done if c["expect"] == 1 and c["got"] == 0)
    fp = sum(1 for c in done if c["expect"] == 0 and c["got"] == 1)
    tn = sum(1 for c in done if c["expect"] == 0 and c["got"] == 0)

    print("=" * 78)
    print("HARD CONFUSION MATRIX (rows = truth, cols = verdict)")
    print("                  graded CORRECT   graded WRONG")
    print("  truly correct   {:>12}   {:>12}".format(tp, fn))
    print("  truly wrong     {:>12}   {:>12}".format(fp, tn))
    if tp + fn:
        print("  sensitivity on EQUIVALENT restatements: {:.3f}".format(tp / (tp + fn)))
    if fp + tn:
        print("  specificity on NEAR-MISS (25% off)    : {:.3f}".format(tn / (fp + tn)))
    print("=" * 78)

    print("\nPER-KIND:")
    agg = {}
    for c in done:
        a = agg.setdefault(c["kind"], [0, 0])
        a[0] += 1
        if c["got"] == c["expect"]:
            a[1] += 1
    for k, (n, ok) in sorted(agg.items()):
        print("  {:<20} correct {}/{}".format(k, ok, n))

    print("\nMISCLASSIFIED:")
    bad = [c for c in done if c["got"] != c["expect"]]
    if not bad:
        print("  (none)")
    for c in bad:
        print("  uid={} kind={}".format(c["uid"], c["kind"]))
        print("     gold     : {!r}".format(c["gold"]))
        print("     candidate: {!r}".format(c["candidate"]))
        print("     expect={} got={} hint={!r}".format(c["expect"], c["got"],
                                                       (c.get("hint") or "")[:160]))

    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps({"confusion": {"tp": tp, "fn": fn, "fp": fp, "tn": tn},
                                "cases": done}, indent=2, ensure_ascii=False))
    print("\nwrote {}".format(outp))


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
