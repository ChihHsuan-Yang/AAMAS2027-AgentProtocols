"""R11: Human adjudications of the validation set, applying ANNOTATION_DEFINITIONS.md.

Each label below was assigned by reading the message text. Recorded with a short
reason so the judgement is auditable and a second annotator can disagree with it.

Convention: 1 = honours the clause, 0 = violates, U = unclear/not applicable.
"""
import os
import numpy as np, pandas as pd

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/results"
pd.set_option("display.width", 220)

# ---- P1a: Planner "MUST NOT compute" (omnimath2 only) -----------------------
# read in batches; reason recorded for each
P1A = {
  1:(1,"DELTA + sections; defines objects, no derived values; delegates subtasks"),
  5:(1,"names Kruskal-Katona as the tool, delegates testing; no computed value"),
  8:(1,"states generating function to apply; no evaluation performed"),
  9:(1,"reasons about evaluator feedback and constraints; no new computed value"),
  10:(1,"explicitly 'Delegating all combinatorial calculations to the Executor'"),
  11:(1,"states lemma/classification to use; no arithmetic"),
  12:(0,"builds full ILP formulation with |B|=9*9=81 computed; derives structure"),
  13:(1,"names ceil/floor ops for Executor to perform; does not evaluate them"),
  14:(0,"derives conditions and invokes Dirichlet with worked residue reasoning"),
  17:(1,"pure strategy/defn listing; no computation"),
  22:(1,"states the geometric lemma; asks Executor to determine the distance"),
  23:(0,"derives constraints on coefficients a,b,c from the conditions"),
  24:(1,"case decomposition + multiplication principle named, not evaluated"),
  26:(0,"derives inequalities/bounds from the limit condition"),
  27:(0,"tracks root counts, sets up recurrence with interval values"),
  28:(0,"reframes and derives worst-case bound reasoning with board numbers"),
  29:(1,"states the target closed form from evaluator feedback; outlines lemma"),
  30:(0,"derives group structure (Z/100Z)* = C2 x C20 and covering number 2"),
  31:(0,"specifies modular case analysis and asserts results about k=3/k=4"),
  33:(1,"lists givens and names the rate formula; delegates the division"),
  34:(0,"names Heron and the derivation chain toward AG with side values"),
  35:(1,"defines objects and candidate list; delegates bound-finding"),
  36:(0,"mixes in mass values and extraction steps; derived content present"),
  37:(1,"formalises game mechanics only"),
  38:(0,"directs verification but embeds sum calculations for n=2,3"),
  43:(0,"asserts residue invariant and count 10^8; reasons about k bound"),
  44:(1,"lists unit-conversion facts as givens; delegates the multiplications"),
  46:(0,"derives the constant-solution condition and fractional-part constraint"),
  50:(1,"defines pyramid structure; delegates the count"),
  51:(1,"strategy only; no computation"),
  53:(1,"strategy revision only; no derived values"),
  55:(0,"gives explicit union-size formulas |U|=3,4,5 and the IE expression"),
  57:(1,"defines objects, sets up ratio equations symbolically; no evaluation"),
  58:(1,"states givens and defines n; explicitly defers arithmetic"),
  59:(0,"derives k_i=s_i^2 combinations and polygon-inequality checks"),
  60:(1,"meta-guidance to the Executor; no computation"),
  61:(0,"VIOLATION despite disclaimer: supplies computed coordinates C=(3s/2,(sqrt3/2)s) and asserts inradius s/2 and ratio pi/(4 sqrt3)"),
  63:(0,"derives the constant 101, the pairing, and the count 49!*2^49"),
  64:(1,"hypothesis/strategy revision; no derived values"),
  66:(0,"derives AM=c-a, AN=b-a and the expansion strategy with identities applied"),
  69:(0,"introduces s1,s2 and solves-for-x,y framing with constraint checks"),
  72:(0,"applies the recurrence r^4=3r^2+11 to reduce powers -- symbolic derivation"),
  74:(1,"stages for data extraction and a membership test; no derived values"),
  77:(1,"names binomial/factorial to use; defers the arithmetic"),
  79:(1,"redefines the formal setup symbolically; no evaluation"),
  80:(1,"restates the given equation and names the equality property"),
  81:(0,"asserts the optimal bound T_min=2021 and the 2021-edge argument"),
  82:(0,"re-derives c(p,2)=p^(p^2) and the product formula"),
  83:(0,"derives degree from the homogeneity condition, discusses P(x,y)=x-2y"),
  84:(0,"reduces to Pell x^2-3y^2=1 and the derived form (m-2)^2-3k^2=5"),
  85:(0,"VIOLATION despite n_eq=0: states the expected final answer 4^(n-2)+2^(n+1)"),
  86:(1,"outline + names the attaining construction; no computed value"),
  89:(0,"asserts the bound floor((n-1)/2) and the strategy analysis"),
  90:(0,"derives n=d5^2+n^2 impossibility and the bound d6<sqrt(n)<d6 sqrt2"),
  92:(1,"diagnoses prior failure and redirects approach; no derivation"),
  96:(0,"switches group to C_6 and specifies recomputed Burnside/IE counts"),
  98:(1,"defines the equation and delegates the inequality conversion"),
  102:(0,"reasons that n>3 for k=3 and directs specific graph families"),
  103:(1,"debugging guidance for the Executor; no derivation"),
  104:(1,"names interval decomposition strategy; no evaluation"),
  105:(1,"defines the visibility condition geometrically; no computation"),
  107:(0,"enumerates s=0..6 with add-block counts s+1 and r=100-s"),
  108:(0,"asserts the solution family f(x)=x+c and -x+c to be proved"),
  109:(1,"n=1, s_1=2,3,4 are search-INSTRUCTIONS to the Executor, not values the Planner computed"),
  111:(1,"L(m)L(n)=80 and ab=80 are RESTATED GIVENS/targets, not derived; contract permits restating givens"),
  112:(1,"names linearity of expectation and symmetry; no integration"),
  113:(1,"enforces a data-retrieval prerequisite; no derivation"),
  115:(1,"names rational-root/synthetic-division strategy; restates the polynomial given"),
  116:(1,"conceptual re-framing of maximality; no derivation"),
  117:(0,"asserts the extremal configuration and the scaling reduction with a bound"),
  118:(0,"ANNOTATOR ERROR CORRECTED: computes 2024=2^3*11*23 and divisor count (3+1)(1+1)(1+1)=16"),
  119:(0,"constructs the contradiction argument with f(q1),f(q2),f(n-1)=0"),



}

