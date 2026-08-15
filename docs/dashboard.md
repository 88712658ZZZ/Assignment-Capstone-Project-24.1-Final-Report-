# Live Dashboard

`dashboard/index.html` is a standalone, dependency-light HTML dashboard
for DLP operations, fed by a pre-aggregated JSON payload generated from
`data/raw/dlp_alerts.csv` and `data/raw/users.csv`.

## Why pre-aggregated JSON instead of loading the CSV directly

The raw alert dataset is 100,000 rows (~16MB as CSV). Parsing and
aggregating that in the browser on every page load would be slow and
wasteful. `src/build_dashboard_data.py` computes everything the
dashboard needs once and writes a compact `dashboard/data.json`
(~25KB), which the dashboard fetches on load.

## Running it

```bash
# 1. Build (or rebuild) the dashboard data payload
python src/build_dashboard_data.py

# 2. Serve the dashboard folder over HTTP (fetch() requires this --
#    opening index.html directly via file:// will not load data.json)
cd dashboard
python -m http.server 8000

# 3. Open http://localhost:8000 in a browser
```

Re-run step 1 any time `dlp_alerts.csv`, `users.csv`, or the review
threshold/queue size changes.

## Views

### Management view

Organization-wide KPIs for leadership/SOC management:

- **Total workers** — size of the monitored population (from `users.csv`), with watchlist/departing-soon counts.
- **Total incidents** — all-time alert volume, with the % auto-resolved.
- **Incidents today** — alerts fired on the most recent date in the dataset, with the high-risk subset.
- **Incidents year-to-date** — alerts since January 1 of the current year, with the high-risk subset.
- **Daily incident volume (30-day trend)** — line chart of total vs. high-risk alerts per day, for spotting spikes.
- **Auto-resolve performance** — donut chart of the auto-resolved vs. escalated split, computed from the trained model's actual decision at its measured operating threshold (`models/best_model.joblib`, threshold from `reports/metrics.json`) — not the raw ground-truth class balance. This is the project's core efficiency metric.
- **Incidents by department / event type** — horizontal bar breakdowns, each bar split into auto-resolved (blue) vs. high-risk (red) segments.

### Analyst view — manual review queue

A ranked queue of users whose most recent alert the trained model
actually scored above its measured auto-resolve threshold
(`model_probability >= threshold`, where `threshold` defaults to the
value in `reports/metrics.json` for the selected model — 0.33 for the
current Logistic Regression), one row per user, sorted by the model's
own predicted probability descending. **This is a genuine model
prediction, computed by scoring every alert through
`models/best_model.joblib`** — earlier versions of this script ranked
the queue by `predicted_risk_probability`, a column that is the noisy
latent score the ground-truth label is itself thresholded from, which
made the queue trivially "perfect" rather than reflecting what the
model actually learned. For each row:

- User identity, department, role, and recent flagged alert details (event type, timestamp).
- A visual risk-probability bar and percentage.
- Policy matched and destination category for the flagged alert.
- Badges for **Watchlist**, **Departing soon**, and **Critical**/**High** risk tiers.

Clicking a row opens a detail drawer with the full alert payload
(destination reputation, regex/PII match count, payload size) and that
user's broader alert history (total alerts, high-risk count and rate),
plus placeholder "Mark reviewed" / "Escalate" actions for an analyst's
workflow. These actions are UI-only in this prototype — wiring them to
a real case-management system is a natural extension point (see
`PROJECT_STEPS.md`).

## Configuring the review queue

`src/build_dashboard_data.py` accepts:

```bash
python src/build_dashboard_data.py \
  --review-threshold 0.5 \
  --review-queue-size 25
```

- `--review-threshold` — minimum real model probability (`model_probability`) for an alert to be considered "queue-worthy." Defaults to the model's own measured auto-resolve threshold from `reports/metrics.json` if not set. Raise it to show only the most urgent cases; lower it to widen the queue.
- `--review-queue-size` — maximum number of users shown in the queue (one row per user, their single most recent qualifying alert).

## Customizing for real data

To point this dashboard at real DLP alert exports instead of the
synthetic dataset, your CSV needs to provide (at minimum) the same
columns documented in `docs/data_dictionary.md`, particularly `user_id`
and `timestamp`, plus every feature column `src/preprocessing.py`
expects. You'll also need a model trained on that schema at
`models/best_model.joblib` and its `reports/metrics.json` -- the
dashboard scores each alert through the pipeline itself rather than
reading a precomputed probability column, so there is no
`predicted_risk_probability`-equivalent field to supply. Then re-run
`build_dashboard_data.py` against your file paths.
