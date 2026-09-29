import re,sys
t=open('blinded/BLINDED_TRAJECTORIES.md').read()
parts=re.split(r'^={94}$', t, flags=re.M)[1:]
a,b=int(sys.argv[1]),int(sys.argv[2])
HEAD={'planner':1400,'executor':1800,'reviewer':1800}
TAIL={'planner':500,'executor':700,'reviewer':500}
for p in parts:
    tid=re.search(r'## (T\d\d\d)',p).group(1); n=int(tid[1:])
    if not(a<=n<=b): continue
    print('\n'+'#'*70); print(tid)
    for m in re.finditer(r'### \[(\w+)\]  \((\d+) chars\)\n\n```\n(.*?)\n```', p, re.S):
        role,ch,txt=m.group(1),m.group(2),m.group(3)
        h,tl=HEAD[role],TAIL[role]
        if len(txt)>h+tl: txt=txt[:h]+f'\n ...[cut {len(txt)-h-tl} chars]... \n'+txt[-tl:]
        print(f'--[{role}] {ch}ch--'); print(txt)
