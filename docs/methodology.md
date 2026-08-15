# Methodology

## 1. Problem Framing

This is framed as a **supervised binary classification** problem:

- **Positive class (1)** — high-risk alert, requires human analyst review.
- **Negative class (0)** — low-risk alert, eligible for automatic
  resolution/dismissal.

The operational goal is not maximum overall accuracy — it is **very high
precision on the auto-resolve decision**. A false negative here (a real
threat mislabeled "low-risk" and silently dismissed) is far more costly
than a false positive (a benign alert that still gets escalated to a
human, just at a smaller efficiency gain). This shapes every modeling
choice below.

## 2. Synthetic Data Generation

Real DLP alert logs contain sensitive operational and behavioral data
that cannot be published publicly. `src/generate_data.py` generates a
**100,000-row synthetic dataset** that mirrors the *structure* and
*statistical relationships* of real DLP/UEBA logs without exposing any
real organization's data.

Key design choices:
- Categorical fields (event type, policy name, department, destination
  category, device type) are sampled from realistic value pools with
  non-uniform weights (e.g., corporate-approved destinations are most
  common; competitor-domain destinations are rare).
- Numeric fields use distributions appropriate to their real-world
  shape: payload size is log-normal (many small transfers, occasional
  huge ones), violation history and regex match counts are Poisson-like
  with rare high-count outliers (repeat offenders / heavy PII matches).
- The target label is derived from a **weighted composite risk score**
  (destination reputation, PII match density, payload size, violation
  history, severity, watchlist status, file extension risk, classifier
  confidence, **and the user's baseline risk propensity, which carries
  the single largest weight, 0.20**) plus injected Gaussian noise, then
  thresholded. This ensures the dataset has genuine, learnable signal —
  mirroring how a real analyst's disposition decision would be
  influenced by these same factors — without being trivially separable.

  **Limitation:** because this risk score is a linear combination of
  features plus noise, it structurally favors linear models. Logistic
  Regression outperforming the ensemble models in this project's results
  is partly a property of this generator, not necessarily a finding that
  would generalize to real DLP alert data with more complex, non-linear
  risk structure.

## 3. Feature Engineering (`src/preprocessing.py`)

- **Categorical encoding** — One-hot encoding via `ColumnTransformer`,
  with `handle_unknown="ignore"` so unseen categories at inference time
  don't break the pipeline.
- **Numeric scaling** — `StandardScaler` for all numeric features.
- **Derived features**:
  - `is_after_hours` — binary flag collapsing `after_hours`, `weekend`,
    and `overnight` time buckets, since after-hours activity is a
    known risk indicator independent of the specific bucket.
  - `payload_size_kb_log` — log1p transform to stabilize the heavily
    right-skewed payload size distribution.

## 4. Handling Class Imbalance

Two interchangeable strategies are implemented (selectable via
`--imbalance-strategy`):

1. **`class_weight='balanced'`** — reweights the loss function so
   minority-class errors are penalized more heavily, without altering
   the training set itself.
2. **SMOTE (Synthetic Minority Over-sampling Technique)** — generates
   synthetic minority-class samples by interpolating between each
   minority sample and its k-nearest minority neighbors (Chawla et al.,
   2002). A lightweight from-scratch implementation is provided in
   `src/smote.py` (numpy + scikit-learn's `NearestNeighbors` only, no
   extra dependency required), with automatic preference for the more
   battle-tested `imbalanced-learn` library if it's installed.

Both strategies are applied **only to the training split**, never to
the test split, to avoid data leakage and to ensure evaluation reflects
real-world deployment conditions.

## 5. Models Evaluated

| Model | Role | Why |
|---|---|---|
| Logistic Regression | Baseline | Highly interpretable coefficients support governance, audit, and explainability requirements common in security operations. |
| Random Forest | Ensemble | Captures non-linear feature interactions (e.g., destination reputation × payload size) without heavy hyperparameter tuning. |
| XGBoost *(optional)* | Ensemble | Gradient boosting often achieves the best raw performance on tabular, high-dimensional behavioral data; included if the `xgboost` package is installed. |

## 6. Evaluation Strategy

Standard classification metrics (precision, recall, F1, ROC-AUC, PR-AUC)
are reported per class, with particular attention to **PR-AUC** since
the positive (high-risk) class is the minority class and PR-AUC is more
informative than ROC-AUC under imbalance.

The **primary business metric** is an explicit **threshold sweep**:
for each candidate decision threshold on `P(high_risk)`, we compute (a)
the precision of the auto-resolve decision (i.e., among alerts the
model would auto-resolve, what fraction are truly low-risk) and (b) the
resulting % of total alert volume that gets auto-resolved. We report the
most permissive threshold that still keeps auto-resolve precision ≥ 98%,
directly answering the project's stated goal: *"confidently auto-resolve
30–40% of the daily alert volume."*

## 7. Reproducibility

All randomized steps (data generation, train/test split, SMOTE, model
training) accept a `random_state`/`seed` parameter, defaulting to `42`
throughout, so results are fully reproducible end-to-end via:

```bash
python src/generate_users.py --seed 42
python src/generate_data.py --seed 42 --users data/raw/users.csv
python src/train.py --random-state 42 --imbalance-strategy class_weight
python src/evaluate.py --random-state 42
```

Note: `train.py` now defaults `--imbalance-strategy` to `class_weight`
(matching the committed `reports/metrics.json`), so the flag above is
technically redundant but is included for clarity. Also note that the
model and its auto-resolve threshold are both selected using the same
held-out test set that is reported as the final evaluation metrics —
there is no separate validation split, so these numbers should be read
as optimistic in-sample estimates rather than an unbiased estimate of
production performance.
