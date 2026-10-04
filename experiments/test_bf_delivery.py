#!/usr/bin/env python3
"""Offline check of Arm Bf (role-free + evaluator feedback delivered).

Zero API calls: uses the runner's own dry-run stub (first evaluator verdict
FAIL, later ones PASS). Asserts, for runner.py and runner_xdomain.py:

  1. Arm B prompts never contain the evaluator's feedback (the defect).
  2. Arm Bf prompts are byte-identical to Arm B's until the first FAIL.
  3. After a FAIL, every Arm Bf prompt of the next cycle contains exactly the
     advice string Arm A receives in ${advice}, and nothing else differs
     from the Arm B prompt at the same position.
  4. The per-message flag evaluator_feedback_in_prompt agrees with the prompt.

Run:  python3 experiments/test_bf_delivery.py      (exit 0 = all pass)
"""
import asyncio, importlib, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

FAIL_ADVICE = ("Evaluator feedback: FAIL / Score: False\n"
               "Repair hint: answer-shape mismatch; give a general family.")


def run(mod, arm):
    R = importlib.import_module(mod)
    backend = R.Backend(R.TokenProvider(dry_run=True), dry_run=True,
                        stub=R.StubResponder())
    seen = []
    orig = backend.chat

    async def chat(model, messages, *a, **kw):
        tag = kw.get("tag") or (a[0] if a else "")
        if not str(tag).endswith("|evaluator"):
            seen.append(messages[0]["content"])
        return await orig(model, messages, *a, **kw)

    backend.chat = chat
    traj = asyncio.run(R.run_trajectory(
        R.STUB_PROBLEMS[0], arm, "stub/actor", backend, "test"))
    return seen, traj


ok = True
def check(cond, msg):
    global ok
    print(("PASS  " if cond else "FAIL  ") + msg)
    ok = ok and bool(cond)


for mod in ("runner", "runner_xdomain"):
    print("== {}".format(mod))
    pa, ta = run(mod, "A")
    pb, tb = run(mod, "B")
    pf, tf = run(mod, "Bf")
    check(len(pb) == len(pf) == 6, "B and Bf both run 2 cycles (FAIL then PASS): %d, %d prompts" % (len(pb), len(pf)))
    check(any(FAIL_ADVICE in p for p in pa[3:6]), "Arm A sees the evaluator feedback in cycle 2 (reference behaviour)")
    check(not any("Evaluator feedback" in p for p in pb), "Arm B prompts never contain evaluator feedback")
    check(pb[:3] == pf[:3], "Bf prompts are byte-identical to B before the first FAIL")
    block = "[Evaluator]\n" + FAIL_ADVICE
    check(all(p.count(block) == 1 for p in pf[3:6]), "every Bf prompt in the cycle after FAIL contains the feedback exactly once")
    check(all(pf[i].replace("\n\n" + block, "") == pb[i] for i in range(3, 6)),
          "removing that block from a Bf prompt gives the B prompt exactly")
    msgs = [m for m in tf.messages if m.get("role") in ("planner", "executor", "reviewer")]
    flags = [m.get("evaluator_feedback_in_prompt") for m in msgs]
    check(flags == [False] * 3 + [True] * 3, "logged flag matches: %s" % flags)
    check(tf.arm == "Bf" and tf.evaluator_calls == tb.evaluator_calls == 2, "evaluator calls: Bf=%d B=%d" % (tf.evaluator_calls, tb.evaluator_calls))

print("\nALL PASS" if ok else "\nSOME CHECKS FAILED")
sys.exit(0 if ok else 1)
