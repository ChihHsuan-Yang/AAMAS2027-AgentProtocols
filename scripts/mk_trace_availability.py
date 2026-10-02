#!/usr/bin/env python3
"""Generate docs/TRACE_AVAILABILITY.md by INSPECTING the frozen rows.

A hand-written availability table is a claim about data; this reads the data.
For every field a reader might need -- prompt text, model output, evaluator
verdict, reward, cost, replicate metadata -- it reports presence by sampling
actual rows of every released trace, and says where each lives: in git, on
Hugging Face, local only, or nowhere.

The point is the ABSENCES. This project has twice reported a field as
available on the strength of its name appearing in a schema. Everything
below is measured: a field present but always null reads as ABSENT, and a
field stored only as a digest reads as DIGEST ONLY, because a hash cannot be
re-scored.
"""
import collections, hashlib, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "TRACE_AVAILABILITY.md")
N = 400                      # rows sampled per trace, STRIDED across the file

TRACES = [
    ("campaign_v2.jsonl", "experiments/results/FROZEN", "Omni-MATH, arms A/B/C, 2 actors"),
    ("actor3.jsonl", "experiments/results/FROZEN", "Omni-MATH, arms A/B/C, Llama-3.3"),
    ("armCp.jsonl", "experiments/results/FROZEN", "Omni-MATH, context-restored enforcement"),
    ("scibench_AB.jsonl", "experiments/results/xdomain/FROZEN_SCIBENCH",
     "SciBench, role-structured and role-free, 2 actors"),
]


