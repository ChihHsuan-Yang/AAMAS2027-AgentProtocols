#!/usr/bin/env python3
"""Build the v1.1.0 SciBench (second-domain) additions to the artifact.

ADDITIVE BY CONSTRUCTION. This script writes only NEW paths:

    raw/scibench_AB.jsonl               exact frozen bytes
    raw/MANIFEST_SCIBENCH.json          copied from the FROZEN_SCIBENCH manifest
    data/scibench/trajectories.parquet
    data/scibench/role_messages.parquet
    data/scibench/evaluator_calls.parquet
    manifests/cell_census_scibench.json
    manifests/problem_sample_scibench.json
    manifests/FROZEN_MANIFEST_SCIBENCH.json

It never opens a v1.0.0 file for writing, and it ASSERTS at the end that every
v1.0.0 sha256 in CHECKSUMS.txt is unchanged -- so "additive" is verified, not
promised.

There is no Arm C in this campaign, so there is no enforcement_events table and
no adjudication table for this domain. Those stay v1.0.0 / Omni-MATH only.

Every derived column reuses the IMPORTED definition from build_artifact.py --
not a copy of it -- so the two domains cannot silently drift apart.

Usage:  python3 scripts/build_scibench.py
"""
import json, os, sys, hashlib, collections, shutil
import pyarrow as pa
import pyarrow.parquet as pq

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
PROJ = os.path.dirname(ART)

sys.path.insert(0, HERE)
# Reuse, do NOT re-implement. A copied function body is not a copied definition.
from build_artifact import (                      # noqa: E402
    actor, ev, graded, fp, fin_prereg, fin_asgraded, boxed_all, nrm,
    first3, ansseq, routes, func_collapse, unanimous, sanitize_error,
    sha256_file,
)

FROZEN_SB = os.path.join(PROJ, "experiments", "results", "xdomain", "FROZEN_SCIBENCH")
TRACE = "scibench_AB.jsonl"
OUT = os.path.join(ART, "data", "scibench")
MAN = os.path.join(ART, "manifests")
RAW = os.path.join(ART, "raw")

# The published v1.0.0 digests. Asserted unchanged at the end of the build.
V100_FILES = (
    "raw/actor3.jsonl", "raw/armCp.jsonl", "raw/campaign_v2.jsonl",
    "raw/MANIFEST.json",
    "data/trajectories.parquet", "data/role_messages.parquet",
    "data/evaluator_calls.parquet", "data/enforcement_events.parquet",
    "data/adjudication.parquet",
    "manifests/FROZEN_MANIFEST.json", "manifests/cell_census.json",
    "manifests/problem_sample.json",
    "config/prompts.json", "config/run_config.json", "config/schemas.json",
)


def read_checksums():
    d = {}
    for line in open(os.path.join(ART, "CHECKSUMS.txt")):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        h, rel = line.split(None, 1)
        d[rel.strip()] = h
    return d


