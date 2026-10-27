# API reference

Base URL (local): `http://127.0.0.1:5000/api`. All responses: `{"status":"ok","data":...}` or `{"status":"error","error":{"code","message","details?"}}`.

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Service status and which artifacts exist. Always 200 even when artifacts are missing. |
| GET | `/summary` | EDA summary from the real dataset (404 until `python -m ml.eda` has run). |
| GET | `/models` | Models, thresholds, validation and test metrics (404 until trained). |
| GET | `/metrics` | Full evaluation: confusion matrices, curves, error analysis, tuning, imbalance experiment. |
| POST | `/predict` | One prediction. |
| POST | `/predict/batch` | Up to `MAX_BATCH_SIZE` (default 100) predictions. |
| GET | `/transactions` | Paginated rows. Query: `page`, `page_size` (≤100), `class` (0/1), `min_amount`, `max_amount`, `id`. |
| GET | `/transactions/sample` | One real dataset row (`class` optional) for trying the form. Extra endpoint beyond the brief. |

## POST /predict

```json
{ "features": { "Time": 406, "V1": -2.31, "...": 0, "V28": 0.02, "Amount": 0.0 }, "model": "random_forest" }
```
`features` must contain exactly `Time`, `V1`..`V28`, `Amount` as finite JSON numbers (not strings or booleans). `Time` ≥ 0, `Amount` ≥ 0, |V| ≤ 1000. `model` is optional (defaults to the validation-selected model).

Response (`data`): `model`, `kind` (`supervised`|`anomaly`), `label` (0/1), `label_name`, `probability`, `anomaly_score`, `threshold`, `disclaimer`.
* Supervised models return an **uncalibrated** probability; `anomaly_score` is `null`.
* Isolation Forest returns `anomaly_score` (higher = more anomalous) and **no probability**.

Errors: 400 malformed body / unknown model, 413 body too large, 422 field-level validation (`error.details` maps field → message), 503 models not trained.

## POST /predict/batch
```json
{ "transactions": [ {"...30 features..."}, {"...30 features..."} ], "model": "xgboost" }
```
Returns `results[i]` = `{index, valid: true, prediction}` or `{index, valid: false, errors}`, plus `valid_count` and `invalid_count`. Empty list → 400; too many → 413.

## Example (PowerShell)
```powershell
$body = '{"features":{"Time":0,"V1":0,"V2":0,"V3":0,"V4":0,"V5":0,"V6":0,"V7":0,"V8":0,"V9":0,"V10":0,"V11":0,"V12":0,"V13":0,"V14":0,"V15":0,"V16":0,"V17":0,"V18":0,"V19":0,"V20":0,"V21":0,"V22":0,"V23":0,"V24":0,"V25":0,"V26":0,"V27":0,"V28":0,"Amount":10}}'
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/api/predict -ContentType "application/json" -Body $body
```
(An all-zero vector is only a syntax example, not a genuine transaction. Use `/transactions/sample` for real rows.)
