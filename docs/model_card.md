# Model Card — CyberSentinel

**Intended use:** educational demonstration of fraud/anomaly detection. Not for real credit decisions.
**Models:** Logistic Regression (scaled, class-weighted), Random Forest (class-weighted), Isolation Forest (unsupervised).
**Data:** Kaggle "Credit Card Fraud Detection" (mlg-ulb). V1–V28 are anonymised transforms; Time and Amount are raw. Counts, prevalence and splits are recorded in `models/metadata.json` after training.
**Evaluation:** stratified 60/20/20 split, seed 42. Threshold = max F1 on validation; best model = highest validation average precision; test set used only for final reporting. Metrics: precision, recall, F1, ROC-AUC, average precision (scikit-learn step-wise definition), balanced accuracy, FPR, FNR, confusion matrix.
**Results:** pending — see `models/metrics.json` after running `python -m ml.train` on the real dataset. No results are claimed here.
**Class imbalance:** fraud is a tiny minority, so accuracy is misleading. Class weighting and threshold tuning are used; resampling is not.
**Risks:** false negatives = missed fraud and financial loss; false positives = blocked legitimate customers and alert fatigue. Probabilities are not calibrated. The data covers one period and one region, so drift and generalisation are unknown. A single split gives no confidence interval.
**Limitations:** no cross-validation, no adversarial robustness testing, no fairness analysis (no demographic fields exist), V1–V28 cannot be interpreted.
