# CyberSentinel — Cybersecurity-Based Credit Card Fraud and Anomaly Detection Using Machine Learning

An end-to-end educational prototype: dataset validation → EDA → leakage-safe preprocessing → three models → evaluation → saved artifacts → Flask REST API → React dashboard. **Not a production banking system.**

**Authors:** Pratham Patel (2410111114), Ved Chaudhari (2410111012)

## Problem and motivation

Card fraud is rare but costly; detecting it needs methods that handle extreme class imbalance and balance missed fraud against false alarms.

## Dataset

[Kaggle: mlg-ulb/creditcardfraud](https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud) — `creditcard.csv` (Time, V1–V28, Amount, Class). Download manually and place at `data/raw/creditcard.csv`. It is git-ignored; never commit it. All numbers shown in the app are computed from your actual file.

## Stack

Python 3.13.2 tested locally, pandas, NumPy, scikit-learn, Matplotlib/Seaborn, joblib, Flask, Flask-CORS, pydantic, pytest; React 18, Vite, Recharts, Lucide.

## ML workflow and methodology

Stratified 60/20/20 split (seed 42). Scalers live inside pipelines (fit on train only). Logistic Regression and Random Forest use class weighting. Isolation Forest is trained without labels. Thresholds are chosen on validation (max F1) and locked before test evaluation. The best model is chosen by validation average precision, not accuracy. See `docs/model_card.md` and `docs/architecture.md`.

## Structure

`backend/` Flask app · `ml/` pipeline · `frontend/` React · `tests/` · `docs/` · `models/` (generated) · `reports/` (generated) · `data/raw/` (you add the CSV).

## Windows setup (PowerShell)

**Verified on Windows using Python 3.13.2. All 35 automated tests passed, and the Vite production build completed successfully.** Run commands from the project root unless noted.

```powershell
# Activate the existing virtual environment, or create one first:
# py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1            # if blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
python -m pip install --upgrade pip
python -m pip install -r backend\requirements.txt
cd frontend; npm ci; cd ..              # Node.js required
# Put creditcard.csv in data\raw\
python -m ml.eda                         # once: writes reports\
python -m ml.train                       # once: writes models\
python backend\run.py                    # Terminal 1: API on http://127.0.0.1:5000
cd frontend; npm run dev                 # Terminal 2: UI on http://localhost:5173
python -m pytest -q                      # automated tests
```

Settings are read from environment variables (see `.env.example`), e.g. `$env:FRONTEND_ORIGIN="http://localhost:5173"`.

## API

See `docs/api.md`. Without trained models, endpoints return `status: unavailable` instead of crashing.

## Security notes

Strict feature schema (no extras/NaN/inf), request-size and batch/page limits, CORS restricted to `FRONTEND_ORIGIN`, no stack traces or paths in errors, no transaction data in logs, no upload endpoint, models loaded only from the local `models/` directory. **Not fully secure.** A real deployment would also need authentication, rate limiting, HTTPS, audit logging, monitoring and a hardened server (local dev uses Flask's built-in server).

## Git workflow (run yourself; nothing is pushed for you)

```powershell
git init
git add .
git status        # confirm no CSV, .env or node_modules is staged
git commit -m "Initial commit: CyberSentinel"
git branch -M main
git remote add origin https://github.com/<you>/cybersentinel.git
git push -u origin main
```

## Troubleshooting

`Dataset not found` → place the CSV in `data\raw\`. "Models not trained" → run `python -m ml.train`. "API offline" → start the backend first. `ModuleNotFoundError: ml` → run from the project root.

## Docker (optional, unverified)

Docker configuration has been written but has not been tested. Docker is optional for local development.

## Limitations and ethics

Single-split evaluation, uncalibrated scores, anonymised features, one dataset. Automated decisions about people can cause harm; real use needs human review, fairness and privacy assessment. Screenshots: _to be added after you run the app on the real dataset._
