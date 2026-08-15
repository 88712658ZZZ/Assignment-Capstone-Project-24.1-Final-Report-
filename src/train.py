"""
train.py
--------
Trains and compares models for the DLP alert risk-tier classification task:

    1. Logistic Regression (baseline, prioritized for interpretability /
       governance per the project's Discussion Post)
    2. Random Forest (ensemble, captures non-linear relationships)
    3. XGBoost (ensemble, gradient boosting; used if the `xgboost`
       package is installed -- skipped gracefully otherwise)

Class imbalance is addressed two ways, selectable via --imbalance-strategy:
    - "class_weight": use class_weight='balanced' (no resampling)
    - "smote": oversample the training set with SMOTE before fitting

Saves the best-performing model to models/best_model.joblib and a full
metrics report to reports/metrics.json. "Best" is chosen under a recall
floor on the high-risk class (missing a real threat is far more costly
than an extra escalation), not raw PR-AUC -- see the selection logic in
main() for details.

NOTE: the model/threshold selection below uses the same held-out test
set that is also reported as the final evaluation metrics. There is no
separate validation split. Metrics for the selected model and threshold
should be read as optimistic in-sample estimates, not as an unbiased
estimate of production performance.

Usage:
    python src/train.py --data data/raw/dlp_alerts.csv --imbalance-strategy class_weight
"""

import argparse
import json
import os
import sys
import time

import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    average_precision_score, confusion_matrix, classification_report,
)
from sklearn.pipeline import Pipeline

sys.path.append(os.path.dirname(__file__))
from preprocessing import build_preprocessor, load_and_split  # noqa: E402
from smote import smote_oversample  # noqa: E402

# Prefer imbalanced-learn's SMOTE if available (more battle-tested);
# fall back to our lightweight implementation in smote.py otherwise.
try:
    from imblearn.over_sampling import SMOTE as ImblearnSMOTE
    HAS_IMBLEARN = True
except ImportError:
    HAS_IMBLEARN = False

try:
    from xgboost import XGBClassifier
    HAS_XGBOOST = True
except Exception:
    # Catches ImportError (package not installed) AND runtime import
    # failures such as XGBoostError (subclasses ValueError, not
    # ImportError) -- e.g. the xgboost wheel is present but the OpenMP
    # runtime it needs is missing, which is the default state on macOS.
    # Either way, we want to skip the model, not crash the whole script.
    HAS_XGBOOST = False


def get_models(imbalance_strategy: str, random_state: int = 42):
    """Returns a dict of {name: unfit sklearn estimator}."""
    use_class_weight = (imbalance_strategy == "class_weight")
    cw = "balanced" if use_class_weight else None

    models = {
        "logistic_regression": LogisticRegression(
            max_iter=1000, class_weight=cw, random_state=random_state
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=300, max_depth=10, min_samples_leaf=3,
            class_weight=cw, random_state=random_state, n_jobs=-1
        ),
    }

    if HAS_XGBOOST:
        xgb_params = dict(
            n_estimators=300, max_depth=5, learning_rate=0.08,
            subsample=0.9, colsample_bytree=0.9, eval_metric="logloss",
            random_state=random_state,
        )
        models["xgboost"] = XGBClassifier(**xgb_params)
    else:
        print("[info] xgboost not installed -- skipping XGBoost model. "
              "Install with `pip install xgboost` to include it.")

    return models


def apply_resampling(X_train_transformed, y_train, strategy, random_state=42):
    if strategy != "smote":
        return X_train_transformed, y_train

    if HAS_IMBLEARN:
        sm = ImblearnSMOTE(random_state=random_state)
        return sm.fit_resample(X_train_transformed, y_train)
    else:
        print("[info] imbalanced-learn not installed -- using built-in "
              "SMOTE implementation (src/smote.py).")
        return smote_oversample(X_train_transformed, y_train.values
                                 if hasattr(y_train, "values") else y_train,
                                 random_state=random_state)


def evaluate_model(name, model, X_test_transformed, y_test):
    y_pred = model.predict(X_test_transformed)
    y_proba = model.predict_proba(X_test_transformed)[:, 1]

    metrics = {
        "precision_high_risk": round(precision_score(y_test, y_pred, pos_label=1), 4),
        "recall_high_risk": round(recall_score(y_test, y_pred, pos_label=1), 4),
        "f1_high_risk": round(f1_score(y_test, y_pred, pos_label=1), 4),
        "precision_low_risk": round(precision_score(y_test, y_pred, pos_label=0), 4),
        "recall_low_risk": round(recall_score(y_test, y_pred, pos_label=0), 4),
        "roc_auc": round(roc_auc_score(y_test, y_proba), 4),
        "pr_auc": round(average_precision_score(y_test, y_proba), 4),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
    }

    # Business-relevant metric: at what precision can we auto-resolve
    # low-risk alerts, and what % of volume does that cover?
    # We sweep thresholds on P(high_risk) and find the lowest threshold
    # (i.e., most permissive auto-resolve cutoff) where low-risk precision
    # stays >= 0.98, then report the resulting auto-resolved volume %.
    low_risk_precision_target = 0.98
    best_auto_resolve_pct = 0.0
    best_threshold = None
    for t in np.arange(0.05, 0.95, 0.01):
        pred_t = (y_proba >= t).astype(int)  # 1 = escalate, 0 = auto-resolve
        if (pred_t == 0).sum() == 0:
            continue
        low_risk_mask = (pred_t == 0)
        # precision of the "auto-resolve" decision = how often auto-resolved
        # alerts were truly low-risk
        true_low_risk_among_resolved = (y_test[low_risk_mask] == 0).mean()
        if true_low_risk_among_resolved >= low_risk_precision_target:
            auto_resolve_pct = low_risk_mask.mean()
            if auto_resolve_pct > best_auto_resolve_pct:
                best_auto_resolve_pct = auto_resolve_pct
                best_threshold = round(float(t), 2)

    metrics["auto_resolve_threshold"] = best_threshold
    metrics["auto_resolved_volume_pct"] = round(best_auto_resolve_pct * 100, 1)
    metrics["auto_resolve_precision_target"] = low_risk_precision_target

    return metrics


