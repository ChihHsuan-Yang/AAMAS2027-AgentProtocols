#!/usr/bin/env python3
"""Build the release-ready HF artifact from the FROZEN snapshot.

Deterministic and idempotent: re-running over an unchanged FROZEN/ produces
byte-identical parquet (no timestamps, no RNG, stable row order).

Every derived column reuses the definition in
`analysis/scripts/FINAL_TABLES.py`. Where a definition is subtle it is copied
verbatim and the source table (T0, T1, T5, T6, T19...) is named in SCHEMA.md.
Nothing here recomputes a headline number a different way -- per SOURCE_OF_TRUTH.md
FINAL_TABLES.py remains the only authority for manuscript numbers. This script
emits the ROWS those numbers are computed over.

Usage:  python3 scripts/build_artifact.py
"""
import json, glob, re, os, sys, hashlib, collections
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # hf_artifact/
PROJ = os.path.dirname(ROOT)                                                 # project root
FROZEN = os.path.join(PROJ, "experiments", "results", "FROZEN")
ADJ_SRC = os.path.join(PROJ, "adjudication")
OUT = os.path.join(ROOT, "data")
MAN = os.path.join(ROOT, "manifests")
ADJ_OUT = os.path.join(ROOT, "adjudication")

# ----------------------------------------------------------------- definitions
# verbatim from FINAL_TABLES.py
BOX = re.compile(r"\\boxed\s*\{")


def actor(r):
    return r["actor_model"].split("/")[-1]


def ev(r):
    return r.get("evaluator_history") or []


def graded(r):
    return bool(ev(r)) and r.get("correct") is not None


def fp(r):
    return int(ev(r)[0].get("correctness") or 0) if ev(r) else None


def fin_prereg(r):
    return int(r.get("correct") or 0)        # ungraded -> 0


def fin_asgraded(r):
    return r.get("correct")                  # may be None


def boxed_all(t):
    o = []
    for m in BOX.finditer(t or ""):
        i, dd = m.end() - 1, 0
        for j in range(i, min(len(t), i + 4000)):
            if t[j] == "{":
                dd += 1
            elif t[j] == "}":
                dd -= 1
                if dd == 0:
                    o.append(t[i + 1:j])
                    break
    return o


def jans(t):
    o = [m.group(1) for m in re.finditer(r'"answer"\s*:\s*"((?:[^"\\]|\\.)*)"', t or "")]
    o += [m.group(1) for m in re.finditer(r'"answer"\s*:\s*(-?[0-9][0-9.eE+/-]*)', t or "")]
    return o


def nrm(s):
    """Normalization used for every answer-string comparison in the project
    (T6 noise floor, T19 F18 mismatch). Whitespace stripped, $ delimiters
    stripped. Empty -> None."""
    if s is None:
        return None
    s = re.sub(r"\s+", "", str(s)).strip("$").strip()
    return s or None


def first3(r):
    return [m for m in (r.get("messages") or [])
            if m.get("role") in ("planner", "executor", "reviewer")][:3]


def ansseq(r):
    seq, arm = [], r.get("arm")
    for m in (r.get("messages") or []):
        if m.get("role") not in ("planner", "executor", "reviewer"):
            continue
        t = m.get("text") or ""
        for b in boxed_all(t) + (jans(t) if arm in ("C", "Cp") else []):
            x = nrm(b)
            if x and (not seq or seq[-1] != x):
                seq.append(x)
    return seq


def routes(r):
    return [m.get("route") for m in (r.get("messages") or [])
            if m.get("role") == "reviewer" and m.get("route")]


def func_collapse(r):
    f = first3(r)
    if len(f) != 3:
        return None
    return all(BOX.search(m.get("text") or "") for m in f)


def unanimous(r):
    f = first3(r)
    if len(f) != 3:
        return None
    a = []
    for m in f:
        b = boxed_all(m.get("text") or "")
        if not b:
            return None
        a.append(nrm(b[-1]))
    return len(set(a)) == 1


# ------------------------------------------------------- error-string sanitizer
# Some `error` values embed an upstream HTTP response body (a Cloudflare block
# page naming the operating institution; a 500 whose JSON carries a server-side
# filesystem path; an nginx 502 page). Those are internal-infrastructure
# details and, in the Cloudflare case, DEANONYMIZING. Keep the failure CLASS,
# drop the body.
HTTP_RE = re.compile(r"HTTP\s+(\d{3})")


