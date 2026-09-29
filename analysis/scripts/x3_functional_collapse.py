"""X3: LEVEL-2 (semantic) and LEVEL-3 (functional) role redundancy.

Exact byte-identity collapse is already audited (x2_collapse.csv).  This script
asks the two follow-on questions the paper needs:

  LEVEL 2  how SIMILAR are the three role outputs, on a continuous scale?
  LEVEL 3  does a later role CONTRIBUTE anything material (new evaluated
           equations, new content tokens, a changed answer, novel critique)?

The load-bearing comparison is ARM A vs ARM B.  If Arm A executors are also
functionally inert much of the time, the "roles are differentiated in A and
collapse in B" story does not hold.

UNIT OF ANALYSIS
  A *cycle* = (trajectory, outer_round, inner_round) in which all three roles
  have an ACCEPTED message (validation.ok is not False -- prereg says the
  regenerated message is the one analysed).  The PRIMARY unit is the FIRST
  complete accepted cycle of each trajectory, so every trajectory contributes
  exactly one row and no trajectory is over-weighted by its round count.
  An all-cycles variant is written as a sensitivity file.

ORDERING
  Within a cycle: planner -> executor -> reviewer.  "Earlier" for the primary
  analysis means earlier *within the cycle*.  The all-cycles variant uses the
  full preceding trajectory history.

EMBEDDINGS
  sentence-transformers is NOT installed and this script does NOT install it.
  Level 2 therefore uses (a) difflib SequenceMatcher ratio on
  whitespace-normalized characters and (b) token-set Jaccard.  No embedding
  metric is reported.  Stated in the output header.

KNOWN MEASUREMENT HAZARDS, handled explicitly
  * difflib ratio = 2M/T is CAPPED by length asymmetry.  An Arm A reviewer
    (mean 652 chars) compared to an Arm A executor (mean 3292 chars) cannot
    exceed 2*652/3944 = 0.33 no matter how redundant it is.  We therefore also
    report a *containment* metric (matched / len(shorter)) and the Szymkiewicz-
    Simpson overlap coefficient, neither of which is length-capped.
  * A similarity number is meaningless without a null.  We compute a
    CROSS-PROBLEM null: same arm, same actor, same role pair, DIFFERENT
    problem.  Arm A similarity must be read against that floor.
  * Arm C's contracts structurally remove the planner's and reviewer's answer
    channel, so "answer change" in Arm C is architectural, not behavioural.
  * autojunk=True changes difflib ratios by up to 0.83 on this corpus, so it is
    forced OFF.

Usage:
  python3 x3_functional_collapse.py <paths...>
"""
from __future__ import annotations

import argparse
import collections
import difflib
import glob
import json
import multiprocessing as mp
import os
import random
import re
import sys

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(os.path.dirname(HERE), "results")
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, os.path.join(REPO, "experiments"))
try:
    from schemas import extract_json_object  # project's own tolerant JSON reader
except Exception:                                            # pragma: no cover
    extract_json_object = None

pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 60)
RNG = np.random.default_rng(20260929)
ROLES = ("planner", "executor", "reviewer")
CHAR_CAP = 20000            # difflib is O(n*m); longest message here is ~37k
N_BOOT = 2000

# ---------------------------------------------------------------- primitives
EVAL_EQ = re.compile(r"=\s*[-+]?\d+(?:\.\d+)?")          # frozen, from x2
CRITIQUE = re.compile(r"incorrect|wrong|error|mistake|flaw|missing|should be|instead",
                      re.I)
WS = re.compile(r"\s+")
TOKEN = re.compile(r"[a-z]+|[0-9]+(?:\.[0-9]+)?")

STOP = set("""a about above after again against all am an and any are aren as at be because been
before being below between both but by can cannot could couldn did didn do does doesn doing don
down during each few for from further had hadn has hasn have haven having he her here hers herself
him himself his how i if in into is isn it its itself let me more most mustn my myself no nor not
of off on once only or other ought our ours ourselves out over own same shan she should shouldn so
some such than that the their theirs them themselves then there these they this those through to
too under until up very was wasn we were weren what when where which while who whom why with won
would wouldn you your yours yourself yourselves s t will just now also using use used get given
""".split())


def wsnorm(t: str) -> str:
    return WS.sub(" ", t or "").strip()


def content_tokens(t: str) -> list:
    return [w for w in TOKEN.findall((t or "").lower()) if w not in STOP]


def eq_tokens(t: str) -> list:
    """Normalized evaluated-numeric-equality tokens, e.g. '=5', '=-3.25'."""
    return [WS.sub("", m) for m in EVAL_EQ.findall(t or "")]


def boxed_all(t: str) -> list:
    """All \\boxed{...} payloads, brace-balanced so nesting unwraps correctly."""
    out, i, t = [], 0, t or ""
    while True:
        j = t.find("\\boxed", i)
        if j < 0:
            return out
        k = t.find("{", j)
        if k < 0 or k - j > 8:
            i = j + 6
            continue
        depth = 0
        for p in range(k, len(t)):
            if t[p] == "{":
                depth += 1
            elif t[p] == "}":
                depth -= 1
                if depth == 0:
                    out.append(t[k + 1:p])
                    i = p + 1
                    break
        else:
            return out


_ANS_STRIP = re.compile(r"\\(?:left|right|!|,|;|:|quad|qquad|displaystyle|text|mathrm)\b")
_SINGLE_BRACE = re.compile(r"\{(.)\}")


def norm_answer(a):
    """Light LaTeX normalization for answer EQUALITY comparison.

    Deleting braces outright collides \\frac{1}{27} with \\frac{12}{7}; on this
    corpus that mis-called 21 of 16518 cycle answer comparisons.  So redundant
    single-token braces are unwrapped first ({2} -> 2, so \\frac{2}{3} still
    matches \\frac23), and any brace that survives becomes a real '#' delimiter
    instead of vanishing.  Checked against 9 hand-built cases including both
    collision shapes; see the self-test under `--selftest`.
    """
    if a is None:
        return None
    a = str(a).replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac")
    a = _ANS_STRIP.sub("", a).replace("$", "")
    a = re.sub(r"\s+", "", a)
    prev = None
    while prev != a:
        prev, a = a, _SINGLE_BRACE.sub(r"\1", a)
    a = re.sub(r"[{}]", "#", a)
    a = re.sub(r"#+", "#", a)
    a = a.rstrip(".").strip("#").strip()
    return a or None


