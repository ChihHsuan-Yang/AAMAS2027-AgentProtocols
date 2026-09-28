"""R2: ROLE DISTINGUISHABILITY -- can we recover the role from behaviour alone?

Deliberately separate from fidelity. Distinguishability asks only: are the three
roles behaviourally different? A team can be highly distinguishable while being
unfaithful to the intended functions (e.g. Planner reliably writes DELTA: but
also computes).

Two versions, because they answer different questions:
  (a) FULL feature set -- includes format markers the prompt template forces
      (DELTA:, [Route:...], Diagnosis:). High accuracy here is near-trivial:
      it mostly shows the template was followed.
  (b) FUNCTION-ONLY feature set -- strips every template/format marker and keeps
      only behaviour: computation density, arithmetic, plan reference, length,
      answer commitment. THIS is the scientifically meaningful one.

Held-out by TRAJECTORY (never by message) to avoid leakage.
"""
import os
import numpy as np, pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score, confusion_matrix
from sklearn.model_selection import GroupKFold

OUT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + "/results"
pd.set_option("display.width", 250)

P = pd.read_parquet(OUT + "/r1_role_messages.parquet")

TEMPLATE = ["f_delta", "f_givens", "f_target_form", "f_route_planner",
            "f_route_executor", "f_agree", "f_diagnosis", "f_fix_instruction",
            "f_final_for_eval", "f_bare_route"]
FUNCTION = ["eval_eq_density", "f_arith_op", "f_sqrt_num", "f_approx", "f_boxed",
            "f_numbered_steps", "f_imperative_step", "f_ref_plan", "f_ref_planner",
            "f_ref_step", "f_error_word", "n_chars"]
FULL = FUNCTION + TEMPLATE

def run(df, feats, label, model="gb"):
    X = df[feats].astype(float).values
    y = df.sender.values
    g = df.trajectory_uid.values
    preds = np.empty(len(y), dtype=object)
    for tr, te in GroupKFold(n_splits=5).split(X, y, groups=g):
        m = (HistGradientBoostingClassifier(max_iter=200, random_state=0) if model == "gb"
             else LogisticRegression(max_iter=2000))
        m.fit(X[tr], y[tr]); preds[te] = m.predict(X[te])
    ba = balanced_accuracy_score(y, preds)
    print(f"\n--- {label} ---  n={len(y)}  features={len(feats)}")
    print(f"  balanced accuracy = {ba:.4f}   (chance = 0.3333)")
    cm = pd.DataFrame(confusion_matrix(y, preds, labels=["Planner", "Executor", "Reviewer"]),
                      index=["true_Planner", "true_Executor", "true_Reviewer"],
                      columns=["pred_Planner", "pred_Executor", "pred_Reviewer"])
    print(cm.to_string())
    rec = (cm.values.diagonal() / cm.values.sum(1))
    print("  per-role recall:", dict(zip(["Planner", "Executor", "Reviewer"], rec.round(3))))
    return ba, preds

print("="*80)
print("ROLE DISTINGUISHABILITY — can behaviour alone reveal which role wrote a message?")
print("="*80)
ba_full, _ = run(P, FULL, "ALL features (incl. prompt-template markers)")
ba_fn, pred_fn = run(P, FUNCTION, "FUNCTION-ONLY (template markers removed)")

# Planner vs Executor is the contrast the role contract is ABOUT
pe = P[P.sender.isin(["Planner", "Executor"])].copy()
print("\n" + "="*80)
print("PLANNER vs EXECUTOR only — the pair the 'hard role separation' clause governs")
print("="*80)
def run2(df, feats, label):
    X = df[feats].astype(float).values; y = (df.sender == "Executor").astype(int).values
    g = df.trajectory_uid.values
    pr = np.zeros(len(y))
    for tr, te in GroupKFold(n_splits=5).split(X, y, groups=g):
        m = HistGradientBoostingClassifier(max_iter=200, random_state=0)
        m.fit(X[tr], y[tr]); pr[te] = m.predict_proba(X[te])[:, 1]
    from sklearn.metrics import roc_auc_score
    print(f"  {label:42s} AUC={roc_auc_score(y, pr):.4f}  acc={((pr>.5)==y).mean():.4f}")
    return roc_auc_score(y, pr)
a_full = run2(pe, FULL, "all features")
a_fn = run2(pe, FUNCTION, "function-only")
a_comp = run2(pe, ["eval_eq_density", "f_arith_op", "f_approx", "f_sqrt_num"], "COMPUTATION features only")
a_len = run2(pe, ["n_chars"], "message length only (nuisance control)")

P["pred_function_only"] = pred_fn
P.to_parquet(OUT + "/r2_with_preds.parquet", index=False)
pd.DataFrame([dict(scope="3-way full", score=ba_full, metric="bal_acc"),
              dict(scope="3-way function-only", score=ba_fn, metric="bal_acc"),
              dict(scope="P-vs-E full", score=a_full, metric="auc"),
              dict(scope="P-vs-E function-only", score=a_fn, metric="auc"),
              dict(scope="P-vs-E computation-only", score=a_comp, metric="auc"),
              dict(scope="P-vs-E length-only", score=a_len, metric="auc"),
              ]).to_csv(OUT + "/r2_distinguishability.csv", index=False)
