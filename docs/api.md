# API

All responses: `{"status": "ok"|"unavailable"|"error", "data": ..., "error": {"code","message","fields"?}}`.

| Endpoint | Notes |
|---|---|
| `GET /api/health` | `models_available`, `dataset_available`, `eda_available`. |
| `GET /api/summary` | EDA summary; `status: unavailable` if `python -m ml.eda` has not been run. |
| `GET /api/models` | Models, thresholds, test metrics (no curves). |
| `GET /api/metrics` | Full metrics incl. confusion matrices, curves, experiments. |
| `POST /api/predict` | Body `{"features": {Time, V1..V28, Amount}, "model": optional}` -> 200, or 422 with per-field errors. |
| `POST /api/predict/batch` | Body `{"transactions": [features...], "model": optional}`; max `MAX_BATCH_SIZE` (default 100, else 413). Whole batch rejected if any item is invalid; errors keyed like `1.V3`. |
| `GET /api/transactions` | `page`, `page_size` (max 100), `class` (0/1), `min_amount`, `max_amount`. Needs local dataset. |

Models: `logistic_regression`, `random_forest`, `isolation_forest`. Supervised models return `fraud_probability` (uncalibrated). Isolation Forest returns `anomaly_score` and `is_anomaly`, and `fraud_probability: null`.

```powershell
# $features must contain all 30 keys: Time, V1..V28, Amount
$body = @{ features = $features } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/predict -ContentType 'application/json' -Body $body
```
