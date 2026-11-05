# Model card: CyberSentinel fraud detectors

**Version:** 1.0.0 · **Authors:** Pratham Patel, Ved Chaudhari · **Status:** educational prototype (ECSCI24302 project), not a production banking system.

## Intended use
Compare supervised and unsupervised approaches to flagging suspicious card transactions on a public, anonymised dataset, and demonstrate an ML-to-web pipeline. **Not** for real payment decisions, customer blocking, or any automated action against a person.

## Training data
Kaggle "Credit Card Fraud Detection" (ULB Machine Learning Group): 284,807 transactions from two days in September 2013 by European cardholders, 492 fraud (0.173%). Features: `Time`, `Amount`, and 28 PCA components `V1`–`V28` whose meaning is undisclosed. In our copy: 0 missing values, 1,081 exact duplicate rows (removed before splitting → 283,726 rows).
Split (stratified, seed 42): train 170,235 (284 fraud) · validation 56,745 (94 fraud) · test 56,746 (95 fraud).

## Models and procedure
Dummy baseline, Logistic Regression, Random Forest, XGBoost, Isolation Forest. Engineered features: `log_amount`, `hour_elapsed_mod24` (relative, not clock time). Scaling inside pipelines (LR, Isolation Forest). Supervised hyper-parameters tuned by randomised search (5 configurations, stratified 3-fold CV, average precision) on a stratified 25,000-row subsample of the training split, then refitted on the full training split. Isolation Forest fitted without labels; its small grid was scored on validation average precision. Decision thresholds maximise validation F2 (recall weighted twice as much as precision). The model was selected by validation PR-AUC. The test set was scored once with locked thresholds.

## Current model selection and results

**Selected model in the current application run: XGBoost.** This is the model shown as selected in the current dashboard/run, as confirmed by the project owner. Selection is dynamic, not hard-coded: the training code chooses the candidate with the highest validation PR-AUC (average precision, rounded to four decimal places), using validation F1 to break ties. The held-out test set is not used to choose the model.

The previous results table identified Random Forest as selected. Those figures belong to an older run and have been removed from the current results section to avoid presenting them as current XGBoost results.

The current generated `models/metrics.json` was not present in the supplied project archive, so the latest XGBoost test metrics cannot be independently verified or safely populated here. Fill this snapshot from the exact metrics file produced by the run shown in the dashboard.

| Current XGBoost result | Value from current `models/metrics.json` |
|---|---|
| Precision (test) | To be copied from current run |
| Recall (test) | To be copied from current run |
| F1 (test) | To be copied from current run |
| PR-AUC / average precision (test) | To be copied from current run |
| ROC-AUC (test) | To be copied from current run |
| Decision threshold (selected on validation) | To be copied from current run |
| Confusion matrix (TN, FP, FN, TP) | To be copied from current run |
| Validation PR-AUC used for selection | To be copied from current run |
| Validation F1 used as tie-breaker | To be copied from current run |

**Interpretation:** XGBoost is the selected model in the current run under the project's validation-based selection rule. Report its held-out test metrics separately from validation scores. PR-AUC is especially relevant because fraud is a very small minority class.

## Risks
* **False negatives** let fraud through (22 of 95 here at the chosen threshold). **False positives** inconvenience legitimate customers and cost analyst time (9 here, but at real transaction volumes even a 0.016% false-positive rate means many alerts).
* The data is from 2013, from two days, from one region; fraud patterns drift. Performance on current data is unknown.
* Because V1–V28 are anonymised PCA outputs, the model cannot be explained in business terms and fairness cannot be assessed.

## Not done / future work
Probability calibration, cost-sensitive threshold choice with real costs, repeated-split or nested-CV variance estimates, time-based splitting, SHAP-style explanations, drift monitoring.
