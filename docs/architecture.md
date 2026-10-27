# Architecture

```
creditcard.csv ──► data_loader (validate) ──► eda ──► reports/summary.json, figures, eda_findings.md
      │
      └──► drop duplicates ──► stratified 60/20/20 split ──► preprocess (Pipeline) ──► train
                                                                │  CV tuning on TRAIN only
                                                                │  thresholds + model choice on VALIDATION only
                                                                ▼  single evaluation on TEST
                                           models/*.joblib, metadata.json, metrics.json, reports/*.md, figures
                                                                │
                                   Flask API (loads artifacts, never retrains) ──► React dashboard
```

Training and serving are separate commands: `python -m ml.train` writes artifacts; `python backend/run.py` only reads them.

## Modules

| Path | Purpose |
|---|---|
| `ml/config.py` | Paths, feature schema, seed, split sizes, threshold rule (all overridable by environment variables). |
| `ml/data_loader.py` | Loads and validates the CSV (columns, numeric types, binary target), quality report, duplicate removal, stratified split. |
| `ml/eda.py` | Reproducible EDA: `reports/summary.json`, `reports/eda_findings.md`, six figures. |
| `ml/preprocess.py` | `FeatureEngineer` (log amount, relative hour), `build_pipeline` (engineer → optional scaler → model), training-only under-sampling helper. |
| `ml/train.py` | Hyper-parameter search, fitting, validation-based threshold/model selection, one test evaluation, artifact writing. |
| `ml/evaluate.py` | Metrics, threshold selection, ROC/PR curves, error analysis, plots. |
| `ml/predict.py` | `Predictor`: loads saved pipelines, enforces feature order, returns label/probability or anomaly score. |
| `backend/app/` | Flask factory, config, routes (`health`, `analysis`, `predict`, `transactions`), strict pydantic schema, artifact and dataset services, error handlers. |
| `frontend/src/` | React pages (Dashboard, Transaction analysis, Model comparison, Data explorer), API client, validation, charts. |
| `tests/` | pytest suite on synthetic fixtures (+ one optional integration test on the real file). |

## Leakage controls

* Duplicates removed **before** splitting so identical rows cannot appear in both train and test.
* Scalers live inside sklearn `Pipeline`s: fitted on training rows only (and inside each CV fold).
* Hyper-parameters: CV on the training split. Isolation Forest: validation average precision (model fitted without labels).
* Thresholds (maximise validation F2) and the winning model (highest validation PR-AUC) are fixed **before** the test set is scored.
* The test set is scored once per model; nothing is tuned afterwards.

## Security design

Strict input schema (exactly 30 finite numbers, bounded, no extra keys), request-size limit, bounded pagination and batch size, CORS limited to configured origins, JSON-only errors with no stack traces or paths, security headers, no upload endpoint, models loaded only from the local `models/` directory, no feature values in logs. See the README for production gaps (authentication, rate limiting, TLS, monitoring).
