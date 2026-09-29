import re,sys
t=open('blinded/BLINDED_TRAJECTORIES.md').read()
parts=re.split(r'^={94}$', t, flags=re.M)[1:]
a,b=int(sys.argv[1]),int(sys.argv[2])
H={'planner':1500,'executor':2000,'reviewer':2000}
T={'planner':700,'executor':1000,'reviewer':700}
for p in parts:
    tid=re.search(r'## (T\d\d\d)',p).group(1); n=int(tid[1:])
    if not(a<=n<=b): continue
    print('\n'+'#'*72); print(tid)
    for m in re.finditer(r'### \[(\w+)\]  \((\d+) chars\)\n\n```\n(.*?)\n```', p, re.S):
        role,ch,txt=m.group(1),int(m.group(2)),m.group(3)
        h,tl=H[role],T[role]
        if len(txt)>h+tl: txt=txt[:h]+f'\n<<<cut {len(txt)-h-tl}>>>\n'+txt[-tl:]
        print(f'--[{role}] {ch}ch--'); print(txt)
