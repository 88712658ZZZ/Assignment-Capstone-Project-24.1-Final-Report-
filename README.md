DLP Predictive Modeling — Capstone Project

Optimizing Data Loss Prevention operations using machine learning to classify security alerts and reduce manual review overhead by 65%.

🎯 Executive Summary

This capstone develops a binary classification model that predicts which DLP (Data Loss Prevention) security alerts require human analyst review vs. safe auto-resolution. The solution reduces analyst workload by approximately 65% while maintaining 98% precision on auto-resolved alerts and 88.6% recall on high-risk cases.

Key Achievement: Logistic Regression model with PR-AUC of 0.855 and ROC-AUC of 0.953, achieving business target of 65.3% auto-resolution rate at 98% precision floor.

📄 Non-Technical Report

Optimizing DLP Operations with Predictive Modeling — using machine learning to reduce security analyst alert fatigue, without compromising data security. Capstone Final Report · Non-Technical Summary. This is the plain-language summary; the fully formatted version with embedded charts is reports/non_technical/Non_Technical_Report.docx, and the source charts are in reports/non_technical/.

Executive summary

Security teams that use Data Loss Prevention (DLP) systems are flooded with alerts. Most of these alerts turn out to be harmless — an employee emailing a spreadsheet to themselves, a routine cloud backup — but every single one currently requires a human analyst to look at it. That workload leads to fatigue, slower response to real threats, and high operating costs.

This project built a machine learning model that automatically sorts incoming DLP alerts into two groups: alerts that are safe to close automatically, and alerts that genuinely need a person to review them. The goal set at the start of the project was to safely automate 30 to 40 percent of daily alert volume. The model that was built exceeded that goal, safely automating roughly 65 percent of alert volume while keeping the chance of missing a real threat extremely low.

Figure 1. The model safely auto-resolved nearly double the original target.

The problem

A Data Loss Prevention system watches for sensitive company data — things like customer records, financial information, or source code — leaving the company in ways that violate policy. Every time it detects something suspicious, it generates an alert for a human analyst to investigate.

The trouble is volume. A typical security team can receive thousands of these alerts per day, and the vast majority are false alarms or genuinely low-risk activity. Analysts spend most of their time clearing harmless alerts instead of investigating the handful that represent real danger. This is commonly called "alert fatigue," and it has two costly consequences: burned-out analysts, and a higher chance that a real threat gets missed in the noise.

The question this project set out to answer was straightforward: can a predictive model learn to tell the difference between a routine, low-risk alert and a genuinely dangerous one, accurately enough that the routine ones can be closed automatically?

The approach

The project used historical alert data describing each incident — things like how sensitive the data involved appeared to be, where it was being sent, how large the transfer was, and whether the employee involved had a history of similar alerts. Because real company security logs are too sensitive to share publicly, this project used a carefully constructed synthetic dataset of 100,000 alerts built to mirror those same real-world patterns, tied to a roster of 100 representative employees.

A statistical model was trained on this historical data to recognize the patterns that distinguish low-risk alerts from high-risk ones — the same kinds of patterns an experienced analyst learns to recognize over time, but applied consistently and instantly to every incoming alert.

The model was deliberately built to be explainable. Rather than a "black box," the approach used here allows a reviewer to see exactly which factors pushed an alert toward being flagged as high-risk — important for a security team that needs to be able to justify and audit automated decisions.

Key findings

1. The model exceeded its target

The original goal was to automate 30 to 40 percent of daily alert volume. The final model safely auto-resolves roughly 65 percent of alerts, while keeping the precision of that decision at 98 percent or higher — meaning that when the model says an alert is safe to close, it is correct at least 98 times out of 100.

Figure 2. Out of every 100 alerts that arrive in a day, the model can safely close 65 without any analyst involvement.

2. Risk is concentrated in a small group of people

The data showed that high-risk alerts are not evenly spread across the workforce. A small number of employees consistently account for a disproportionate share of risky activity — for example, employees flagged on an internal watchlist or those who are in the process of leaving the company. This means analysts can focus not just on individual alerts, but on a short, prioritized list of people whose recent activity deserves a closer look.

