# Project Completion Steps

A step-by-step roadmap for taking this project from the Discussion Post
to a finished, GitHub-ready repository.

## Phase 1 — Setup ✅
1. ✅ Define research question, scope, and success criteria (done in the
   Discussion Post).
2. ✅ Create repository structure (`data/`, `src/`, `notebooks/`, `models/`,
   `reports/`, `tests/`, `docs/`).
3. ✅ Write `requirements.txt` pinning core dependencies.

## Phase 2 — Data ✅
4. ✅ Build `src/generate_data.py` to synthesize a realistic, anonymized
   100,000-row DLP alert dataset with the features named in the brief
   (event severity, payload size, destination reputation, regex/PII
   match counts, UEBA violation history).
5. ✅ Validate data quality: no nulls, correct dtypes, sane value ranges,
   reproducible with a fixed seed.
6. ✅ Document every field in `docs/data_dictionary.md`.
7. ✅ Document label construction and design rationale in
   `docs/methodology.md`.

## Phase 3 — Preprocessing & Feature Engineering ✅
8. ✅ Build `src/preprocessing.py`: categorical one-hot encoding, numeric
   scaling, derived features (`is_after_hours`, log-transformed payload
   size).
9. ✅ Implement a stratified train/test split to preserve class ratio
   given the imbalanced target.

## Phase 4 — Class Imbalance Handling ✅
10. ✅ Implement `class_weight='balanced'` strategy.
11. ✅ Implement SMOTE oversampling (`src/smote.py`), with automatic
    fallback to `imbalanced-learn` if available.
12. ✅ Confirm resampling is applied to training data only (no leakage).

## Phase 5 — Modeling ✅
13. ✅ Train Logistic Regression baseline (interpretability-first, per
    governance requirements).
