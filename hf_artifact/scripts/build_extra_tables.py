#!/usr/bin/env python3
"""Build the two tables the v1.0.0 staging tree was missing:

  data/enforcement_events.parquet  -- Arm C / C' validation attempts, rejections
                                      and regenerations, one row per attempt
  data/adjudication.parquet        -- the model-adjudication study as a table

Both are derived from experiments/results/FROZEN/ (hash-verified first, the
same discipline as build_artifact.py: refuse to build on a mismatch) and from
adjudication/{ITEMS_blinded,VERDICTS,KEY}.jsonl.

Deterministic: rows are sorted by a stable key, so a rebuild is byte-identical.
"""
import json, os, sys, hashlib
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ART  = os.path.dirname(HERE)
PROJ = os.path.dirname(ART)
FROZEN = os.path.join(PROJ, "experiments", "results", "FROZEN")


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def verify_frozen():
    man = json.load(open(os.path.join(FROZEN, "MANIFEST.json")))
    bad = []
    for fn, meta in man["files"].items():
        got = sha256_file(os.path.join(FROZEN, fn))
        print(f"  {fn:22s} {'OK' if got == meta['sha256'] else 'MISMATCH'}")
        if got != meta["sha256"]:
            bad.append(fn)
    if bad:
        sys.exit(f"FROZEN hash mismatch in {bad}; refusing to build")
    return man


def load_rows():
    rows = []
    for fn in ("campaign_v2", "actor3", "armCp"):
        with open(os.path.join(FROZEN, f"{fn}.jsonl")) as f:
            for line in f:
                rows.append(json.loads(line))
    return rows


def actor(r):
    return r["actor_model"].split("/")[-1]


# ---------------------------------------------------------- enforcement_events
def build_enforcement(rows):
    out = []
    for r in rows:
        tkey = f"{r['problem_uid']}|{r['arm']}|{actor(r)}"
        for i, e in enumerate(r.get("regeneration_events") or []):
            vr = e.get("validation_result") or {}
            ok = bool(vr.get("ok", True))
            viol = vr.get("violated_constraint")
            if viol is None:
                viol = e.get("violated_constraint")
            allv = vr.get("all_violations") or []
            out.append(dict(
                trajectory_key=tkey,
                problem_uid=r["problem_uid"],
                arm=r["arm"],
                actor_model=actor(r),
                event_index=i,
                role=e.get("role"),
                outer_round=e.get("outer_round"),
                inner_round=e.get("inner_round"),
                attempt_index=e.get("attempt_index"),
                validation_ok=ok,
                was_rejected=(not ok),
                was_regenerated=bool(e.get("regenerated", False)),
                violated_constraint=viol,
                validation_detail=vr.get("detail"),
                n_violations=len(allv),
                all_violations=json.dumps(allv) if allv else None,
                soft_signals=json.dumps(vr.get("soft_signals") or []) or None,
                rejected_output_truncated_2000chars=e.get("raw_output_truncated_2000chars"),
                finish_reason=e.get("finish_reason"),
                used_reasoning_fallback=bool(e.get("used_reasoning_fallback", False)),
                latency_s=e.get("latency_s"),
                prompt_sha256_12=e.get("prompt_sha256_12"),
                prompt_chars=e.get("prompt_chars"),
                timestamp=e.get("timestamp"),
            ))
    df = pd.DataFrame(out).sort_values(
        ["trajectory_key", "event_index"], kind="mergesort").reset_index(drop=True)
    return df


# -------------------------------------------------------------- adjudication
def build_adjudication():
    adj = os.path.join(ART, "adjudication")
    items = {}
    with open(os.path.join(adj, "ITEMS_blinded.jsonl")) as f:
        for line in f:
            d = json.loads(line)
            items[d["tid"]] = d
    key = {}
    with open(os.path.join(adj, "KEY.jsonl")) as f:
        for line in f:
            d = json.loads(line)
            key[d["tid"]] = d

    out = []
    with open(os.path.join(adj, "VERDICTS.jsonl")) as f:
        for line in f:
            v = json.loads(line)
            tid = v["tid"]
            k = key.get(tid, {})
            p = v.get("parsed") or {}
            q = {f"q{i}": p.get(f"Q{i}") for i in range(1, 6)}
            # the automated label this study validates, carried from the KEY
            out.append(dict(
                item_id=tid,                       # anonymized item id
                repetition_index=v.get("rep"),
                judge_model=v.get("model"),
                judge_temperature=v.get("temperature"),
                rubric_version="RUBRIC_v1",
                rubric_sha256_12=v.get("rubric_sha"),
                prompt_sha256_12=v.get("prompt_sha"),
                judged_at_utc=v.get("utc"),
                raw_judge_output=v.get("raw"),
                judge_error=v.get("error"),
                parse_ok=bool(p),
                q1_semantic_redundancy=q["q1"],
                q2_functional_redundancy=q["q2"],
                q3_new_information=q["q3"],
                q4_answer_influence=q["q4"],
                q5_division_of_labour_present=q["q5"],
                judge_reason=p.get("reason"),
                # linkage back to the trajectory, from KEY.jsonl
                problem_uid=k.get("problem_uid"),
                arm=k.get("arm"),
                actor_model=k.get("actor"),
                run_id=k.get("run_id"),
                config_version=k.get("config_version"),
                trajectory_correct=k.get("correct"),
                automated_collapse_label=k.get("auto_collapse"),
                trajectory_key=(
                    f"{k['problem_uid']}|{k['arm']}|{k['actor']}"
                    if k.get("problem_uid") and k.get("arm") and k.get("actor")
                    else None),
            ))
    df = pd.DataFrame(out).sort_values(
        ["item_id", "repetition_index"], kind="mergesort").reset_index(drop=True)
    return df


def main():
    print("verifying FROZEN snapshot before deriving anything")
    verify_frozen()
    rows = load_rows()
    print(f"  loaded {len(rows)} trajectories")

    enf = build_enforcement(rows)
    adj = build_adjudication()

    os.makedirs(os.path.join(ART, "data"), exist_ok=True)
    p1 = os.path.join(ART, "data", "enforcement_events.parquet")
    p2 = os.path.join(ART, "data", "adjudication.parquet")
    enf.to_parquet(p1, index=False, compression="snappy")
    adj.to_parquet(p2, index=False, compression="snappy")

    print(f"\nenforcement_events.parquet  {enf.shape[0]:>7} rows, {enf.shape[1]} cols")
    print("  by arm:", enf.arm.value_counts().to_dict())
    print("  rejections (validation_ok=False):", int((~enf.validation_ok).sum()))
    print(f"adjudication.parquet        {adj.shape[0]:>7} rows, {adj.shape[1]} cols")
    print("  distinct items:", adj.item_id.nunique(),
          "| reps:", sorted(adj.repetition_index.dropna().unique().tolist()),
          "| judge:", adj.judge_model.dropna().unique().tolist())


if __name__ == "__main__":
    main()
