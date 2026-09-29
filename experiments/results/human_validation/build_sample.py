#!/usr/bin/env python3
"""Build the blinded stratified sample per the FROZEN rubric (seed 20260929)."""
import json, random, os, collections

SNAP='experiments/results/human_validation/SNAPSHOT_campaign_v2_frozen.jsonl'
OUT='experiments/results/human_validation'
SEED=20260929
DEV_LINES={1,4,10}          # rubric development set, excluded
TARGET_PER_CELL=18   # see rubric AMENDMENT A1

rows=[]
for i,line in enumerate(open(SNAP)):
    if i in DEV_LINES: continue
    r=json.loads(line)
    if r['arm'] not in ('A','B'): continue
    if r['correct'] is None: continue
    rm=[m for m in r['messages'] if m.get('role') in ('planner','executor','reviewer')]
    f3=rm[:3]
    if len(f3)!=3: continue
    coll = len(set(m['response_sha256_12'] for m in f3))<3
    rows.append(dict(line_no=i, arm=r['arm'], actor=r['actor_model'],
                     uid=r['problem_uid'], correct=r['correct'], collapse=coll,
                     hashes=[m['response_sha256_12'] for m in f3],
                     roles=[m['role'] for m in f3],
                     texts=[m['text'] for m in f3],
                     nmsg_total=len(rm),
                     rounds_used=r.get('rounds_used'),
                     final_answer=r.get('final_answer')))

cells=collections.defaultdict(list)
for r in rows:
    cells[(r['arm'], r['actor'], r['collapse'], r['correct'])].append(r)

print('=== ELIGIBLE POPULATION BY CELL ===')
for k in sorted(cells, key=str):
    print(f'  {k}: {len(cells[k])}')

rng=random.Random(SEED)
sample=[]
for k in sorted(cells, key=str):
    pool=sorted(cells[k], key=lambda r:(r['uid'], r['line_no']))
    take=min(TARGET_PER_CELL, len(pool))
    sample.extend(rng.sample(pool, take))

rng.shuffle(sample)
for n,r in enumerate(sample, 1):
    r['tid']=f'T{n:03d}'

os.makedirs(f'{OUT}/blinded', exist_ok=True)

# blinded readable file (single file, easier to annotate linearly)
with open(f'{OUT}/blinded/BLINDED_TRAJECTORIES.md','w') as f:
    f.write('# Blinded trajectories for human collapse annotation\n\n')
    f.write('Arm, actor, collapse flag, correctness, hashes and problem_uid are WITHHELD.\n')
    f.write(f'n = {len(sample)}. Seed {SEED}. Rubric: notes/COLLAPSE_ANNOTATION_RUBRIC.md\n\n')
    for r in sample:
        f.write('\n'+'='*94+'\n')
        f.write(f"## {r['tid']}\n\n")
        for role,txt in zip(r['roles'], r['texts']):
            f.write(f"### [{role}]  ({len(txt)} chars)\n\n```\n")
            f.write(txt if len(txt)<=6000 else txt[:6000]+'\n...[TRUNCATED FOR DISPLAY]...')
            f.write('\n```\n\n')

# key file, held separately
with open(f'{OUT}/SAMPLE_KEY.jsonl','w') as f:
    for r in sample:
        f.write(json.dumps({k:r[k] for k in
            ('tid','line_no','arm','actor','uid','correct','collapse','hashes',
             'roles','nmsg_total','rounds_used','final_answer')})+'\n')

# per-trajectory char lengths, for the record (not used for judging)
print(f'\n=== SAMPLE n={len(sample)} ===')
c=collections.Counter((r['arm'],r['actor'],r['collapse'],r['correct']) for r in sample)
for k in sorted(c, key=str): print(f'  {k}: {c[k]}')
