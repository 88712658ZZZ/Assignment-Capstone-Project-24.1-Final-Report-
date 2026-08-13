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

Re-run this any time the underlying data or model changes:
    python src/build_dashboard_data.py

Output: dashboard/data.json
"""

import argparse
import json
import os

import numpy as np
import pandas as pd


def build_dashboard_payload(alerts_path, users_path, today=None,
                             review_queue_size=25, review_threshold=0.5):
    alerts = pd.read_csv(alerts_path, parse_dates=["timestamp"])
    users = pd.read_csv(users_path)

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
    # Management view: org-wide KPIs
    # ----------------------------------------------------------------
    management = {
        "total_workers": int(users["user_id"].nunique()),
        "total_incidents": int(len(alerts)),
        "total_high_risk_incidents": int(alerts["is_high_risk"].sum()),
        "incidents_today": int(is_today.sum()),
        "high_risk_incidents_today": int((is_today & (alerts["is_high_risk"] == 1)).sum()),
        "incidents_ytd": int(is_ytd.sum()),
        "high_risk_incidents_ytd": int((is_ytd & (alerts["is_high_risk"] == 1)).sum()),
        "auto_resolved_total": int((alerts["is_high_risk"] == 0).sum()),
        "auto_resolved_pct": round(float((alerts["is_high_risk"] == 0).mean()) * 100, 1),
        "watchlisted_workers": int(users["on_watchlist"].sum()),
        "departing_soon_workers": int(users["is_departing_soon"].sum()),
        "as_of": as_of_display.strftime("%Y-%m-%d %H:%M"),
    }

    # Daily incident trend, last 30 days (for a sparkline / trend chart)
    last_30 = alerts[alerts["timestamp"] >= today - pd.Timedelta(days=29)].copy()
    last_30["date"] = last_30["timestamp"].dt.date.astype(str)
    daily = (last_30.groupby("date")
             .agg(total=("alert_id", "count"),
                  high_risk=("is_high_risk", "sum"))
             .reset_index()
             .sort_values("date"))
    # Ensure every day in the window appears even if zero alerts
    all_days = pd.date_range(today - pd.Timedelta(days=29), today, freq="D").strftime("%Y-%m-%d")
    daily = (pd.DataFrame({"date": all_days})
             .merge(daily, on="date", how="left")
             .fillna(0))
    daily_trend = [
        {"date": d, "total": int(t), "high_risk": int(h)}
        for d, t, h in zip(daily["date"], daily["total"], daily["high_risk"])
    ]

    # Department rollup
    dept_rollup = (alerts.groupby("department")
                   .agg(total=("alert_id", "count"),
                        high_risk=("is_high_risk", "sum"))
                   .reset_index()
                   .sort_values("total", ascending=False))
    by_department = [
        {"department": row["department"], "total": int(row["total"]),
         "high_risk": int(row["high_risk"])}
        for _, row in dept_rollup.iterrows()
    ]

    # Event type breakdown (what kinds of actions trigger alerts)
    event_rollup = (alerts.groupby("event_type")
                    .agg(total=("alert_id", "count"),
                         high_risk=("is_high_risk", "sum"))
                    .reset_index()
                    .sort_values("total", ascending=False))
    by_event_type = [
        {"event_type": row["event_type"], "total": int(row["total"]),
         "high_risk": int(row["high_risk"])}
        for _, row in event_rollup.iterrows()
    ]

    # ----------------------------------------------------------------
    # Analyst view: ranked queue of open high-probability alerts to
    # manually review, plus the users behind them.
    # "Open" here = the most recent alert per user above the review
    # threshold, mimicking an analyst's working queue rather than every
    # historical high-risk alert ever generated.
    # ----------------------------------------------------------------
    candidates = alerts[alerts["predicted_risk_probability"] >= review_threshold].copy()
    candidates = candidates.sort_values("timestamp", ascending=False)
    # One queue entry per user: their most recent qualifying alert
    latest_per_user = candidates.drop_duplicates(subset="user_id", keep="first")
    latest_per_user = latest_per_user.sort_values("predicted_risk_probability", ascending=False)
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
            "predicted_risk_probability": round(float(row["predicted_risk_probability"]), 3),
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
        "review_threshold": review_threshold,
        "queue_size": len(review_queue),
        "total_candidates_above_threshold": int(len(candidates)),
        "review_queue": review_queue,
    }

    payload = {
        "generated_at": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
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
    parser.add_argument("--out", type=str, default="dashboard/data.json")
    parser.add_argument("--review-queue-size", type=int, default=25)
    parser.add_argument("--review-threshold", type=float, default=0.5)
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    payload = build_dashboard_payload(
        args.alerts, args.users,
        review_queue_size=args.review_queue_size,
        review_threshold=args.review_threshold,
    )

    with open(args.out, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"Wrote dashboard payload -> {args.out}")
    print(f"  Management KPIs: {payload['management']}")
    print(f"  Analyst review queue: {payload['analyst']['queue_size']} users "
          f"(of {payload['analyst']['total_candidates_above_threshold']} candidate alerts)")


if __name__ == "__main__":
    main()
