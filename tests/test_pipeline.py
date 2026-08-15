"""
test_pipeline.py
-----------------
Lightweight unit/integration tests for the DLP alert classification project.
Run with: pytest tests/
"""

import os
import sys
import numpy as np
import pandas as pd

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from generate_data import generate_dataset  # noqa: E402
from generate_users import generate_users  # noqa: E402
from preprocessing import engineer_features, build_preprocessor, load_and_split  # noqa: E402
from smote import smote_oversample  # noqa: E402
from build_dashboard_data import build_dashboard_payload  # noqa: E402


def test_generate_dataset_shape_and_columns():
    df = generate_dataset(n=200, seed=1)
    assert len(df) == 200
    expected_cols = {
        "alert_id", "timestamp", "event_type", "policy_name", "department",
        "device_type", "time_of_day_bucket", "destination_category",
        "destination_reputation_score", "regex_pii_match_count",
        "payload_size_kb", "user_violation_history_90d", "event_severity",
        "content_classifier_confidence", "on_watchlist",
        "is_sanctioned_destination", "hours_since_last_user_alert",
        "high_risk_file_extension", "is_high_risk",
    }
    assert expected_cols.issubset(set(df.columns))


def test_generate_dataset_no_nulls():
    df = generate_dataset(n=200, seed=1)
    assert df.isnull().sum().sum() == 0


def test_generate_dataset_label_is_binary():
    df = generate_dataset(n=200, seed=1)
    assert set(df["is_high_risk"].unique()).issubset({0, 1})


def test_generate_dataset_reproducible_with_seed():
    df1 = generate_dataset(n=100, seed=99)
    df2 = generate_dataset(n=100, seed=99)
    pd.testing.assert_frame_equal(df1, df2)


def test_engineer_features_adds_columns():
    df = generate_dataset(n=50, seed=1)
    df_eng = engineer_features(df)
    assert "is_after_hours" in df_eng.columns
    assert "payload_size_kb_log" in df_eng.columns
    assert df_eng["is_after_hours"].isin([0, 1]).all()


def test_preprocessor_output_shape():
    df = generate_dataset(n=200, seed=1)
    df.to_csv("/tmp/_test_dlp.csv", index=False)
    X_train, X_test, y_train, y_test = load_and_split("/tmp/_test_dlp.csv", test_size=0.2, random_state=1)

    preprocessor = build_preprocessor()
    X_train_t = preprocessor.fit_transform(X_train)
    X_test_t = preprocessor.transform(X_test)

    assert X_train_t.shape[0] == len(X_train)
    assert X_test_t.shape[0] == len(X_test)
    assert X_train_t.shape[1] == X_test_t.shape[1]  # same feature space
    os.remove("/tmp/_test_dlp.csv")


def test_train_test_split_is_stratified():
    df = generate_dataset(n=500, seed=1)
    df.to_csv("/tmp/_test_dlp2.csv", index=False)
    X_train, X_test, y_train, y_test = load_and_split("/tmp/_test_dlp2.csv", test_size=0.2, random_state=1)

    train_ratio = y_train.mean()
    test_ratio = y_test.mean()
    assert abs(train_ratio - test_ratio) < 0.05  # stratified split keeps ratios close
    os.remove("/tmp/_test_dlp2.csv")


def test_smote_balances_classes():
    rng = np.random.default_rng(0)
    # Imbalanced synthetic data: 90 majority, 10 minority
    X_majority = rng.normal(0, 1, size=(90, 4))
    X_minority = rng.normal(3, 1, size=(10, 4))
    X = np.vstack([X_majority, X_minority])
    y = np.array([0] * 90 + [1] * 10)

    X_res, y_res = smote_oversample(X, y, k_neighbors=5, random_state=0, target_ratio=1.0)

    unique, counts = np.unique(y_res, return_counts=True)
    counts_dict = dict(zip(unique.tolist(), counts.tolist()))
    assert counts_dict[0] == counts_dict[1]  # fully balanced
    assert X_res.shape[0] == y_res.shape[0]


