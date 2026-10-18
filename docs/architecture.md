# Architecture

```
creditcard.csv -> data_loader (validate) -> eda -> preprocess (split + pipelines) -> train -> evaluate
   -> models/*.joblib + metadata.json + metrics.json -> Flask API (loads artifacts) -> React dashboard
```

| Module | Purpose |
|---|---|
| `ml/data_loader.py` | Loads CSV, validates schema/labels, reports actual dimensions, missing values, duplicates, class balance. |
| `ml/eda.py` | Writes `reports/eda_summary.json`, `reports/eda_findings.md`, figures. Everything computed from the loaded file. |
| `ml/preprocess.py` | Stratified 60/20/20 split (seed 42); model pipelines (scaler inside the pipeline, fit on train only). |
| `ml/evaluate.py` | Validation-only threshold selection; all metrics, confusion matrix, ROC/PR curves. |
| `ml/train.py` | Trains the 3 models, locks thresholds on validation, reports test metrics, runs class-weight and threshold experiments (validation only), saves artifacts. Separate command. |
| `ml/predict.py` | Loads our own artifacts, checks feature schema, returns predictions. |
| `backend/app/schemas` | Strict pydantic schemas (all 30 features required, no extras, no NaN/inf, no strings/bools). |
| `backend/app/routes/api.py` | REST endpoints. |
| `backend/app/services/store.py` | Lazy, failure-tolerant loading of models, reports, dataset. |
| `frontend/src` | React pages (Dashboard, Analysis, Comparison, Explorer), API client with timeout, loading/error/unavailable states. |

Design decisions: the API never trains; Isolation Forest is fit without labels, its score is `-score_samples` (higher = more anomalous) and its threshold is chosen on validation F1 against known labels (offline evaluation only); no resampling was applied.
