"""Metrics, threshold selection (validation only), curves, error analysis and plots."""
import numpy as np
from sklearn.metrics import (average_precision_score, balanced_accuracy_score, classification_report,
                             confusion_matrix, f1_score, fbeta_score, precision_recall_curve,
                             precision_score, recall_score, roc_auc_score, roc_curve)

from . import config


def choose_threshold(y_val, scores_val, beta: float = config.THRESHOLD_BETA) -> float:
    """Pick the score threshold that maximises F-beta on VALIDATION data only."""
    prec, rec, thr = precision_recall_curve(y_val, scores_val)
    prec, rec = prec[:-1], rec[:-1]
    denom = beta ** 2 * prec + rec
    fb = np.divide((1 + beta ** 2) * prec * rec, denom, out=np.zeros_like(denom), where=denom > 0)
    best = np.flatnonzero(fb == fb.max())[-1]  # ties -> higher threshold (fewer false alarms)
    return float(thr[best])


def compute_metrics(y_true, scores, threshold: float) -> dict:
    """All metrics at a fixed, pre-selected threshold. PR-AUC = average precision (sklearn)."""
    y_true = np.asarray(y_true)
    y_pred = (np.asarray(scores) >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    report = classification_report(y_true, y_pred, labels=[0, 1],
                                   target_names=["legitimate", "fraud"], output_dict=True, zero_division=0)
    return {
        "threshold": float(threshold),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "f2": float(fbeta_score(y_true, y_pred, beta=2, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, scores)),
        "pr_auc_average_precision": float(average_precision_score(y_true, scores)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "accuracy": float((y_pred == y_true).mean()),
        "false_positive_rate": float(fp / (fp + tn)) if (fp + tn) else 0.0,
        "false_negative_rate": float(fn / (fn + tp)) if (fn + tp) else 0.0,
        "prevalence": float(y_true.mean()),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
        "classification_report": report,
    }


def curves(y_true, scores, max_points: int = 150) -> dict:
    """ROC and precision-recall curve points, down-sampled for the dashboard."""
    fpr, tpr, _ = roc_curve(y_true, scores)
    prec, rec, _ = precision_recall_curve(y_true, scores)

    def thin(a, b):
        if len(a) <= max_points:
            return a, b
        idx = np.unique(np.linspace(0, len(a) - 1, max_points).astype(int))
        return a[idx], b[idx]

    fpr, tpr = thin(fpr, tpr)
    rec, prec = thin(rec, prec)
    r = lambda v: [round(float(x), 5) for x in v]
    return {"roc": {"fpr": r(fpr), "tpr": r(tpr)}, "pr": {"recall": r(rec), "precision": r(prec)}}


def error_analysis(X_test, y_test, scores, threshold: float) -> dict:
    """Aggregate error analysis (no raw rows): what do missed frauds and false alarms look like?"""
    y = np.asarray(y_test)
    pred = (np.asarray(scores) >= threshold).astype(int)
    amount = X_test["Amount"].to_numpy()
    groups = {"true_positive": (y == 1) & (pred == 1), "false_negative": (y == 1) & (pred == 0),
              "false_positive": (y == 0) & (pred == 1), "true_negative": (y == 0) & (pred == 0)}
    out = {}
    for name, mask in groups.items():
        n = int(mask.sum())
        out[name] = {"count": n,
                     "amount_median": float(np.median(amount[mask])) if n else None,
                     "amount_mean": float(amount[mask].mean()) if n else None,
                     "score_median": float(np.median(np.asarray(scores)[mask])) if n else None}
    fn = groups["false_negative"]
    out["missed_fraud_score_percentile_vs_legit"] = (
        float(np.mean([(np.asarray(scores)[y == 0] < s).mean() for s in np.asarray(scores)[fn]])) if fn.any() else None)
    return out


# ----------------------------------------------------------------------------- plots
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

_COLORS = ["#94a3b8", "#38bdf8", "#34d399", "#fbbf24", "#f43f5e"]


def plot_curves(results: dict, path):
    """ROC and precision-recall curves for all models (held-out test set)."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for (name, r), col in zip(results.items(), _COLORS):
        if not r.get("curves"):
            continue
        c = r["curves"]
        axes[0].plot(c["roc"]["fpr"], c["roc"]["tpr"], color=col, label=f"{r['label']} (AUC {r['test']['roc_auc']:.3f})")
        axes[1].plot(c["pr"]["recall"], c["pr"]["precision"], color=col, label=f"{r['label']} (AP {r['test']['pr_auc_average_precision']:.3f})")
    axes[0].plot([0, 1], [0, 1], "k:", lw=1); axes[0].set(title="ROC (test)", xlabel="False positive rate", ylabel="True positive rate")
    prev = next(iter(results.values()))["test"]["prevalence"]
    axes[1].axhline(prev, color="k", ls=":", lw=1, label=f"Prevalence {prev:.4f}")
    axes[1].set(title="Precision-recall (test)", xlabel="Recall", ylabel="Precision")
    for a in axes: a.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(path, dpi=130); plt.close(fig)


def plot_confusions(results: dict, path):
    names = list(results)
    fig, axes = plt.subplots(1, len(names), figsize=(3.2 * len(names), 3.4))
    for ax, n in zip(np.atleast_1d(axes), names):
        cm = results[n]["test"]["confusion_matrix"]
        m = np.array([[cm["tn"], cm["fp"]], [cm["fn"], cm["tp"]]])
        ax.imshow(np.log1p(m), cmap="Blues")
        for i in range(2):
            for j in range(2):
                ax.text(j, i, f"{m[i, j]:,}", ha="center", va="center", color="black", fontsize=11)
        ax.set(title=results[n]["label"], xticks=[0, 1], yticks=[0, 1], xticklabels=["Pred legit", "Pred fraud"],
               yticklabels=["True legit", "True fraud"])
        ax.title.set_fontsize(9)
    fig.tight_layout(); fig.savefig(path, dpi=130); plt.close(fig)


def plot_importance(results: dict, path):
    items = [(r["label"], r["feature_importance"]) for r in results.values() if r.get("feature_importance")]
    fig, axes = plt.subplots(1, len(items), figsize=(4.6 * len(items), 4.8))
    for ax, (label, fi) in zip(np.atleast_1d(axes), items):
        fi = fi[:12][::-1]
        ax.barh([f["feature"] for f in fi], [f["importance"] for f in fi], color="#38bdf8")
        ax.set_title(label, fontsize=10)
    fig.tight_layout(); fig.savefig(path, dpi=130); plt.close(fig)
