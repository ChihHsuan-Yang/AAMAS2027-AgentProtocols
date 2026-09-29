#!/usr/bin/env python3
"""Unblind and compute the pre-declared analysis (rubric Part 3)."""
import json, collections, itertools

ann={json.loads(l)['tid']: json.loads(l) for l in open('ANNOTATIONS.jsonl')}
key={json.loads(l)['tid']: json.loads(l) for l in open('SAMPLE_KEY.jsonl')}
assert set(ann)==set(key), 'tid mismatch'
rows=[]
for t in sorted(ann):
    r=dict(ann[t]); r.update(key[t]); rows.append(r)

def yn(v): return {'Y':True,'N':False,'U':None}[v]

for r in rows:
    r['Q1_any']= yn(r['Q1_E']) or yn(r['Q1_R'])
    r['Q2_any']= yn(r['Q2_E']) or yn(r['Q2_R'])
    r['Q4_any']= yn(r['Q4_E']) or yn(r['Q4_R'])
    r['Q3_all']= yn(r['Q3_E']) and yn(r['Q3_R'])
    r['Q3_any']= yn(r['Q3_E']) or yn(r['Q3_R'])
    r['Q5b']  = yn(r['Q5'])
    r['actorS']= 'gpt-oss' if 'gpt-oss' in r['actor'] else 'gemma-4'

print('='*78); print('UNCLEAR COUNT'); print('='*78)
u=sum(1 for r in rows if r['Q5']=='U'); print(f'  Q5 = UNCLEAR: {u} (excluded from agreement)')

def confusion(sub, label):
    # flag positive = collapse True ; human positive = Q5 == NO (no division of labor)
    tp=fp=fn=tn=0
    for r in sub:
        if r['Q5b'] is None: continue
        f=r['collapse']; h=(r['Q5b']==False)
        if f and h: tp+=1
        elif f and not h: fp+=1
        elif (not f) and h: fn+=1
        else: tn+=1
    n=tp+fp+fn+tn
    if n==0: print(f'\n{label}: empty'); return
    agree=(tp+tn)/n
    prec = tp/(tp+fp) if tp+fp else float('nan')
    rec  = tp/(tp+fn) if tp+fn else float('nan')
    # Cohen's kappa
    po=agree
    p_f=(tp+fp)/n; p_h=(tp+fn)/n
    pe=p_f*p_h + (1-p_f)*(1-p_h)
    kappa=(po-pe)/(1-pe) if pe!=1 else float('nan')
    print(f'\n{label}  (n={n})')
    print(f'                      human Q5=NO   human Q5=YES')
    print(f'  flag collapse=T        {tp:5d}         {fp:5d}')
    print(f'  flag collapse=F        {fn:5d}         {tn:5d}')
    print(f'  raw agreement = {agree:.3f}   precision = {prec:.3f}   recall = {rec:.3f}   kappa = {kappa:.3f}')
    return dict(tp=tp,fp=fp,fn=fn,tn=tn,agree=agree,prec=prec,rec=rec,kappa=kappa)

print('\n'+'='*78); print('1. AUTOMATED EXACT-COLLAPSE FLAG vs HUMAN Q5'); print('='*78)
confusion(rows, 'POOLED over arms A+B, both actors  [CONFOUNDED - see rubric Part 3]')
confusion([r for r in rows if r['arm']=='B' and r['actorS']=='gpt-oss'],
          'WITHIN (arm B x gpt-oss) only  [the honest number: this is where the flag varies]')
confusion([r for r in rows if r['arm']=='A'], 'Arm A only (flag never fires)')
confusion([r for r in rows if r['actorS']=='gemma-4'], 'gemma-4 only (flag never fires)')

print('\n'+'='*78); print('2. Q5 = NO RATE (no meaningful division of labor), BY CELL'); print('='*78)
print(f'{"arm":>4} {"actor":>9} {"collapse":>9} {"n":>4} {"Q5=NO":>6} {"rate":>7}')
for k in sorted({(r['arm'],r['actorS'],r['collapse']) for r in rows}, key=str):
    sub=[r for r in rows if (r['arm'],r['actorS'],r['collapse'])==k and r['Q5b'] is not None]
    no=sum(1 for r in sub if r['Q5b']==False)
    print(f'{k[0]:>4} {k[1]:>9} {str(k[2]):>9} {len(sub):>4} {no:>6} {no/len(sub):>7.3f}')

