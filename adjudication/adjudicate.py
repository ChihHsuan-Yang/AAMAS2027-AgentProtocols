"""Blinded frontier-model adjudication of organizational collapse.

Primary judge: Opus 5 (claude-opus-5). Each item is judged K times with
independent calls so judge stability can be estimated; disagreements are
recorded, never averaged away silently.

Audit trail written per call: model id, decoding settings, rubric hash,
prompt hash, timestamp, raw output, parsed labels.
"""
import argparse, hashlib, json, os, random, sys, time
from datetime import datetime, timezone
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RUBRIC = open(HERE + "/RUBRIC_v1.md").read()
RUBRIC_SHA = hashlib.sha256(RUBRIC.encode()).hexdigest()[:16]

SYSTEM = """You are adjudicating transcripts from a three-agent AI system that solves mathematics problems. Three agents act in sequence on the same problem.

Judge ONLY what the transcript shows. You are not told which system produced it, what configuration it used, or whether the final answer was right. Do not speculate about those. There is no expected or preferred answer to any question below.

Apply this rubric exactly:

{rubric}

Return STRICT JSON only, no prose before or after:
{{"Q1":"YES|NO","Q2":"YES|NO","Q3":"YES|NO","Q4":"YES|NO","Q5":"YES|NO","reason":"<=25 words"}}"""

def _judge_creds():
    """Resolve judge endpoint + token. Uses the local argo-shim when present
    (ANTHROPIC_BASE_URL + apiKeyHelper from ~/.claude/settings.json), else the
    public API with ANTHROPIC_API_KEY. NEVER logs the token."""
    import subprocess
    base = (os.environ.get("ANTHROPIC_BASE_URL") or "https://api.anthropic.com").rstrip("/")
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        try:
            cfg = json.load(open(os.path.expanduser("~/.claude/settings.json")))
            h = cfg.get("apiKeyHelper")
            if h:
                key = subprocess.run(h, shell=True, capture_output=True,
                                     text=True, timeout=30).stdout.strip()
        except Exception:
            key = None
    return base, key


def call_judge(transcript, model, temperature, seed_note):
    base, key = _judge_creds()
    if not key:
        return None, "no judge credential available"
    # NOTE: the judge endpoint rejects `temperature` ("deprecated"), so decoding
    # is left at the served default. Judge stability is therefore estimated
    # empirically from repeated independent calls (--reps), which is the more
    # meaningful check anyway. Recorded in the audit trail as temperature=null.
    body = json.dumps({
        "model": model, "max_tokens": 1200,
        "system": SYSTEM.format(rubric=RUBRIC),
        "messages": [{"role": "user",
                      "content": f"Transcript to adjudicate:\n\n{transcript}\n\nReturn the JSON verdict."}],
    }).encode()
    req = urllib.request.Request(
        base + "/v1/messages", data=body,
        headers={"x-api-key": key, "anthropic-version": "2023-06-01",
                 "content-type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            d = json.loads(r.read().decode())
        return "".join(b.get("text", "") for b in d.get("content", [])), None
    except Exception as e:
        return None, f"{type(e).__name__}: {str(e)[:200]}"

def parse(txt):
    """Parse a verdict. Salvages responses truncated mid-JSON by max_tokens:
    29/125 of the first batch were cut off after Q4 with all five labels
    recoverable by regex. Discarding them would have silently biased coverage
    toward short verdicts."""
    if not txt: return None
    s = txt.strip()
    i, j = s.find("{"), s.rfind("}")
    o = None
    if i >= 0 and j > i:
        try: o = json.loads(s[i:j+1])
        except Exception: o = None
    if o is None:
        import re as _re
        o = {}
        for q in ("Q1","Q2","Q3","Q4","Q5"):
            m = _re.search(rf'"{q}"\s*:\s*"(YES|NO)"', s)
            if not m: return None
            o[q] = m.group(1)
        m = _re.search(r'"reason"\s*:\s*"([^"]*)', s)
        o["reason"] = m.group(1) if m else ""
    out = {}
    for q in ("Q1","Q2","Q3","Q4","Q5"):
        v = str(o.get(q, "")).strip().upper()
        if v not in ("YES","NO"): return None
        out[q] = v
    out["reason"] = str(o.get("reason",""))[:200]
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="claude-opus-5")
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--out", default=HERE + "/VERDICTS.jsonl")
    a = ap.parse_args()

    items = [json.loads(l) for l in open(HERE + "/ITEMS_blinded.jsonl")]
    if a.limit: items = items[:a.limit]
    done = set()
    if os.path.exists(a.out):
        for l in open(a.out):
            try:
                v = json.loads(l); done.add((v["tid"], v["rep"]))
            except Exception: pass
    print(f"items={len(items)} reps={a.reps} model={a.model} rubric={RUBRIC_SHA} "
          f"already_done={len(done)}")

    rng = random.Random(20260929)
    todo = [(it, rep) for rep in range(a.reps) for it in items
            if (it["tid"], rep) not in done]
    rng.shuffle(todo)                      # randomize presentation order
    ok = err = 0
    with open(a.out, "a") as fh:
        for n, (it, rep) in enumerate(todo, 1):
            raw, e = call_judge(it["transcript"], a.model, a.temperature, rep)
            rec = {"tid": it["tid"], "rep": rep, "model": a.model,
                   "temperature": None, "rubric_sha": RUBRIC_SHA,
                   "prompt_sha": hashlib.sha256(it["transcript"].encode()).hexdigest()[:16],
                   "utc": datetime.now(timezone.utc).isoformat(),
                   "raw": (raw or "")[:2000], "error": e}
            p = parse(raw)
            rec["parsed"] = p
            fh.write(json.dumps(rec) + "\n"); fh.flush()
            ok += bool(p); err += bool(e)
            if n % 20 == 0 or e:
                print(f"  {n}/{len(todo)} ok={ok} err={err}" + (f" last_err={e}" if e else ""))
            if e and "no ANTHROPIC_API_KEY" in str(e):
                print("ABORT: no API key available; cannot run the judge."); return 2
    print(f"done: parsed={ok} errors={err}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