def extract_answer(arm: str, role: str, text: str):
    """Answer channel is arm-dependent.

    A/B  : the LAST \\boxed{...} in the text (the runner's own extraction rule).
    C/C' : the schema's answer field (the contract *forbids* \\boxed for planner
           and reviewer, so those roles structurally have no answer channel);
           \\boxed is kept only as a fallback for contract-violating text.
    """
    if arm in ("C", "Cp"):
        obj = None
        if extract_json_object is not None:
            try:
                obj, _ = extract_json_object(text or "")
            except Exception:
                obj = None
        if isinstance(obj, dict):
            if role == "executor" and isinstance(obj.get("answer"), str):
                return obj["answer"].strip() or None
            if role in ("planner", "reviewer"):
                return None                      # no answer channel by contract
        b = boxed_all(text)
        return b[-1].strip() if b else None
    b = boxed_all(text)
    return b[-1].strip() if b else None


# ---------------------------------------------------------- pairwise metrics
def pair_metrics(x: str, y: str) -> dict:
    """Level-2 similarity between two whitespace-normalized texts.

    ratio        difflib SequenceMatcher, character level, autojunk OFF
    containment  matched chars / len(shorter)   -- NOT capped by length skew
    jaccard      content-token set Jaccard
    overlap      content-token overlap coefficient |A&B| / min(|A|,|B|)
    """
    xc, yc = x[:CHAR_CAP], y[:CHAR_CAP]
    sm = difflib.SequenceMatcher(None, xc, yc, autojunk=False)
    matched = sum(b.size for b in sm.get_matching_blocks())
    denom = len(xc) + len(yc)
    ratio = (2.0 * matched / denom) if denom else 1.0
    shorter = min(len(xc), len(yc))
    contain = (matched / shorter) if shorter else 1.0
    a, b = set(content_tokens(x)), set(content_tokens(y))
    inter = len(a & b)
    jac = inter / len(a | b) if (a or b) else 1.0
    ov = inter / min(len(a), len(b)) if (a and b) else (1.0 if not (a or b) else 0.0)
    return dict(ratio=ratio, containment=min(contain, 1.0), jaccard=jac, overlap=ov,
                capped=int(len(x) > CHAR_CAP or len(y) > CHAR_CAP))


