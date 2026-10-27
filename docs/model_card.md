# Model card: CyberSentinel fraud detectors

**Version:** 1.0.0 · **Authors:** Pratham Patel, Ved Chaudhari · **Status:** educational prototype (ECSCI24302 project), not a production banking system.

## Intended use
Compare supervised and unsupervised approaches to flagging suspicious card transactions on a public, anonymised dataset, and demonstrate an ML-to-web pipeline. **Not** for real payment decisions, customer blocking, or any automated action against a person.

## Training data
Kaggle "Credit Card Fraud Detection" (ULB Machine Learning Group): 284,807 transactions from two days in September 2013 by European cardholders, 492 fraud (0.173%). Features: `Time`, `Amount`, and 28 PCA components `V1`–`V28` whose meaning is undisclosed. In our copy: 0 missing values, 1,081 exact duplicate rows (removed before splitting → 283,726 rows).
Split (stratified, seed 42): train 170,235 (284 fraud) · validation 56,745 (94 fraud) · test 56,746 (95 fraud).

## Models and procedure
Dummy baseline, Logistic Regression, Random Forest, XGBoost, Isolation Forest. Engineered features: `log_amount`, `hour_elapsed_mod24` (relative, not clock time). Scaling inside pipelines (LR, Isolation Forest). Supervised hyper-parameters tuned by randomised search (5 configurations, stratified 3-fold CV, average precision) on a stratified 25,000-row subsample of the training split, then refitted on the full training split. Isolation Forest fitted without labels; its small grid was scored on validation average precision. Decision thresholds maximise validation F2 (recall weighted twice as much as precision). The model was selected by validation PR-AUC. The test set was scored once with locked thresholds.

## Results (held-out test set, 95 frauds, prevalence 0.167%)
| Model | Precision | Recall | F1 | PR-AUC (avg. precision) | ROC-AUC | False alarms | Missed fraud |
|---|---|---|---|---|---|---|---|
| Dummy baseline | 0.000 | 0.000 | 0.000 | 0.0017 | 0.500 | 0 | 95 |
| Logistic Regression | 0.791 | 0.758 | 0.774 | 0.685 | 0.957 | 19 | 23 |
| **Random Forest (selected)** | 0.890 | 0.768 | 0.825 | 0.783 | 0.963 | 9 | 22 |
| XGBoost | 0.920 | 0.726 | 0.812 | 0.778 | 0.932 | 6 | 26 |
| Isolation Forest | 0.160 | 0.463 | 0.238 | 0.166 | 0.943 | 231 | 51 |

Random Forest confusion matrix: TN 56,642 · FP 9 · FN 22 · TP 73. These numbers come from `models/metrics.json` of the run documented here; re-training on another machine or library version can change them slightly.

## Interpretation and caveats
* With only 95 test frauds, one extra caught or missed case moves recall by about one percentage point. Random Forest and XGBoost are **statistically indistinguishable** here; the selection rule (validation PR-AUC) picked Random Forest, but a different seed could reorder them.
* Validation PR-AUC (0.877 for Random Forest) is higher than test PR-AUC (0.783): the model selection is optimistic on validation, so report the test figure.
* The Isolation Forest has a high ROC-AUC but low precision: ROC-AUC hides the false-alarm burden when negatives dominate. Anomalous is not the same as fraudulent.
* Accuracy is ~99.9% even for a model that never flags fraud, so it is not used.
* Probabilities are uncalibrated. Isolation Forest scores are not probabilities.
* Missed frauds (median amount ≈ 2.0) score like ordinary transactions; the model likely cannot separate them using these features alone.

## Risks
* **False negatives** let fraud through (22 of 95 here at the chosen threshold). **False positives** inconvenience legitimate customers and cost analyst time (9 here, but at real transaction volumes even a 0.016% false-positive rate means many alerts).
* The data is from 2013, from two days, from one region; fraud patterns drift. Performance on current data is unknown.
* Because V1–V28 are anonymised PCA outputs, the model cannot be explained in business terms and fairness cannot be assessed.

## Not done / future work
Probability calibration, cost-sensitive threshold choice with real costs, repeated-split or nested-CV variance estimates, time-based splitting, SHAP-style explanations, drift monitoring.
