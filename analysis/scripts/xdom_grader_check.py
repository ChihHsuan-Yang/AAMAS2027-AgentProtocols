#!/usr/bin/env python3
"""Grading-path check for the SciBench cross-domain replication.

WHY: SciBench answers carry units ("24 $\\mathrm{atm}$").  If the evaluator
mishandles unit equivalence, we would measure a grading artifact and report it
as a domain difference.  This tests the EXACT evaluator prompt and model the
runner uses -- imported from runner_xdomain, never retyped.

DESIGN: the positives are not invented by me.  They are real model answers
from the upstream released SciBench run (same benchmark, same two actors,
same evaluator model), joined to gold by problem_uid, so the "known-correct"
label comes from an independent scoring pass rather than from my own
judgement.  I add hand-built NEGATIVES in the specific shapes the evaluator
must catch -- wrong unit, power of ten, wrong sign -- because the released
corpus does not label failure modes, and a grader must be shown to FAIL on
purpose, not only to pass.  (A verifier only run on good data detects
nothing known.)

Outputs a 2x2 confusion matrix plus a per-case dump.
"""
from __future__ import annotations
import argparse, asyncio, importlib.util, json, random, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent.parent / "experiments"
sys.path.insert(0, str(EXP))

spec = importlib.util.spec_from_file_location("rx", str(EXP / "runner_xdomain.py"))
RX = importlib.util.module_from_spec(spec)
sys.modules["rx"] = RX
sys.argv = ["xdom_grader_check"]
spec.loader.exec_module(RX)

TRAJ = ("/Users/bellayang/Documents/note/projects/IEEE-BigData-SciAgentTrace/"
        "analysis/hf_cache/release/data/trajectories/part-00000.parquet")