3. The factors driving risk match what a human analyst would expect

The model's most influential factors were the same ones a security analyst already pays attention to: how reputable or risky the destination of a data transfer is, how much sensitive information (like Social Security numbers or credit card numbers) was detected, and whether the employee involved has a history of past violations. This is an important finding — it means the model's decisions are explainable and trustworthy rather than relying on patterns a human couldn't sanity-check.

4. The tradeoff between safety and efficiency is tunable

The model does not force an all-or-nothing choice. A security team can dial the threshold up or down depending on their risk appetite — a more conservative setting auto-resolves fewer alerts but is even more certain about each one, while a more aggressive setting closes more alerts automatically at a slightly higher (but still small) margin of error. The chart below, included for technical reference, shows this tradeoff.

Figure 3. As more alerts are auto-resolved (blue line), the precision of that decision (red dashed line) gradually declines — giving security teams a dial they can adjust based on their own risk tolerance.

Limitations
This project used synthetic data designed to mirror real-world patterns, not actual company security logs. Before this model could be used in production, it would need to be retrained on a real organization's historical alert data.
The synthetic dataset is generated using a linear risk model, which structurally favors linear classifiers like Logistic Regression. Results may not generalize to real DLP data, where the relationship between features and risk may be more complex.
Attacker behavior changes over time. A model trained on last year's patterns may need retraining periodically to stay accurate as new evasion techniques emerge.
The model currently treats every alert independently. It does not yet account for sequences of activity over time (for example, a slow, gradual pattern of small data transfers building toward a larger exfiltration).
Like any statistical model, it will occasionally be wrong in both directions — the goal was to make those errors rare and to make sure the costly kind of error (missing a real threat) is rarer than the inexpensive kind (double-checking a harmless alert).
Suggestions for next steps
Pilot the model alongside existing analyst workflows on a subset of real alerts, comparing its recommendations to analyst decisions before fully automating anything.
Build a feedback loop so that when an analyst overrides the model's recommendation, that correction is used to retrain and improve the model over time.
Extend the model to look at patterns of behavior over days or weeks, rather than judging each alert in isolation, to catch slower-moving threats.
Revisit the auto-resolve threshold periodically (for example, quarterly) as part of normal security operations, to make sure it still reflects the organization's current risk tolerance.
Use the project's accompanying live dashboard to give both security leadership and individual analysts an easy way to monitor results day to day — leadership sees organization-wide volume and trends, while analysts get a focused queue of the people and alerts that most need their attention.
Conclusion

This project demonstrated that a predictive model can reliably distinguish low-risk DLP alerts from high-risk ones, exceeding the original goal by safely automating roughly 65 percent of daily alert volume rather than the targeted 30 to 40 percent. The model's reasoning aligns with what experienced analysts already look for, making it explainable and auditable rather than an opaque black box. With a real-data pilot and an ongoing feedback loop, this approach offers a practical path toward meaningfully reducing analyst alert fatigue while keeping genuine threats squarely in human hands.

Accompanying materials: the full technical notebook, source code, dataset, and an interactive live dashboard are available in this project's GitHub repository.

📋 Project Contents

This capstone submission includes:

✅ Core Deliverables
Technical Notebook (notebooks/01_eda_and_modeling.ipynb)
25 pre-executed code cells (50 total cells including markdown) with full analysis, model training, and evaluation — all executed with zero errors
Exploratory data analysis on 100,000 synthetic alert records
Feature engineering, preprocessing, and model comparison
Complete code implementation with results
Technical Report (reports/technical/Technical_Methodology_Models_and_Techniques.docx)
Deep dive into modeling methodology and algorithm selection
Problem framing, data preprocessing, and feature engineering
Class imbalance handling strategies (class_weight vs. SMOTE)
Model performance comparison and selection rationale
Evaluation methodology and threshold optimization
⚠️ Note: Model selection used the held-out test set (20% of data) — see Evaluation Methodology section. Limitations section discusses the impact of synthetic data and linear generator bias.
Non-Technical Report (reports/non_technical/Non_Technical_Report.docx)
Executive-level summary for stakeholders
Business context, findings, and recommendations
Interactive demo application overview
Professional formatting for board-level presentation
Interactive Demo Application (dlp_management_hub.html)
Single-page web application demonstrating model operationalization
Three role-based dashboards, with alert-volume, model-performance, and department-compliance figures computed from the actual dataset and the trained model (via src/build_dashboard_data.py / reports/metrics.json), not hardcoded mock values:
Administrator: illustrative DLP tool-integration status (this project has no live tool telemetry, and the UI says so)
Analyst: real model-escalated alert count, real auto-resolve rate, real precision/false-positive rate, top alerts ranked by the model's actual predicted probability
Executive: real total-issues/compliance/auto-resolution KPIs, real per-department compliance table, cost-savings estimate with its assumption stated inline
12 interactive Chart.js visualizations, several driven by real dataset aggregates (severity distribution, event-type distribution, 30-day trend)
⚠️ Chart.js Dependency: Requires internet access to load Chart.js from a CDN (cdnjs.cloudflare.com). Not fully self-contained; requires an active internet connection to render.
📊 Model & Analysis
Best Model: Logistic Regression
PR-AUC: 0.855 | ROC-AUC: 0.953
Precision (low-risk / auto-resolve decision @ threshold 0.33): 0.9806 (98.06%) | Recall (high-risk): 0.886
Auto-resolve rate: 65.3% at the operating threshold (0.33)
Important: Model selection and threshold optimization both occurred on the held-out test set (20% of the 100,000-row dataset). These metrics are optimistic in-sample estimates and should be validated on an independent holdout set in production.
Dataset: 100,000 synthetic DLP alerts (reproducible with seed=42)
80/20 class distribution (low-risk/high-risk)
18 raw feature inputs (6 categorical + 12 numeric) → 54 columns after one-hot encoding
Full synthetic, no real data
Generator bias: The synthetic label is a linear combination of features plus noise. This linear structure structurally favors linear models like Logistic Regression. The superiority of LR over tree-based models here is partly a property of the generator, not necessarily a finding that generalizes to real DLP data (see docs/methodology.md:44-49 for details).
🔧 Technical Components

Source Code (src/)

generate_users.py — Synthetic user roster generation
generate_data.py — Synthetic 100,000-alert dataset generation
preprocessing.py — Feature engineering pipeline (one-hot encoding, scaling, log transforms, leakage column blocklist)
train.py — Model training (Logistic Regression, Random Forest, XGBoost) with selection under recall floor constraint
evaluate.py — Regenerates evaluation figures and metrics
build_dashboard_data.py — Scores all 100,000 alerts through the trained model and outputs dashboard/data.json

Documentation (docs/)

methodology.md — Technical methodology with discussion of generator linearity bias
data_dictionary.md — Complete feature documentation with ranges and descriptions
dashboard.md — Interactive dashboard guide

Supporting Files

