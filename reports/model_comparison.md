# Model comparison (held-out test set, thresholds locked from validation)

Selection rule: highest validation PR-AUC (average precision, rounded to 4 d.p.), ties broken by validation F1; test set not used

Selected model: **XGBoost**

Test prevalence of fraud: 0.1674% (precision of a random classifier equals prevalence).

| Model | Best hyper-parameters | CV AP (train) | Val AP | Threshold | Test precision | Test recall | Test F1 | Test PR-AUC | Test ROC-AUC | FP | FN |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Dummy baseline | `{}` | - | 0.0017 | 0.5 | 0.0000 | 0.0000 | 0.0000 | 0.0017 | 0.5000 | 0 | 95 |
| Logistic Regression | `{"class_weight": null, "C": 0.1}` | 0.6855 | 0.7990 | 0.0392 | 0.7551 | 0.7789 | 0.7668 | 0.6950 | 0.9523 | 24 | 21 |
| Random Forest | `{"n_estimators": 100, "min_samples_leaf": 3, "max_features": "sqrt", "max_depth": 16, "class_weight": "balanced_subsample"}` | 0.7889 | 0.8649 | 0.2995 | 0.9157 | 0.8000 | 0.8539 | 0.8097 | 0.9327 | 7 | 19 |
| XGBoost | `{"subsample": 0.8, "scale_pos_weight": 24.462604401095707, "n_estimators": 300, "max_depth": 6, "learning_rate": 0.2}` | 0.8141 | 0.8878 | 0.1369 | 0.9036 | 0.7895 | 0.8427 | 0.8218 | 0.9703 | 8 | 20 |
| Isolation Forest | `{"max_samples": 1024, "n_estimators": 100}` | - | 0.2721 | 0.587 | 0.1600 | 0.4632 | 0.2378 | 0.1657 | 0.9434 | 231 | 51 |
