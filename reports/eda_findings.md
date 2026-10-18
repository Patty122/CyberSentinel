# EDA Findings (generated from the actual dataset)

- Rows: 284,807; columns: 31
- Missing values: 0
- Duplicate rows: 1,081
- Legitimate: 284,315; fraud: 492 (0.1727%)

## Why accuracy is misleading
A model that labels every transaction legitimate scores 99.8273% accuracy while catching zero fraud. This project therefore reports precision, recall, F1, PR-AUC, ROC-AUC, and balanced accuracy instead.

## Features most correlated with Class (V1-V28 are anonymised; no meaning is assumed)
- V17: -0.326
- V14: -0.303
- V12: -0.261
- V10: -0.217
- V16: -0.197
- V3: -0.193
- V7: -0.187
- V11: +0.155
- V4: +0.133
- V18: -0.111