# ---------------------------------------------------------------- worker job
def analyse_cycle(job: dict) -> dict:
    """job carries arm, actor, uid, correct, collapse flags and the 3 texts."""
    arm = job["arm"]
    P, E, R = job["p_text"], job["e_text"], job["r_text"]
    hist_before_e = job["hist_e"]     # concatenated earlier text (all-cycles mode)
    hist_before_r = job["hist_r"]
    o = {k: job[k] for k in ("arm", "actor", "problem_uid", "correct", "correct0",
                             "traj_collapse", "cycle_collapse", "cycle_collapse_all3",
                             "cycle_key", "n_msgs", "rounds_used", "is_first_cycle",
                             "n_unlogged")}
    nP, nE, nR = wsnorm(P), wsnorm(E), wsnorm(R)
    o["len_P"], o["len_E"], o["len_R"] = len(nP), len(nE), len(nR)

    # ---- LEVEL 2 -----------------------------------------------------------
    for tag, (x, y) in (("PE", (nP, nE)), ("PR", (nP, nR)), ("ER", (nE, nR))):
        m = pair_metrics(x, y)
        for k, v in m.items():
            o[f"{k}_{tag}"] = v
    o["ratio_max"] = max(o["ratio_PE"], o["ratio_PR"], o["ratio_ER"])
    o["jaccard_max"] = max(o["jaccard_PE"], o["jaccard_PR"], o["jaccard_ER"])

    # ---- LEVEL 3.1 new evaluated equations ---------------------------------
    eP, eE, eR = eq_tokens(P), eq_tokens(E), eq_tokens(R)
    sP, sE = set(eP), set(eE)
    o["eq_P"], o["eq_E"], o["eq_R"] = len(eP), len(eE), len(eR)
    o["eq_P_distinct"] = len(sP)
    o["new_eq_E_distinct"] = len(sE - sP)
    o["new_eq_E_instances"] = sum(1 for t in eE if t not in sP)
    o["new_eq_E_frac"] = (o["new_eq_E_instances"] / len(eE)) if eE else np.nan
    prior_R = sP | sE
    o["new_eq_R_distinct"] = len(set(eR) - prior_R)
    o["new_eq_R_instances"] = sum(1 for t in eR if t not in prior_R)
    o["new_eq_R_frac"] = (o["new_eq_R_instances"] / len(eR)) if eR else np.nan

    # ---- LEVEL 3.2 new content-token rate ----------------------------------
    tP, tE, tR = content_tokens(P), content_tokens(E), content_tokens(R)
    setP, setE = set(tP), set(tE)
    o["ntok_P"], o["ntok_E"], o["ntok_R"] = len(tP), len(tE), len(tR)
    o["new_tok_E"] = (sum(1 for w in tE if w not in setP) / len(tE)) if tE else np.nan
    o["new_tok_E_type"] = (len(setE - setP) / len(setE)) if setE else np.nan
    priorR = setP | setE
    o["new_tok_R"] = (sum(1 for w in tR if w not in priorR) / len(tR)) if tR else np.nan
    o["new_tok_R_type"] = (len(set(tR) - priorR) / len(set(tR))) if tR else np.nan
    # full-history variant (only differs for cycles after the first)
    if hist_before_e:
        hE = set(content_tokens(hist_before_e))
        o["new_tok_E_hist"] = (sum(1 for w in tE if w not in hE) / len(tE)) if tE else np.nan
    else:
        o["new_tok_E_hist"] = o["new_tok_E"]
    if hist_before_r:
        hR = set(content_tokens(hist_before_r))
        o["new_tok_R_hist"] = (sum(1 for w in tR if w not in hR) / len(tR)) if tR else np.nan
    else:
        o["new_tok_R_hist"] = o["new_tok_R"]

    # ---- LEVEL 3.3 answer change -------------------------------------------
    aP = norm_answer(extract_answer(arm, "planner", P))
    aE = norm_answer(extract_answer(arm, "executor", E))
    aR = norm_answer(extract_answer(arm, "reviewer", R))
    o["ans_P"], o["ans_E"], o["ans_R"] = aP, aE, aR
    o["has_ans_P"], o["has_ans_E"], o["has_ans_R"] = int(aP is not None), int(aE is not None), int(aR is not None)
    # tri-state comparison: absence is a distinct value, so "planner had none,
    # executor produced one" counts as the executor contributing an answer.
    o["ans_differs_E"] = int(aP != aE)
    o["ans_differs_R"] = int(aE != aR)
    o["ans_both_E"] = int(aP is not None and aE is not None)
    o["ans_both_R"] = int(aE is not None and aR is not None)
    o["ans_differs_E_bothpresent"] = (int(aP != aE) if o["ans_both_E"] else np.nan)
    o["ans_differs_R_bothpresent"] = (int(aE != aR) if o["ans_both_R"] else np.nan)
    o["ans_introduced_E"] = int(aP is None and aE is not None)
    o["ans_introduced_R"] = int(aE is None and aR is not None)

    # ---- LEVEL 3.4 critique content ----------------------------------------
    cR = set(w.lower() for w in CRITIQUE.findall(R or ""))
    cPE = set(w.lower() for w in CRITIQUE.findall((P or "") + " " + (E or "")))
    o["critique_terms_R"] = len(cR)
    o["has_critique_R"] = int(bool(cR))
    o["novel_critique_R"] = len(cR - cPE)
    o["has_novel_critique_R"] = int(bool(cR - cPE))

    # ---- INERTNESS ---------------------------------------------------------
    o["exec_inert"] = int(o["new_eq_E_distinct"] == 0 and o["ans_differs_E"] == 0)
    o["rev_inert"] = int(o["new_eq_R_distinct"] == 0 and o["ans_differs_R"] == 0)
    # DESIGN-NEUTRAL variants.  The answer clause is NOT comparable across arms:
    # Arm A's planner prompt forbids an answer (0.0/17.3% carry one), Arm B tells
    # every agent to emit one (~90-98%), Arm C forbids it by schema for planner
    # and reviewer (0%).  So a no-answer-change is near-automatic in A and C and
    # near-impossible in B, for reasons of prompt design, not behaviour.  These
    # variants drop that clause and use only channels every arm can populate.
    o["exec_inert_eqonly"] = int(o["new_eq_E_distinct"] == 0)
    o["rev_inert_eqonly"] = int(o["new_eq_R_distinct"] == 0)
    o["exec_inert_tok10"] = int((o["new_tok_E"] if o["new_tok_E"] == o["new_tok_E"] else 0) < 0.10)
    o["rev_inert_tok10"] = int((o["new_tok_R"] if o["new_tok_R"] == o["new_tok_R"] else 0) < 0.10)
    o["exec_inert_neutral"] = int(o["exec_inert_eqonly"] == 1 and o["exec_inert_tok10"] == 1)
    o["rev_inert_neutral"] = int(o["rev_inert_eqonly"] == 1 and o["rev_inert_tok10"] == 1)
    o["exec_inert_strong"] = int(o["exec_inert"] == 1 and (o["new_tok_E"] or 0) < 0.05)
    o["rev_inert_strong"] = int(o["rev_inert"] == 1 and (o["new_tok_R"] or 0) < 0.05
                                and o["has_novel_critique_R"] == 0)
    o["rev_inert_3c"] = int(o["rev_inert"] == 1 and o["has_novel_critique_R"] == 0)
    return o


# ------------------------------------------------------------------- loading
def iter_rows(paths):
    for p in paths:
        files = [p] if os.path.isfile(p) else sorted(glob.glob(os.path.join(p, "*.jsonl")))
        for f in files:
            if "BUG" in os.path.basename(f):
                print(f"  SKIP quarantined: {os.path.basename(f)}")
                continue
            print(f"  reading {os.path.basename(f)}")
            with open(f) as fh:
                for ln in fh:
                    ln = ln.strip()
                    if not ln:
                        continue
                    try:
                        yield json.loads(ln)
                    except json.JSONDecodeError:
                        pass


def build_jobs(paths, reservoir_n=500):
    """Stream trajectories -> cycle jobs.  Also fill a reservoir for the null."""
    jobs, res = [], collections.defaultdict(list)
    stats = collections.Counter()
    for d in iter_rows(paths):
        arm = d.get("arm")
        actor = (d.get("actor_model") or "").split("/")[-1]
        uid = d.get("problem_uid")
        stats["trajectories"] += 1
        msgs = d.get("messages") or []
        # accepted role messages, in file order (= chronological)
        acc = []
        for m in msgs:
            if m.get("role") not in ROLES:
                continue
            v = m.get("validation") or {}
            if v.get("ok", True) is False:
                stats["rejected_msgs_excluded"] += 1
                continue
            acc.append(m)
        # trajectory-level exact collapse, matching x2's definition
        h = [m.get("response_sha256_12") for m in (d.get("messages") or [])
             if m.get("role") in ROLES and m.get("response_sha256_12")]
        traj_collapse = int(len(h) >= 2 and len(set(h)) < len(h))

        by_cycle = collections.OrderedDict()
        for m in acc:
            by_cycle.setdefault((m.get("outer_round"), m.get("inner_round")), {})
            by_cycle[(m.get("outer_round"), m.get("inner_round"))].setdefault(m["role"], m)
        running_hist = []
        first_done = False
        for ck, g in by_cycle.items():
            if not all(r in g for r in ROLES):
                for r in ROLES:
                    if r in g:
                        running_hist.append(g[r].get("text") or "")
                stats["incomplete_cycles"] += 1
                continue
            P, E, R = (g[r].get("text") or "" for r in ROLES)
            hh = [m.get("response_sha256_12") for m in (g[r] for r in ROLES)]
            # visible chars per second of latency; far below the corpus norm means
            # the model spent that time on tokens the runner never logged.
            n_unlogged = 0
            for r in ROLES:
                lat = g[r].get("latency_s") or 0.0
                if lat > 0.2 and len(g[r].get("text") or "") / lat < 20.0:
                    n_unlogged += 1
            jobs.append(dict(
                arm=arm, actor=actor, problem_uid=uid,
                correct=d.get("correct"),
                correct0=(0 if d.get("correct") is None else int(d.get("correct"))),
                traj_collapse=traj_collapse,
                cycle_collapse=int(len(set(hh)) < 3),
                cycle_collapse_all3=int(len(set(hh)) == 1),
                cycle_key=f"{ck[0]}.{ck[1]}", n_unlogged=n_unlogged,
                n_msgs=len(msgs), rounds_used=d.get("rounds_used"),
                is_first_cycle=int(not first_done),
                p_text=P, e_text=E, r_text=R,
                hist_e=" ".join(running_hist + [P]) if running_hist else "",
                hist_r=" ".join(running_hist + [P, E]) if running_hist else "",
            ))
            first_done = True
            running_hist += [P, E, R]
            stats["complete_cycles"] += 1
            for r, t in zip(ROLES, (P, E, R)):
                k = (arm, actor, r)
                if len(res[k]) < reservoir_n:
                    res[k].append((uid, wsnorm(t)))
    return jobs, res, stats