def main():
    before = read_checksums()

    # ---- verify the frozen snapshot BEFORE deriving anything from it
    print("verifying FROZEN_SCIBENCH ...")
    man = json.load(open(os.path.join(FROZEN_SB, "MANIFEST.json")))
    meta = man["files"][TRACE]
    src = os.path.join(FROZEN_SB, TRACE)
    got, nbytes = sha256_file(src), os.path.getsize(src)
    print(f"  {TRACE}  sha256 {'OK' if got == meta['sha256'] else 'MISMATCH'}  "
          f"bytes {'OK' if nbytes == meta['bytes'] else 'MISMATCH'}")
    if got != meta["sha256"] or nbytes != meta["bytes"]:
        sys.exit("FROZEN_SCIBENCH hash/bytes mismatch; refusing to build")

    rows = [json.loads(l) for l in open(src)]
    assert len(rows) == man["total_rows"] == 2296, (len(rows), man["total_rows"])
    print(f"  {len(rows)} trajectories, hash verified")

    # ---- gold, from the SAME parquet the grader read
    import pandas as pd
    PQ = os.path.join(os.path.dirname(PROJ), "IEEE-BigData-SciAgentTrace",
                      "analysis", "hf_cache", "release", "data", "problems",
                      "part-00000.parquet")
    _df = pd.read_parquet(PQ)
    _df = _df[_df["benchmark_id"] == "scibench"]
    GOLD = dict(zip(_df["problem_uid"].astype(str), _df["answer"].astype(str)))
    missing = sum(1 for r in rows if r["problem_uid"] not in GOLD)
    assert missing == 0, f"gold coverage incomplete ({missing} rows)"
    print(f"  gold: {len(GOLD)} scibench problems, 0 uncovered trajectories")

    # ---- one domain, one benchmark: assert it, do not assume it
    assert {r.get("benchmark_id") for r in rows} == {"scibench"}
    assert {r.get("domain") for r in rows} == {"science"}
    assert {r.get("arm") for r in rows} == {"A", "B"}, "Arm C must not be here"

    traj, calls, msgs = [], [], []
    for r in rows:
        a, arm, uid = actor(r), r["arm"], r["problem_uid"]
        tkey = f"{uid}|{arm}|{a}"
        h = ev(r)
        rt = routes(r)
        seq = ansseq(r)
        last_sub = nrm((h[-1] or {}).get("candidate")) if h else None
        held = nrm(r.get("final_answer"))
        gold = nrm(GOLD.get(uid))
        f18 = (held is not None and last_sub is not None and held != last_sub)
        n_low = 0
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

        for i, e in enumerate(h):
            calls.append(dict(
                trajectory_key=tkey, problem_uid=uid, arm=arm, actor_model=a,
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

        for j, m in enumerate(r.get("messages") or []):
            if m.get("role") not in ("planner", "executor", "reviewer"):
                continue
            t = m.get("text") or ""
            lat = m.get("latency_s")
            msgs.append(dict(
                trajectory_key=tkey, problem_uid=uid, arm=arm, actor_model=a,
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

    traj.sort(key=lambda d: d["trajectory_key"])
    calls.sort(key=lambda d: (d["trajectory_key"], d["call_index"]))
    msgs.sort(key=lambda d: (d["trajectory_key"], d["message_index"]))

    # ---- column parity with the v1.0.0 Omni tables, asserted
    pairs = (("trajectories.parquet", traj), ("evaluator_calls.parquet", calls),
             ("role_messages.parquet", msgs))
    for fn, recs in pairs:
        omni_cols = pq.read_schema(os.path.join(ART, "data", fn)).names
        if list(recs[0].keys()) != list(omni_cols):
            sys.exit(f"column drift in {fn}:\n  omni={omni_cols}\n  sci ={list(recs[0].keys())}")
    print("  column parity with the v1.0.0 Omni tables: OK (3/3 tables)")

    os.makedirs(OUT, exist_ok=True)

    def write(name, recs, **kw):
        t = pa.Table.from_pylist(recs)
        p = os.path.join(OUT, name)
        pq.write_table(t, p, compression="zstd", **kw)
        print(f"  wrote data/scibench/{name}: {len(recs)} rows, "
              f"{os.path.getsize(p)/1e6:.1f} MB")

    print("writing parquet ...")
    write("trajectories.parquet", traj)
    write("evaluator_calls.parquet", calls)
    write("role_messages.parquet", msgs, compression_level=10)

    # ---- raw trace, EXACT BYTES
    shutil.copyfile(src, os.path.join(RAW, TRACE))
    assert sha256_file(os.path.join(RAW, TRACE)) == meta["sha256"], "copy changed bytes"
    print(f"  copied raw/{TRACE} (exact bytes, sha256 re-verified after copy)")

    shutil.copy(os.path.join(FROZEN_SB, "MANIFEST.json"),
                os.path.join(RAW, "MANIFEST_SCIBENCH.json"))
    shutil.copy(os.path.join(FROZEN_SB, "MANIFEST.json"),
                os.path.join(MAN, "FROZEN_MANIFEST_SCIBENCH.json"))

    # ---- manifests
    census = collections.Counter((d["actor_model"], d["arm"]) for d in traj)
    gr = collections.Counter((d["actor_model"], d["arm"]) for d in traj if d["graded"])
    hf_ = collections.Counter((d["actor_model"], d["arm"]) for d in traj if d["hard_failure"])
    cells = [dict(actor_model=a, arm=m, n=census[(a, m)], graded=gr[(a, m)],
                  ungraded=census[(a, m)] - gr[(a, m)], hard_failure=hf_[(a, m)])
             for (a, m) in sorted(census)]
    json.dump(cells, open(os.path.join(MAN, "cell_census_scibench.json"), "w"), indent=1)

    uids = sorted({d["problem_uid"] for d in traj})
    per_actor = {a: sorted({d["problem_uid"] for d in traj if d["actor_model"] == a})
                 for a in sorted({d["actor_model"] for d in traj})}
    json.dump(dict(
        n_distinct_problems=len(uids),
        benchmark_id="scibench",
        slice_id="text_only",
        source_dataset="SciBench (https://github.com/mandyyyyii/scibench), MIT",
        denominators=("692 upstream -> 580 in the release registry -> 574 carrying the "
                      "text_only slice -> all 574 run. NO sub-sampling. The 692->580 "
                      "exclusions are NOT recoverable from this release; see the card."),
        note=("problem_uid is the SciAgentTrace registry id; join to upstream text via "
              "data/problems/part-00000.parquet in that corpus. Problem TEXT and GOLD "
              "ANSWERS are NOT redistributed here -- see SCHEMA.md."),
        problem_uids=uids,
        problem_uids_per_actor={k: len(v) for k, v in per_actor.items()},
    ), open(os.path.join(MAN, "problem_sample_scibench.json"), "w"), indent=1)
    print(f"  wrote manifests: {len(cells)} cells, {len(uids)} problems")

    # ---- ADDITIVITY PROOF: every v1.0.0 digest must be unchanged
    bad = []
    for rel in V100_FILES:
        p = os.path.join(ART, rel)
        if not os.path.exists(p):
            bad.append(f"{rel}: MISSING")
            continue
        if sha256_file(p) != before.get(rel):
            bad.append(f"{rel}: sha256 CHANGED")
    if bad:
        sys.exit("ADDITIVITY VIOLATED -- v1.0.0 bytes moved:\n  " + "\n  ".join(bad))
    print(f"\nadditivity verified: all {len(V100_FILES)} v1.0.0 files byte-unchanged")


if __name__ == "__main__":
    main()
