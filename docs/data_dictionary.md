# Data Dictionary

## `dlp_alerts.csv`

100,000 synthetic DLP alert records. One row = one alert event, attributed
to a user from `users.csv`.

| Column | Type | Description |
|---|---|---|
| `alert_id` | string | Unique alert identifier (e.g., `DLP-100042`). |
| `timestamp` | datetime | When the alert fired (`YYYY-MM-DD HH:MM:SS`). Spans a rolling 365-day window ending "today". |
| `user_id` | string | Foreign key into `users.csv` — the user who triggered the alert. |
| `event_type` | categorical | Action that triggered the alert: `email_exfil`, `usb_transfer`, `cloud_upload`, `print_job`, `clipboard_copy`, `web_upload`, `removable_media`, `screen_capture`. |
| `policy_name` | categorical | DLP policy that matched, e.g., `PCI-DSS_CardData`, `PII_SSN_Match`, `Source_Code_Exfil`, `HR_Confidential`, `Financial_Records`, `Customer_PII`, `Healthcare_PHI`, `Credentials_Leak`, `Generic_Confidential`. |
| `department` | categorical | Department of the user who triggered the alert (mirrors `users.csv`). |
| `device_type` | categorical | `corporate_managed`, `byod_mobile`, `byod_laptop`, or `unmanaged` (mirrors the user's primary device). |
| `time_of_day_bucket` | categorical | `business_hours`, `after_hours`, `weekend`, `overnight`. |
| `destination_category` | categorical | Classification of the data's destination, e.g., `corporate_approved`, `personal_cloud_storage`, `webmail`, `unknown_external`, `competitor_domain`, `file_sharing_service`, `social_media`, `pastebin_code_sharing`. |
| `destination_reputation_score` | int (0–100) | Reputation score of the destination domain/service; lower = worse reputation. |
| `regex_pii_match_count` | int | Number of PII/PCI regex pattern matches found in the payload (e.g., SSNs, credit card numbers). |
| `payload_size_kb` | float | Size of the transferred/exfiltrated data in kilobytes. |
| `user_violation_history_90d` | int | Number of DLP policy violations by this user in the trailing 90 days (UEBA metadata), correlated with the user's stable baseline risk propensity. |
| `event_severity` | int (1–5) | Native severity score assigned by the DLP engine at alert time. |
| `content_classifier_confidence` | float (0–1) | Confidence score from the content-sensitivity classifier. |
| `on_watchlist` | binary (0/1) | Whether the user is on an active security/HR watchlist at alert time (mirrors `users.csv`). |
| `is_sanctioned_destination` | binary (0/1) | Whether the destination is an approved/sanctioned business partner. |
| `hours_since_last_user_alert` | float | Hours elapsed since this user's previous DLP alert (recency signal). |
| `high_risk_file_extension` | binary (0/1) | Whether the transferred file has a higher-risk extension. |
| `predicted_risk_probability` | float (0–1) | ⚠️ **Never use as a model feature.** This is the noisy latent score that `is_high_risk` is directly thresholded from at generation time (see `src/generate_data.py`) — it is the label's own source, not a model output. `src/preprocessing.py` excludes it via an explicit `LEAKAGE_COLS` blocklist with a runtime assertion. The dashboard now ranks alerts by a genuine model prediction (`model_probability`, computed by scoring alerts through `models/best_model.joblib`), not by this column — see lines below and `docs/dashboard.md`. |
| `is_high_risk` | binary (0/1) | **Target label.** `1` = high-risk, should be escalated to a human analyst. `0` = low-risk, safe to auto-resolve. |

## `users.csv`

100 synthetic users that alerts in `dlp_alerts.csv` are attributed to.

| Column | Type | Description |
|---|---|---|
| `user_id` | string | Unique user identifier (e.g., `U-1042`). |
| `full_name` | string | Synthetic display name. |
| `email` | string | Synthetic corporate email address (`@example-corp.com`). |
| `department` | categorical | Same department pool as `dlp_alerts.csv`. |
| `job_level` | categorical | `IC1`, `IC2`, `IC3`, `Senior`, `Manager`, `Director`, `VP`. |
| `primary_device_type` | categorical | `corporate_managed`, `byod_mobile`, `byod_laptop`, `unmanaged`. |
| `location` | categorical | Synthetic office/remote location. |
| `hire_date` | date | Synthetic hire date, derived from `tenure_days`. |
| `tenure_days` | int | Days since hire (1 month to 10 years). |
| `is_departing_soon` | binary (0/1) | Whether the user is flagged as departing soon (elevated insider-risk signal). |
| `on_watchlist` | binary (0/1) | Whether the user is on an active security/HR watchlist. |
| `baseline_risk_propensity` | float (0–1) | Stable per-user risk propensity driving that user's alert generation rate and the likelihood any given alert of theirs is high-risk. Concentrates risk in a minority of users, consistent with insider-threat research, and is what makes the Analyst review queue a short, meaningful list rather than noise. |

## Label & Probability Construction (synthetic data only)

`is_high_risk` and `predicted_risk_probability` in `dlp_alerts.csv` are
derived from a weighted composite "risk score" combining regex/PII match
density, destination reputation, payload size, user violation history,
severity, watchlist status, file extension risk, content classifier
confidence, and the triggering user's `baseline_risk_propensity` — plus
injected random noise to avoid a trivially separable dataset. See
`src/generate_data.py` for the exact formula and `docs/methodology.md`
for rationale. In a production setting, `is_high_risk` would instead come
from historical analyst dispositions logged in the SOC case management
system, and `predicted_risk_probability` would be the output of the
trained classifier in `models/best_model.joblib`.