# ----------------------------------------------------------------- inference
def cluster_boot(df, col, cluster="problem_uid", n=N_BOOT, rng=None):
    """Mean with a cluster (by problem) bootstrap CI."""
    rng = rng or RNG
    d = df[[cluster, col]].dropna()
    if len(d) < 3:
        return (np.nan, np.nan, np.nan, len(d))
    groups = [g[col].to_numpy(float) for _, g in d.groupby(cluster, sort=False)]
    k = len(groups)
    if k < 3:
        v = d[col].to_numpy(float)
        return (v.mean(), np.nan, np.nan, len(d))
    sums = np.array([g.sum() for g in groups])
    cnts = np.array([len(g) for g in groups], float)
    idx = rng.integers(0, k, size=(n, k))
    bs = sums[idx].sum(1) / cnts[idx].sum(1)
    return (float(d[col].mean()), float(np.percentile(bs, 2.5)),
            float(np.percentile(bs, 97.5)), int(len(d)))


def summarise(df, cols, keys=("arm", "actor")):
    rows = []
    for k, g in df.groupby(list(keys), sort=True):
        k = k if isinstance(k, tuple) else (k,)
        row = dict(zip(keys, k), n=len(g))
        for c in cols:
            m, lo, hi, nn = cluster_boot(g, c)
            row[f"{c}_mean"] = m
            row[f"{c}_lo"] = lo
            row[f"{c}_hi"] = hi
            row[f"{c}_median"] = g[c].median()
            row[f"{c}_n"] = nn
        rows.append(row)
    return pd.DataFrame(rows)


def paired_contrast(df, col, a="A", b="B", n=N_BOOT):
    """Paired (by problem_uid) A-minus-B contrast within actor, cluster boot."""
    out = []
    for actor, g in df.groupby("actor"):
        w = g.pivot_table(index="problem_uid", columns="arm", values=col, aggfunc="first")
        if a not in w or b not in w:
            continue
        d = (w[a] - w[b]).dropna()
        if len(d) < 10:
            continue
        v = d.to_numpy(float)
        idx = RNG.integers(0, len(v), size=(n, len(v)))
        bs = v[idx].mean(1)
        lo, hi = np.percentile(bs, [2.5, 97.5])
        out.append(dict(actor=actor, metric=col, arm_a=a, arm_b=b, n_pairs=len(v),
                        mean_a=float(w[a].dropna().mean()), mean_b=float(w[b].dropna().mean()),
                        diff=float(v.mean()), lo=float(lo), hi=float(hi),
                        sig=int(not (lo < 0 < hi))))
    return out


# --------------------------------------------------------------------- nulls
def cross_problem_null(res, n_pairs=300):
    """Same arm/actor/role-pair, DIFFERENT problem.  The interpretive floor."""
    rng = random.Random(4242)
    rows = []
    seen = set()
    for (arm, actor, r1) in list(res.keys()):
        for r2 in ROLES:
            key = (arm, actor, tuple(sorted((r1, r2))))
            if r1 == r2 or key in seen:
                continue
            seen.add(key)
            A, B = res.get((arm, actor, r1), []), res.get((arm, actor, r2), [])
            if len(A) < 20 or len(B) < 20:
                continue
            got = 0
            tries = 0
            while got < n_pairs and tries < n_pairs * 8:
                tries += 1
                u1, t1 = rng.choice(A)
                u2, t2 = rng.choice(B)
                if u1 == u2 or not t1 or not t2:
                    continue
                m = pair_metrics(t1, t2)
                rows.append(dict(arm=arm, actor=actor, pair="".join(
                    sorted((r1[0].upper(), r2[0].upper()))), **m))
                got += 1
    return pd.DataFrame(rows)


# -------------------------------------------------------------------- output
def h(t):
    print("\n" + "=" * 92)
    print(t)
    print("=" * 92)


