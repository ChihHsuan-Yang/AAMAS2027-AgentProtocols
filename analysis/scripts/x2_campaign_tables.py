"""X2: the tables the mock review requires, computed from runner JSONL.

Adds, over x1:
  - manipulation check on BOTH clauses (P2 = the redesignated check, P1a reported
    as a finding), computed on ACCEPTED messages only
  - attrition per arm x actor, with the pre-registered Nones->0 rule applied
    AND the drop-Nones version, because the two disagree
  - Arm C' context control: C'-C
  - enforcement rate from BOUNDARY violations only (D4/D6/D8 rule)
  - coercion / parse-repair rates, so a reader can see they did not do the work
  - Arm B collapse rate, per actor, stratified informative vs ceiling
"""
import argparse, glob, json, os, re, collections
import numpy as np, pandas as pd

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/results"
os.makedirs(OUT, exist_ok=True)
pd.set_option("display.width", 250)
RNG = np.random.default_rng(20261008)
EVAL_EQ = re.compile(r"=\s*[-+]?\d+(?:\.\d+)?")
ANSWER = re.compile(r"\\boxed|Final Answer")
BOUND = ("additional_property", "answer_leak", "missing_field", "wrong_type",
         "conditional_required")

def load(paths):
    rows = []
    for p in paths:
        for f in ([p] if os.path.isfile(p) else glob.glob(p + "/*.jsonl")):
            if "PREFIX_BUG" in f or "TRUNCATION_BUG" in f:
                print(f"  SKIP quarantined: {os.path.basename(f)}"); continue
            for ln in open(f):
                ln = ln.strip()
                if ln:
                    try: rows.append(json.loads(ln))
                    except json.JSONDecodeError: pass
    return pd.DataFrame(rows)

def boot(d, n=4000):
    d = np.asarray(d, float); d = d[~np.isnan(d)]
    if len(d) < 2: return (np.nan, np.nan, np.nan)
    b = RNG.choice(d, (n, len(d))).mean(1)
    return d.mean(), *np.percentile(b, [2.5, 97.5])

