"""
build_dashboard_data.py
------------------------
Aggregates the 100k-row alert dataset (data/raw/dlp_alerts.csv) and the
100-user roster (data/raw/users.csv) into a compact JSON payload that
powers the live HTML dashboard (dashboard/index.html).

Why pre-aggregate instead of loading the raw CSV in the browser?
The raw alert dataset is ~100,000 rows (~16MB as CSV). Parsing and
aggregating that client-side on every page load is slow and wasteful --
all the dashboard actually needs are summary KPIs, time-series trends,
department rollups, and a short ranked list of high-risk-probability
alerts/users. This script computes those once and writes a small JSON
file (~tens of KB) that the dashboard fetches instead.

IMPORTANT -- model vs. ground truth (fixed per correctness review):
Earlier versions of this script published dashboard KPIs computed
directly from the ground-truth `is_high_risk` label and ranked the
analyst queue by `predicted_risk_probability` -- a column that is
literally the noisy latent score the label is thresholded from
(see generate_data.py). That made every dashboard number "ground truth
dressed up as a model prediction": a model trained to reproduce that
same label would look artificially perfect, and the published
auto-resolve rate (~79.8%, the raw class balance) had nothing to do
with the trained model's actual, measured auto-resolve rate (~65.3%
at the governance-required 98% precision floor, per reports/metrics.json).

This version scores every alert through the actual trained pipeline at
models/best_model.joblib and uses the classification threshold that
was fit and measured in reports/metrics.json. Every "model_*" field in
the output payload is now a genuine model prediction. Ground-truth
fields are kept, but explicitly prefixed `ground_truth_*` so the two
are never confused again.

Re-run this any time the underlying data or model changes:
    python src/build_dashboard_data.py

Output: dashboard/data.json
"""

import argparse
import json
import os
import sys

import joblib
import numpy as np
import pandas as pd

sys.path.append(os.path.dirname(__file__))
from preprocessing import engineer_features  # noqa: E402


def _load_model_and_threshold(model_path, metrics_path):
    """
    Loads the trained pipeline and the auto-resolve threshold that was
    measured for it in reports/metrics.json, so the dashboard uses the
    exact same operating point that the technical report describes --
    not an arbitrary re-guessed cutoff.
    """
    model = joblib.load(model_path)

    with open(metrics_path) as f:
        metrics = json.load(f)

    best_name = metrics["best_model"]
    model_metrics = metrics["results_by_model"][best_name]

    return model, {
        "model_name": best_name,
        "auto_resolve_threshold": model_metrics["auto_resolve_threshold"],
        "auto_resolve_precision_target": model_metrics["auto_resolve_precision_target"],
        "auto_resolved_volume_pct_measured": model_metrics["auto_resolved_volume_pct"],
        "precision_low_risk": model_metrics["precision_low_risk"],
        "precision_high_risk": model_metrics["precision_high_risk"],
        "recall_high_risk": model_metrics["recall_high_risk"],
        "roc_auc": model_metrics["roc_auc"],
        "pr_auc": model_metrics["pr_auc"],
    }