def selftest():
    """Every primitive must be shown to FAIL on a case it should reject.

    A check only ever run on inputs it is guaranteed to pass detects nothing.
    """
    fails = []

    def chk(ok, label, detail=""):
        print(("  OK   " if ok else "  FAIL ") + label + ("  " + detail if detail else ""))
        if not ok:
            fails.append(label)

    print("boxed_all (must unwrap nesting, and must find nothing when absent):")
    chk(boxed_all(r"\boxed{\dfrac{1}{27}}") == [r"\dfrac{1}{27}"], "nested unwrap")
    chk(boxed_all(r"a \boxed{5} b \boxed{\frac{a}{b}}") == ["5", r"\frac{a}{b}"], "two boxes")
    chk(boxed_all("no box here") == [], "NEGATIVE: absent -> []")
    chk(boxed_all(r"\boxed {7}") == ["7"], "space before brace")

    print("norm_answer (must equate notation variants, must SEPARATE different values):")
    for a, b, exp, why in [
            (r"\frac{1}{27}", r"\frac{12}{7}", False, "NEGATIVE: digit-regroup collision"),
            (r"x^{10}", r"x^{1}0", False, "NEGATIVE: exponent collision"),
            ("674", "675", False, "NEGATIVE: distinct numbers"),
            (r"\frac{1}{27}", r"\dfrac{1}{27}", True, "dfrac equivalence"),
            (r"\frac23", r"\frac{2}{3}", True, "optional-brace equivalence"),
            (r"-\frac14", r"-\frac{1}{4}", True, "optional-brace equivalence 2"),
            (r"\left(1,2\right)", "(1,2)", True, "left/right"),
            (r"\sin^{2}1^\circ", r"\sin^2 1^\circ", True, "exponent braces")]:
        chk((norm_answer(a) == norm_answer(b)) == exp, why,
            f"{norm_answer(a)!r} vs {norm_answer(b)!r}")

    print("eq_tokens (must catch signed/decimal, must NOT catch a symbolic rhs):")
    chk(eq_tokens("x = 5 and y=-3.25, z = a+b, total= 100") == ["=5", "=-3.25", "=100"],
        "numeric only")
    chk(eq_tokens("z = a + b") == [], "NEGATIVE: symbolic rhs ignored")

    print("pair_metrics (identical -> 1, disjoint -> low, containment not length-capped):")
    i = pair_metrics("abc def ghi", "abc def ghi")
    d = pair_metrics("aaa bbb", "xxx yyy")
    c = pair_metrics("hello world", "hello world " + "filler " * 200)
    chk(i["ratio"] == 1.0 and i["jaccard"] == 1.0, "identical -> 1.000")
    chk(d["jaccard"] == 0.0 and d["ratio"] < 0.3, "NEGATIVE: disjoint -> ~0",
        f"ratio={d['ratio']:.3f}")
    chk(c["ratio"] < 0.05 and c["containment"] == 1.0,
        "length-skew: ratio collapses but containment stays 1",
        f"ratio={c['ratio']:.3f} cont={c['containment']:.3f}")

    print("content_tokens (stopwords dropped, content kept):")
    chk("the" not in content_tokens("the answer") and "answer" in content_tokens("the answer"),
        "stopword filter")

    print(f"\n  {'ALL PASS' if not fails else str(len(fails)) + ' FAILURES: ' + str(fails)}")
    return not fails


