"""
preprocessing.py
-----------------
Feature engineering and preprocessing pipeline for the DLP alert
classification project.

Responsibilities:
    1. Load raw alert data
    2. Engineer time-based features from the raw timestamp
    3. Build a scikit-learn ColumnTransformer that:
         - one-hot encodes categorical fields
         - scales numeric fields
    4. Provide a single `build_preprocessor()` + `load_and_split()`
       entry point used by both train.py and evaluate.py so that
       train/test transformations always stay consistent.
"""

import pandas as pd
import numpy as np
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.model_selection import train_test_split

TARGET_COL = "is_high_risk"

CATEGORICAL_FEATURES = [
    "event_type",
    "policy_name",
    "department",
    "device_type",
    "time_of_day_bucket",
    "destination_category",
]

NUMERIC_FEATURES = [
    "destination_reputation_score",
    "regex_pii_match_count",
    "payload_size_kb",
    "user_violation_history_90d",
    "event_severity",
    "content_classifier_confidence",
    "on_watchlist",
    "is_sanctioned_destination",
    "hours_since_last_user_alert",
    "high_risk_file_extension",
    "is_after_hours",  # engineered below
]

ID_COLS = ["alert_id", "timestamp"]

# Columns that must NEVER be used as model features. predicted_risk_probability
# is the noisy latent score that is_high_risk is directly thresholded from
# (see generate_data.py: is_high_risk = risk_score > 0.34, and
# predicted_risk_probability = round(risk_score, 4) -- same number, rounded).
# Including it as a feature produces a near-perfect classifier that has
# learned nothing but the label's own source column.
LEAKAGE_COLS = ["predicted_risk_probability"]


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived features. Operates on a copy; returns a new DataFrame."""
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["is_after_hours"] = df["time_of_day_bucket"].isin(
        ["after_hours", "weekend", "overnight"]
    ).astype(int)
    # Log-transform heavily right-skewed payload size to stabilize variance.
    df["payload_size_kb_log"] = np.log1p(df["payload_size_kb"])
    return df


def build_preprocessor() -> ColumnTransformer:
    """Returns an unfit ColumnTransformer for categorical + numeric features."""
    categorical_pipe = Pipeline(steps=[
        ("onehot", OneHotEncoder(handle_unknown="ignore")),
    ])
    numeric_pipe = Pipeline(steps=[
        ("scaler", StandardScaler()),
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", categorical_pipe, CATEGORICAL_FEATURES),
            ("num", numeric_pipe, NUMERIC_FEATURES + ["payload_size_kb_log"]),
        ],
        remainder="drop",
    )
    return preprocessor


def load_and_split(csv_path: str, test_size: float = 0.2, random_state: int = 42):
    """
    Loads raw CSV, engineers features, and performs a stratified
    train/test split (stratified because the target is imbalanced).

    Returns:
        X_train, X_test, y_train, y_test (all DataFrames/Series with
        original feature columns intact; transformation happens later
        via build_preprocessor()).
    """
    df = pd.read_csv(csv_path)
    df = engineer_features(df)

    feature_cols = CATEGORICAL_FEATURES + NUMERIC_FEATURES + ["payload_size_kb_log"]

    leaked = set(feature_cols) & set(LEAKAGE_COLS)
    assert not leaked, (
        f"Refusing to train: {leaked} is a leakage column (the label's own "
        f"source), not a legitimate feature. Remove it from CATEGORICAL_FEATURES "
        f"/ NUMERIC_FEATURES before proceeding."
    )

    X = df[feature_cols]
    y = df[TARGET_COL]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )
    return X_train, X_test, y_train, y_test
