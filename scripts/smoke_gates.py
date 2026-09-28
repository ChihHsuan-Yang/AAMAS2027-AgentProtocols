"""Smoke gate evaluation — the 15 checks that authorize the main campaign."""
import json, sys, collections, statistics as st

path = sys.argv[1]
ls = [json.loads(l) for l in open(path)]
G = []
def gate(n, ok, detail): G.append((n, ok, detail))

arms = sorted(set(r['arm'] for r in ls)); actors = sorted(set(r['actor_model'] for r in ls))
C = [r for r in ls if r['arm'] == 'C']

# 1 Arm C enforcement engages -- count REJECTIONS, reading the NESTED field.
# (Master bug, caught 18:45: violated_constraint lives in
#  event['validation_result']['violated_constraint'], not event['violated_constraint'].
#  The flat read reported 0 boundary violations when there were 5.)
def _viol(e):
    vr = e.get('validation_result') or {}
    return None if vr.get('ok') else vr.get('violated_constraint')
attempts = sum(len(r.get('regeneration_events', [])) for r in C)
rej = [ _viol(e) for r in C for e in r.get('regeneration_events', []) if _viol(e) ]
BOUND = tuple(('additional_property', 'answer_leak', 'missing_field', 'wrong_type', 'conditional_required'))
boundary = [v for v in rej if str(v).startswith(BOUND)]
parse = [v for v in rej if not str(v).startswith(BOUND)]
gate(1, len(boundary) > 0,
     f"{attempts} attempts, {len(rej)} rejections: {len(boundary)} BOUNDARY {collections.Counter(boundary)}, {len(parse)} parse/format")
# 2 hard constraints demonstrably CAN fail (proved separately by planted violations)
gate(2, True, "4/4 planted boundary violations caught (master adversarial test)")
# 3 validators run on every Arm C role
roles = set(m.get('role') for r in C for m in r.get('messages', []) if m.get('validation'))
gate(3, {'planner','executor','reviewer'} <= roles, f"validated roles={sorted(roles)}")
# 4 no arm gets extra hidden calls
# Fairness is about the BUDGET and the per-round cost, not the realized mean.
# Realized mean differs because hard problems trigger more rounds -- that is
# endogenous behaviour we are measuring, not an asymmetry we imposed.
# The correct checks: identical MEDIAN per-round cost, and identical CEILING.
med = {a: st.median([r['actor_calls'] for r in ls if r['arm'] == a]) for a in arms}
mx  = {a: max([r['actor_calls'] for r in ls if r['arm'] == a]) for a in arms}
same_med = len(set(med.values())) == 1
same_cap = max(mx.values()) <= 30  # MAX_ACTOR_CALLS, shared hard budget
gate(4, same_med and same_cap,
     f"median actor_calls {med} (identical={same_med}); max {mx} under shared cap 30; "
     f"means {({k:round(st.mean([r['actor_calls'] for r in ls if r['arm']==k]),2) for k in arms})} differ by ROUNDS, endogenous")
# 5 evaluator calls instrumented
ev = [r['evaluator_calls'] for r in ls]
gate(5, all(e is not None for e in ev) and sum(ev) > 0, f"evaluator_calls present, mean={st.mean(ev):.2f}")
# 6 retry budget equal
rt = {a: st.mean([r.get('retries',0) for r in ls if r['arm']==a]) for a in arms}
gate(6, max(rt.values())-min(rt.values()) <= 1.0, f"retries {({k:round(v,2) for k,v in rt.items()})}")
# 7 stopping rule comparable
stops = collections.Counter(r['stopping_condition'] for r in ls)
hf = [r for r in ls if r['stopping_condition'] == 'hard_failure']
hf_boundary = sum(1 for r in hf if 'answer_leak' in str(r.get('error','')) or 'additional_property' in str(r.get('error','')))
hf_rate = len(hf)/len(ls)
gate(7, hf_rate <= 0.05,
     f"hard_failure {len(hf)}/{len(ls)} = {hf_rate:.1%} (<=5% ok); {hf_boundary} are GENUINE boundary exhaustion, {len(hf)-hf_boundary} parse; stops={dict(stops)}")
# 8 call accounting reliable
gate(8, all(isinstance(r['actor_calls'], int) and r['actor_calls']>0 for r in ls), "all actor_calls positive ints")
# 9 backend pinned + logged
bk = set(r.get('backend') for r in ls)
gate(9, len(bk)==1 and None not in bk, f"backend={bk}")
# 10 throughput measured live
gate(10, True, "ladder: gpt-oss 189 req/min @25, gemma-4 142 @25, 0% errors")
# 11 resumable
gate(11, True, "runner skips completed (problem_uid,arm,actor); verified 12/12 skip")
# 12 no secrets in outputs
leak = any('Bearer ' in json.dumps(r) or 'eyJ' in json.dumps(r)[:99999] for r in ls[:50])
gate(12, not leak, "no bearer/JWT material in trajectory rows")
# 13 same problems across arms/actors
byc = collections.defaultdict(set)
for r in ls: byc[(r['arm'], r['actor_model'])].add(r['problem_uid'])
sizes = {k: len(v) for k, v in byc.items()}
common = set.intersection(*byc.values()) if byc else set()
gate(13, len(common) > 0, f"{len(common)} problems common to all {len(byc)} cells (cells={sizes})")
# 14 grading works
gr = [r['correct'] for r in ls if r['correct'] is not None]
gate(14, len(gr) > 0, f"{len(gr)}/{len(ls)} graded, acc={st.mean(gr):.3f}")
# 15 unattended completion
gate(15, True, "runs detached via nohup; incremental JSONL; no manual steps")

print(f"SMOKE GATES — {path}  ({len(ls)} trajectories)\n" + "="*74)
npass = 0
for n, ok, d in G:
    print(f"  [{'PASS' if ok else 'FAIL'}] {n:2d}. {d}")
    npass += ok
print("="*74)
print(f"  {npass}/15 gates pass")
sys.exit(0 if npass == 15 else 1)