def test_smote_no_op_when_already_balanced():
    X = np.random.normal(0, 1, size=(100, 4))
    y = np.array([0] * 50 + [1] * 50)
    X_res, y_res = smote_oversample(X, y, target_ratio=1.0)
    assert len(y_res) == len(y)  # nothing added


def test_generate_users_shape_and_uniqueness():
    users = generate_users(n=100, seed=42)
    assert len(users) == 100
    assert users["user_id"].nunique() == 100
    assert users["full_name"].nunique() == 100
    assert users["on_watchlist"].isin([0, 1]).all()
    assert users["baseline_risk_propensity"].between(0, 1).all()


def test_generate_users_reproducible_with_seed():
    u1 = generate_users(n=50, seed=7)
    u2 = generate_users(n=50, seed=7)
    pd.testing.assert_frame_equal(u1, u2)


def test_alerts_reference_valid_users():
    users = generate_users(n=20, seed=1)
    users.to_csv("/tmp/_test_users.csv", index=False)
    alerts = generate_dataset(n=500, seed=1, users_path="/tmp/_test_users.csv")

    assert set(alerts["user_id"].unique()).issubset(set(users["user_id"]))
    # Every one of the 20 users should appear at least once across 500 alerts
    assert alerts["user_id"].nunique() == len(users)

    os.remove("/tmp/_test_users.csv")


def test_alert_risk_concentrates_by_user():
    """Users with high baseline_risk_propensity should produce a higher
    share of high-risk alerts than low-propensity users -- this is what
    makes the Analyst review queue meaningful rather than random."""
    users = generate_users(n=30, seed=3)
    users.to_csv("/tmp/_test_users2.csv", index=False)
    alerts = generate_dataset(n=3000, seed=3, users_path="/tmp/_test_users2.csv")

    user_risk_rate = alerts.groupby("user_id")["is_high_risk"].mean()
    # There should be meaningful spread, not every user clustered near
    # the same rate (which would indicate propensity has no effect).
    assert user_risk_rate.max() - user_risk_rate.min() > 0.15

    os.remove("/tmp/_test_users2.csv")


def test_build_dashboard_payload_structure():
    # Requires a trained model + metrics.json (produced by train.py) since
    # build_dashboard_payload now scores every alert through the real
    # pipeline rather than reading the label's own source column. Skip
    # gracefully if train.py hasn't been run yet in this environment.
    model_path = "models/best_model.joblib"
    metrics_path = "reports/metrics.json"
    if not (os.path.exists(model_path) and os.path.exists(metrics_path)):
        pytest.skip("models/best_model.joblib or reports/metrics.json not "
                     "present -- run src/train.py first")

    users = generate_users(n=15, seed=5)
    users.to_csv("/tmp/_test_users3.csv", index=False)
    alerts = generate_dataset(n=2000, seed=5, users_path="/tmp/_test_users3.csv")
    alerts.to_csv("/tmp/_test_alerts3.csv", index=False)

    payload = build_dashboard_payload(
        "/tmp/_test_alerts3.csv", "/tmp/_test_users3.csv",
        model_path, metrics_path,
        review_queue_size=10, review_threshold=0.5,
    )

    assert payload["management"]["total_workers"] == 15
    assert payload["management"]["total_incidents"] == 2000
    assert payload["management"]["incidents_today"] >= 0
    assert payload["management"]["incidents_ytd"] >= payload["management"]["incidents_today"]
    assert len(payload["daily_trend"]) == 30
    assert len(payload["analyst"]["review_queue"]) <= 10
    if payload["analyst"]["review_queue"]:
        row = payload["analyst"]["review_queue"][0]
        assert row["model_probability"] >= 0.5
        assert "full_name" in row

    os.remove("/tmp/_test_users3.csv")
    os.remove("/tmp/_test_alerts3.csv")
