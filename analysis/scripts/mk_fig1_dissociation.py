"""Figure 1: the dissociation. Top = organizational collapse, bottom = accuracy.
A reviewer should understand the paper from this figure alone."""
import json, glob, os
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ROOT = "/Users/bellayang/Documents/note/projects/AAMAS2027-AgentProtocols"
RNG = np.random.default_rng(1)

rows = []
for f in glob.glob(ROOT + "/experiments/results/main/*.jsonl"):
    if "BUG" in f: continue
    for l in open(f):
        try: rows.append(json.loads(l))
        except Exception: pass
df = pd.DataFrame(rows)
df["actor"] = df.actor_model.str.split("/").str[-1]
df["c0"] = df.correct.fillna(0)
def coll(r):
    """PRIMARY rule: first pipeline pass only (first 3 role messages).
    The all-message rule is confounded with trajectory length -- longer
    trajectories get more chances to collapse, and the actors differ in
    length. See COLLAPSE_MEASUREMENT_AUDIT.md round 2."""
    h = [m.get("response_sha256_12") for m in (r.get("messages") or [])
         if m.get("role") in ("planner","executor","reviewer")
         and m.get("response_sha256_12")][:3]
    return (len(set(h)) < len(h)) if len(h) >= 2 else np.nan
df["collapse"] = [coll(r) for r in rows]

ARMS = ["A","B","C"]
LBL = {"A":"A\nsoft roles","B":"B\nno roles","C":"C\nenforced"}
ACT = ["gpt-oss-120b","gemma-4-31B-it"]
COL = {"gpt-oss-120b":"#2166ac","gemma-4-31B-it":"#b2182b"}

def ci(v):
    v = np.asarray(v,float); v = v[~np.isnan(v)]
    if len(v) < 3: return np.nan, np.nan, np.nan
    b = RNG.choice(v,(3000,len(v))).mean(1)
    return v.mean(), *np.percentile(b,[2.5,97.5])

fig, ax = plt.subplots(2,1, figsize=(6.4,5.4), sharex=True,
                       gridspec_kw={"hspace":0.13})
x = np.arange(len(ARMS))
for k,a in enumerate(ACT):
    off = (k-0.5)*0.17
    for i,(metric,axis) in enumerate([("collapse",ax[0]),("c0",ax[1])]):
        m,lo,hi = [],[],[]
        for arm in ARMS:
            g = df[(df.actor==a)&(df.arm==arm)][metric]
            v = ci(g.values); m.append(v[0]); lo.append(v[0]-v[1]); hi.append(v[2]-v[0])
        axis.errorbar(x+off, m, yerr=[lo,hi], marker="o", ms=7, lw=2.2,
                      capsize=3, color=COL[a], label=a if i==0 else None)

ax[0].set_ylabel("organizational collapse\n(identical outputs, first pass)")
ax[0].set_ylim(-0.05,1.0); ax[0].grid(alpha=.25, axis="y")
ax[0].legend(frameon=False, fontsize=9, loc="center left")
ax[0].set_title("Organization moves a lot.  Accuracy does not.", fontsize=11, pad=8)
ax[1].set_ylabel("task accuracy")
ax[1].set_ylim(0.70,0.95); ax[1].grid(alpha=.25, axis="y")
ax[1].set_xticks(x); ax[1].set_xticklabels([LBL[a] for a in ARMS])
for s in ("top","right"):
    ax[0].spines[s].set_visible(False); ax[1].spines[s].set_visible(False)
fig.savefig(ROOT+"/figures/fig1_dissociation.pdf", bbox_inches="tight")
fig.savefig(ROOT+"/figures/fig1_dissociation.png", dpi=180, bbox_inches="tight")

print("=== numbers behind Figure 1 ===")
for a in ACT:
    for arm in ARMS:
        g = df[(df.actor==a)&(df.arm==arm)]
        c = ci(g.collapse.values); q = ci(g.c0.values)
        print(f"  {a:16s} {arm}  n={len(g):4d}  collapse={c[0]:.3f} [{c[1]:.3f},{c[2]:.3f}]"
              f"   acc={q[0]:.3f} [{q[1]:.3f},{q[2]:.3f}]")
print("\nwrote figures/fig1_dissociation.{pdf,png}")
