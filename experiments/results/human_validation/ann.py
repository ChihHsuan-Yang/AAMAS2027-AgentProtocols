#!/usr/bin/env python3
"""Append annotation rows. Usage: ann.py TID Q1E Q2E Q3E Q4E Q1R Q2R Q3R Q4R Q5 "reason"
   Values: Y N U"""
import sys, json, os
F='ANNOTATIONS.jsonl'
a=sys.argv[1:]
assert len(a)==11, f'need 11 args, got {len(a)}'
tid=a[0]; vals=a[1:10]; reason=a[10]
for v in vals: assert v in ('Y','N','U'), v
row=dict(tid=tid, Q1_E=vals[0],Q2_E=vals[1],Q3_E=vals[2],Q4_E=vals[3],
         Q1_R=vals[4],Q2_R=vals[5],Q3_R=vals[6],Q4_R=vals[7],Q5=vals[8], reason=reason)
seen=set()
if os.path.exists(F):
    seen={json.loads(l)['tid'] for l in open(F)}
assert tid not in seen, f'{tid} already annotated'
with open(F,'a') as f: f.write(json.dumps(row)+'\n')
print('ok', tid, sum(1 for _ in open(F)))
