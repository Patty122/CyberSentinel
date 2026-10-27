# Class-imbalance experiment (Logistic Regression, validation set)

| Strategy | Train rows | Precision | Recall | F1 | PR-AUC | False positives |
|---|---|---|---|---|---|---|
| no_imbalance_handling | 170,235 | 0.6833 | 0.8723 | 0.7664 | 0.8001 | 38 |
| class_weight_balanced | 170,235 | 0.8667 | 0.8298 | 0.8478 | 0.7882 | 12 |
| undersample_10_to_1_train_only | 3,124 | 0.7207 | 0.8511 | 0.7805 | 0.7997 | 31 |
