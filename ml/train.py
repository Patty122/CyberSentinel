"""Train, tune, validate and evaluate all models, then save artifacts.

Run from the project root (training is a separate command from serving):
    python -m ml.train            # full run
    python -m ml.train --quick    # small search grids, for a fast smoke test

Order of operations (no test-set leakage):
 1. Remove exact duplicate rows, then a stratified 60/20/20 train/validation/test split.
 2. Hyper-parameter search: stratified 3-fold CV on TRAIN only (LR, RF, XGBoost);
    Isolation Forest is tuned on validation average precision (labels used only to score, never to fit).
 3. Fit final models on TRAIN only.
 4. Choose each decision threshold and the best model on VALIDATION only.
 5. Evaluate ONCE on TEST with the locked thresholds.
"""
import argparse
import json
import logging
import platform
import time
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, precision_recall_curve
from sklearn.model_selection import ParameterGrid, RandomizedSearchCV, StratifiedKFold, train_test_split

from . import config
from .data_loader import drop_duplicates, load_dataset, split_data, split_info
from .evaluate import (choose_threshold, compute_metrics, curves, error_analysis, plot_confusions,
                       plot_curves, plot_importance)
from .predict import score_pipeline
from .preprocess import FeatureEngineer, build_pipeline, random_undersample

try:
    from xgboost import XGBClassifier
except Exception:  # optional dependency
    XGBClassifier = None

log = logging.getLogger("train")

LABELS = {"dummy": "Dummy baseline", "logistic_regression": "Logistic Regression",
          "random_forest": "Random Forest", "xgboost": "XGBoost", "isolation_forest": "Isolation Forest"}


def search_spaces(quick: bool, pos_weight: float) -> dict:
    """Hyper-parameter search spaces (documented in the README and saved in metadata)."""
    if quick:
        return {
            "logistic_regression": {"clf__C": [0.1, 1.0], "clf__class_weight": [None, "balanced"]},
            "random_forest": {"clf__n_estimators": [30], "clf__max_depth": [6, 10], "clf__min_samples_leaf": [1, 3]},
            "xgboost": {"clf__n_estimators": [40], "clf__max_depth": [3, 4], "clf__learning_rate": [0.1]},
            "isolation_forest": {"n_estimators": [50], "max_samples": [128, 256]},
        }
    return {
        "logistic_regression": {"clf__C": [0.01, 0.1, 1.0, 10.0, 100.0], "clf__class_weight": [None, "balanced"]},
        "random_forest": {"clf__n_estimators": [100], "clf__max_depth": [10, 16],
                          "clf__min_samples_leaf": [1, 3, 5], "clf__max_features": ["sqrt"],
                          "clf__class_weight": [None, "balanced_subsample"]},
        "xgboost": {"clf__n_estimators": [100, 200, 300], "clf__max_depth": [3, 4, 6],
                    "clf__learning_rate": [0.05, 0.1, 0.2], "clf__subsample": [0.8, 1.0],
                    "clf__scale_pos_weight": [1.0, float(np.sqrt(pos_weight)), float(pos_weight)]},
        "isolation_forest": {"n_estimators": [100, 200], "max_samples": [256, 1024]},
    }


def base_pipelines(seed: int, use_xgb: bool, if_params: dict | None = None) -> dict:
    p = {
        "dummy": build_pipeline(DummyClassifier(strategy="prior"), scale=False),
        "logistic_regression": build_pipeline(LogisticRegression(max_iter=3000, random_state=seed), scale=True),
        "random_forest": build_pipeline(RandomForestClassifier(n_jobs=-1, random_state=seed), scale=False),
    }
    if use_xgb and XGBClassifier is not None:
        p["xgboost"] = build_pipeline(XGBClassifier(tree_method="hist", eval_metric="aucpr", n_jobs=-1,
                                                    random_state=seed, verbosity=0), scale=False)
    p["isolation_forest"] = build_pipeline(IsolationForest(n_jobs=-1, random_state=seed, **(if_params or {})), scale=True)
    return p


KIND = {"isolation_forest": "anomaly"}


def kind_of(name): return KIND.get(name, "supervised")