def build_dashboard_payload(alerts_path, users_path, model_path, metrics_path,
                             today=None, review_queue_size=25,
                             review_threshold=None):
    alerts = pd.read_csv(alerts_path, parse_dates=["timestamp"])
    users = pd.read_csv(users_path)

    model, model_info = _load_model_and_threshold(model_path, metrics_path)

    # --------------------------------------------------------------
    # Score every alert through the actual trained pipeline. The
    # pipeline includes its own preprocessing (ColumnTransformer), so
    # we only need to run the same feature-engineering step used at
    # training time (engineer_features) before calling predict_proba;
    # extra columns in `alerts` are ignored by the pipeline's
    # ColumnTransformer (remainder="drop").
    # --------------------------------------------------------------
    engineered = engineer_features(alerts)
    model_proba = model.predict_proba(engineered)[:, 1]
    alerts["model_probability"] = np.round(model_proba, 4)

    threshold = model_info["auto_resolve_threshold"]
    # Same convention as train.py's evaluate_model(): proba >= threshold
    # means escalate to a human analyst; proba < threshold means the
    # model calls it safe to auto-resolve.
    alerts["model_auto_resolve"] = alerts["model_probability"] < threshold

    if today is None:
        today = alerts["timestamp"].max().normalize()
        as_of_display = alerts["timestamp"].max()
    else:
        today = pd.Timestamp(today)
        as_of_display = today

    year_start = pd.Timestamp(year=today.year, month=1, day=1)

    is_today = alerts["timestamp"].dt.date == today.date()
    is_ytd = alerts["timestamp"] >= year_start

    # ----------------------------------------------------------------
    # Management view: org-wide KPIs.
    # auto_resolved_* now reflects the MODEL's actual decision at its
    # measured operating threshold, not the ground-truth class balance.
    # ground_truth_* fields are kept for transparency/comparison only
    # and are clearly labeled so they can't be mistaken for model output.
    # ----------------------------------------------------------------
    auto_resolved_mask = alerts["model_auto_resolve"]
    management = {
        "total_workers": int(users["user_id"].nunique()),
        "total_incidents": int(len(alerts)),
        "total_high_risk_incidents": int(alerts["is_high_risk"].sum()),
        "incidents_today": int(is_today.sum()),
        "high_risk_incidents_today": int((is_today & (alerts["is_high_risk"] == 1)).sum()),
        "incidents_ytd": int(is_ytd.sum()),
        "high_risk_incidents_ytd": int((is_ytd & (alerts["is_high_risk"] == 1)).sum()),

        # --- Real model output ---
        "model_name": model_info["model_name"],
        "model_auto_resolve_threshold": threshold,
        "auto_resolved_total": int(auto_resolved_mask.sum()),
        "auto_resolved_pct": round(float(auto_resolved_mask.mean()) * 100, 1),
        "escalated_total": int((~auto_resolved_mask).sum()),
        "escalated_pct": round(float((~auto_resolved_mask).mean()) * 100, 1),
        "model_precision_low_risk_measured": model_info["precision_low_risk"],
        "model_recall_high_risk_measured": model_info["recall_high_risk"],
        "model_pr_auc": model_info["pr_auc"],
        "model_roc_auc": model_info["roc_auc"],
        "auto_resolve_precision_target": model_info["auto_resolve_precision_target"],

        # --- Ground truth, for comparison only -- NOT a model output ---
        "ground_truth_low_risk_total": int((alerts["is_high_risk"] == 0).sum()),
        "ground_truth_low_risk_pct": round(float((alerts["is_high_risk"] == 0).mean()) * 100, 1),

        "watchlisted_workers": int(users["on_watchlist"].sum()),
        "departing_soon_workers": int(users["is_departing_soon"].sum()),
        "as_of": as_of_display.strftime("%Y-%m-%d %H:%M"),
    }

    # Daily incident trend, last 30 days (for a sparkline / trend chart).
    # "auto_resolved" per day is now also the model's real decision.
    last_30 = alerts[alerts["timestamp"] >= today - pd.Timedelta(days=29)].copy()
    last_30["date"] = last_30["timestamp"].dt.date.astype(str)
    daily = (last_30.groupby("date")
             .agg(total=("alert_id", "count"),
                  high_risk=("is_high_risk", "sum"),
                  model_auto_resolved=("model_auto_resolve", "sum"))
             .reset_index()
             .sort_values("date"))
    all_days = pd.date_range(today - pd.Timedelta(days=29), today, freq="D").strftime("%Y-%m-%d")
    daily = (pd.DataFrame({"date": all_days})
             .merge(daily, on="date", how="left")
             .fillna(0))
    daily_trend = [
        {"date": d, "total": int(t), "high_risk": int(h), "model_auto_resolved": int(a)}
        for d, t, h, a in zip(daily["date"], daily["total"], daily["high_risk"],
                               daily["model_auto_resolved"])
    ]

    # Department rollup
    dept_rollup = (alerts.groupby("department")
                   .agg(total=("alert_id", "count"),
                        high_risk=("is_high_risk", "sum"),
                        model_auto_resolved=("model_auto_resolve", "sum"))
                   .reset_index()
                   .sort_values("total", ascending=False))
    by_department = [
        {"department": row["department"], "total": int(row["total"]),
         "high_risk": int(row["high_risk"]),
         "model_auto_resolved": int(row["model_auto_resolved"])}
        for _, row in dept_rollup.iterrows()
    ]

    # Event type breakdown (what kinds of actions trigger alerts)
    event_rollup = (alerts.groupby("event_type")
                    .agg(total=("alert_id", "count"),
                         high_risk=("is_high_risk", "sum"),
                         model_auto_resolved=("model_auto_resolve", "sum"))
                    .reset_index()
                    .sort_values("total", ascending=False))
    by_event_type = [
        {"event_type": row["event_type"], "total": int(row["total"]),
         "high_risk": int(row["high_risk"]),
         "model_auto_resolved": int(row["model_auto_resolved"])}
        for _, row in event_rollup.iterrows()
    ]

    # ----------------------------------------------------------------
    # Analyst view: ranked queue of open alerts to manually review,
    # plus the users behind them. The queue is now the set of alerts
    # the MODEL actually decided to escalate (model_probability >=
    # threshold), ranked by the model's own probability -- previously
    # this used predicted_risk_probability, the label's own source
    # column, which made the queue trivially "perfect."
    # "Open" here = the most recent qualifying alert per user, mimicking
    # an analyst's working queue rather than every historical alert.
    # ----------------------------------------------------------------
    queue_threshold = threshold if review_threshold is None else review_threshold
    candidates = alerts[alerts["model_probability"] >= queue_threshold].copy()
    candidates = candidates.sort_values("timestamp", ascending=False)
    latest_per_user = candidates.drop_duplicates(subset="user_id", keep="first")
    latest_per_user = latest_per_user.sort_values("model_probability", ascending=False)
    queue = latest_per_user.head(review_queue_size)

    users_indexed = users.set_index("user_id")

    review_queue = []
    for _, row in queue.iterrows():
        uid = row["user_id"]
        if uid in users_indexed.index:
            u = users_indexed.loc[uid]
            full_name = u["full_name"]
            job_level = u["job_level"]
            location = u["location"]
            on_watchlist_user = bool(u["on_watchlist"])
            is_departing = bool(u["is_departing_soon"])
        else:
            full_name, job_level, location = uid, "Unknown", "Unknown"
            on_watchlist_user, is_departing = False, False

        # This user's broader alert history, for context in the review panel
        user_alerts = alerts[alerts["user_id"] == uid]
        review_queue.append({
            "alert_id": row["alert_id"],
            "user_id": uid,
            "full_name": full_name,
            "job_level": job_level,
            "department": row["department"],
            "location": location,
            "timestamp": row["timestamp"].strftime("%Y-%m-%d %H:%M"),
            "model_probability": round(float(row["model_probability"]), 3),
            "event_type": row["event_type"],
            "policy_name": row["policy_name"],
            "destination_category": row["destination_category"],
            "destination_reputation_score": int(row["destination_reputation_score"]),
            "regex_pii_match_count": int(row["regex_pii_match_count"]),
            "payload_size_kb": float(row["payload_size_kb"]),
            "on_watchlist": on_watchlist_user,
            "is_departing_soon": is_departing,
            "user_total_alerts": int(len(user_alerts)),
            "user_high_risk_alerts": int(user_alerts["is_high_risk"].sum()),
            "user_high_risk_rate": round(float(user_alerts["is_high_risk"].mean()), 3),
        })

    analyst = {
        "model_name": model_info["model_name"],
        "review_threshold": queue_threshold,
        "queue_size": len(review_queue),
        "total_candidates_above_threshold": int(len(candidates)),
        "review_queue": review_queue,
    }

    payload = {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
        "model_info": model_info,
        "management": management,
        "daily_trend": daily_trend,
        "by_department": by_department,
        "by_event_type": by_event_type,
        "analyst": analyst,
    }
    return payload