def main(paths):
    df = load(paths)
    if df.empty: print("no data"); return
    df["actor"] = df.actor_model.str.split("/").str[-1]
    print(f"\ntrajectories={len(df)}  arms={sorted(df.arm.unique())}  actors={sorted(df.actor.unique())}")

    # ---------- 1. MANIPULATION CHECK (both clauses, accepted msgs only) -----
    print("\n" + "="*78); print("1. MANIPULATION CHECK — accepted Planner messages")
    print("   P2 = redesignated check (Arm C enforces this). P1a = reported as a FINDING.")
    print("="*78)
    rows = []
    for r in df.itertuples():
        for m in (r.messages or []):
            if m.get("role") != "planner": continue
            v = m.get("validation") or {}
            if not v.get("ok", True): continue
            t = m.get("text") or ""
            if not t: continue
            rows.append(dict(arm=r.arm, actor=r.actor,
                             p1a=int(not EVAL_EQ.search(t)),
                             p2=int(not ANSWER.search(t)),
                             chars=len(t)))
    M = pd.DataFrame(rows)
    if len(M):
        g = M.groupby(["arm", "actor"]).agg(n=("p1a","size"), P1a=("p1a","mean"),
                                            P2=("p2","mean"), mean_chars=("chars","mean"))
        print(g.round(3).to_string())
        g.to_csv(OUT + "/x2_manipulation.csv")
        # length-robust P1a (review R-8): density instead of presence
        M["density"] = [len(EVAL_EQ.findall(t or "")) for t in
                        [mm.get("text","") for r in df.itertuples() for mm in (r.messages or [])
                         if mm.get("role")=="planner" and (mm.get("validation") or {}).get("ok",True)
                         and mm.get("text")]][:len(M)]
        M["eq_per_1k"] = 1000*M.density/M.chars.clip(lower=1)
        print("\n  length-robust (evaluated equations per 1k chars):")
        print(M.groupby(["arm","actor"]).eq_per_1k.mean().round(2).to_string())

    # ---------- 2. ATTRITION, both conventions -------------------------------
    print("\n" + "="*78); print("2. ATTRITION per arm x actor (the two conventions DISAGREE)")
    print("="*78)
    a = df.groupby(["arm","actor"]).agg(
        n=("problem_uid","size"),
        hard_fail=("stopping_condition", lambda s: (s=="hard_failure").sum()),
        ungraded=("correct", lambda s: s.isna().sum()))
    a["attrition"] = (a.hard_fail/a.n).round(3)
    acc_drop, acc_zero = [], []
    for k, g in df.groupby(["arm","actor"]):
        v = g.correct.dropna()
        acc_drop.append(v.mean() if len(v) else np.nan)
        acc_zero.append(g.correct.fillna(0).mean())
    a["acc_dropNone"] = np.round(acc_drop,3); a["acc_NoneZero_PREREG"] = np.round(acc_zero,3)
    a["delta"] = (a.acc_dropNone - a.acc_NoneZero_PREREG).round(3)
    print(a.to_string())
    a.to_csv(OUT + "/x2_attrition.csv")

    # ---------- 3. ENFORCEMENT: boundary only --------------------------------
    print("\n" + "="*78); print("3. ENFORCEMENT (boundary violations only; parse/format excluded)")
    print("="*78)
    er = []
    for k, g in df[df.arm.isin(["C","Cp"])].groupby(["arm","actor"]):
        b = p = att = 0; soft = collections.Counter()
        for r in g.itertuples():
            for e in (r.regeneration_events or []):
                att += 1
                vr = e.get("validation_result") or {}
                for s in (vr.get("soft_signals") or []): soft[s.split(":")[0]] += 1
                if vr.get("ok"): continue
                v = str(vr.get("violated_constraint"))
                if v.startswith(BOUND): b += 1
                else: p += 1
        er.append(dict(arm=k[0], actor=k[1], n=len(g), attempts=att,
                       boundary=b, parse_format=p,
                       boundary_per_traj=round(b/max(len(g),1),3), soft=dict(soft)))
    if er:
        E = pd.DataFrame(er); print(E.to_string(index=False)); E.to_csv(OUT+"/x2_enforcement.csv", index=False)

    # ---------- 4. Arm C' context control ------------------------------------
    print("\n" + "="*78); print("4. CONTEXT CONTROL: C' - C  (identified comparison)")
    print("="*78)
    if {"C","Cp"} <= set(df.arm.unique()):
        w = df.pivot_table(index=["problem_uid","actor"], columns="arm",
                           values="correct", aggfunc="first")
        for actor, g in w.reset_index().groupby("actor"):
            if "C" in g and "Cp" in g:
                d = (g["Cp"] - g["C"]).dropna()
                if len(d) >= 5:
                    m, lo, hi = boot(d)
                    print(f"  {actor:16s} n={len(d):4d}  C'-C = {m:+.4f} [{lo:+.4f},{hi:+.4f}]")
        # context actually delivered
        cc = []
        for r in df[df.arm.isin(["A","C","Cp"])].itertuples():
            for m in (r.messages or []):
                if m.get("prompt_chars") and m.get("role") in ("planner","executor","reviewer"):
                    cc.append(dict(arm=r.arm, role=m["role"], chars=m["prompt_chars"]))
        if cc:
            print("\n  mean prompt chars (is the control doing anything?):")
            print(pd.DataFrame(cc).pivot_table(index="role", columns="arm",
                  values="chars", aggfunc="mean").round(0).to_string())
    else:
        print("  (C' not yet present)")

    # ---------- 5. Arm B collapse, per actor ---------------------------------
    print("\n" + "="*78); print("5. ARM B ROLE COLLAPSE (byte-identical responses), per actor")
    print("="*78)
    cr = []
    for k, g in df.groupby(["arm","actor"]):
        tot = coll = 0
        for r in g.itertuples():
            h = [m.get("response_sha256_12") for m in (r.messages or [])
                 if m.get("role") in ("planner","executor","reviewer") and m.get("response_sha256_12")]
            if len(h) >= 2:
                tot += 1; coll += (len(set(h)) < len(h))
        if tot: cr.append(dict(arm=k[0], actor=k[1], n=tot, collapse_rate=round(coll/tot,3), collapsed=coll))
    if cr:
        Cdf = pd.DataFrame(cr); print(Cdf.to_string(index=False)); Cdf.to_csv(OUT+"/x2_collapse.csv", index=False)

    # ---------- 6. primary paired contrasts ----------------------------------
    print("\n" + "="*78); print("6. PRIMARY: paired accuracy contrasts (prereg Nones->0)")
    print("="*78)
    df["corr0"] = df.correct.fillna(0)
    w = df.pivot_table(index=["problem_uid","actor"], columns="arm", values="corr0", aggfunc="first")
    w = w.reset_index()
    for actor, g in w.groupby("actor"):
        for x, y in [("C","A"),("B","A"),("Cp","A")]:
            if x in g and y in g:
                d = (g[x]-g[y]).dropna()
                if len(d) >= 10:
                    m, lo, hi = boot(d)
                    flag = "" if lo < 0 < hi else "  *"
                    print(f"  {actor:16s} {x}-{y}  n={len(d):4d}  {m:+.4f} [{lo:+.4f},{hi:+.4f}]{flag}")
    w.to_csv(OUT + "/x2_paired.csv", index=False)
    print(f"\nwrote x2_* to {OUT}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("paths", nargs="+")
    main(ap.parse_args().paths)