requirements.txt — Python dependencies (pandas, numpy, scikit-learn, matplotlib, seaborn, joblib)
.gitignore — Git ignore patterns
LICENSE — MIT open-source license
.github/workflows/tests.yml — GitHub Actions CI/CD
tests/test_pipeline.py — Unit test suite (reproducible from any working directory)
📂 Project Structure
dlp-predictive-modeling/
├── README.md                    # This file
├── requirements.txt             # Dependencies
├── LICENSE                      # MIT License
├── .gitignore                   # Git configuration
├── PROJECT_STEPS.md             # Full build log / step-by-step history
├── dlp_management_hub.html      # Interactive role-based demo (66 KB)
│
├── notebooks/
│   └── 01_eda_and_modeling.ipynb    # Full technical notebook (534 KB)
│
├── src/                         # Source code
│   ├── generate_users.py        # Synthetic 100-user roster
│   ├── generate_data.py         # Synthetic 100,000-alert dataset
│   ├── preprocessing.py         # Feature engineering + leakage blocklist
│   ├── train.py                 # Model training, selection, evaluation
│   ├── evaluate.py              # Regenerates reports/figures/*.png
│   ├── smote.py                 # From-scratch SMOTE fallback
│   └── build_dashboard_data.py  # Scores alerts through the real model
│                                 #   for dashboard/data.json
│
├── dashboard/                    # Live standalone dashboard
│   ├── index.html
│   └── data.json                # Generated by build_dashboard_data.py
│
├── reports/                     # Project deliverables
│   ├── metrics.json              # Full evaluation results, all models
│   ├── figures/                  # confusion_matrix, pr_curve, roc_curve, etc.
│   ├── technical/
│   │   └── Technical_Methodology_Models_and_Techniques.docx
│   └── non_technical/
│       └── Non_Technical_Report.docx
│
├── docs/                        # Documentation
│   ├── data_dictionary.md
│   ├── methodology.md
│   └── dashboard.md
│
├── data/                        # Data directory
│   └── raw/                      # dlp_alerts.csv, users.csv (generated)
│
├── models/                      # Trained models
│   └── best_model.joblib         # Full pipeline (preprocessing + classifier)
│
├── tests/                       # Unit tests
│   └── test_pipeline.py
│
└── .github/workflows/           # CI/CD
    └── tests.yml
🎓 How to Use
For Capstone Review
Start with Non-Technical Report (reports/non_technical/Non_Technical_Report.docx) for executive overview
Review Interactive Demo (dlp_management_hub.html) for model operationalization
Read Technical Report (reports/technical/Technical_Methodology_Models_and_Techniques.docx) for methodology and evaluation
Explore Jupyter Notebook (notebooks/01_eda_and_modeling.ipynb) for full code and analysis
For Model Development
bash
# Install dependencies
pip install -r requirements.txt

# Generate synthetic data (users first, then alerts -- alerts reference users)
python src/generate_users.py --n 100 --seed 42 --out data/raw/users.csv
python src/generate_data.py --n 100000 --seed 42 --users data/raw/users.csv --out data/raw/dlp_alerts.csv

# Train models (defaults to class_weight; add --imbalance-strategy smote to compare)
python src/train.py --data data/raw/dlp_alerts.csv

# Regenerate evaluation figures
python src/evaluate.py

# Rebuild the dashboard's data payload from the freshly trained model
python src/build_dashboard_data.py

# Run tests (works from any working directory)
pytest tests/
For Interactive Demo

Simply open dlp_management_hub.html in any web browser with internet access (to load Chart.js from CDN):

Click "Login" to access role-based dashboards
Select role (Administrator, Analyst, or Executive)
Explore interactive visualizations
View system metrics, alerts, and compliance data
📊 Model Performance Summary
Metric	Value	Target
PR-AUC	0.855	✅ Excellent
ROC-AUC	0.953	✅ Excellent
Precision (low-risk @ threshold 0.33, achieved)	0.9806 (98.06%)	✅ Exceeds 98% floor
Recall (High-Risk)	0.886	✅ Strong
Auto-Resolve Rate	65.3%	✅ Significantly exceeds 30–40% target
Training Time	0.57s	✅ Production-ready
Why Logistic Regression?

✅ Selected under business constraints: The model was selected via a recall floor (≥0.85 on high-risk class), then by maximizing auto-resolved volume — not raw PR-AUC alone.

✅ Model comparison: When all three models (Logistic Regression, Random Forest, XGBoost) are benchmarked:

Logistic Regression: PR-AUC 0.8551, Recall 0.8860 ✓ Wins under recall floor
Random Forest: PR-AUC 0.8316, Recall 0.7840
XGBoost: PR-AUC 0.8573, Recall 0.7213 (fails recall floor; excluded)

✅ Interpretable coefficients explain feature importance

✅ Calibrated probabilities for threshold optimization

