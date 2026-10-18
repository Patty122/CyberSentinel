"""Metrics on held-out predictions. Thresholds are chosen on validation data only."""
from __future__ import annotations

import numpy as np
from sklearn.metrics import (average_precision_score, balanced_accuracy_score, classification_report,
                             confusion_matrix, f1_score, precision_recall_curve, precision_score,
                             recall_score, roc_auc_score, roc_curve)


def select_threshold(y_val, scores) -> tuple[float, float]:
    """Return (threshold, F1) maximising F1 on validation data."""
    p, r, t = precision_recall_curve(y_val, scores)
    f1 = 2 * p[:-1] * r[:-1] / np.maximum(p[:-1] + r[:-1], 1e-12)
    i = int(np.argmax(f1))
    return float(t[i]), float(f1[i])


def _downsample(*arrays, max_points: int = 150):
    n = len(arrays[0])
    if n <= max_points:
        return [np.asarray(a).round(6).tolist() for a in arrays]
    idx = np.unique(np.linspace(0, n - 1, max_points).astype(int))
    return [np.asarray(a)[idx].round(6).tolist() for a in arrays]


def compute_metrics(y_true, scores, threshold: float, include_curves: bool = False) -> dict:
    y_true = np.asarray(y_true)
    scores = np.asarray(scores)
    y_pred = (scores >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    both = len(np.unique(y_true)) == 2
    m = {
        "threshold": float(threshold),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, scores)) if both else None,
        # sklearn average_precision_score: step-wise area under the PR curve (not trapezoidal)
        "average_precision": float(average_precision_score(y_true, scores)) if both else None,
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "false_positive_rate": float(fp / (fp + tn)) if (fp + tn) else 0.0,
        "false_negative_rate": float(fn / (fn + tp)) if (fn + tp) else 0.0,
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "prevalence": float(y_true.mean()),
        "n_samples": int(len(y_true)),
        "classification_report": classification_report(
            y_true, y_pred, labels=[0, 1], target_names=["legitimate", "fraud"],
            output_dict=True, zero_division=0),
    }
    if include_curves and both:
        fpr, tpr, _ = roc_curve(y_true, scores)
        p, r, _ = precision_recall_curve(y_true, scores)
        fpr, tpr = _downsample(fpr, tpr)
        p, r = _downsample(p, r)
        m["curves"] = {"roc": {"fpr": fpr, "tpr": tpr}, "pr": {"precision": p, "recall": r}}
    return m
