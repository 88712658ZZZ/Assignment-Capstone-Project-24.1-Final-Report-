[README.md](https://github.com/user-attachments/files/31020280/README.md)
# DLP Predictive Modeling — Capstone Project

Optimizing Data Loss Prevention operations using machine learning to classify security alerts and reduce manual review overhead by 65%.

## 🎯 Executive Summary

This capstone develops a **binary classification model** that predicts which DLP (Data Loss Prevention) security alerts require human analyst review vs. safe auto-resolution. The solution reduces analyst workload by approximately 65% while maintaining 98% precision on auto-resolved alerts and 88.6% recall on high-risk cases.

**Key Achievement:** Logistic Regression model with PR-AUC of 0.855 and ROC-AUC of 0.953, achieving business target of 65.3% auto-resolution rate at 98% precision floor.

---

## 📝 Non-Technical Report (Full Text)

*The complete text of `reports/non_technical/Non_Technical_Report.docx` is reproduced below for quick reading directly in the repository. The original formatted document (with charts) remains available at that path.*

### Optimizing DLP Operations with Predictive Modeling
*Using machine learning to reduce security analyst alert fatigue, without compromising data security*

Capstone Final Report · Non-Technical Summary — prepared to accompany the project's technical Jupyter notebook and GitHub repository.

#### Executive Summary

Security teams that use Data Loss Prevention (DLP) systems are flooded with alerts. Most of these alerts turn out to be harmless — an employee emailing a spreadsheet to themselves, a routine cloud backup — but every single one currently requires a human analyst to look at it. That workload leads to fatigue, slower response to real threats, and high operating costs.

This project built a machine learning model that automatically sorts incoming DLP alerts into two groups: alerts that are safe to close automatically, and alerts that genuinely need a person to review them. The goal set at the start of the project was to safely automate 30 to 40 percent of daily alert volume. The model that was built exceeded that goal, safely automating roughly 65 percent of alert volume while keeping the chance of missing a real threat extremely low.

> *Figure 1 (in the full report). The model safely auto-resolved nearly double the original target.*

#### The Problem

A Data Loss Prevention system watches for sensitive company data — things like customer records, financial information, or source code — leaving the company in ways that violate policy. Every time it detects something suspicious, it generates an alert for a human analyst to investigate.

The trouble is volume. A typical security team can receive thousands of these alerts per day, and the vast majority are false alarms or genuinely low-risk activity. Analysts spend most of their time clearing harmless alerts instead of investigating the handful that represent real danger. This is commonly called "alert fatigue," and it has two costly consequences: burned-out analysts, and a higher chance that a real threat gets missed in the noise.

The question this project set out to answer was straightforward: can a predictive model learn to tell the difference between a routine, low-risk alert and a genuinely dangerous one, accurately enough that the routine ones can be closed automatically?

#### The Approach

The project used historical alert data describing each incident — things like how sensitive the data involved appeared to be, where it was being sent, how large the transfer was, and whether the employee involved had a history of similar alerts. Because real company security logs are too sensitive to share publicly, this project used a carefully constructed synthetic dataset of 100,000 alerts built to mirror those same real-world patterns, tied to a roster of 100 representative employees.

A statistical model was trained on this historical data to recognize the patterns that distinguish low-risk alerts from high-risk ones — the same kinds of patterns an experienced analyst learns to recognize over time, but applied consistently and instantly to every incoming alert.

The model was deliberately built to be explainable. Rather than a "black box," the approach used here allows a reviewer to see exactly which factors pushed an alert toward being flagged as high-risk — important for a security team that needs to be able to justify and audit automated decisions.

#### Key Findings

**1. The model exceeded its target**

The original goal was to automate 30 to 40 percent of daily alert volume. The final model safely auto-resolves roughly 65 percent of alerts, while keeping the precision of that decision at 98 percent or higher — meaning that when the model says an alert is safe to close, it is correct at least 98 times out of 100.

> *Figure 2 (in the full report). Out of every 100 alerts that arrive in a day, the model can safely close 65 without any analyst involvement.*

**2. Risk is concentrated in a small group of people**

The data showed that high-risk alerts are not evenly spread across the workforce. A small number of employees consistently account for a disproportionate share of risky activity — for example, employees flagged on an internal watchlist or those who are in the process of leaving the company. This means analysts can focus not just on individual alerts, but on a short, prioritized list of people whose recent activity deserves a closer look.

**3. The factors driving risk match what a human analyst would expect**

The model's most influential factors were the same ones a security analyst already pays attention to: how reputable or risky the destination of a data transfer is, how much sensitive information (like Social Security numbers or credit card numbers) was detected, and whether the employee involved has a history of past violations. This is an important finding — it means the model's decisions are explainable and trustworthy rather than relying on patterns a human couldn't sanity-check.

**4. The tradeoff between safety and efficiency is tunable**

The model does not force an all-or-nothing choice. A security team can dial the threshold up or down depending on their risk appetite — a more conservative setting auto-resolves fewer alerts but is even more certain about each one, while a more aggressive setting closes more alerts automatically at a slightly higher (but still small) margin of error.

> *Figure 3 (in the full report). As more alerts are auto-resolved, the precision of that decision gradually declines — giving security teams a dial they can adjust based on their own risk tolerance.*

#### Limitations

- This project used synthetic data designed to mirror real-world patterns, not actual company security logs. Before this model could be used in production, it would need to be retrained on a real organization's historical alert data.
- Attacker behavior changes over time. A model trained on last year's patterns may need retraining periodically to stay accurate as new evasion techniques emerge.
- The model currently treats every alert independently. It does not yet account for sequences of activity over time (for example, a slow, gradual pattern of small data transfers building toward a larger exfiltration).
- Like any statistical model, it will occasionally be wrong in both directions — the goal was to make those errors rare and to make sure the costly kind of error (missing a real threat) is rarer than the inexpensive kind (double-checking a harmless alert).

#### Suggestions for Next Steps

- Pilot the model alongside existing analyst workflows on a subset of real alerts, comparing its recommendations to analyst decisions before fully automating anything.
- Build a feedback loop so that when an analyst overrides the model's recommendation, that correction is used to retrain and improve the model over time.
- Extend the model to look at patterns of behavior over days or weeks, rather than judging each alert in isolation, to catch slower-moving threats.
- Revisit the auto-resolve threshold periodically (for example, quarterly) as part of normal security operations, to make sure it still reflects the organization's current risk tolerance.
- Use the project's accompanying live dashboard to give both security leadership and individual analysts an easy way to monitor results day to day — leadership sees organization-wide volume and trends, while analysts get a focused queue of the people and alerts that most need their attention.

#### Conclusion

This project demonstrated that a predictive model can reliably distinguish low-risk DLP alerts from high-risk ones, exceeding the original goal by safely automating roughly 65 percent of daily alert volume rather than the targeted 30 to 40 percent. The model's reasoning aligns with what experienced analysts already look for, making it explainable and auditable rather than an opaque black box. With a real-data pilot and an ongoing feedback loop, this approach offers a practical path toward meaningfully reducing analyst alert fatigue while keeping genuine threats squarely in human hands.

*Accompanying materials: the full technical notebook, source code, dataset, and an interactive live dashboard are available in this project's GitHub repository.*

---

## 📋 Project Contents

This capstone submission includes:

### ✅ Core Deliverables
1. **Technical Notebook** (`notebooks/01_eda_and_modeling.ipynb`)
   - 32 pre-executed cells with full analysis, model training, and evaluation
   - Exploratory data analysis on 100,000 synthetic alert records
   - Feature engineering, preprocessing, and model comparison
   - Complete code implementation with results

2. **Technical Report** (`reports/technical/Technical_Methodology_Models_and_Techniques.docx`)
   - Deep dive into modeling methodology and algorithm selection
   - Problem framing, data preprocessing, and feature engineering
   - Class imbalance handling strategies (class_weight vs. SMOTE)
   - Model performance comparison and selection rationale
   - Evaluation methodology and threshold optimization

3. **Non-Technical Report** (`reports/non_technical/Non_Technical_Report.docx`)
   - Executive-level summary for stakeholders
   - Business context, findings, and recommendations
   - Interactive demo application overview
   - Professional formatting for board-level presentation

4. **Interactive Demo Application** (`dlp_management_hub.html`)
   - Single-page web application demonstrating model operationalization
   - Three role-based dashboards:
     - **Administrator:** DLP tool connections, system health metrics (99.8% uptime)
     - **Analyst:** Active alerts queue (156 high-risk), remediation tracking (42 in-progress)
     - **Executive:** KPIs (187 resolved/week, $47K cost savings), compliance trends
   - 12 interactive Chart.js visualizations
   - Self-contained HTML (no external dependencies required)

### 📊 Model & Analysis
- **Best Model:** Logistic Regression
  - PR-AUC: 0.855 | ROC-AUC: 0.953
  - Precision: 0.980 | Recall: 0.886
  - Auto-resolve rate: 65.3% (at 98% precision target)
  
- **Dataset:** 100,000 synthetic DLP alerts (reproducible with seed=42)
  - 80/20 class distribution (low-risk/high-risk)
  - 13 features covering alert properties, user attributes, temporal factors
  - Full synthetic, no real data

### 🔧 Technical Components

**Source Code** (`src/`)
- `generate_users.py` — Synthetic user roster generation
- `preprocessing.py` — Feature engineering pipeline (one-hot encoding, scaling, log transforms)
- `train.py` — Model training (Logistic Regression, Random Forest, XGBoost)

**Documentation** (`docs/`)
- `data_dictionary.md` — Complete feature documentation with ranges and descriptions
- Additional methodology and dashboard guides

**Supporting Files**
- `requirements.txt` — Python dependencies (pandas, numpy, scikit-learn, matplotlib, seaborn, joblib)
- `.gitignore` — Git ignore patterns
- `LICENSE` — MIT open-source license
- `.github/workflows/tests.yml` — GitHub Actions CI/CD
- `tests/test_pipeline.py` — Unit test suite

## 📂 Project Structure

```
dlp-predictive-modeling/
├── README.md                    # This file
├── requirements.txt             # Dependencies
├── LICENSE                      # MIT License
├── .gitignore                   # Git configuration
├── dlp_management_hub.html      # Interactive demo (60 KB)
│
├── notebooks/
│   └── 01_eda_and_modeling.ipynb    # Full technical notebook (534 KB)
│
├── src/                         # Source code
│   ├── generate_users.py
│   ├── preprocessing.py
│   └── train.py
│
├── reports/                     # Project deliverables
│   ├── technical/
│   │   └── Technical_Methodology_Models_and_Techniques.docx
│   └── non_technical/
│       └── Non_Technical_Report.docx
│
├── docs/                        # Documentation
│   └── data_dictionary.md
│
├── data/                        # Data directory (for generated files)
│
├── models/                      # Models directory (for trained models)
│
├── tests/                       # Unit tests
│   └── test_pipeline.py
│
└── .github/workflows/           # CI/CD
    └── tests.yml
```

## 🎓 How to Use

### For Capstone Review
1. Start with **Non-Technical Report** (`reports/non_technical/Non_Technical_Report.docx`) for executive overview
2. Review **Interactive Demo** (`dlp_management_hub.html`) for model operationalization
3. Read **Technical Report** (`reports/technical/Technical_Methodology_Models_and_Techniques.docx`) for methodology
4. Explore **Jupyter Notebook** (`notebooks/01_eda_and_modeling.ipynb`) for full code and analysis

### For Model Development
```bash
# Install dependencies
pip install -r requirements.txt

# Generate synthetic data
python src/generate_users.py --n 100 --seed 42 --out data/raw/users.csv

# Train models
python src/train.py

# Run tests
pytest tests/
```

### For Interactive Demo
Simply open `dlp_management_hub.html` in any web browser:
- Click "Login" to access role-based dashboards
- Select role (Administrator, Analyst, or Executive)
- Explore interactive visualizations
- View system metrics, alerts, and compliance data

## 📊 Model Performance Summary

| Metric | Value | Target |
|--------|-------|--------|
| PR-AUC | 0.855 | ✅ Excellent |
| ROC-AUC | 0.953 | ✅ Excellent |
| Precision (Low-Risk) | 0.980 | ✅ Meets 98% floor |
| Recall (High-Risk) | 0.886 | ✅ Strong |
| Auto-Resolve Rate | 65.3% | ✅ High efficiency |
| Training Time | < 0.3s | ✅ Fast |

**Why Logistic Regression?**
- ✅ Highest performance on all primary metrics
- ✅ Interpretable coefficients explain feature importance
- ✅ Calibrated probabilities for threshold optimization
- ✅ Fast training and inference (suitable for production)
- ✅ Superior to Random Forest and XGBoost on this dataset

## 🔄 Pipeline Architecture

```
Raw Data → Preprocessing → Feature Engineering → Model Training → Evaluation → Deployment
```

**Key Technical Decisions:**
- Class imbalance handling: `class_weight='balanced'`
- Feature encoding: OneHotEncoder for categories, StandardScaler for numerics
- Feature engineering: Log-transform for right-skewed payload sizes
- Evaluation: Precision-Recall AUC (appropriate for imbalanced classification)
- Threshold optimization: Business-metric-driven (98% precision floor)

## ✨ Deliverables Checklist

✅ Technical Notebook (32 cells, 534 KB)  
✅ Technical Report (296 KB, comprehensive methodology)  
✅ Non-Technical Report (148 KB, executive summary)  
✅ Interactive Demo Application (60 KB, self-contained)  
✅ Source Code (fully functional Python modules)  
✅ Configuration Files (requirements, .gitignore, LICENSE)  
✅ Tests & CI/CD (GitHub Actions workflow)  
✅ Complete Documentation (data dictionary, guides)  

## 📚 Key Features

- **Reproducible:** All results with seed=42
- **Production-Ready:** Self-contained demo, trained model, evaluation metrics
- **Well-Documented:** Technical and executive reports, code comments
- **Tested:** Unit tests included, CI/CD configured
- **Professional:** MIT license, proper project structure, comprehensive README

## 🎯 Capstone Assessment

This project demonstrates:
- ✅ Complete ML pipeline from problem definition to deployment
- ✅ Handling class imbalance in high-stakes decision-making
- ✅ Model selection based on business constraints
- ✅ Interpretability in security operations context
- ✅ Professional documentation and stakeholder communication
- ✅ Reproducible, production-quality code
- ✅ Interactive visualization for model operationalization

## 📄 License

MIT License — See LICENSE file for details

---

**Status:** ✅ Complete & Ready for Submission  
**Date:** August 2026  
**Format:** Comprehensive Capstone Project Package