print('\n  --- by arm (pooled over actors) ---')
for a in ['A','B']:
    sub=[r for r in rows if r['arm']==a and r['Q5b'] is not None]
    no=sum(1 for r in sub if r['Q5b']==False)
    print(f'   arm {a}: {no}/{len(sub)} = {no/len(sub):.3f} judged NO division of labor')
print('\n  --- by arm x actor ---')
for a in ['A','B']:
    for ac in ['gpt-oss','gemma-4']:
        sub=[r for r in rows if r['arm']==a and r['actorS']==ac and r['Q5b'] is not None]
        no=sum(1 for r in sub if r['Q5b']==False)
        print(f'   arm {a} / {ac:>8}: {no}/{len(sub)} = {no/len(sub):.3f}')

print('\n'+'='*78); print('3. Q1-Q4 RATES PER ARM PER ACTOR (rollups; frozen rules)'); print('='*78)
print(f'{"arm":>4} {"actor":>9} {"n":>4} | {"Q1any":>6} {"Q2any":>6} {"Q3all":>6} {"Q3any":>6} {"Q4any":>6}')
for a in ['A','B']:
    for ac in ['gpt-oss','gemma-4']:
        sub=[r for r in rows if r['arm']==a and r['actorS']==ac]
        n=len(sub)
        f=lambda k: sum(1 for r in sub if r[k])/n
        print(f'{a:>4} {ac:>9} {n:>4} | {f("Q1_any"):>6.3f} {f("Q2_any"):>6.3f} {f("Q3_all"):>6.3f} {f("Q3_any"):>6.3f} {f("Q4_any"):>6.3f}')

print('\n  --- per role (E = executor rel. planner, R = reviewer rel. planner+executor) ---')
print(f'{"arm":>4} {"actor":>9} | {"Q1E":>5} {"Q2E":>5} {"Q3E":>5} {"Q4E":>5} | {"Q1R":>5} {"Q2R":>5} {"Q3R":>5} {"Q4R":>5}')
for a in ['A','B']:
    for ac in ['gpt-oss','gemma-4']:
        sub=[r for r in rows if r['arm']==a and r['actorS']==ac]; n=len(sub)
        g=lambda k: sum(1 for r in sub if r[k]=='Y')/n
        print(f'{a:>4} {ac:>9} | '+' '.join(f'{g(k):>5.2f}' for k in ['Q1_E','Q2_E','Q3_E','Q4_E'])
              +' | '+' '.join(f'{g(k):>5.2f}' for k in ['Q1_R','Q2_R','Q3_R','Q4_R']))

print('\n'+'='*78); print('4. Q5 BY CORRECTNESS'); print('='*78)
for a in ['A','B']:
    for c in [0,1]:
        sub=[r for r in rows if r['arm']==a and r['correct']==c and r['Q5b'] is not None]
        no=sum(1 for r in sub if r['Q5b']==False)
        print(f'   arm {a} correct={c}: {no}/{len(sub)} = {no/len(sub):.3f} NO division')

print('\n'+'='*78); print('5. CONFUSION CASES (enumerated)'); print('='*78)
fp=[r for r in rows if r['collapse'] and r['Q5b']==True]
fn=[r for r in rows if (not r['collapse']) and r['Q5b']==False]
print(f'\n  (a) flag says COLLAPSE but human sees REAL DIVISION OF LABOUR: n={len(fp)}')
for r in fp: print(f'      {r["tid"]} {r["arm"]}/{r["actorS"]} correct={r["correct"]} :: {r["reason"][:120]}')
print(f'\n  (b) flag says NO COLLAPSE but human sees NO DIVISION OF LABOUR: n={len(fn)}')
for r in fn[:200]: print(f'      {r["tid"]} {r["arm"]}/{r["actorS"]} correct={r["correct"]} :: {r["reason"][:115]}')

print('\n'+'='*78); print('6. WHAT THE FLAG ACTUALLY TRACKS: exact/semantic/functional'); print('='*78)
# Q3_all (every later role mainly restated) is the human "all-redundant" signal
for a in ['A','B']:
    for ac in ['gpt-oss','gemma-4']:
        for c in [True,False]:
            sub=[r for r in rows if r['arm']==a and r['actorS']==ac and r['collapse']==c]
            if not sub: continue
            q3=sum(1 for r in sub if r['Q3_all'])
            q5=sum(1 for r in sub if r['Q5b']==False)
            print(f'   {a}/{ac:>8} collapse={str(c):>5} n={len(sub):>3}  Q3_all(every later role restates)={q3/len(sub):.3f}  Q5=NO={q5/len(sub):.3f}')