def main(paths, workers=None, quick=0):
    print("X3 functional / semantic collapse validation")
    print("  sentence-transformers: NOT INSTALLED -> Level 2 uses difflib + Jaccard only.")
    h("-1. PRIMITIVE SELF-TEST (each check must also reject a case it should reject)")
    if not selftest():
        print("  ABORTING: a measurement primitive is broken.")
        return
    jobs, res, stats = build_jobs(paths)
    if quick:
        random.Random(1).shuffle(jobs)
        jobs = jobs[:quick]
    print(f"\n  {dict(stats)}")
    print(f"  cycle-jobs to score: {len(jobs)}")

    workers = workers or max(1, min(12, (os.cpu_count() or 4) - 2))
    if workers > 1:
        with mp.Pool(workers) as pool:
            rows = pool.map(analyse_cycle, jobs, chunksize=16)
    else:
        rows = [analyse_cycle(j) for j in jobs]
    df = pd.DataFrame(rows)
    df.to_csv(os.path.join(OUT, "x3_per_cycle.csv"), index=False)
    first = df[df.is_first_cycle == 1].copy()
    first.to_csv(os.path.join(OUT, "x3_per_trajectory.csv"), index=False)
    print(f"  scored cycles={len(df)}  first-cycle rows={len(first)}  "
          f"difflib length-capped pairs={int(df[['capped_PE','capped_PR','capped_ER']].sum().sum())}")

    # =================================================================== ctrl
    h("0. CONTROLS -- does the instrument discriminate?")
    ident = pair_metrics("the value is = 5 and x=3", "the value is = 5 and x=3")
    diffr = pair_metrics("the value is = 5 and x=3", "a totally unrelated sentence about frogs")
    print(f"  positive control  identical text   ratio={ident['ratio']:.3f} "
          f"jaccard={ident['jaccard']:.3f}   (expect 1.000/1.000)")
    print(f"  negative control  unrelated text   ratio={diffr['ratio']:.3f} "
          f"jaccard={diffr['jaccard']:.3f}")
    bc = df[df.cycle_collapse_all3 == 1]
    print(f"\n  ON-CORPUS positive control: cycles whose 3 responses are BYTE-IDENTICAL "
          f"(n={len(bc)})")
    if len(bc):
        print(f"    ratio_PE mean={bc.ratio_PE.mean():.4f} min={bc.ratio_PE.min():.4f}   "
              f"jaccard_PE mean={bc.jaccard_PE.mean():.4f} min={bc.jaccard_PE.min():.4f}")
        print("    -> if these are not ~1.000 the similarity metric is broken.")
    ctrl = pd.DataFrame([dict(control="synthetic_identical", **ident),
                         dict(control="synthetic_unrelated", **diffr),
                         dict(control="corpus_byte_identical_cycles",
                              ratio=bc.ratio_PE.mean() if len(bc) else np.nan,
                              containment=bc.containment_PE.mean() if len(bc) else np.nan,
                              jaccard=bc.jaccard_PE.mean() if len(bc) else np.nan,
                              overlap=bc.overlap_PE.mean() if len(bc) else np.nan,
                              capped=len(bc))])
    ctrl.to_csv(os.path.join(OUT, "x3_controls.csv"), index=False)

    # ============================================================== LEVEL TWO
    h("1. LEVEL 2 -- SEMANTIC SIMILARITY between the three role outputs "
      "(first complete accepted cycle)")
    print("   ratio = difflib char ratio (CAPPED by length skew); containment = matched/len(shorter)")
    l2cols = [f"{m}_{p}" for p in ("PE", "PR", "ER")
              for m in ("ratio", "containment", "jaccard", "overlap")]
    L2 = summarise(first, l2cols)
    L2.to_csv(os.path.join(OUT, "x3_level2_similarity.csv"), index=False)
    disp = L2[["arm", "actor", "n"] + [f"{m}_{p}_mean" for p in ("PE", "PR", "ER")
                                       for m in ("ratio", "jaccard")]]
    disp.columns = ["arm", "actor", "n", "ratio_PE", "jac_PE", "ratio_PR", "jac_PR",
                    "ratio_ER", "jac_ER"]
    print(disp.round(3).to_string(index=False))
    print("\n   length-robust view (containment = matched chars / shorter text):")
    d2 = L2[["arm", "actor"] + [f"containment_{p}_mean" for p in ("PE", "PR", "ER")]
            + [f"overlap_{p}_mean" for p in ("PE", "PR", "ER")]]
    d2.columns = ["arm", "actor", "cont_PE", "cont_PR", "cont_ER",
                  "ovl_PE", "ovl_PR", "ovl_ER"]
    print(d2.round(3).to_string(index=False))
    print("\n   median text length per role (chars, whitespace-normalized) -- the cap driver:")
    print(first.groupby(["arm", "actor"])[["len_P", "len_E", "len_R"]].median().to_string())

    h("2. LEVEL 2 NULL -- cross-problem pairs (same arm/actor/roles, DIFFERENT problem)")
    NUL = cross_problem_null(res)
    if len(NUL):
        g = NUL.groupby(["arm", "actor", "pair"])[["ratio", "containment", "jaccard", "overlap"]].mean()
        g.to_csv(os.path.join(OUT, "x3_level2_null.csv"))
        print(g.round(3).to_string())
        print("\n   Read every observed similarity against its own row here.")
    else:
        print("   (insufficient reservoir)")

    # tail of the similarity distribution: how many cycles are near-duplicates
    h("3. NEAR-DUPLICATE RATE -- fraction of cycles with any role pair above a threshold")
    nd = []
    for k, g in first.groupby(["arm", "actor"]):
        row = dict(arm=k[0], actor=k[1], n=len(g),
                   exact_byte_any2=float((g.cycle_collapse == 1).mean()),
                   exact_byte_all3=float((g.cycle_collapse_all3 == 1).mean()))
        for thr in (0.95, 0.9, 0.8, 0.5):
            row[f"ratio_max>={thr}"] = float((g.ratio_max >= thr).mean())
        for thr in (0.9, 0.8, 0.5):
            row[f"jac_max>={thr}"] = float((g.jaccard_max >= thr).mean())
        nd.append(row)
    ND = pd.DataFrame(nd)
    ND.to_csv(os.path.join(OUT, "x3_nearduplicate.csv"), index=False)
    print(ND.round(3).to_string(index=False))

    # ============================================================ LEVEL THREE
    h("4. LEVEL 3 -- FUNCTIONAL CONTRIBUTION (first complete accepted cycle)")
    l3cols = ["new_eq_E_distinct", "new_eq_E_frac", "new_tok_E", "ans_differs_E",
              "new_eq_R_distinct", "new_eq_R_frac", "new_tok_R", "ans_differs_R",
              "has_critique_R", "has_novel_critique_R"]
    L3 = summarise(first, l3cols)
    L3.to_csv(os.path.join(OUT, "x3_level3_metrics.csv"), index=False)
    print("  EXECUTOR contribution beyond the planner:")
    e = L3[["arm", "actor", "n", "new_eq_E_distinct_mean", "new_eq_E_distinct_lo",
            "new_eq_E_distinct_hi", "new_eq_E_distinct_median", "new_tok_E_mean",
            "new_tok_E_lo", "new_tok_E_hi", "ans_differs_E_mean"]]
    e.columns = ["arm", "actor", "n", "newEq_mean", "lo", "hi", "newEq_med",
                 "newTok_mean", "tlo", "thi", "ansChg"]
    print(e.round(3).to_string(index=False))
    print("\n  REVIEWER contribution beyond planner+executor:")
    r = L3[["arm", "actor", "n", "new_eq_R_distinct_mean", "new_eq_R_distinct_lo",
            "new_eq_R_distinct_hi", "new_eq_R_distinct_median", "new_tok_R_mean",
            "new_tok_R_lo", "new_tok_R_hi", "ans_differs_R_mean",
            "has_critique_R_mean", "has_novel_critique_R_mean"]]
    r.columns = ["arm", "actor", "n", "newEq_mean", "lo", "hi", "newEq_med",
                 "newTok_mean", "tlo", "thi", "ansChg", "critique", "novelCritique"]
    print(r.round(3).to_string(index=False))

    h("5. ANSWER CHANNEL -- coverage first, then change rate (the denominators matter)")
    ac = first.groupby(["arm", "actor"]).agg(
        n=("has_ans_P", "size"),
        hasAns_P=("has_ans_P", "mean"), hasAns_E=("has_ans_E", "mean"),
        hasAns_R=("has_ans_R", "mean"),
        E_differs_tristate=("ans_differs_E", "mean"),
        E_bothpresent_n=("ans_both_E", "sum"),
        E_differs_bothpresent=("ans_differs_E_bothpresent", "mean"),
        E_introduced=("ans_introduced_E", "mean"),
        R_differs_tristate=("ans_differs_R", "mean"),
        R_bothpresent_n=("ans_both_R", "sum"),
        R_differs_bothpresent=("ans_differs_R_bothpresent", "mean"),
        R_introduced=("ans_introduced_R", "mean"))
    ac.to_csv(os.path.join(OUT, "x3_answer_channel.csv"))
    print(ac.round(3).to_string())
    print("\n  NOTE Arm A's planner prompt FORBIDS producing an answer and Arm C's")
    print("       schema forbids it architecturally, so hasAns_P is a design fact,")
    print("       not a behaviour.  Read E_differs_bothpresent only where n is large.")

    h("6. FUNCTIONAL INERTNESS (zero new distinct evaluated equations AND no answer change)")
    icols = ["exec_inert", "rev_inert", "exec_inert_strong", "rev_inert_strong", "rev_inert_3c"]
    IN = summarise(first, icols)
    IN.to_csv(os.path.join(OUT, "x3_inertness.csv"), index=False)
    p = IN[["arm", "actor", "n"] + [f"{c}_mean" for c in icols]
           + ["exec_inert_lo", "exec_inert_hi", "rev_inert_lo", "rev_inert_hi"]]
    p.columns = ["arm", "actor", "n", "execInert", "revInert", "execInert_strong",
                 "revInert_strong", "revInert_3c", "eLo", "eHi", "rLo", "rHi"]
    print(p.round(3).to_string(index=False))

    print("\n  ---- DESIGN-NEUTRAL inertness (answer clause DROPPED) ----")
    print("  The answer clause is not comparable across arms (see section 5): Arm A's")
    print("  planner is told not to answer, Arm B's is told to, Arm C's cannot.  These")
    print("  variants use only the equation and token channels, which every arm has.")
    ncols = ["exec_inert_eqonly", "rev_inert_eqonly", "exec_inert_tok10",
             "rev_inert_tok10", "exec_inert_neutral", "rev_inert_neutral"]
    NI = summarise(first, ncols)
    NI.to_csv(os.path.join(OUT, "x3_inertness_neutral.csv"), index=False)
    q = NI[["arm", "actor", "n"] + [f"{c}_mean" for c in ncols]
           + ["exec_inert_eqonly_lo", "exec_inert_eqonly_hi"]]
    q.columns = ["arm", "actor", "n", "E_0newEq", "R_0newEq", "E_tok<10%", "R_tok<10%",
                 "E_neutralInert", "R_neutralInert", "E_0newEq_lo", "E_0newEq_hi"]
    print(q.round(3).to_string(index=False))

    h("7. ARM A vs ARM B -- the comparison the paper's claim rests on (paired by problem)")
    pc = []
    for c in ["exec_inert", "rev_inert", "exec_inert_eqonly", "rev_inert_eqonly",
              "exec_inert_neutral", "rev_inert_neutral",
              "new_eq_E_distinct", "new_tok_E",
              "ans_differs_E", "new_eq_R_distinct", "new_tok_R", "ans_differs_R",
              "has_novel_critique_R", "ratio_max", "jaccard_max",
              "containment_PE", "containment_ER"]:
        pc += paired_contrast(first, c, "A", "B")
    PC = pd.DataFrame(pc)
    PC.to_csv(os.path.join(OUT, "x3_AB_paired.csv"), index=False)
    if len(PC):
        print(PC.round(4).to_string(index=False))
        print("\n  sig=1 means the 95% cluster-bootstrap CI on the paired A-B difference excludes 0.")
    # also A vs C for context
    pc2 = []
    for c in ["exec_inert", "rev_inert", "ratio_max", "new_tok_E"]:
        pc2 += paired_contrast(first, c, "A", "C")
    if pc2:
        print("\n  (context) A vs C:")
        print(pd.DataFrame(pc2).round(4).to_string(index=False))

    h("8. CROSS-TAB -- inertness vs exact byte-collapse, and vs correctness")
    xt = []
    for k, g in first.groupby(["arm", "actor"]):
        for flagname, flag in (("exec_inert", g.exec_inert), ("rev_inert", g.rev_inert)):
            for cv in (0, 1):
                s = g[flag == cv]
                if not len(s):
                    continue
                xt.append(dict(arm=k[0], actor=k[1], metric=flagname, value=cv, n=len(s),
                               acc_prereg=float(s.correct0.mean()),
                               acc_dropNone=float(s.correct.dropna().mean())
                               if s.correct.notna().any() else np.nan,
                               collapse_rate=float(s.cycle_collapse.mean()),
                               traj_collapse_rate=float(s.traj_collapse.mean())))
    XT = pd.DataFrame(xt)
    XT.to_csv(os.path.join(OUT, "x3_crosstab.csv"), index=False)
    print(XT.round(3).to_string(index=False))

    print("\n  inertness -> accuracy, as a paired-by-nothing risk difference with cluster CI:")
    rd = []
    for k, g in first.groupby(["arm", "actor"]):
        for flagname in ("exec_inert", "rev_inert"):
            a = g[g[flagname] == 1]
            b = g[g[flagname] == 0]
            if len(a) < 20 or len(b) < 20:
                continue
            ma, _, _, _ = cluster_boot(a, "correct0")
            mb, _, _, _ = cluster_boot(b, "correct0")
            # bootstrap the difference by resampling problems within each stratum
            va, vb = a.correct0.to_numpy(float), b.correct0.to_numpy(float)
            ia = RNG.integers(0, len(va), size=(N_BOOT, len(va)))
            ib = RNG.integers(0, len(vb), size=(N_BOOT, len(vb)))
            bs = va[ia].mean(1) - vb[ib].mean(1)
            lo, hi = np.percentile(bs, [2.5, 97.5])
            rd.append(dict(arm=k[0], actor=k[1], flag=flagname, n_inert=len(a),
                           n_active=len(b), acc_inert=ma, acc_active=mb,
                           diff=ma - mb, lo=lo, hi=hi, sig=int(not (lo < 0 < hi))))
    RD = pd.DataFrame(rd)
    RD.to_csv(os.path.join(OUT, "x3_inert_vs_correct.csv"), index=False)
    if len(RD):
        print(RD.round(3).to_string(index=False))

    h("8b. DIFFICULTY CONFOUND -- the same contrasts stratified on problem difficulty")
    print("  A collapsed/inert trajectory may simply be an EASY problem.  Difficulty is")
    print("  the mean correctness of that problem in the OTHER arms (never the arm under")
    print("  test), so the adjustment is not circular.  Weighted over 10 difficulty strata.")
    diffic = {}
    for arm in first.arm.unique():
        others = first[first.arm != arm]
        if len(others):
            diffic[arm] = others.groupby("problem_uid").correct0.mean()
    srows = []
    for k, g in first.groupby(["arm", "actor"]):
        arm = k[0]
        if arm not in diffic:
            continue
        g = g.join(diffic[arm].rename("difficulty"), on="problem_uid").dropna(subset=["difficulty"])
        for flagname in ("cycle_collapse", "exec_inert", "rev_inert",
                         "exec_inert_eqonly", "exec_inert_neutral"):
            a, b = g[g[flagname] == 1], g[g[flagname] == 0]
            if len(a) < 25 or len(b) < 25:
                continue
            raw = a.correct0.mean() - b.correct0.mean()
            gg = g.copy()
            gg["strat"] = pd.qcut(gg.difficulty.rank(method="first"), 10, labels=False)

            def strat_diff(frame):
                parts, wts = [], []
                for _, hh in frame.groupby("strat"):
                    x, y = hh[hh[flagname] == 1].correct0, hh[hh[flagname] == 0].correct0
                    if len(x) < 2 or len(y) < 2:
                        continue
                    parts.append(x.mean() - y.mean())
                    wts.append(len(hh))
                return float(np.average(parts, weights=wts)) if parts else np.nan

            pt = strat_diff(gg)
            bs = []
            for _ in range(600):
                v = strat_diff(gg.sample(len(gg), replace=True,
                                         random_state=int(RNG.integers(1e9))))
                if not np.isnan(v):
                    bs.append(v)
            lo, hi = (np.percentile(bs, [2.5, 97.5]) if len(bs) > 50 else (np.nan, np.nan))
            srows.append(dict(arm=arm, actor=k[1], flag=flagname, n=len(gg),
                              n_flagged=int(len(a)),
                              difficulty_flagged=float(a.join(
                                  diffic[arm].rename("d"), on="problem_uid").d.mean()),
                              difficulty_not=float(b.join(
                                  diffic[arm].rename("d"), on="problem_uid").d.mean()),
                              raw_diff=raw, strat_diff=pt, lo=lo, hi=hi,
                              sig=int(not (lo < 0 < hi)) if not np.isnan(lo) else 0))
    SR = pd.DataFrame(srows)
    SR.to_csv(os.path.join(OUT, "x3_difficulty_stratified.csv"), index=False)
    if len(SR):
        print(SR.round(3).to_string(index=False))
        print("\n  A large gap between raw_diff and strat_diff means the raw association was")
        print("  mostly the difficulty of the problems, not an effect of collapse/inertness.")

    h("8a2. COLLAPSE DECOMPOSITION -- within-cycle role collapse vs same-role repetition")
    print("  x2's collapse flag counts ANY duplicate sha among a trajectory's role messages,")
    print("  which pools two different mechanisms:")
    print("    within-cycle  : two DIFFERENT roles, SAME turn, identical bytes = role collapse")
    print("    same-role rpt : ONE role repeating itself across rounds = a stuck loop")
    dec = []
    for k, g in df.groupby(["arm", "actor"]):
        byt = g.groupby("problem_uid")
        n = g.problem_uid.nunique()
        wfirst = g[g.is_first_cycle == 1].cycle_collapse.mean()
        wany = byt.cycle_collapse.max().mean()
        dec.append(dict(arm=k[0], actor=k[1], n_traj=n,
                        within_cycle_first=wfirst, within_cycle_any=wany,
                        x2_traj_flag=byt.traj_collapse.max().mean()))
    DEC = pd.DataFrame(dec)
    DEC["same_role_repeat_implied"] = (DEC.x2_traj_flag - DEC.within_cycle_any).clip(lower=0)
    DEC.to_csv(os.path.join(OUT, "x3_collapse_decomposition.csv"), index=False)
    print()
    print(DEC.round(3).to_string(index=False))
    print("\n  Where within_cycle_any is ~0 but x2_traj_flag is not, the headline collapse")
    print("  number for that cell is same-role repetition, NOT role collapse.")

    h("8c. MEASUREMENT ARTIFACT CHECK -- unlogged reasoning tokens")
    print("  runner.py logs message.content and falls back to message.reasoning ONLY when")
    print("  content is empty.  gpt-oss-120b is a reasoning model, so a SHORT content with")
    print("  a long hidden reasoning trace is logged as the short content and the reasoning")
    print("  is discarded.  A message whose VISIBLE characters-per-second of latency is far")
    print("  below the corpus norm spent that time on tokens we never recorded.")
    ur = []
    for j in jobs:
        if not j["is_first_cycle"]:
            continue
        ur.append(dict(arm=j["arm"], actor=j["actor"],
                       cycle_collapse=j["cycle_collapse"],
                       n_unlogged=j.get("n_unlogged", 0),
                       all3_unlogged=int(j.get("n_unlogged", 0) == 3)))
    UR = pd.DataFrame(ur)
    if len(UR) and "n_unlogged" in UR:
        t = UR.groupby(["arm", "actor"]).agg(
            n=("n_unlogged", "size"),
            msgs_unlogged_frac=("n_unlogged", lambda s: s.sum() / (3 * len(s))),
            all3_unlogged=("all3_unlogged", "mean"))
        print()
        print(t.round(3).to_string())
        ct = UR.groupby(["arm", "actor", "cycle_collapse"]).all3_unlogged.agg(["size", "mean"])
        ct.to_csv(os.path.join(OUT, "x3_unlogged_reasoning.csv"))
        print("\n  all-3-messages-unlogged rate, split by whether the cycle byte-collapsed:")
        print(ct.round(3).to_string())
        print("\n  If collapse and unlogged reasoning coincide, the byte-identical outputs are")
        print("  the visible TIP of three separate hidden computations -- NOT three agents")
        print("  doing the same (or no) work.  Level-2/3 metrics see only the tip.")

    h("9. SENSITIVITY -- all complete accepted cycles, full-history novelty")
    allc = summarise(df, ["exec_inert", "rev_inert", "new_tok_E_hist", "new_tok_R_hist",
                          "ratio_max"])
    allc.to_csv(os.path.join(OUT, "x3_allcycles.csv"), index=False)
    s = allc[["arm", "actor", "n", "exec_inert_mean", "rev_inert_mean",
              "new_tok_E_hist_mean", "new_tok_R_hist_mean", "ratio_max_mean"]]
    print(s.round(3).to_string(index=False))

    print(f"\nwrote x3_* to {OUT}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--quick", type=int, default=0)
    ap.add_argument("--selftest", action="store_true", help="run primitive checks and exit")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(0 if selftest() else 1)
    main(a.paths, a.workers, a.quick)
