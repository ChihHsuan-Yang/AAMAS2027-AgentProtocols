"""x4 — the canonical RECOVERY analysis.

Answers Bella's Sections 3, 4, 6, 7, 10, 23 with one frozen set of
definitions. Every number the manuscript quotes about recovery must come
from here, so the definitions live in exactly one place.

DEFINITIONS (frozen 2026-09-29)
-------------------------------
first_pass_wrong : the FIRST evaluator verdict on the trajectory is incorrect.
                   Trajectories with zero evaluator calls are EXCLUDED and
                   counted separately (they never entered the judged loop).
recovered        : first_pass_wrong AND the trajectory's final answer is correct.
recovery rate    : recovered / first_pass_wrong   (denominator printed always)

Recovery is therefore ALWAYS conditional on the same failure state, and is
never mixed with unconditional P(correct).
"""
import json, glob, collections, re, sys
import numpy as np

ROOT = "/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols"
RNG = np.random.default_rng(20261008)
BOX = re.compile(r"\\boxed\s*\{")

# ---------------------------------------------------------------- load
def load():
    rows = []
    for f in sorted(glob.glob(ROOT + "/experiments/results/main/*.jsonl")):
        if "BUG" in f or "SNAPSHOT" in f:
            continue
        for l in open(f):
            try:
                rows.append(json.loads(l))
            except Exception:
                pass
    return rows

def actor(r):  return r["actor_model"].split("/")[-1]
def cell(r):   return (actor(r), r["arm"])

def evals(r):  return r.get("evaluator_history") or []

def first_pass_correct(r):
    e = evals(r)
    if not e:
        return None          # never judged -> excluded from every recovery stat
    return int(e[0].get("correctness") or 0)

def final_correct(r):
    return int(r.get("correct") or 0)

def norm_ans(s):
    """Normalise a candidate answer for the distinct-answer count."""
    if s is None:
        return None
    s = str(s).strip()
    s = re.sub(r"\s+", "", s)
    s = s.strip("$").strip()
    return s or None

def boot_ci(x, n=4000):
    x = np.asarray(x, float)
    if len(x) < 5:
        return (np.nan, np.nan)
    bs = [RNG.choice(x, len(x)).mean() for _ in range(n)]
    return tuple(np.percentile(bs, [2.5, 97.5]))

# ---------------------------------------------------------------- main
rows = load()
ACTORS = sorted({actor(r) for r in rows})
ARMS = ["A", "B", "C", "Cp"]
ARMS = [a for a in ARMS if any(r["arm"] == a for r in rows)]

print("=" * 78)
print("x4  RECOVERY  —  frozen definitions, explicit denominators")
print("=" * 78)
print(f"trajectories loaded: {len(rows)}")
print(f"actors: {ACTORS}")
print(f"arms:   {ARMS}")

# ---- S3: the recovery table with every denominator spelled out ----------
print("\n" + "-" * 78)
print("S3  RECOVERY TABLE  (denominators explicit)")
print("-" * 78)
hdr = (f"{'actor':<24}{'arm':<5}{'n':>6}{'nojudge':>8}{'judged':>8}"
       f"{'fp_wrong':>9}{'recov':>7}{'rate':>8}{'   95% CI':<20}")
print(hdr)
recov_store = {}
for a in ACTORS:
    for arm in ARMS:
        sub = [r for r in rows if actor(r) == a and r["arm"] == arm]
        if not sub:
            continue
        nojudge = sum(1 for r in sub if first_pass_correct(r) is None)
        judged = [r for r in sub if first_pass_correct(r) is not None]
        fpw = [r for r in judged if first_pass_correct(r) == 0]
        rec = [final_correct(r) for r in fpw]
        rate = np.mean(rec) if rec else float("nan")
        lo, hi = boot_ci(rec) if rec else (np.nan, np.nan)
        recov_store[(a, arm)] = (rec, fpw)
        print(f"{a:<24}{arm:<5}{len(sub):>6}{nojudge:>8}{len(judged):>8}"
              f"{len(fpw):>9}{int(sum(rec)):>7}{rate:>8.3f}"
              f"   [{lo:.3f},{hi:.3f}]")