def main():
    parser = argparse.ArgumentParser(description="Build the dashboard JSON payload.")
    parser.add_argument("--alerts", type=str, default="data/raw/dlp_alerts.csv")
    parser.add_argument("--users", type=str, default="data/raw/users.csv")
    parser.add_argument("--model", type=str, default="models/best_model.joblib")
    parser.add_argument("--metrics", type=str, default="reports/metrics.json")
    parser.add_argument("--out", type=str, default="dashboard/data.json")
    parser.add_argument("--review-queue-size", type=int, default=25)
    parser.add_argument("--review-threshold", type=float, default=None,
                         help="Defaults to the model's own measured "
                              "auto-resolve threshold from reports/metrics.json.")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    payload = build_dashboard_payload(
        args.alerts, args.users, args.model, args.metrics,
        review_queue_size=args.review_queue_size,
        review_threshold=args.review_threshold,
    )

    with open(args.out, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"Wrote dashboard payload -> {args.out}")
    print(f"  Model: {payload['model_info']['model_name']} "
          f"(threshold={payload['model_info']['auto_resolve_threshold']})")
    print(f"  Management KPIs: {payload['management']}")
    print(f"  Analyst review queue: {payload['analyst']['queue_size']} users "
          f"(of {payload['analyst']['total_candidates_above_threshold']} candidate alerts)")


if __name__ == "__main__":
    main()