def sanitize_error(e):
    if not e:
        return None
    s = str(e)
    m = HTTP_RE.search(s)
    if m:
        prefix = "call failed: retries exhausted: " if "retries exhausted" in s else "call failed: "
        return f"RuntimeError: {prefix}HTTP {m.group(1)}: [upstream response body redacted]"
    if "ReadTimeout" in s:
        return "RuntimeError: call failed: retries exhausted: ReadTimeout"
    # the remaining classes are short, structured, and carry no host/path
    return s.strip()


def load():
    rows = []
    for f in sorted(glob.glob(FROZEN + "/*.jsonl")):
        for l in open(f):
            try:
                rows.append(json.loads(l))
            except Exception:
                pass
    return rows


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    print("reading FROZEN ...")
    rows = load()
    print(f"  {len(rows)} trajectories")

    # ---- verify the snapshot hashes before deriving anything from it
    man = json.load(open(os.path.join(FROZEN, "MANIFEST.json")))
    bad = []
    for fn, meta in man["files"].items():
        got = sha256_file(os.path.join(FROZEN, fn))
        status = "OK" if got == meta["sha256"] else "MISMATCH"
        if got != meta["sha256"]:
            bad.append(fn)
        print(f"  {fn:22s} {status}")
    if bad:
        sys.exit(f"FROZEN hash mismatch in {bad}; refusing to build")
    assert len(rows) == man["total_rows"], (len(rows), man["total_rows"])

    # gold, from the SAME parquet the grader read (see FINAL_TABLES.py T19)
    import pandas as pd
    PQ = os.path.join(os.path.dirname(PROJ), "IEEE-BigData-SciAgentTrace",
                      "analysis", "hf_cache", "release", "data", "problems",
                      "part-00000.parquet")
    _df = pd.read_parquet(PQ)
    _df = _df[_df["benchmark_id"] == "omnimath2"]
    GOLD = dict(zip(_df["problem_uid"].astype(str), _df["answer"].astype(str)))
    missing = sum(1 for r in rows if r["problem_uid"] not in GOLD)
    assert missing == 0, f"gold coverage incomplete ({missing} rows)"
    print(f"  gold: {len(GOLD)} omnimath2 problems, 0 uncovered trajectories")

    # ------------------------------------------------------ per-trajectory table
    traj, calls, msgs = [], [], []
    for r in rows:
        a, arm, uid = actor(r), r["arm"], r["problem_uid"]
        tkey = f"{uid}|{arm}|{a}"                    # unique: verified 11600/11600
        h = ev(r)
        rt = routes(r)
        seq = ansseq(r)
        last_sub = nrm((h[-1] or {}).get("candidate")) if h else None
        held = nrm(r.get("final_answer"))
        gold = nrm(GOLD.get(uid))
        f18 = (held is not None and last_sub is not None and held != last_sub)
        n_low = 0                                     # F13 proxy: slow-but-short
        for m in (r.get("messages") or []):
            if m.get("role") not in ("planner", "executor", "reviewer"):
                continue
            lat = m.get("latency_s") or 0
            if lat > 0 and (len(m.get("text") or "") / lat) < 10:
                n_low += 1
        traj.append(dict(
            trajectory_key=tkey,
            problem_uid=uid,
            arm=arm,
            actor_model=a,
            actor_model_full=r["actor_model"],
            evaluator_model=r["evaluator_model"],
            run_id=r.get("run_id"),
            config_version=r.get("config_version"),
            benchmark_id=r.get("benchmark_id"),
            domain=r.get("domain"),
            graded=bool(graded(r)),
            first_pass_correct=fp(r),
            final_correct_prereg=fin_prereg(r),
            final_correct_asgraded=fin_asgraded(r),
            first_pass_wrong=bool(graded(r) and fp(r) == 0),
            cycles=r.get("inner_used"),
            rounds_used=r.get("rounds_used"),
            submissions=len(h),
            evaluator_calls=len(h),
            actor_calls=r.get("actor_calls"),
            retries=r.get("retries"),
            reviewer_first_route=(rt[0] if rt else None),
            reviewer_never_declines=(bool(rt) and all(z == "agree" for z in rt)) if rt else None,
            functional_collapse=func_collapse(r),
            unanimous_first_pass=unanimous(r),
            frozen_answer=(len(set(seq)) <= 1),
            n_distinct_answers=len(set(seq)),
            final_answer_held=r.get("final_answer"),
            last_submitted_answer=(h[-1] or {}).get("candidate") if h else None,
            f18_mismatch=f18,
            f18_under_credited=bool(f18 and gold is not None and held == gold
                                    and fin_prereg(r) == 0),
            f13_n_low_chars_per_sec=n_low,
            hard_failure=r.get("hard_failure"),
            attrition=(not graded(r)),
            stopping_condition=r.get("stopping_condition"),
            error=sanitize_error(r.get("error")),
            wall_time_s=r.get("wall_time_s"),
            started_at=r.get("started_at"),
            ended_at=r.get("ended_at"),
            n_role_messages=len(first3(r)) and sum(
                1 for m in (r.get("messages") or [])
                if m.get("role") in ("planner", "executor", "reviewer")),
            n_regeneration_rejects=sum(
                1 for e in (r.get("regeneration_events") or [])
                if not (e.get("validation_result") or {}).get("ok", True)),
        ))

        # --------------------------------------------- per-evaluator-call table
        for i, e in enumerate(h):
            calls.append(dict(
                trajectory_key=tkey,
                problem_uid=uid,
                arm=arm,
                actor_model=a,
                call_index=i,
                candidate_raw=e.get("candidate"),
                candidate_normalized=nrm(e.get("candidate")),
                verdict=int(e["correctness"]) if e.get("correctness") is not None else None,
                is_first_pass=(i == 0),
                latency_s=e.get("latency_s"),
                finish_reason=e.get("finish_reason"),
                timestamp=e.get("timestamp"),
                evaluator_raw=e.get("raw"),
            ))

        # ------------------------------------------------------- message table
        for j, m in enumerate(r.get("messages") or []):
            if m.get("role") not in ("planner", "executor", "reviewer"):
                continue
            t = m.get("text") or ""
            lat = m.get("latency_s")
            msgs.append(dict(
                trajectory_key=tkey,
                problem_uid=uid,
                arm=arm,
                actor_model=a,
                message_index=j,
                role=m.get("role"),
                outer_round=m.get("outer_round"),
                inner_round=m.get("inner_round"),
                attempt_index=m.get("attempt_index"),
                rejected=bool(m.get("rejected", False)),
                text=t,
                n_chars=len(t),
                latency_s=lat,
                chars_per_sec=(len(t) / lat) if lat else None,
                used_reasoning_fallback=bool(m.get("used_reasoning_fallback", False)),
                finish_reason=m.get("finish_reason"),
                route=m.get("route"),
                answer_owner_after_turn=m.get("answer_owner_after_turn"),
                validation_ok=(m.get("validation") or {}).get("ok"),
                violated_constraint=(m.get("validation") or {}).get("violated_constraint"),
                prompt_sha256_12=m.get("prompt_sha256_12"),
                response_sha256_12=m.get("response_sha256_12"),
                prompt_chars=m.get("prompt_chars"),
                timestamp=m.get("timestamp"),
            ))

    # stable sort so re-runs are byte-identical
    traj.sort(key=lambda d: d["trajectory_key"])
    calls.sort(key=lambda d: (d["trajectory_key"], d["call_index"]))
    msgs.sort(key=lambda d: (d["trajectory_key"], d["message_index"]))

    os.makedirs(OUT, exist_ok=True)
    os.makedirs(MAN, exist_ok=True)

    def write(name, recs, **kw):
        t = pa.Table.from_pylist(recs)
        p = os.path.join(OUT, name)
        pq.write_table(t, p, compression="zstd", **kw)
        print(f"  wrote {name}: {len(recs)} rows, {os.path.getsize(p)/1e6:.1f} MB")
        return t

    print("writing parquet ...")
    write("trajectories.parquet", traj)
    write("evaluator_calls.parquet", calls)
    write("role_messages.parquet", msgs, compression_level=10)

    # ---------------------------------------------------------------- manifests
    import shutil
    shutil.copy(os.path.join(FROZEN, "MANIFEST.json"),
                os.path.join(MAN, "FROZEN_MANIFEST.json"))

    census = collections.Counter((d["actor_model"], d["arm"]) for d in traj)
    gr = collections.Counter((d["actor_model"], d["arm"]) for d in traj if d["graded"])
    hf_ = collections.Counter((d["actor_model"], d["arm"]) for d in traj if d["hard_failure"])
    cells = [dict(actor_model=a, arm=m, n=census[(a, m)], graded=gr[(a, m)],
                  ungraded=census[(a, m)] - gr[(a, m)], hard_failure=hf_[(a, m)])
             for (a, m) in sorted(census)]
    json.dump(cells, open(os.path.join(MAN, "cell_census.json"), "w"), indent=1)

    uids = sorted({d["problem_uid"] for d in traj})
    per_actor = {a: sorted({d["problem_uid"] for d in traj if d["actor_model"] == a})
                 for a in sorted({d["actor_model"] for d in traj})}
    json.dump(dict(
        n_distinct_problems=len(uids),
        benchmark_id="omnimath2",
        source_dataset="Omni-MATH-2 (martheballon/Omni-MATH-2), Apache-2.0",
        note=("problem_uid is the SciAgentTrace registry id; join to upstream text "
              "via data/problems/part-00000.parquet in that corpus. Problem TEXT and "
              "GOLD ANSWERS are NOT redistributed here -- see SCHEMA.md."),
        problem_uids=uids,
        problem_uids_per_actor={k: len(v) for k, v in per_actor.items()},
    ), open(os.path.join(MAN, "problem_sample.json"), "w"), indent=1)
    print(f"  wrote manifests: {len(cells)} cells, {len(uids)} problems")

    # ------------------------------------------------------------- adjudication
    # Two real leaks are neutralized on copy, reproducibly (not by hand):
    #   build_sample.py  hardcodes the author's home directory -> DEANONYMIZING
    #   PROTOCOL.md      names the internal judge proxy and its credential helper
    # Each substitution is asserted to actually fire, so a silent upstream
    # rename cannot turn this into a no-op that still reports success.
    # The patterns are written as REGEXES rather than literal leaked strings, so
    # this sanitizer does not itself reintroduce into the artifact the very text
    # it exists to remove.
    ADJ_SUBS = {
        "build_sample.py": [(
            re.compile(r'^ROOT\s*=\s*"/(?:Users|home)/[^"]*"', re.M),
            'ROOT = os.environ.get("PROJECT_ROOT", ".")  # [path anonymized for review]',
        )],
        "PROTOCOL.md": [(
            re.compile(r"- primary: \*\*Opus 5\*\* \(`claude-opus-5`\), reached via[^\n]*\n[^\n]*"
                       r"No credential is logged or committed\."),
            "- primary: **Opus 5** (`claude-opus-5`), reached through an institutional\n"
            "  API gateway. [Endpoint and credential mechanism redacted for review; no\n"
            "  credential was ever logged or committed.]",
        )],
    }
    os.makedirs(ADJ_OUT, exist_ok=True)
    for f in ("ITEMS_blinded.jsonl", "VERDICTS.jsonl", "KEY.jsonl",
              "RUBRIC_v1.md", "SAMPLING_MANIFEST.json", "PROTOCOL.md",
              "build_sample.py", "analyze.py"):
        src, dst = os.path.join(ADJ_SRC, f), os.path.join(ADJ_OUT, f)
        if f in ADJ_SUBS:
            txt = open(src, encoding="utf-8").read()
            for rx, new in ADJ_SUBS[f]:
                txt, n = rx.subn(new, txt)
                assert n == 1, f"sanitizer matched {n}x (expected 1) in {f}: {rx.pattern[:60]!r}"
            open(dst, "w", encoding="utf-8").write(txt)
            print(f"  copied {f} (sanitized)")
        else:
            shutil.copy(src, dst)
    print(f"  copied 8 adjudication artifacts (2 sanitized)")
    print("NOTE: adjudicate.py is NOT copied (it resolves an endpoint + credential "
          "helper). See adjudication/README.md.")


if __name__ == "__main__":
    main()
