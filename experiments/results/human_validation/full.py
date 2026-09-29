import re,sys
t=open('blinded/BLINDED_TRAJECTORIES.md').read()
parts=re.split(r'^={94}$', t, flags=re.M)[1:]
tid=sys.argv[1]; role=sys.argv[2] if len(sys.argv)>2 else None
for p in parts:
    if re.search(r'## '+tid+r'\b',p):
        for m in re.finditer(r'### \[(\w+)\]  \((\d+) chars\)\n\n```\n(.*?)\n```', p, re.S):
            if role and m.group(1)!=role: continue
            print(f'--[{m.group(1)}] {m.group(2)}ch--'); print(m.group(3))