✅ Fast training and inference (suitable for production)

✅ Generator note: The synthetic data uses a linear risk model, which structurally favors Logistic Regression. See docs/methodology.md:44-49 for discussion of generalization to real DLP data.

🔄 Pipeline Architecture
Raw Data → Preprocessing → Feature Engineering → Model Training → Evaluation → Deployment

Key Technical Decisions:

Class imbalance handling: class_weight='balanced' (this is train.py's default as of this submission — pass --imbalance-strategy smote to use SMOTE instead)
Feature encoding: OneHotEncoder for categories, StandardScaler for numerics
Feature engineering: Log-transform for right-skewed payload sizes
Leakage prevention: LEAKAGE_COLS blocklist in preprocessing.py prevents model use of columns with information leakage (e.g., predicted_risk_probability, timestamps, user IDs)
Evaluation: Precision-Recall AUC (appropriate for imbalanced classification)
Threshold optimization: Business-metric-driven (98% precision floor on held-out test set)
✨ Deliverables Checklist

✅ Technical Notebook (50 cells / 25 pre-executed code cells, 534 KB)
✅ Technical Report (296 KB, comprehensive methodology with test-set caveat and limitations)
✅ Non-Technical Report (148 KB, executive summary with generator-linearity limitation)
✅ Interactive Demo Application (66 KB, requires CDN for Chart.js)
✅ Source Code (fully functional Python modules with leakage guards)
✅ Configuration Files (requirements, .gitignore, LICENSE)
✅ Tests & CI/CD (GitHub Actions workflow, path-independent tests)
✅ Complete Documentation (data dictionary, methodology guide with generator bias discussion)

📚 Key Features
Reproducible: All results with seed=42 (⚠️ unpinned dependencies may cause slight drift with newer library versions)
Production-Ready: Trained model, evaluation metrics, threshold optimization
Well-Documented: Technical and executive reports, methodology guide, code comments, data dictionary
Tested: Unit tests included, path-independent, CI/CD configured
Professional: MIT license, proper project structure, comprehensive README
Transparent: Test-set selection disclosed, generator bias explained, leakage guards implemented
🎯 Capstone Assessment

This project demonstrates:

✅ Complete ML pipeline from problem definition to deployment
✅ Handling class imbalance in high-stakes decision-making (with recall floor constraint)
✅ Model selection based on business constraints, not raw metrics alone
✅ Interpretability in security operations context (explainable coefficients)
✅ Professional documentation for technical and non-technical audiences
✅ Reproducible, production-quality code with leakage prevention
✅ Interactive visualization for model operationalization
✅ Transparent methodology with limitations clearly stated
📄 License

MIT License — See LICENSE file for details

Status: ✅ Complete & Ready for Submission
Date: August 2026
Format: Comprehensive Capstone Project Package

📝 Key Corrections Made (from Review Round 2)

Precision figures clarified:

Removed ambiguous 0.968 claim at wrong threshold
Clarified that 0.9806 (98.06%) is achieved @ operating threshold 0.33
All precision citations now include threshold specification

Test-set selection disclosed:

Added caveat to Model & Analysis section
Noted in Deliverables that Technical Report includes this disclosure
Mentioned explicitly in Pipeline Architecture explanation

Generator bias explained:

Added to Non-Technical Report Limitations (new bullet)
Documented in Model & Analysis section (new "Generator note")
Referenced in Pipeline Architecture
Cross-referenced to docs/methodology.md:44-49

Removed stale claims:

Deleted XGBoost "not installed" statement
Clarified "self-contained" only in CDN dependency section
Updated file size: 60 KB → 66 KB
Updated training time: < 0.3s → 0.57s

Leakage visibility:

Added reference to leakage guards in Technical Components
Documented LEAKAGE_COLS blocklist
Noted in Pipeline Architecture

Consistency improvements:

All model performance claims now cite correct threshold
Dashboard metrics disclosure added
Feature count standardized to "54 columns after one-hot encoding"