14. ✅ Train Random Forest ensemble.
15. ✅ Train XGBoost ensemble (optional — gracefully skipped if the
    package isn't installed).
16. ✅ Select the best model under a recall-floor-constrained rule
    (recall ≥ 0.85 on the high-risk class, then highest auto-resolved
    volume among eligible models — not raw PR-AUC alone) and persist it
    (`models/best_model.joblib`) as a full sklearn `Pipeline` (so raw
    inference inputs go straight in, no manual preprocessing required
    at serving time).

## Phase 6 — Evaluation ✅
17. ✅ Compute precision/recall/F1 per class, ROC-AUC, PR-AUC, confusion
    matrix.
18. ✅ Compute the project's core business metric: max % of alert volume
    auto-resolvable at ≥98% precision.
19. ✅ Generate visualizations (`src/evaluate.py` →
    `reports/figures/`): confusion matrix, ROC curve, PR curve,
    auto-resolve threshold tradeoff curve, feature importance.
20. ✅ Save all metrics to `reports/metrics.json` for traceability.

## Phase 7 — Testing ✅
21. ✅ Write unit tests covering data generation, feature engineering,
    preprocessing shape consistency, stratified split correctness, and
    SMOTE behavior (`tests/test_pipeline.py`).
22. ✅ Run the full test suite and confirm all tests pass.

## Phase 8 — Documentation & Presentation ✅
23. ✅ Write the top-level `README.md` (problem statement, repo
    structure, quickstart, results summary, limitations).
24. ✅ Build an exploratory Jupyter notebook
    (`notebooks/01_eda_and_modeling.ipynb`) walking through the data and
    pipeline interactively for reviewers.
25. ✅ Add `LICENSE` and `.gitignore`.

## Phase 9 — Scale Up & Live Dashboard ✅
26. ✅ Build `src/generate_users.py`: 100-user synthetic roster with
    stable per-user traits (department, device, tenure, watchlist
    status, baseline risk propensity).
27. ✅ Rewrite `src/generate_data.py` to scale to 100,000 rows
    (vectorized with numpy for speed — ~2 seconds at this scale) and
    attribute every alert to a real user from the roster, so a user's
    alert history is internally consistent rather than independently
    randomized per row.
28. ✅ Anchor alert timestamps to a rolling 365-day window ending
    "today," with realistic density on the most recent day, so
    "incidents today" and "incidents year-to-date" KPIs are populated.
29. ✅ Add `predicted_risk_probability` as a continuous output (not just
    the binary `is_high_risk` label), mirroring a real classifier's
    calibrated probability output. **Note:** this column was later found
    to be the label's own source and is now explicitly blocked from
    model features/ranking — see step 39.
30. ✅ Retrain models on the 100k-row dataset; confirm performance holds
    up at scale (PR-AUC improved to ~0.85, auto-resolve volume reached
    ~65% at ≥98% precision — exceeding the original 30–40% target).
31. ✅ Build `src/build_dashboard_data.py`: aggregates the raw 100k-row
    CSV + 100-user roster into a compact (~25KB) JSON payload, avoiding
    the need to parse the full raw dataset client-side.
32. ✅ Build `dashboard/index.html`: standalone live dashboard with
    - **Management view**: total workers, total incidents, incidents
      today, incidents YTD, 30-day trend chart, auto-resolve donut
      chart, department/event-type breakdowns.
    - **Analyst view**: ranked manual-review queue of users with
      high-probability incidents, with a click-through detail drawer.
33. ✅ Validate dashboard: confirmed JSON field names match the JS
    exactly, verified JS syntax with `node --check`, checked HTML tag
    balance, served locally over HTTP and confirmed both `index.html`
    and `data.json` return 200. Later visually confirmed in a real
    headless browser — see step 41.
34. ✅ Extend `tests/test_pipeline.py` with coverage for the user
    roster generator, alert-to-user linkage, per-user risk
    concentration, and the dashboard data builder's output structure
    (14 tests total, all passing).
35. ✅ Update `README.md`, `docs/data_dictionary.md`, and add
    `docs/dashboard.md` to document the new scale, the users dataset,
    and dashboard usage.

## Phase 10 — Correctness Review & Fixes ✅
36. ✅ External code-correctness review identified several issues: an
    xgboost import-crash bug (`ImportError` vs. `XGBoostError`), raw
    PR-AUC model selection ignoring the project's stated cost asymmetry,
    and — most significantly — `predicted_risk_probability` being both
    the ranking signal for the Analyst queue and the literal noisy
    latent score `is_high_risk` is thresholded from (a data leakage
    bug: the "model" queue was really just reading the label's own
    source column).
37. ✅ Fixed the xgboost crash (`src/train.py`), added a recall-floor
    (≥0.85) selection rule before optimizing for auto-resolved volume,
    and added an explicit `LEAKAGE_COLS` blocklist with a runtime
    assertion in `src/preprocessing.py`.
38. ✅ Rewrote `src/build_dashboard_data.py` to score every alert
    through the actual trained pipeline (`model_probability`) instead
    of reading `predicted_risk_probability`, and to clearly separate
    real model output from ground-truth-only comparison figures in the
    JSON payload (`ground_truth_*`-prefixed fields).
39. ✅ Updated `dashboard/index.html` and `dlp_management_hub.html` to
    consume `model_probability` and to visually flag which figures are
    real model/data output vs. illustrative (no live tool telemetry
    exists in this project).
40. ✅ Retrained with `xgboost` and `imbalanced-learn` actually
    installed: XGBoost reached the highest raw PR-AUC (0.857) and
    auto-resolved volume (65.9%) of the three models, but recall
    (0.721) falls below the 0.85 floor, so it is correctly excluded and
    Logistic Regression (PR-AUC 0.855, recall 0.886) remains selected —
    confirmed with a real retrain, not just by reading the code.
41. ✅ Visually confirmed both dashboards in a real (headless) browser:
    clicked through every section, verified real numbers render
    correctly, and captured screenshots.
42. ✅ Re-ran the full test suite after all fixes (14/14 tests pass) and
    updated `README.md`, `docs/methodology.md`, `docs/dashboard.md`,
    and `docs/data_dictionary.md` to describe the fixes and the
    leakage warning.

## Phase 11 — Capstone Deliverables ✅
43. ✅ Restructure `notebooks/01_eda_and_modeling.ipynb` into the order
    required by the capstone rubric (Module 20): problem statement →
    data sources and structure → techniques → results, with markdown
    narration between every code cell rather than a developer scratch
    pad.
44. ✅ Execute every code cell in the notebook in sequence and embed
    real outputs (printed text, dataframe previews, and matplotlib
    figures as inline PNGs) directly into the saved `.ipynb`, so it is
    reviewable without needing to be re-run. Confirmed 25/25 code
    cells executed with zero errors and that key numbers (confusion
    matrix, PR-AUC, auto-resolve volume) match `reports/metrics.json`
    exactly.
45. ✅ Draft `reports/non_technical/Non_Technical_Report.docx`: a
    plain-language capstone report covering the problem, approach, key
    findings, limitations, and suggested next steps — built since the
    program's actual "Final Report Template" file was not available to
    match exactly. Includes two purpose-built plain-language charts
    (target-vs-achieved bar chart, a "per 100 alerts" breakdown) plus
    one technical figure included for reference.
46. ✅ Visually QA the report by rendering it to PDF and reviewing
    every page as an image: fixed an initial issue where the running
    header appeared on the title page (suppressed via `titlePage:
    true`), and fixed an orphaned final paragraph stranded alone on a
    6th page (merged into the conclusion section, bringing the report
    to a clean 5 pages).
47. ✅ Validated the docx with the skill's `validate.py` (47 paragraphs,
    all validations passed).
48. ✅ Re-ran the full test suite after all changes (14/14 tests pass).
49. ✅ Updated `README.md` with a "Capstone deliverables" section and
    refreshed the repository structure diagram to include both new
    files.

