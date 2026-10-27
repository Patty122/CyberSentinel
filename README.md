# CyberSentinel

**Cybersecurity-Based Credit Card Fraud and Anomaly Detection Using Machine Learning**
Course project for ECSCI24302 Machine Learning Essentials (Project-Based Learning).

An end-to-end platform: validated CSV → EDA → leakage-safe preprocessing → tuned models (Logistic Regression, Random Forest, XGBoost, Isolation Forest, plus a Dummy baseline) → saved artifacts → Flask REST API → React dashboard.
This is an **educational prototype**, not a production banking system.

## Problem statement and motivation
Fraud is rare (0.172% of rows) and costly. Manual review and simple rules struggle, and accuracy is meaningless when 99.8% of transactions are legitimate. The project compares models using precision, recall, F1, PR-AUC, ROC-AUC and confusion matrices, and studies class imbalance, threshold choice and error analysis.

## Dataset
[Kaggle: Credit Card Fraud Detection (ULB MLG)](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud). Cite it in any report. **The CSV is not in this repository.** Download `creditcard.csv` manually (free Kaggle account) and place it at `data/raw/creditcard.csv`.
Actual properties of the file we used (computed by `ml/eda.py`): 284,807 rows × 31 columns; 0 missing values; 1,081 duplicate rows; 492 fraud (0.1727%). V1–V28 are PCA components with undisclosed meaning.

## Technology
Python 3.11+, pandas, NumPy, scikit-learn, XGBoost (optional), Matplotlib/Seaborn, joblib · Flask, Flask-CORS, pydantic, pytest · React 18, Vite, Recharts, Lucide · Docker (written, unverified).

## Project layout
```
ml/        data_loader.py eda.py preprocess.py train.py evaluate.py predict.py config.py
backend/   app/{routes,services,schemas,utils}  run.py  requirements.txt
frontend/  src/{components,pages,services,hooks,styles}  package.json vite.config.js
tests/     test_data.py test_preprocessing.py test_models.py test_api.py
docs/      architecture.md api.md model_card.md
data/raw/  (put creditcard.csv here)   models/ (generated)   reports/ (generated)
```

## Windows setup (PowerShell)
Prerequisites: Python 3.11+ and Node.js 20+ (check with `python --version`, `node --version`).