# ---- E2: Executor "must execute the Planner's plan" -------------------------
E2 = {
  13:(0,"re-derives by own case analysis, no trace of plan"),
  23:(1,"'Step 1..Step 8' executes an ordered plan"),
  29:(0,"'We need to solve the problem' then independent derivation"),
  40:(0,"own notation and lower-bound argument, independent"),
  42:(1,"explicit Step 1/2/3 execution of a plan"),
  0:(0,"'We need to determine...' own reasoning from primers, no plan trace"),
  2:(0,"applies Menelaus independently, self-corrects mid-message, no plan ref"),
  3:(0,"own proof architecture with its own numbered sections, independent"),
  4:(0,"restates problem and explores independently"),
  6:(0,"own greedy-condition development, independent"),
  7:(1,"'we follow the structured plan' + Step 1/Step 2 matching plan steps"),
  16:(1,"'we follow the planned steps' + Step 1/Step 2"),
  18:(0,"'We need to compute...' own computation from scratch"),
  19:(0,"FALSE POSITIVE: zero occurrences of plan/Planner; auto fired on 'Step 0/Inductive step' which is the Executor's OWN construction, not plan consumption"),
  25:(1,"'We need to execute plan: compute theta...' explicit plan reference"),
  32:(0,"restates and solves independently"),
  41:(1,"Step 1..Step 4 structured execution"),
}

# ---- R4: Reviewer "do not restate the full derivation" ----------------------
R4 = {}

S = pd.read_parquet(OUT + "/r10_validation_v2.parquet")
rows = []
for meas, book in [("P1a", P1A), ("E2", E2), ("R4", R4)]:
    for aid, (lab, why) in book.items():
        m = S[S.ann_id == aid]
        if len(m) == 0: continue
        r = m.iloc[0]
        if r.measure != meas: continue
        rows.append(dict(ann_id=aid, measure=meas, actor=r.actor_model_id,
                         auto=r.auto, human=lab, n_eq=r.n_eval_eq, reason=why))
A = pd.DataFrame(rows)
A.to_csv(OUT + "/r11_annotations.csv", index=False)
print(f"adjudicated: {len(A)}")
print(A.groupby("measure").size().to_string())

for meas, g in A.groupby("measure"):
    g = g[g.human != "U"]
    if len(g) < 5: continue
    auto = g.auto.astype(int).values; hum = np.array(g.human, dtype=int)
    agree = (auto == hum).mean()
    tp = ((auto == 1) & (hum == 1)).sum(); fp = ((auto == 1) & (hum == 0)).sum()
    fn = ((auto == 0) & (hum == 1)).sum(); tn = ((auto == 0) & (hum == 0)).sum()
    prec = tp / max(tp + fp, 1); rec = tp / max(tp + fn, 1)
    # Cohen's kappa
    po = agree
    pe = ((auto == 1).mean() * (hum == 1).mean() + (auto == 0).mean() * (hum == 0).mean())
    kappa = (po - pe) / (1 - pe) if pe < 1 else np.nan
    print(f"\n=== {meas} (n={len(g)}) ===")
    print(f"  agreement {agree:.3f}   kappa {kappa:.3f}   precision {prec:.3f}   recall {rec:.3f}")
    print(f"  confusion: TP={tp} FP={fp} FN={fn} TN={tn}")
    dis = g[g.auto.astype(int) != np.array(g.human, dtype=int)]
    if len(dis):
        print("  DISAGREEMENTS:")
        for _, d in dis.iterrows():
            print(f"    [{d.ann_id}] auto={int(d.auto)} human={d.human} n_eq={d.n_eq} :: {d.reason}")
