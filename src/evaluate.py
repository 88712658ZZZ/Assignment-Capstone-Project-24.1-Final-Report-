"""
evaluate.py
-----------
Loads the saved best model, re-runs evaluation on the held-out test
split, and produces visualizations for the project report:
    - Confusion matrix heatmap
    - ROC curve
    - Precision-Recall curve
    - Feature importance (for tree-based models) or coefficients
      (for Logistic Regression)
    - Auto-resolve threshold sweep: precision/volume tradeoff curve

All figures are saved to reports/figures/.

Usage:
    python src/evaluate.py --data data/raw/dlp_alerts.csv --model models/best_model.joblib
"""

import argparse
import os
import sys

import joblib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    confusion_matrix, roc_curve, auc, precision_recall_curve,
)

sys.path.append(os.path.dirname(__file__))
from preprocessing import load_and_split, CATEGORICAL_FEATURES, NUMERIC_FEATURES  # noqa: E402

sns.set_style("whitegrid")


def plot_confusion_matrix(y_test, y_pred, out_path):
    cm = confusion_matrix(y_test, y_pred)
    fig, ax = plt.subplots(figsize=(5, 4.5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=["Low-Risk (auto)", "High-Risk (escalate)"],
                yticklabels=["Low-Risk (auto)", "High-Risk (escalate)"], ax=ax)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title("Confusion Matrix - DLP Alert Risk Classifier")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_roc_curve(y_test, y_proba, out_path):
    fpr, tpr, _ = roc_curve(y_test, y_proba)
    roc_auc = auc(fpr, tpr)
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    ax.plot(fpr, tpr, label=f"ROC curve (AUC = {roc_auc:.3f})", linewidth=2)
    ax.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Random baseline")
    ax.set_xlabel("False Positive Rate")
    ax.set_ylabel("True Positive Rate")
    ax.set_title("ROC Curve")
    ax.legend(loc="lower right")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_pr_curve(y_test, y_proba, out_path):
    precision, recall, _ = precision_recall_curve(y_test, y_proba)
    fig, ax = plt.subplots(figsize=(5.5, 4.5))
    ax.plot(recall, precision, linewidth=2, color="darkorange")
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title("Precision-Recall Curve (High-Risk class)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_threshold_sweep(y_test, y_proba, out_path):
    """
    Shows the operational tradeoff central to the project's goal:
    as we raise the auto-resolve confidence threshold, what % of
    alert volume can we safely auto-resolve, and at what precision?
    """
    thresholds = np.arange(0.05, 0.96, 0.01)
    volumes, precisions = [], []
    for t in thresholds:
        pred_t = (y_proba >= t).astype(int)
        auto_mask = (pred_t == 0)
        if auto_mask.sum() == 0:
            volumes.append(0)
            precisions.append(np.nan)
            continue
        volumes.append(auto_mask.mean() * 100)
        precisions.append((y_test[auto_mask] == 0).mean())

    fig, ax1 = plt.subplots(figsize=(7, 4.5))
    ax2 = ax1.twinx()
    ax1.plot(thresholds, volumes, color="steelblue", linewidth=2, label="Auto-resolved volume %")
    ax2.plot(thresholds, precisions, color="firebrick", linewidth=2, linestyle="--",
              label="Precision of auto-resolve decision")
    ax2.axhline(0.98, color="gray", linestyle=":", linewidth=1)
    ax1.set_xlabel("High-Risk Probability Threshold")
    ax1.set_ylabel("Auto-Resolved Volume (%)", color="steelblue")
    ax2.set_ylabel("Auto-Resolve Precision", color="firebrick")
    ax1.set_title("Auto-Resolve Threshold Tradeoff")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def plot_feature_importance(pipeline, out_path):
    clf = pipeline.named_steps["classifier"]
    preprocessor = pipeline.named_steps["preprocessor"]

    cat_feature_names = preprocessor.named_transformers_["cat"]["onehot"] \
        .get_feature_names_out(CATEGORICAL_FEATURES).tolist()
    num_feature_names = NUMERIC_FEATURES + ["payload_size_kb_log"]
    all_feature_names = cat_feature_names + num_feature_names

    if hasattr(clf, "feature_importances_"):
        importances = clf.feature_importances_
        title = f"{type(clf).__name__} - Feature Importances"
    elif hasattr(clf, "coef_"):
        importances = np.abs(clf.coef_[0])
        title = f"{type(clf).__name__} - |Coefficient| Magnitudes"
    else:
        print("[warn] Model has no interpretable feature importance attribute; skipping plot.")
        return

    top_n = 15
    idx = np.argsort(importances)[-top_n:]
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.barh([all_feature_names[i] for i in idx], importances[idx], color="teal")
    ax.set_title(title)
    ax.set_xlabel("Importance")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description="Evaluate the trained DLP risk classifier.")
    parser.add_argument("--data", type=str, default="data/raw/dlp_alerts.csv")
    parser.add_argument("--model", type=str, default="models/best_model.joblib")
    parser.add_argument("--figures-dir", type=str, default="reports/figures")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--random-state", type=int, default=42)
    args = parser.parse_args()

    os.makedirs(args.figures_dir, exist_ok=True)

    print(f"Loading model from {args.model} ...")
    pipeline = joblib.load(args.model)

    print(f"Loading and splitting data from {args.data} ...")
    X_train, X_test, y_train, y_test = load_and_split(
        args.data, test_size=args.test_size, random_state=args.random_state
    )

    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]
    y_test_arr = y_test.values

    print("Generating figures ...")
    plot_confusion_matrix(y_test_arr, y_pred, os.path.join(args.figures_dir, "confusion_matrix.png"))
    plot_roc_curve(y_test_arr, y_proba, os.path.join(args.figures_dir, "roc_curve.png"))
    plot_pr_curve(y_test_arr, y_proba, os.path.join(args.figures_dir, "pr_curve.png"))
    plot_threshold_sweep(y_test_arr, y_proba, os.path.join(args.figures_dir, "threshold_tradeoff.png"))
    plot_feature_importance(pipeline, os.path.join(args.figures_dir, "feature_importance.png"))

    print(f"Saved 5 figures to {args.figures_dir}/")


if __name__ == "__main__":
    main()