# ---- S3b: first-pass accuracy, the other half of the dissociation -------
print("\n" + "-" * 78)
print("S3b  FIRST-PASS ACCURACY  (judged trajectories only)")
print("-" * 78)
print(f"{'actor':<24}{'arm':<5}{'judged':>8}{'fp_acc':>9}{'   95% CI':<20}")
for a in ACTORS:
    for arm in ARMS:
        sub = [first_pass_correct(r) for r in rows
               if actor(r) == a and r["arm"] == arm]
        sub = [x for x in sub if x is not None]
        if not sub:
            continue
        lo, hi = boot_ci(sub)
        print(f"{a:<24}{arm:<5}{len(sub):>8}{np.mean(sub):>9.3f}   [{lo:.3f},{hi:.3f}]")

# ---- S4: SAME-PROBLEM paired recovery transitions -----------------------
print("\n" + "-" * 78)
print("S4  PAIRED RECOVERY TRANSITIONS  (same problems, wrong on first pass")
print("    under BOTH arms — the only comparison not driven by different")
print("    initial-error sets)")
print("-" * 78)
by = collections.defaultdict(dict)
for r in rows:
    fp = first_pass_correct(r)
    if fp is None:
        continue
    by[cell(r)][r["problem_uid"]] = (fp, final_correct(r))

for a in ACTORS:
    for x, y in (("A", "B"), ("A", "C"), ("B", "C")):
        P, Q = by.get((a, x), {}), by.get((a, y), {})
        both = [p for p in set(P) & set(Q) if P[p][0] == 0 and Q[p][0] == 0]
        if len(both) < 10:
            continue
        t = collections.Counter()
        for p in both:
            t[(P[p][1], Q[p][1])] += 1
        n = len(both)
        b, c = t[(1, 0)], t[(0, 1)]           # discordant pairs
        # exact McNemar (binomial), two-sided
        from math import comb
        if b + c:
            k, m = min(b, c), b + c
            pv = min(1.0, 2 * sum(comb(m, i) for i in range(k + 1)) / 2 ** m)
        else:
            pv = 1.0
        print(f"\n  {a}  {x} vs {y}   n(both first-pass wrong) = {n}")
        print(f"    both recover        {t[(1,1)]:>5}")
        print(f"    {x} recovers, {y} fails {t[(1,0)]:>5}   <- discordant")
        print(f"    {x} fails, {y} recovers {t[(0,1)]:>5}   <- discordant")
        print(f"    both fail           {t[(0,0)]:>5}")
        print(f"    recovery {x}={(t[(1,1)]+t[(1,0)])/n:.3f}  "
              f"{y}={(t[(1,1)]+t[(0,1)])/n:.3f}   McNemar exact p={pv:.2e}")

# ---- S7: evaluator exposure conditional on first-pass wrong -------------
print("\n" + "-" * 78)
print("S7  EVALUATOR EXPOSURE, conditional on first-pass wrong")
print("    (does the role-free team get fewer chances, or the same chances?)")
print("-" * 78)
print(f"{'actor':<24}{'arm':<5}{'n_fpw':>7}{'P(>1 eval)':>12}"
      f"{'mean_eval':>11}{'med_eval':>10}{'P(exhaust)':>12}{'recovery':>10}")
for a in ACTORS:
    for arm in ARMS:
        _, fpw = recov_store.get((a, arm), ([], []))
        if len(fpw) < 10:
            continue
        ne = np.array([len(evals(r)) for r in fpw], float)
        rec = np.array([final_correct(r) for r in fpw], float)
        print(f"{a:<24}{arm:<5}{len(fpw):>7}{np.mean(ne > 1):>12.3f}"
              f"{ne.mean():>11.2f}{np.median(ne):>10.1f}"
              f"{np.mean(ne >= 6):>12.3f}{rec.mean():>10.3f}")

# ---- S7b: recovery at MATCHED evaluator-call counts ---------------------
print("\n" + "-" * 78)
print("S7b  RECOVERY AT MATCHED OPPORTUNITY (same number of evaluator calls)")
print("     If B is worse here, it is a per-attempt capability deficit.")
print("     If B is not worse, the deficit is in HOW MANY attempts it uses.")
print("-" * 78)
for a in ACTORS:
    lines = []
    for k in range(2, 7):
        cellvals = {}
        for arm in ("A", "B"):
            _, fpw = recov_store.get((a, arm), ([], []))
            sel = [final_correct(r) for r in fpw if len(evals(r)) == k]
            if len(sel) >= 10:
                cellvals[arm] = (np.mean(sel), len(sel))
        if len(cellvals) == 2:
            lines.append((k, cellvals))
    if lines:
        print(f"\n  {a}")
        print(f"    {'eval calls':<12}{'Arm A':<20}{'Arm B':<20}")
        for k, cv in lines:
            (ma, na), (mb, nb) = cv["A"], cv["B"]
            print(f"    {k:<12}{ma:.3f} (n={na}){'':<6}{mb:.3f} (n={nb})")