def tune_supervised(name, pipe, space, X, y, n_iter, seed, tune_rows):
    """Randomised search with stratified 3-fold CV on TRAIN only, scoring = average precision."""
    if tune_rows and len(y) > tune_rows:  # speed: search on a stratified subsample, refit on full train later
        X, _, y, _ = train_test_split(X, y, train_size=tune_rows, stratify=y, random_state=seed)
    n_comb = len(ParameterGrid(space))
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=seed)
    rs = RandomizedSearchCV(pipe, space, n_iter=min(n_iter, n_comb), scoring="average_precision", cv=cv,
                            random_state=seed, n_jobs=1, refit=False)
    t = time.time(); rs.fit(X, y)
    log.info("%s: CV search %.0fs, best AP=%.4f %s", name, time.time() - t, rs.best_score_, rs.best_params_)
    best = {k.replace("clf__", ""): v for k, v in rs.best_params_.items()}
    return best, float(rs.best_score_), int(len(y)), min(n_iter, n_comb)


def tune_isolation(space, X_tr, X_va, y_va, seed):
    best, best_ap, rows = None, -1, []
    for params in ParameterGrid(space):
        p = base_pipelines(seed, False, params)["isolation_forest"].fit(X_tr)  # unsupervised fit (no labels)
        ap = average_precision_score(y_va, score_pipeline(p, "anomaly", X_va))
        rows.append({"params": params, "validation_average_precision": float(ap)})
        if ap > best_ap:
            best, best_ap = params, float(ap)
    return best, best_ap, rows


def threshold_table(y_val, s_val, targets=(0.7, 0.8, 0.85, 0.9, 0.95)):
    """Validation trade-off: highest threshold that still reaches each recall target."""
    prec, rec, thr = precision_recall_curve(y_val, s_val)
    y = np.asarray(y_val); n_pos = int(y.sum()); out = []
    for t in targets:
        ok = np.flatnonzero(rec[:-1] >= t)
        if not len(ok):
            continue
        i = ok[-1]
        flagged = int((s_val >= thr[i]).sum()); tp = int(round(prec[i] * flagged))
        out.append({"target_recall": t, "threshold": float(thr[i]), "precision": float(prec[i]), "recall": float(rec[i]),
                    "flagged": flagged, "false_positives": flagged - tp, "missed_fraud": n_pos - tp})
    return out


def imbalance_experiment(splits, seed) -> dict:
    """Logistic Regression: no handling vs class weighting vs TRAIN-ONLY random under-sampling (validation results)."""
    X_tr, y_tr = splits["train"]; X_va, y_va = splits["val"]
    Xu, yu = random_undersample(X_tr, y_tr, ratio=10, seed=seed)
    variants = {"no_imbalance_handling": (X_tr, y_tr, None), "class_weight_balanced": (X_tr, y_tr, "balanced"),
                "undersample_10_to_1_train_only": (Xu, yu, None)}
    out = {}
    for name, (X, y, cw) in variants.items():
        p = build_pipeline(LogisticRegression(max_iter=3000, class_weight=cw, random_state=seed), True).fit(X, y)
        s = score_pipeline(p, "supervised", X_va)
        m = compute_metrics(y_va, s, choose_threshold(y_va, s))
        out[name] = {"train_rows": int(len(y)), **{k: m[k] for k in ("precision", "recall", "f1", "f2", "pr_auc_average_precision", "roc_auc")},
                     "false_positives": m["confusion_matrix"]["fp"], "evaluated_on": "validation"}
    return out


def feature_importance(pipe):
    names = list(pipe.named_steps["fe"].transform(pd.DataFrame(columns=config.FEATURES, data=[[0.0] * 30])).columns)
    m = pipe.named_steps["clf"]
    if hasattr(m, "feature_importances_"): v, kind = m.feature_importances_, "impurity/gain importance"
    elif hasattr(m, "coef_"): v, kind = np.abs(m.coef_[0]), "|coefficient| on standardised features"
    else: return None
    order = np.argsort(v)[::-1][:15]
    return [{"feature": names[i], "importance": float(v[i]), "basis": kind} for i in order]


def fmt(x): return f"{x:.4f}"