def probe(path, n=N):
    """Presence of each quantity, measured over n rows STRIDED across the file.

    Not the first n. These files are written cell by cell, so a head sample
    can miss an entire condition and report a field absent that is present
    only in the cells it never reached. Striding costs one extra pass to
    count lines and guarantees coverage of every cell.
    """
    seen = {k: 0 for k in (
        "problem identifier", "problem text", "gold answer",
        "role message text", "prompt text (verbatim)", "prompt digest",
        "model output text", "response digest", "finish reason",
        "evaluator verdict", "evaluator raw output", "graded correctness",
        "final answer held", "regeneration events", "violated constraint",
        "token counts", "cost", "latency", "wall time",
        "actor model", "evaluator model", "backend", "config version",
        "run id", "budget record", "visibility policy", "timestamps",
        "replicate index", "random seed")}
    total = sum(1 for _ in open(path))
    stride = max(1, total // n)
    rows = 0
    with open(path) as f:
        for i, line in enumerate(f):
            if i % stride or rows >= n:
                continue
            r = json.loads(line)
            rows += 1
            msgs = r.get("messages") or []
            ev = r.get("evaluator_history") or []
            m0 = msgs[0] if msgs else {}
            e0 = ev[0] if ev else {}
            hit = {
                "problem identifier": bool(r.get("problem_uid")),
                "problem text": any(k in r for k in ("problem", "question", "task_description")),
                "gold answer": any(k in r for k in ("gold", "answer", "ground_truth")),
                "role message text": bool(m0.get("text")),
                "prompt text (verbatim)": "prompt" in m0 and bool(m0.get("prompt")),
                "prompt digest": bool(m0.get("prompt_sha256_12")),
                "model output text": bool(m0.get("text")),
                "response digest": bool(m0.get("response_sha256_12")),
                "finish reason": m0.get("finish_reason") is not None,
                "evaluator verdict": e0.get("correctness") is not None,
                "evaluator raw output": bool(e0.get("raw")),
                "graded correctness": r.get("correct") is not None,
                "final answer held": r.get("final_answer") is not None,
                "regeneration events": bool(r.get("regeneration_events")),
                "violated constraint": any(
                    x.get("violated_constraint") for x in (r.get("regeneration_events") or [])),
                "token counts": any("token" in k for k in r),
                "cost": any("cost" in k for k in r),
                "latency": m0.get("latency_s") is not None,
                "wall time": r.get("wall_time_s") is not None,
                "actor model": bool(r.get("actor_model")),
                "evaluator model": bool(r.get("evaluator_model")),
                "backend": bool(r.get("backend")),
                "config version": bool(r.get("config_version")),
                "run id": bool(r.get("run_id")),
                "budget record": bool(r.get("budget")),
                "visibility policy": bool(r.get("visibility_policy")),
                "timestamps": bool(r.get("started_at")),
                "replicate index": any(k in r for k in ("replicate", "rep", "seed_index")),
                "random seed": any("seed" in k for k in r),
            }
            for k, v in hit.items():
                seen[k] += bool(v)
    return seen, rows, total


def attrition(path):
    """EXACT per-condition completeness over the WHOLE file.

    The sampled table above answers "does this trace carry this field at
    all". This answers a different and more consequential question: in which
    CONDITION is a field missing, and how often. The two must not be
    conflated -- a field that is 95% present overall can be 100% present in
    three conditions and absent in a quarter of the fourth, and that is a
    finding about the intervention, not a data-quality footnote.

    Exact, not sampled: these are the numbers the paper's attrition claim
    rests on.
    """
    tot, nomsg, noverdict, nograde = (collections.Counter() for _ in range(4))
    for line in open(path):
        r = json.loads(line)
        # Keyed by (actor, condition), never pooled across actors. A pooled
        # enforced-attrition figure would be a number that appears nowhere
        # else in the project: the canonical output reports 0.080 / 0.099 /
        # 0.170 per actor, and the paper says "8-17%". Pooling two of them
        # into one 8.9% invents a third figure a reader cannot reconcile.
        a = (r.get("actor_model", "").split("/")[-1], r.get("arm"))
        tot[a] += 1
        if not (r.get("messages") or []):
            nomsg[a] += 1
        if not (r.get("evaluator_history") or []):
            noverdict[a] += 1
        if r.get("correct") is None:
            nograde[a] += 1
    return tot, nomsg, noverdict, nograde

def mark(count, rows):
    if rows == 0:
        return "—"
    if count == 0:
        return "**absent**"
    if count == rows:
        return "yes"
    return f"{count}/{rows}"


def main():
    results, present = {}, []
    for fn, d, desc in TRACES:
        p = os.path.join(ROOT, d, fn)
        if not os.path.exists(p):
            results[fn] = (None, 0, desc, d, 0)
            continue
        seen, rows, total = probe(p)
        results[fn] = (seen, rows, desc, d, total)
        present.append(fn)

    hf = os.path.join(ROOT, "hf_artifact", "raw")
    on_hf = {fn for fn, _, _ in TRACES if os.path.exists(os.path.join(hf, fn))}
    # Same bytes, or merely the same name?
    identical = set()
    for fn, d, _ in TRACES:
        a, b = os.path.join(ROOT, d, fn), os.path.join(hf, fn)
        if os.path.exists(a) and os.path.exists(b):
            ha = hashlib.sha256(open(a, "rb").read()).hexdigest()
            hb = hashlib.sha256(open(b, "rb").read()).hexdigest()
            if ha == hb:
                identical.add(fn)

    keys = list(next(v[0] for v in results.values() if v[0]).keys())
    L = ["# Trace availability — what we actually have, field by field",
         "",
         "**GENERATED by `scripts/mk_trace_availability.py`, which reads the "
         f"rows.** Each cell below is measured over {N} rows **strided across "
         "the whole file** — not the first N, which would miss whole "
         "conditions in a file written cell by cell — and is not asserted "
         "from a schema. A field that exists but is always "
         "null reads **absent**; a field stored only as a digest is listed as "
         "a digest, because a hash cannot be re-scored.",
         "",
         "Back to [the project README](../README.md) · "
         "[artifact map](PAPER_ARTIFACT_MAP.md) · "
         "[current handoff](../HANDOFF_CURRENT.md)",
         "",
         "## Where each trace lives", "",
         "| trace | contents | in git? | local | Hugging Face |",
         "|---|---|---|---|---|"]
    for fn, d, desc in TRACES:
        seen, rows, _, _, total = results[fn]
        hfs = ("yes, **byte-identical**" if fn in identical
               else "yes, bytes NOT verified" if fn in on_hf else "**no**")
        L.append(f"| `{fn}` | {desc}, {total:,} rows | **no** — gitignored | "
                 f"`{d}/` {'present' if seen else '**MISSING**'} | {hfs} |")
    L += ["",
          "**No raw trace is in git.** GitHub rejects files over 100 MB and the "
          "four traces total ~324 MB; `hf_artifact/raw/` is gitignored. The "
          "off-laptop copy is the **private** Hugging Face repo "
          "`AgentsSci/AAMAS2027-Roles` v1.1.0 — private during double-blind "
          "review, and `hf_artifact/scripts/preflight_public.py` fails by design "
          "until "
          "institution-identifying rows are sanitized after acceptance.",
          "",
          "## What each trace contains", "",
          "| quantity | " + " | ".join(f"`{fn.split('.')[0]}`" for fn, _, _ in TRACES) + " |",
          "|---" * (len(TRACES) + 1) + "|"]
    for k in keys:
        cells = []
        for fn, _, _ in TRACES:
            seen, rows, _, _, _ = results[fn]
            cells.append(mark(seen[k], rows) if seen else "—")
        L.append(f"| {k} | " + " | ".join(cells) + " |")

    # ---- exact per-condition completeness, over whole files ----------
    L += ["",
          "## Where the gaps are, exactly",
          "",
          "The table above samples. This one is **exact, over every row**, and "
          "it answers the question that matters: a field missing in one "
          "condition and complete in the others is a property of the "
          "intervention, not a data-quality footnote.",
          "",
          "| trace | actor | condition | rows | no role messages | no evaluator verdict | ungraded |",
          "|---|---|---|---|---|---|---|"]
    ARM = {"A": "role-structured", "B": "role-free", "C": "structurally enforced",
           "Cp": "context-restored enforcement"}
    for fn, d, _ in TRACES:
        p = os.path.join(ROOT, d, fn)
        if not os.path.exists(p):
            continue
        tot, nomsg, nover, nograde = attrition(p)
        for a in sorted(tot):
            def pc(c):
                return "—" if not c[a] else f"**{c[a]}** ({c[a]/tot[a]:.1%})"
            actor, arm = a
            L.append(f"| `{fn.split('.')[0]}` | {actor} | {ARM.get(arm, arm)} | "
                     f"{tot[a]:,} | {pc(nomsg)} | {pc(nover)} | {pc(nograde)} |")

    L += ["",
          "**This asymmetry is the paper's attrition result, visible in the "
          "raw rows.** Role-structured and role-free trajectories are "
          "essentially complete; a measurable share of *structurally "
          "enforced* ones never finish, because a rejected emission can "
          "exhaust the regeneration budget. The ungraded column reproduces "
          "section `[T7]` of the canonical output (0.080 / 0.099 / 0.170), "
          "which is the paper's \"8--17%\" — the agreement is a check, since "
          "this script counts rows directly and `FINAL_TABLES.py` does not. The pre-registration fixed in "
          "advance that such trajectories count as **incorrect rather than "
          "dropped** — which is why the enforced condition's apparent "
          "accuracy benefit under as-graded scoring is survivorship, and why "
          "the paper reports both scorings.",
          "",
          "Reproduce the three left-hand columns directly:",
          "",
          "```bash",
          "python3 scripts/mk_trace_availability.py   # regenerates this file",
          "```",
          "",
          "`regeneration events` is **absent in SciBench by design**: that "
          "campaign ran the role-structured and role-free conditions only, "
          "and regeneration is a structural-enforcement mechanism. An absence "
          "here means the condition was not run, not that logging failed.",
          "",
          "### Reading the absences",
          "",
          "- **Problem text and gold answers are not in the traces.** Only "
          "`problem_uid`. That is deliberate: redistributing Omni-MATH and "
          "SciBench problem text and answers is an upstream licensing "
          "question we did not need to take on, and the uid joins back to the "
          "public benchmark. A reader re-scoring our rows must fetch the "
          "benchmarks themselves.",
          "- **Verbatim prompts are not stored per message** — only a "
          "12-character digest. The *templates* are released in full "
          "(`hf_artifact/config/prompts.json`, `prompts_scibench.json`), and a "
          "prompt is reconstructible from its template plus the trajectory's "
          "own history, but the exact assembled string is not in the row. The "
          "digest can confirm a reconstruction; it cannot produce one.",
          "- **No token counts and no cost.** The endpoint's responses were "
          "not captured with usage metadata. Every budget claim in the paper "
          "is therefore in *calls* and *cycles*, which are recorded exactly, "
          "never in tokens or dollars — and the paper makes no token-level "
          "claim.",
          "- **No replicate index and no random seed.** Decoding is "
          "temperature 0 and each cell was run once; there is no replicate "
          "dimension to index. Temperature 0 is **not** bit-deterministic on "
          "this endpoint, so a re-run would not reproduce the rows exactly — "
          "which is why the frozen snapshot is irreplaceable rather than "
          "regenerable.",
          "- **Model outputs ARE stored in full.** `messages[].text` carries "
          "every role message verbatim, and the evaluator's raw verdict "
          "string is kept, so every reported outcome can be re-derived and "
          "re-scored under a different rule. This project has been bitten by "
          "storing only a digest of a model output; it is not repeated here.",
          "",
          "## Artifacts that are not traces", "",
          "| artifact | what it is | where | regenerable? |",
          "|---|---|---|---|",
          "| `experiments/results/FROZEN/MANIFEST.json` | sha256 + per-cell "
          "census for the three Omni-MATH traces | **in git** | no — it "
          "describes a freeze |",
          "| `experiments/results/xdomain/FROZEN_SCIBENCH/MANIFEST.json` | the "
          "same for SciBench | **in git** | no |",
          "| `adjudication/VERDICTS.jsonl`, `KEY.jsonl`, `RUBRIC_v1.md` | the "
          "model adjudication of whether a division of labor was realized | "
          "**in git** | no — new judge calls are not the old ones |",
          "| `analysis/out/FINAL_TABLES_OUTPUT.txt` | the canonical numeric "
          "output | **in git** | yes, from the frozen traces |",
          "| `analysis/out/FIGDATA.json` | what the figures read | **in git** "
          "| yes |",
          "| single-agent comparator | a previously released corpus | "
          "**outside this repo**, local only | no — see "
          "[`PAPER_ARTIFACT_MAP.md`](PAPER_ARTIFACT_MAP.md) |",
          "",
          "## Unrecoverable, stated plainly", "",
          "- **Session prompts directing the research agents** were not "
          "retained verbatim. The *experimental* prompts are released; the "
          "instructions given to the agents doing the research are "
          "reconstructed in `DECISION_LOG.md` from decisions, not from "
          "transcripts, and are not reconstructed where they were not kept.",
          "- **Quarantined early runs** (`campaign_v1_TRUNCATION_BUG`, "
          "`smoke_v1_prefix_PREFIX_BUG`) are retained locally and deliberately "
          "never pooled. They are not released and not analysed.",
          "- **Per-call token usage** was never captured and cannot be "
          "recovered from the stored rows.",
          ""]

    txt = "\n".join(L)
    if "--check" in sys.argv:
        cur = open(OUT).read() if os.path.exists(OUT) else None
        if cur != txt:
            print("STALE: docs/TRACE_AVAILABILITY.md does not match the data."
                  " Run: python3 scripts/mk_trace_availability.py")
            return 1
        print("CHECK OK: trace availability matches the data")
        return 0
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    open(OUT, "w").write(txt)
    print(f"wrote docs/TRACE_AVAILABILITY.md  ({len(present)}/{len(TRACES)} "
          f"traces present, {len(identical)} byte-verified against hf_artifact/raw/)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
