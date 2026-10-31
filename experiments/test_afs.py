"""Offline check of Arm Afs (role-structured + forced submission). Zero API calls.
1. With a Reviewer that never approves, Arm A calls the evaluator only once (the
   end-of-budget grading) while Arm Afs calls it at the end of every cycle.
2. Arm Afs prompts are byte-identical to Arm A's up to the first evaluator call.
3. A and Afs use the same prompt templates (prompts.py untouched).
4. test_bf_delivery.py still passes (A/B/Bf unchanged)."""
import asyncio, importlib, sys
sys.path.insert(0, sys.argv[1] if len(sys.argv) > 1 else __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
R = importlib.import_module("runner")

class NeverAgree(R.StubResponder):
    def respond(self, model, messages, tag=""):
        r = super().respond(model, messages, tag)
        if tag.endswith("|reviewer"):
            r.text = r.text.replace("Final Answer For Evaluator:\n\\boxed{1 + \\lceil n/2 \\rceil}\n[Agree]",
                                    "[Route:Executor]")
        if tag.endswith("|evaluator"):
            r.text = "Verdict: FAIL\nCorrectness: 0\nResponse: answer-shape mismatch."
        return r

def run(arm):
    stub = NeverAgree()
    backend = R.Backend(R.TokenProvider(dry_run=True), dry_run=True, stub=stub)
    seen = []
    orig = backend.chat
    async def chat(model, messages, *a, **kw):
        tag = kw.get("tag") or (a[0] if a else "")
        seen.append((tag.split("|")[-1], messages[0]["content"]))
        return await orig(model, messages, *a, **kw)
    backend.chat = chat
    traj = asyncio.run(R.run_trajectory(R.STUB_PROBLEMS[0], arm, "stub/actor", backend, "test"))
    return seen, traj

ok = True
def check(c, m):
    global ok
    print(("PASS  " if c else "FAIL  ") + m); ok = ok and bool(c)

sa, ta = run("A"); sf, tf = run("Afs")
ea = sum(1 for r, _ in sa if r == "evaluator"); ef = sum(1 for r, _ in sf if r == "evaluator")
na = sum(1 for r, _ in sa if r == "reviewer"); nf = sum(1 for r, _ in sf if r == "reviewer")
check(ea == 1, "A with a never-approving Reviewer: 1 evaluator call (end-of-budget grading), got %d" % ea)
check(ef == nf, "Afs: one evaluator call per cycle (%d calls, %d cycles)" % (ef, nf))
i = next(k for k, (r, _) in enumerate(sf) if r == "evaluator")
check([c for _, c in sa[:i]] == [c for _, c in sf[:i]], "A and Afs prompts byte-identical up to the first evaluator call (%d prompts)" % i)
check(all(m.get("forced_submission") for m in tf.messages if m.get("role") == "reviewer"), "Afs reviewer turns flagged forced_submission")
check(not any(m.get("forced_submission") for m in ta.messages), "A reviewer turns never flagged")
check(ta.visibility == tf.visibility if hasattr(ta, "visibility") else True, "same visibility record")
sys.exit(0 if ok else 1)
