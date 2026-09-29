"""x5 — ANSWER LOCK-IN, measured on the message stream, not on submissions.

Corrects a framing hazard in x4/F16. `evaluator_history` only records answers
the team chose to SUBMIT. Arm A submits less often, so any "distinct answers"
count built from submissions is partly a count of submissions. The honest
measure of "did the team change its mind" reads the boxed answers out of the
ACTOR MESSAGES themselves.

Budget symmetry (read off runner.py, not assumed):
  MAX_OUTER_ROUNDS=3 x INNER_ROUNDS=2 = 6 deliberation cycles in EVERY arm.
  The evaluator is called only when the Reviewer approves, so
  n_evaluator_calls = n_cycles_in_which_the_reviewer_approved  (<= 6).
Both arms therefore hold the SAME cycle budget. They differ in how they spend
it: Arm B converts nearly every cycle into a submission; Arm A spends cycles
on internal revision instead.
"""
import json, glob, re, collections
import numpy as np

ROOT = "/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols"
RNG = np.random.default_rng(20261008)
BOXED = re.compile(r"\\boxed\s*\{")

rows = []
for f in sorted(glob.glob(ROOT + "/experiments/results/main/*.jsonl")):
    if "BUG" in f or "SNAPSHOT" in f:
        continue
    for l in open(f):
        try:
            rows.append(json.loads(l))
        except Exception:
            pass

def actor(r): return r["actor_model"].split("/")[-1]
ACTORS = sorted({actor(r) for r in rows})
ARMS = ["A", "B", "C", "Cp"]

def evals(r): return r.get("evaluator_history") or []
def fp_wrong(r):
    e = evals(r)
    return bool(e) and int(e[0].get("correctness") or 0) == 0

def norm(s):
    if s is None: return None
    s = re.sub(r"\s+", "", str(s)).strip("$").strip()
    return s or None

def extract_boxed_all(t):
    """Every \boxed{...} in a message, brace-balanced."""
    out = []
    for m in BOXED.finditer(t or ""):
        i = m.end() - 1
        d = 0
        for j in range(i, min(len(t), i + 4000)):
            if t[j] == "{": d += 1
            elif t[j] == "}":
                d -= 1
                if d == 0:
                    out.append(t[i + 1:j]); break
    return out

def _json_answer(t):
    """Arm C/Cp assert the answer in a JSON `answer` field, never in \\boxed.
    A \\boxed-only extractor silently returns ZERO answers for those arms,
    which would read as 'never changed its answer' -- the exact opposite of
    what the data says. Parse the arm's own answer channel instead."""
    out = []
    for m in re.finditer(r'"answer"\s*:\s*"((?:[^"\\\\]|\\\\.)*)"', t or ""):
        out.append(m.group(1))
    for m in re.finditer(r'"answer"\s*:\s*(-?[0-9][0-9.eE+/-]*)', t or ""):
        out.append(m.group(1))
    return out

def answer_sequence(r):
    """Ordered distinct-on-change sequence of answers asserted in messages.
    ARM-AWARE: A/B author answers as \\boxed{}; C/Cp author them as a JSON
    `answer` field. Using one extractor for both is a measurement error."""
    seq = []
    arm = r.get("arm")
    for m in (r.get("messages") or []):
        if m.get("role") not in ("planner", "executor", "reviewer"):
            continue
        t = m.get("text") or ""
        cands = extract_boxed_all(t) + (_json_answer(t) if arm in ("C", "Cp") else [])
        for b in cands:
            a = norm(b)
            if a and (not seq or seq[-1] != a):
                seq.append(a)
    return seq

def reviewer_routes(r):
    return [m.get("route") for m in (r.get("messages") or [])
            if m.get("role") == "reviewer" and m.get("route")]

print("=" * 78)
print("x5  ANSWER LOCK-IN  (message stream, not submissions)")
print("=" * 78)
print(f"trajectories: {len(rows)}")

# ---- B1 budget symmetry ------------------------------------------------
print("\n" + "-" * 78)
print("B1  CYCLE BUDGET IS IDENTICAL; SPENDING IS NOT")
print("    cycles = deliberation rounds actually run (<=6 in every arm)")
print("-" * 78)
print(f"{'actor':<24}{'arm':<5}{'n_fpw':>7}{'cycles':>9}{'P(6 cyc)':>10}"
      f"{'eval calls':>12}{'submit rate':>13}{'reviewer accept':>17}")