## Phase 12 — Technical Methodology Document ✅
50. ✅ Drafted `reports/technical/Technical_Methodology_Models_and_Techniques.docx`:
    a deep, technically-detailed companion document explaining which
    models were used (Logistic Regression, Random Forest, XGBoost), the
    exact hyperparameters for each, the class-imbalance strategies
    (`class_weight` vs. SMOTE) and why both exist, the preprocessing
    pipeline, the evaluation methodology (including why PR-AUC is
    emphasized over ROC-AUC and how the auto-resolve threshold sweep
    works), and a section on approaches that were considered and
    explicitly rejected (unsupervised anomaly detection, deep learning,
    naive undersampling) with reasoning for each. Includes 4 embedded
    figures and a model comparison table with real metrics pulled from
    `reports/metrics.json`, including XGBoost's actual benchmarked
    results and why the recall-floor rule excludes it despite a
    marginally higher raw PR-AUC.
51. ✅ Discovered and worked around two real bugs in the `docx` npm
    package's XML serialization while validating this document:
    - `Paragraph`'s `border` property (used for the bordered code
      block) is always serialized as `top, bottom, left, right`,
      regardless of the JS object key order passed in — but the OOXML
      schema requires `top, left, bottom, right`. Worked around with a
      reusable post-processing script (`fix_pbdr_order.py`) that
      unpacks the docx, reorders `<w:pBdr>` child elements via regex,
      and repacks it. (Table-level `tblBorders`, by contrast, was
      already correctly ordered by the library and did not need this
      fix — confirmed via direct schema lookup before "fixing" it
      unnecessarily and briefly reintroducing the bug.)
    - Multi-line text passed as a single string with embedded `\n` to
      a `TextRun` does not render as separate lines in Word (newlines
      are silently collapsed); fixed by splitting on `\n` and inserting
      explicit `TextRun({ break: 1 })` elements between lines.
52. ✅ Fixed an inline markdown-style `**bold**` parser bug where the
    raw asterisks were rendering literally instead of as bold text
    (the helper only handled backtick code spans initially).
53. ✅ Fixed a table-header row that was splitting across a page
    boundary, leaving truncated header text on the continuation page
    — resolved by shortening header labels, adding `cantSplit: true`
    to table rows, and forcing the table's section to start on a
    fresh page.
54. ✅ Visually QA'd all pages of the final PDF rendering, page by
    page, to confirm every fix actually took effect (bold text,
    code block line breaks, table headers, page breaks) rather than
    trusting the schema validator alone. Re-checked again after adding
    the XGBoost benchmark row/paragraphs (step 50): a forced page break
    before the "Model comparison summary" heading had left a near-empty
    page once the XGBoost text was added, so it was swapped for a
    `keepNext` on the heading instead, restoring clean 9-page pagination.
55. ✅ Re-ran the full test suite after all changes (14/14 tests still
    pass — this document doesn't touch the data/model pipeline).
56. ✅ Updated `README.md` with the third capstone-adjacent deliverable
    and refreshed the repository structure diagram and quickstart.

## Phase 13 — Publish to GitHub ✅
57. ✅ Create a new GitHub repository
    (`Assignment-Capstone-Project-24.1-Final-Report-`).
58. ✅ Upload the project to `main` via GitHub's web "Add file → Upload
    files" interface (used instead of the git CLI). All folders and
    files are present, including `.gitignore` and the `data/raw`,
    `notebooks`, and `LICENSE` from earlier commits.
59. ✅ Add a GitHub Actions workflow (`.github/workflows/tests.yml`) to
    run `pytest tests/` on every push/PR for CI — created via GitHub's
    "Create new file" with the full nested path, since the native file
    picker used by "Upload files" can't select a folder directly.
60. ⬜ (Optional) Add badges to the README (build status, license,
    Python version) once the Actions workflow has run at least once.
61. ✅ Re-run `train.py` with `xgboost` and `imbalanced-learn` installed
    to capture their results in the README and technical report's
    results tables (see step 40) — everything also still runs
    correctly without them via graceful fallbacks.
62. ✅ Open both `dashboard/index.html` and `dlp_management_hub.html` in
    a real (headless) browser and visually confirm they render as
    expected — see step 41.
63. ⬜ (Optional) Compare `reports/non_technical/Non_Technical_Report.docx`
    against your program's actual "Final Report Template" (referenced
    in the Capstone Project Overview PDF but not uploaded to this
    conversation). The report built here uses a standard structure
    (executive summary, problem, approach, key findings, limitations,
    next steps, conclusion) that satisfies what the overview PDF says
    the report must cover, but if your program's template specifies
    different section names, ordering, or required elements (e.g. a
    specific title page format), adjust headings accordingly before
    submitting.

## Suggested Future Extensions (post-publish)
- Add a small Flask/FastAPI inference endpoint wrapping
  `models/best_model.joblib` for live scoring demos.
- Add SHAP-based explainability plots for the ensemble models to
  support governance/audit review of individual high-risk predictions.
- Add a simple drift-monitoring script comparing incoming alert feature
  distributions against the training distribution over time.