# ---------------------------------------------------------------- negatives
def perturb(ans: str):
    """Build a WRONG answer from a gold answer, in a shape the grader must catch.

    Returns (perturbed, kind) or None if this gold answer has no safe
    perturbation of that kind.
    """
    m = re.match(r"\s*(-?)([0-9]*\.?[0-9]+)\s*(.*)", ans.strip())
    if not m:
        return None
    sign, num, unit = m.group(1), m.group(2), m.group(3)
    try:
        v = float(num)
    except ValueError:
        return None
    if v == 0:
        return None
    kinds = []
    # power of ten
    kinds.append(("{}{:g} {}".format(sign, v * 10, unit).strip(), "power_of_ten"))
    # clearly different magnitude (not a rounding difference)
    kinds.append(("{}{:g} {}".format(sign, v * 2.7, unit).strip(), "wrong_value"))
    # wrong sign, only when the sign is meaningful
    if sign == "-":
        kinds.append(("{:g} {}".format(v, unit).strip(), "wrong_sign"))
    elif v > 0:
        kinds.append(("-{:g} {}".format(v, unit).strip(), "wrong_sign"))
    # incompatible unit swap
    if unit:
        swap = {"atm": "K", "K": "atm", "J": "m", "m": "J",
                "kJ": "kPa", "kPa": "kJ"}
        for k, r in swap.items():
            if k in unit:
                kinds.append((("{}{:g} ".format(sign, v) + unit.replace(k, r)).strip(),
                              "incompatible_unit"))
                break
    return kinds


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-pos", type=int, default=20)
    ap.add_argument("--n-neg", type=int, default=20)
    ap.add_argument("--seed", type=int, default=20270101)
    ap.add_argument("--out", default=str(HERE.parent.parent /
                                         "experiments/results/xdomain/grader_check.json"))
    args = ap.parse_args()

    import pandas as pd

    probs = {p["problem_uid"]: p for p in RX.load_problems(574, 20270101)}

    t = pd.read_parquet(TRAJ)
    t = t[(t.benchmark_id == "scibench") & (t.slice_id == "text_only")]
    # Independent label: scored correct by the upstream run.
    pos_pool = t[(t.final_correct == 1) & t.final_answer.notna()]
    pos_pool = pos_pool[pos_pool.problem_uid.isin(probs)]

    rng = random.Random(args.seed)
    # one per problem_uid, so the positives are 20 distinct problems
    by_uid = {}
    for r in pos_pool.itertuples():
        by_uid.setdefault(r.problem_uid, []).append(r)
    pos_uids = sorted(by_uid)
    rng.shuffle(pos_uids)

    cases = []
    for u in pos_uids[: args.n_pos]:
        r = by_uid[u][0]
        cases.append({"uid": u, "candidate": str(r.final_answer),
                      "expect": 1, "kind": "upstream_correct",
                      "gold": probs[u]["answer"],
                      "actor": r.actor_model_id, "protocol": r.protocol_id})

    # negatives: perturb gold answers of DIFFERENT problems
    neg_uids = [u for u in sorted(probs) if u not in set(pos_uids[: args.n_pos])]
    rng.shuffle(neg_uids)
    want = args.n_neg
    kind_quota = {"power_of_ten": 0, "wrong_value": 0,
                  "wrong_sign": 0, "incompatible_unit": 0}
    for u in neg_uids:
        if len(kind_quota) and sum(kind_quota.values()) >= want:
            break
        ks = perturb(probs[u]["answer"])
        if not ks:
            continue
        # pick the least-used kind available for this problem
        ks.sort(key=lambda kv: kind_quota.get(kv[1], 0))
        cand, kind = ks[0]
        kind_quota[kind] = kind_quota.get(kind, 0) + 1
        cases.append({"uid": u, "candidate": cand, "expect": 0, "kind": kind,
                      "gold": probs[u]["answer"], "actor": "-", "protocol": "-"})

    print("cases: {} positive (upstream-labelled correct), {} negative".format(
        sum(1 for c in cases if c["expect"] == 1),
        sum(1 for c in cases if c["expect"] == 0)))
    print("negative kinds:", {k: v for k, v in kind_quota.items() if v})
    print()

    tokens = RX.TokenProvider()
    backend = RX.Backend(tokens)
    sem = asyncio.Semaphore(8)

    async def judge(c):
        async with sem:
            p = probs[c["uid"]]
            pre = RX.fill(RX.P.EVALUATOR_PREPEND,
                          task_description=p["problem_text"],
                          solution=c["candidate"], result=p["reference"])
            msgs = [{"role": "user",
                     "content": pre + "\n\n" + RX.P.EVALUATOR_APPEND}]
            r = await backend.chat(RX.EVALUATOR_MODEL, msgs, tag="gradercheck")
            if not r.ok:
                c["got"] = None
                c["raw"] = "CALL FAILED: {}".format(r.error)
                return c
            got, hint = RX.parse_evaluator(r.text)
            c["got"] = got
            c["hint"] = (hint or "")[:200]
            return c

    done = await asyncio.gather(*(judge(c) for c in cases))
    await backend.aclose()

    tp = sum(1 for c in done if c["expect"] == 1 and c["got"] == 1)
    fn = sum(1 for c in done if c["expect"] == 1 and c["got"] == 0)
    fp = sum(1 for c in done if c["expect"] == 0 and c["got"] == 1)
    tn = sum(1 for c in done if c["expect"] == 0 and c["got"] == 0)
    nul = sum(1 for c in done if c["got"] is None)

    print("=" * 78)
    print("CONFUSION MATRIX  (rows = truth, cols = evaluator verdict)")
    print("                  graded CORRECT   graded WRONG")
    print("  truly correct   {:>12}   {:>12}".format(tp, fn))
    print("  truly wrong     {:>12}   {:>12}".format(fp, tn))
    print("  unparsed verdicts: {}".format(nul))
    if tp + fn:
        print("  sensitivity (correct kept) : {:.3f}".format(tp / (tp + fn)))
    if fp + tn:
        print("  specificity (wrong caught) : {:.3f}".format(tn / (fp + tn)))
    print("=" * 78)

    print("\nPER-KIND breakdown of negatives:")
    kinds = {}
    for c in done:
        if c["expect"] == 0:
            k = kinds.setdefault(c["kind"], [0, 0])
            k[0] += 1
            if c["got"] == 0:
                k[1] += 1
    for k, (n, caught) in sorted(kinds.items()):
        print("  {:<20} caught {}/{}".format(k, caught, n))

    print("\nMISCLASSIFIED CASES:")
    bad = [c for c in done if c["got"] != c["expect"]]
    if not bad:
        print("  (none)")
    for c in bad:
        print("  uid={} kind={}".format(c["uid"], c["kind"]))
        print("     gold     : {!r}".format(c["gold"]))
        print("     candidate: {!r}".format(c["candidate"]))
        print("     expect={} got={}  hint={!r}".format(
            c["expect"], c["got"], c.get("hint", "")[:160]))

    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(
        {"confusion": {"tp": tp, "fn": fn, "fp": fp, "tn": tn, "unparsed": nul},
         "per_kind": {k: {"n": v[0], "caught": v[1]} for k, v in kinds.items()},
         "config_version": RX.CONFIG_VERSION,
         "evaluator_model": RX.EVALUATOR_MODEL,
         "cases": done}, indent=2, ensure_ascii=False))
    print("\nwrote {}".format(outp))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