for a in ACTORS:
    for arm in ARMS:
        sub = [r for r in rows if actor(r) == a and r["arm"] == arm and fp_wrong(r)]
        if len(sub) < 10: continue
        cyc = np.array([r.get("inner_used") or 0 for r in sub], float)
        ne  = np.array([len(evals(r)) for r in sub], float)
        rr  = [reviewer_routes(r) for r in sub]
        acc = np.array([np.mean([x == "agree" for x in v]) if v else np.nan
                        for v in rr], float)
        with np.errstate(invalid="ignore", divide="ignore"):
            srate = np.nanmean(np.where(cyc > 0, ne / cyc, np.nan))
        print(f"{a:<24}{arm:<5}{len(sub):>7}{cyc.mean():>9.2f}"
              f"{np.mean(cyc >= 6):>10.3f}{ne.mean():>12.2f}"
              f"{srate:>13.3f}{np.nanmean(acc):>17.3f}")

# ---- B2 the lock-in measure --------------------------------------------
print("\n" + "-" * 78)
print("B2  ANSWER LOCK-IN, from the MESSAGE stream")
print("    (among first-pass-wrong trajectories; counts every answer the")
print("     team asserted, whether or not it was submitted)")
print("-" * 78)
print(f"{'actor':<24}{'arm':<5}{'n':>7}{'P(one answer)':>15}{'med distinct':>14}"
      f"{'mean distinct':>15}{'mean switches':>15}")
store = {}
for a in ACTORS:
    for arm in ARMS:
        sub = [r for r in rows if actor(r) == a and r["arm"] == arm and fp_wrong(r)]
        if len(sub) < 10: continue
        nd, sw = [], []
        for r in sub:
            s = answer_sequence(r)
            nd.append(len(set(s)))
            sw.append(max(0, len(s) - 1))
        nd, sw = np.array(nd, float), np.array(sw, float)
        store[(a, arm)] = (sub, nd, sw)
        print(f"{a:<24}{arm:<5}{len(sub):>7}{np.mean(nd <= 1):>15.3f}"
              f"{np.median(nd):>14.1f}{nd.mean():>15.2f}{sw.mean():>15.2f}")

# ---- B3 lock-in among trajectories that used the WHOLE cycle budget -----
print("\n" + "-" * 78)
print("B3  SAME, restricted to trajectories that used ALL 6 CYCLES")
print("    This is the clean comparison: identical spend, identical")
print("    opportunity, the only question is whether the answer moved.")
print("-" * 78)
print(f"{'actor':<24}{'arm':<5}{'n':>7}{'P(one answer)':>15}{'med distinct':>14}"
      f"{'recovery':>10}")
for a in ACTORS:
    for arm in ARMS:
        sub = [r for r in rows if actor(r) == a and r["arm"] == arm
               and fp_wrong(r) and (r.get("inner_used") or 0) >= 6]
        if len(sub) < 10: continue
        nd = np.array([len(set(answer_sequence(r))) for r in sub], float)
        rec = np.mean([int(r.get("correct") or 0) for r in sub])
        print(f"{a:<24}{arm:<5}{len(sub):>7}{np.mean(nd <= 1):>15.3f}"
              f"{np.median(nd):>14.1f}{rec:>10.3f}")

# ---- B4 does moving the answer predict recovery? ------------------------
print("\n" + "-" * 78)
print("B4  DOES CHANGING THE ANSWER PREDICT RECOVERY?")
print("    (descriptive/associational; answer change is post-treatment)")
print("-" * 78)
print(f"{'actor':<24}{'arm':<5}{'recov | never changed':>24}{'recov | changed':>18}")
for a in ACTORS:
    for arm in ARMS:
        got = store.get((a, arm))
        if not got: continue
        sub, nd, _ = got
        rec = np.array([int(r.get("correct") or 0) for r in sub], float)
        m0, m1 = nd <= 1, nd > 1
        if m0.sum() < 5 or m1.sum() < 5: continue
        print(f"{a:<24}{arm:<5}"
              f"{rec[m0].mean():>18.3f} (n={int(m0.sum())})"
              f"{rec[m1].mean():>12.3f} (n={int(m1.sum())})")

# ---- B5 the reviewer's role: refusal rate -------------------------------
print("\n" + "-" * 78)
print("B5  THE REVIEWER'S REFUSAL RATE  (first reviewer turn)")
print("    An 'agree' on turn 1 sends the answer straight to the evaluator.")
print("-" * 78)
print(f"{'actor':<24}{'arm':<5}{'n':>7}{'P(agree turn1)':>16}{'P(ever refuses)':>17}")
for a in ACTORS:
    for arm in ARMS:
        sub = [r for r in rows if actor(r) == a and r["arm"] == arm and fp_wrong(r)]
        if len(sub) < 10: continue
        first = [reviewer_routes(r)[0] if reviewer_routes(r) else None for r in sub]
        ever = [any(x != "agree" for x in reviewer_routes(r)) for r in sub]
        n1 = [x for x in first if x]
        print(f"{a:<24}{arm:<5}{len(sub):>7}"
              f"{np.mean([x=='agree' for x in n1]):>16.3f}{np.mean(ever):>17.3f}")

print("\n" + "=" * 78)