def main():
    parser = argparse.ArgumentParser(description="Train DLP alert risk classifiers.")
    parser.add_argument("--data", type=str, default="data/raw/dlp_alerts.csv")
    parser.add_argument("--imbalance-strategy", type=str, default="class_weight",
                         choices=["smote", "class_weight"])
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    parser.add_argument("--models-dir", type=str, default="models")
    parser.add_argument("--reports-dir", type=str, default="reports")
    args = parser.parse_args()

    os.makedirs(args.models_dir, exist_ok=True)
    os.makedirs(args.reports_dir, exist_ok=True)

    print(f"[1/5] Loading and splitting data from {args.data} ...")
    X_train, X_test, y_train, y_test = load_and_split(
        args.data, test_size=args.test_size, random_state=args.random_state
    )
    print(f"      Train: {len(X_train)} rows | Test: {len(X_test)} rows")
    print(f"      Train class balance: {y_train.value_counts(normalize=True).round(3).to_dict()}")

    print("[2/5] Fitting preprocessing pipeline (one-hot encode + scale) ...")
    preprocessor = build_preprocessor()
    X_train_transformed = preprocessor.fit_transform(X_train)
    X_test_transformed = preprocessor.transform(X_test)
    # Densify if sparse (some models / SMOTE need dense arrays)
    if hasattr(X_train_transformed, "toarray"):
        X_train_transformed = X_train_transformed.toarray()
    if hasattr(X_test_transformed, "toarray"):
        X_test_transformed = X_test_transformed.toarray()

    print(f"[3/5] Applying imbalance strategy: {args.imbalance_strategy} ...")
    X_train_res, y_train_res = apply_resampling(
        X_train_transformed, y_train, args.imbalance_strategy, args.random_state
    )
    if args.imbalance_strategy == "smote":
        unique, cnt = np.unique(y_train_res, return_counts=True)
        print(f"      Post-SMOTE class balance: {dict(zip(unique.tolist(), cnt.tolist()))}")

    print("[4/5] Training models ...")
    models = get_models(args.imbalance_strategy, args.random_state)
    results = {}
    fitted_models = {}

    for name, model in models.items():
        t0 = time.time()
        model.fit(X_train_res, y_train_res)
        elapsed = round(time.time() - t0, 2)
        metrics = evaluate_model(name, model, X_test_transformed, y_test)
        metrics["train_time_sec"] = elapsed
        results[name] = metrics
        fitted_models[name] = model
        print(f"      {name:>20s} | PR-AUC={metrics['pr_auc']:.4f} | "
              f"Recall(high-risk)={metrics['recall_high_risk']:.4f} | "
              f"AutoResolve={metrics['auto_resolved_volume_pct']}% "
              f"(@P>={metrics['auto_resolve_precision_target']})")

    print("[5/5] Saving best model and report ...")
    # Model selection respects the project's stated cost model (a missed
    # real threat is far more expensive than an unnecessary escalation),
    # not just raw PR-AUC. A model that nominally edges out PR-AUC by
    # trading away recall on the high-risk class is not actually better
    # for this use case -- it lets more real threats slip through.
    #
    # Rule: among models that clear a minimum recall floor on the
    # high-risk class, pick the one with the highest auto-resolved
    # volume (the actual business KPI). If nothing clears the floor,
    # fall back to the model with the highest recall so we never
    # silently pick something below the floor.
    RECALL_FLOOR = 0.85
    eligible = {n: r for n, r in results.items() if r["recall_high_risk"] >= RECALL_FLOOR}
    if eligible:
        best_name = max(eligible, key=lambda n: eligible[n]["auto_resolved_volume_pct"])
    else:
        print(f"      [warn] no model reached the {RECALL_FLOOR} recall floor on "
              f"high-risk alerts -- falling back to highest-recall model")
        best_name = max(results, key=lambda n: results[n]["recall_high_risk"])
    best_pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", fitted_models[best_name]),
    ])
    # Note: this saved pipeline was fit on the *original* (non-resampled)
    # preprocessor + the resampled-trained classifier. Since SMOTE is only
    # applied to training data for fitting the classifier, and the
    # preprocessor itself was fit on X_train (pre-resampling), this
    # pipeline correctly transforms new raw data at inference time.

    model_path = os.path.join(args.models_dir, "best_model.joblib")
    joblib.dump(best_pipeline, model_path)

    report_path = os.path.join(args.reports_dir, "metrics.json")
    full_report = {
        "best_model": best_name,
        "imbalance_strategy": args.imbalance_strategy,
        "test_size": args.test_size,
        "random_state": args.random_state,
        "results_by_model": results,
    }
    with open(report_path, "w") as f:
        json.dump(full_report, f, indent=2)

    print(f"\nBest model: {best_name} (PR-AUC={results[best_name]['pr_auc']})")
    print(f"Saved model     -> {model_path}")
    print(f"Saved metrics   -> {report_path}")
    print("\nFull classification report (best model):")
    y_pred_best = fitted_models[best_name].predict(X_test_transformed)
    print(classification_report(y_test, y_pred_best,
                                 target_names=["low_risk (0)", "high_risk (1)"]))


if __name__ == "__main__":
    main()