# ---- S23: DIVERSITY, measured rather than asserted ----------------------
print("\n" + "-" * 78)
print("S23  DIVERSITY OF REVISION  (distinct candidate answers across the")
print("     trajectory, among first-pass-wrong trajectories)")
print("-" * 78)
print(f"{'actor':<24}{'arm':<5}{'n_fpw':>7}{'P(never changes)':>18}"
      f"{'med distinct':>14}{'mean distinct':>15}")
for a in ACTORS:
    for arm in ARMS:
        _, fpw = recov_store.get((a, arm), ([], []))
        if len(fpw) < 10:
            continue
        nd = []
        for r in fpw:
            cands = {norm_ans(e.get("candidate")) for e in evals(r)}
            cands.discard(None)
            nd.append(len(cands))
        nd = np.array(nd, float)
        print(f"{a:<24}{arm:<5}{len(fpw):>7}{np.mean(nd <= 1):>18.3f}"
              f"{np.median(nd):>14.1f}{nd.mean():>15.2f}")

print("\n" + "-" * 78)
print("S23b  SAME, restricted to trajectories that received >=2 evaluator")
print("      calls (i.e. actually had the chance to change their answer)")
print("-" * 78)
print(f"{'actor':<24}{'arm':<5}{'n':>7}{'P(never changes)':>18}{'med distinct':>14}")
for a in ACTORS:
    for arm in ARMS:
        _, fpw = recov_store.get((a, arm), ([], []))
        sub = [r for r in fpw if len(evals(r)) >= 2]
        if len(sub) < 10:
            continue
        nd = []
        for r in sub:
            cands = {norm_ans(e.get("candidate")) for e in evals(r)}
            cands.discard(None)
            nd.append(len(cands))
        nd = np.array(nd, float)
        print(f"{a:<24}{arm:<5}{len(sub):>7}{np.mean(nd <= 1):>18.3f}{np.median(nd):>14.1f}")

# ---- S6: recovery PATH decomposition ------------------------------------
print("\n" + "-" * 78)
print("S6  RECOVERY PATH  (who supplied the repair signal?)")
print("    oracle_assisted : the answer changed only AFTER an evaluator")
print("                      verdict was returned -> ground-truth-informed.")
print("    pre_oracle      : the answer changed within the first judged")
print("                      cycle, before any evaluator feedback.")
print("    NOTE: this protocol's evaluator sees gold, so oracle_assisted")
print("    recovery must NOT be attributed to multi-agent reasoning.")
print("-" * 78)
print(f"{'actor':<24}{'arm':<5}{'recovered':>10}{'oracle_assisted':>17}{'pre_oracle':>12}")
for a in ACTORS:
    for arm in ARMS:
        _, fpw = recov_store.get((a, arm), ([], []))
        rec = [r for r in fpw if final_correct(r) == 1]
        if len(rec) < 5:
            continue
        oracle = sum(1 for r in rec if len(evals(r)) >= 2)
        print(f"{a:<24}{arm:<5}{len(rec):>10}{oracle:>17}{len(rec)-oracle:>12}")

# ---- S10: Arm C recovery vs A and B, stated plainly ---------------------
print("\n" + "-" * 78)
print("S10  ARM C: does structural enforcement restore RECOVERY?")
print("-" * 78)
for a in ACTORS:
    vals = {}
    for arm in ARMS:
        rec, fpw = recov_store.get((a, arm), ([], []))
        if len(rec) >= 10:
            vals[arm] = (np.mean(rec), len(rec), *boot_ci(rec))
    if "A" in vals and "B" in vals and "C" in vals:
        print(f"\n  {a}")
        for arm in ("A", "B", "C", "Cp"):
            if arm in vals:
                m, n, lo, hi = vals[arm]
                print(f"    Arm {arm:<3} recovery {m:.3f}  n={n:<5} [{lo:.3f},{hi:.3f}]")

print("\n" + "=" * 78)
print("END x4")
print("=" * 78)