**Terminal 1: project root, one-time setup**
```powershell
cd C:\path\to\cybersentinel
python -m venv .venv
.\.venv\Scripts\Activate.ps1          # if blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env           # optional; defaults work
```
Place `creditcard.csv` in `data\raw\`.

**Terminal 1: analysis and training (run when you want, NOT on every start)**
```powershell
python -m ml.eda                      # writes reports\summary.json, eda_findings.md, figures
python -m ml.train                    # ~5-10 min; writes models\ and reports\*.md. Add --quick for a fast smoke test, --no-xgboost to skip XGBoost
```
Models must be trained on the machine that serves them (joblib files depend on the scikit-learn version).

**Terminal 1: backend** (venv active)
```powershell
cd backend
python run.py                         # http://127.0.0.1:5000/api/health
```
**Terminal 2: frontend**
```powershell
cd C:\path\to\cybersentinel\frontend
npm install
npm run dev                           # http://localhost:5173 (proxies /api to port 5000)
```
**Tests**
```powershell
python -m pytest                      # root, venv active. Unit tests use synthetic data; one integration test uses the real CSV if present
cd frontend; npm test                 # validation unit tests
```
Docker (optional, unverified): train on the host, then `docker compose up --build` and open http://localhost:8080.

### Troubleshooting
* *`Activate.ps1 cannot be loaded`*: run the `Set-ExecutionPolicy` line above.
* *Dashboard says "models not trained"*: run `python -m ml.train` from the project root, then refresh.
* *`Dataset not found`*: the CSV must be exactly `data\raw\creditcard.csv`.
* *`ModuleNotFoundError: ml`*: run ML commands from the project root and start the API with `python run.py` inside `backend\`.
* *CORS error*: add your frontend origin to `CORS_ORIGINS` in `.env`.
* *XGBoost missing from the dashboard*: it was skipped because the package is not installed. Run `pip install xgboost`, then `python -m ml.train` again (training prints a WARNING when this happens). Check with `python -c "import xgboost"`.
* *Model load error after upgrading packages*: retrain.

## ML workflow
1. Validate CSV (columns, numeric, binary target) and report quality. 2. EDA. 3. Drop exact duplicates, stratified 60/20/20 split (seed 42). 4. Feature engineering (log amount, relative hour) and scaling inside pipelines. 5. Randomised search with stratified 3-fold CV on training data only. 6. Fit on train; choose thresholds (max validation F2) and the best model (validation PR-AUC) using validation only. 7. Score the test set once. 8. Save models, metadata, metrics, reports, figures.

Class imbalance: class weighting, threshold tuning and training-only under-sampling are compared in `reports/imbalance_experiment.md` (Logistic Regression). Feature selection: importance rankings are reported (`feature_importance` in `models/metrics.json`); all features are kept because V1–V28 are already PCA components and no removal was validated.

## Results of the run documented here (test set, 95 frauds)
| Model | Precision | Recall | F1 | PR-AUC | ROC-AUC | FP | FN |
|---|---|---|---|---|---|---|---|
| Dummy | 0.000 | 0.000 | 0.000 | 0.002 | 0.500 | 0 | 95 |
| Logistic Regression | 0.791 | 0.758 | 0.774 | 0.685 | 0.957 | 19 | 23 |
| **Random Forest (selected)** | 0.890 | 0.768 | 0.825 | 0.783 | 0.963 | 9 | 22 |
| XGBoost | 0.920 | 0.726 | 0.812 | 0.778 | 0.932 | 6 | 26 |
| Isolation Forest | 0.160 | 0.463 | 0.238 | 0.166 | 0.943 | 231 | 51 |

With 95 test frauds, Random Forest and XGBoost are not meaningfully different. See `docs/model_card.md` for interpretation. Your own run may differ slightly.

## Metrics glossary
Precision = TP/(TP+FP). Recall = TP/(TP+FN). F1 = harmonic mean. PR-AUC = average precision (scikit-learn `average_precision_score`); its chance level equals prevalence (~0.0017). ROC-AUC can look excellent even when precision is poor. FPR = FP/(FP+TN), FNR = FN/(FN+TP). TP fraud caught · TN legitimate passed · FP false alarm · FN missed fraud.

## API
See `docs/api.md`. Endpoints: `GET /api/health, /summary, /models, /metrics, /transactions` (+ `/transactions/sample`), `POST /api/predict, /predict/batch`.

## Security notes and limits
Implemented: strict schema (30 finite bounded numbers, no extras), 1 MB body limit, bounded pagination and batches, restricted CORS, no stack traces or paths in errors, security headers, no upload endpoint, local-only model loading, no feature values in logs, `.env` ignored.
Not implemented (needed for production): authentication/authorisation, rate limiting, TLS, audit logging, a production WSGI server, monitoring and drift detection, model governance. Running `python run.py` is a local development setup.

## Ethical considerations
False positives burden customers; false negatives cost money. Predictions are estimates for human review, never proof of fraud. The data is anonymised, old and regional, and cannot support fairness analysis.

## Git workflow (no remote is configured; push only when you decide to)
```powershell
git init                              # already initialised locally; staging verified to exclude the CSV, models and .env
git add .
git commit -m "Initial commit: CyberSentinel"
git branch -M main
git remote add origin https://github.com/<your-username>/cybersentinel.git
git push -u origin main               # needs your own GitHub credentials
```

## Screenshots
Add after running the app: `docs/screenshots/dashboard.png`, `analysis.png`, `comparison.png`, `explorer.png`.

## Authors
Pratham Patel (2410111114) · Ved Chaudhari (2410111012). Individual contributions are not recorded here; add them before submission.
