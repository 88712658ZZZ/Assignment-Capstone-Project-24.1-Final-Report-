# DLP Predictive Modeling — Capstone Project

Optimizing Data Loss Prevention operations using machine learning to classify security alerts and reduce manual review overhead by 65%.

## 🎯 Executive Summary

This capstone develops a **binary classification model** that predicts which DLP (Data Loss Prevention) security alerts require human analyst review vs. safe auto-resolution. The solution reduces analyst workload by approximately 65% while maintaining 98% precision on auto-resolved alerts and 88.6% recall on high-risk cases.

**Key Achievement:** Logistic Regression model with PR-AUC of 0.855 and ROC-AUC of 0.953, achieving business target of 65.3% auto-resolution rate at 98% precision floor.

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