def write_reports(reports: Path, meta: dict, results: dict, imb: dict):
    sel = meta["selected_model"]
    L = ["# Model comparison (held-out test set, thresholds locked from validation)\n",
         f"Selection rule: {meta['selection_criterion']}\n\nSelected model: **{results[sel]['label']}**\n",
         f"Test prevalence of fraud: {results[sel]['test']['prevalence']:.4%} (precision of a random classifier equals prevalence).\n",
         "| Model | Best hyper-parameters | CV AP (train) | Val AP | Threshold | Test precision | Test recall | Test F1 | Test PR-AUC | Test ROC-AUC | FP | FN |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for n, r in results.items():
        t, v = r["test"], r["validation"]; cm = t["confusion_matrix"]
        cv = fmt(r["cv_average_precision"]) if r["cv_average_precision"] is not None else "-"
        L.append(f"| {r['label']} | `{json.dumps(r['best_params'])}` | {cv} | {fmt(v['pr_auc_average_precision'])} | {r['threshold']:.4g} | "
                 f"{fmt(t['precision'])} | {fmt(t['recall'])} | {fmt(t['f1'])} | {fmt(t['pr_auc_average_precision'])} | {fmt(t['roc_auc'])} | {cm['fp']} | {cm['fn']} |")
    (reports / "model_comparison.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    E = ["# Error analysis (selected model, test set, aggregate only)\n"]
    ea = results[sel]["error_analysis"]
    E.append("| Outcome | Count | Median amount | Mean amount | Median score |\n|---|---|---|---|---|")
    for k, v in ea.items():
        if isinstance(v, dict):
            f = lambda x: "-" if x is None else f"{x:.4g}"
            E.append(f"| {k} | {v['count']} | {f(v['amount_median'])} | {f(v['amount_mean'])} | {f(v['score_median'])} |")
    p = ea.get("missed_fraud_score_percentile_vs_legit")
    if p is not None:
        E.append(f"\nMissed frauds score higher than on average {p:.1%} of legitimate test transactions, i.e. they look mostly normal to the model.")
    (reports / "error_analysis.md").write_text("\n".join(E) + "\n", encoding="utf-8")

    I = ["# Class-imbalance experiment (Logistic Regression, validation set)\n",
         "| Strategy | Train rows | Precision | Recall | F1 | PR-AUC | False positives |\n|---|---|---|---|---|---|---|"]
    for k, v in imb.items():
        I.append(f"| {k} | {v['train_rows']:,} | {fmt(v['precision'])} | {fmt(v['recall'])} | {fmt(v['f1'])} | {fmt(v['pr_auc_average_precision'])} | {v['false_positives']} |")
    (reports / "imbalance_experiment.md").write_text("\n".join(I) + "\n", encoding="utf-8")


def train(df: pd.DataFrame, models_dir: Path, reports_dir: Path, quick=False, tune_rows=80000,
          use_xgb=True, n_iter=8, seed=config.SEED, data_name="creditcard.csv") -> dict:
    t0 = time.time()
    models_dir.mkdir(parents=True, exist_ok=True); (reports_dir / "figures").mkdir(parents=True, exist_ok=True)
    n_raw = len(df); df = drop_duplicates(df)
    splits = split_data(df, seed=seed); sinfo = split_info(splits)
    log.info("Rows %d -> %d after duplicate removal; split %s", n_raw, len(df), {k: v["rows"] for k, v in sinfo.items()})
    X_tr, y_tr = splits["train"]; X_va, y_va = splits["val"]; X_te, y_te = splits["test"]
    pos_weight = float((y_tr == 0).sum() / max((y_tr == 1).sum(), 1))
    spaces = search_spaces(quick, pos_weight)
    if use_xgb and XGBClassifier is None:
        log.warning("XGBoost is NOT installed, so it will be missing from the results. "
                    "Install it with `pip install xgboost` and re-run `python -m ml.train`.")
        print("WARNING: xgboost is not installed; XGBoost will be skipped. Run: pip install xgboost")
    pipes = base_pipelines(seed, use_xgb)
    tuning, best_params, cv_scores = {}, {}, {}

    for name in [n for n in pipes if n in ("logistic_regression", "random_forest", "xgboost")]:
        bp, cv, rows, tried = tune_supervised(name, pipes[name], spaces[name], X_tr, y_tr, 3 if quick else n_iter, seed, tune_rows)
        best_params[name], cv_scores[name] = bp, cv
        tuning[name] = {"method": "RandomizedSearchCV, stratified 3-fold CV on train, scoring=average_precision",
                        "search_space": {k.replace("clf__", ""): v for k, v in spaces[name].items()},
                        "configurations_tried": tried, "rows_used_for_search": rows, "best_params": bp, "best_cv_average_precision": cv}
        pipes[name].set_params(**{f"clf__{k}": v for k, v in bp.items()})
    bp, ap, rows = tune_isolation(spaces["isolation_forest"], X_tr, X_va, y_va, seed)
    best_params["isolation_forest"] = bp; cv_scores["isolation_forest"] = None
    tuning["isolation_forest"] = {"method": "grid search on validation average precision; model fitted without labels",
                                  "search_space": spaces["isolation_forest"], "results": rows, "best_params": bp,
                                  "best_validation_average_precision": ap}
    pipes["isolation_forest"] = base_pipelines(seed, False, bp)["isolation_forest"]
    imb = imbalance_experiment(splits, seed)

    fitted, s_val = {}, {}
    for name, pipe in pipes.items():
        t = time.time()
        (pipe.fit(X_tr) if name == "isolation_forest" else pipe.fit(X_tr, y_tr))
        log.info("fitted %s in %.0fs", name, time.time() - t)
        fitted[name] = pipe; s_val[name] = score_pipeline(pipe, kind_of(name), X_va)

    thr, val_m = {}, {}
    for name in fitted:
        thr[name] = 0.5 if name == "dummy" else choose_threshold(y_va, s_val[name])
        val_m[name] = compute_metrics(y_va, s_val[name], thr[name])
    cand = [n for n in fitted if n != "dummy"]
    selected = max(cand, key=lambda n: (round(val_m[n]["pr_auc_average_precision"], 4), val_m[n]["f1"]))
    log.info("selected on validation: %s", selected)

    results = {}  # ---- thresholds are locked; single pass over the test set ----
    for name, pipe in fitted.items():
        s = score_pipeline(pipe, kind_of(name), X_te)
        results[name] = {
            "label": LABELS[name], "kind": kind_of(name), "supports_probability": kind_of(name) == "supervised",
            "score_meaning": "predicted fraud probability (uncalibrated)" if kind_of(name) == "supervised"
            else "anomaly score = -score_samples (higher = more anomalous); not a probability",
            "threshold": thr[name], "best_params": best_params.get(name, {}), "cv_average_precision": cv_scores.get(name),
            "validation": val_m[name], "test": compute_metrics(y_te, s, thr[name]),
            "curves": None if name == "dummy" else curves(y_te, s),
            "error_analysis": error_analysis(X_te, y_te, s, thr[name]),
            "feature_importance": feature_importance(pipe),
            "threshold_tradeoff_validation": [] if name == "dummy" else threshold_table(y_va, s_val[name]),
        }
        joblib.dump(pipe, models_dir / f"{name}.joblib", compress=3)

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    criterion = "highest validation PR-AUC (average precision, rounded to 4 d.p.), ties broken by validation F1; test set not used"
    meta = {
        "model_version": config.MODEL_VERSION, "trained_at_utc": now, "selected_model": selected,
        "selection_criterion": criterion, "threshold_rule": f"maximise validation F-beta (beta={config.THRESHOLD_BETA:g})",
        "feature_names": config.FEATURES, "engineered_features": ["log_amount", "hour_elapsed_mod24"], "random_seed": seed,
        "dataset": {"file": data_name, "raw_rows": n_raw, "rows_after_duplicate_removal": len(df),
                    "duplicates_removed": n_raw - len(df), "split_method": "stratified 60/20/20 train/validation/test", "split": sinfo},
        "environment": {"python": platform.python_version(), "scikit_learn": sklearn.__version__},
        "models": {n: {"file": f"{n}.joblib", "label": LABELS[n], "kind": kind_of(n), "threshold": thr[n],
                       "best_params": best_params.get(n, {}), "validation_metrics": {k: v for k, v in val_m[n].items() if k != "classification_report"}}
                   for n in fitted},
        "tuning": tuning, "imbalance_experiment": imb, "training_seconds": round(time.time() - t0, 1), "quick_mode": quick,
    }
    (models_dir / "metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    metrics = {"generated_at_utc": now, "selected_model": selected, "selection_criterion": criterion,
               "dataset": meta["dataset"], "models": results}
    (models_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    write_reports(reports_dir, meta, results, imb)
    fig = reports_dir / "figures"
    plot_curves(results, fig / "roc_pr_curves.png"); plot_confusions(results, fig / "confusion_matrices.png")
    plot_importance(results, fig / "feature_importance.png")
    log.info("done in %.0fs", time.time() - t0)
    return metrics


def main():
    ap = argparse.ArgumentParser(description="Train and evaluate CyberSentinel models")
    ap.add_argument("--data", default=None); ap.add_argument("--quick", action="store_true")
    ap.add_argument("--tune-rows", type=int, default=80000, help="rows used for CV search (0 = all training rows)")
    ap.add_argument("--n-iter", type=int, default=8); ap.add_argument("--no-xgboost", action="store_true")
    a = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    df = load_dataset(a.data)
    m = train(df, config.MODELS_DIR, config.REPORTS_DIR, quick=a.quick, tune_rows=a.tune_rows,
              use_xgb=not a.no_xgboost, n_iter=a.n_iter)
    print(f"Selected model: {m['selected_model']}. Artifacts in {config.MODELS_DIR}")


if __name__ == "__main__":
    main()
