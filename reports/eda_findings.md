# EDA findings (generated from the actual dataset)

- Rows x columns: **284,807 x 31**
- Missing values: **0**
- Exact duplicate rows: **1,081** (removed before splitting during training)
- Legitimate: **284,315**, fraud: **492** (0.1727% of rows)
- Time spans about **48.0 hours**; the highest hourly fraud rate is **2.0548%** at elapsed hour 26 (only 1,752 transactions in that hour).
- Median amount: legitimate **22.0**, fraud **9.25**; mean legitimate **88.291**, fraud **122.2113**.
- Features most correlated with Class: V17 (-0.33), V14 (-0.30), V12 (-0.26), V10 (-0.22), V16 (-0.20).

## Why accuracy is misleading here
A model that labels every transaction legitimate scores about 99.83% accuracy while catching zero fraud.
Precision, recall, F1, PR-AUC and the confusion matrix are used instead.

## Notes
V1-V28 are PCA components with undisclosed meaning, so no real-world interpretation is attached to them.
EDA is exploratory only: no modelling decision (feature removal, thresholds) is taken from it.
