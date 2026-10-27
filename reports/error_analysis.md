# Error analysis (selected model, test set, aggregate only)

| Outcome | Count | Median amount | Mean amount | Median score |
|---|---|---|---|---|
| true_positive | 75 | 30.39 | 146.4 | 0.9998 |
| false_negative | 20 | 2.005 | 189.4 | 1.14e-05 |
| false_positive | 8 | 5.805 | 3240 | 0.4126 |
| true_negative | 56643 | 21.6 | 88.26 | 5.839e-07 |

Missed frauds score higher than on average 85.9% of legitimate test transactions, i.e. they look mostly normal to the model.
