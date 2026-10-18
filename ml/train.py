"""Train and evaluate all models. Run manually:  python -m ml.train
Selection of the 'best' model uses VALIDATION average precision; test data is touched only for
final reporting, after thresholds are locked."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import joblib
import sklearn

from ml.data_loader import FEATURE_COLUMNS, DatasetError, build_report, load_dataset
from ml.evaluate import compute_metrics, select_threshold
from ml.preprocess import MODEL_NAMES, SEED, SUPERVISED, build_model, score_samples, split_data

ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = ROOT / "models"
MODEL_VERSION = "1.0.0"
CRITERION = "Threshold: maximise F1 on validation set. Best model: highest validation average precision."


def train_all(df, models_dir: Path = MODELS_DIR, seed: int = SEED, rf_trees: int = 100,
              run_experiments: bool = True) -> dict:
    models_dir.mkdir(parents=True, exist_ok=True)
    s = split_data(df, seed=seed)
    results, experiments = {}, {}

    for name in MODEL_NAMES:
        pipe = build_model(name, seed, rf_trees)
        if name in SUPERVISED:
            pipe.fit(s.X_train, s.y_train)
        else:
            pipe.fit(s.X_train)  # unsupervised: no labels used
        val_scores = score_samples(name, pipe, s.X_val)
        thr, _ = select_threshold(s.y_val, val_scores)  # validation only; locked from here on
        test_scores = score_samples(name, pipe, s.X_test)
        results[name] = {
            "type": "supervised" if name in SUPERVISED else "unsupervised_anomaly_detection",
            "score_type": "probability" if name in SUPERVISED else "anomaly_score",
            "threshold": thr,
            "validation": compute_metrics(s.y_val, val_scores, thr),
            "test": compute_metrics(s.y_test, test_scores, thr, include_curves=True),
        }
        if name in SUPERVISED:
            experiments.setdefault("threshold_default_vs_tuned_validation", {})[name] = {
                "default_0.5": _brief(compute_metrics(s.y_val, val_scores, 0.5)),
                "tuned": _brief(results[name]["validation"]),
            }
        joblib.dump({"name": name, "model": pipe, "threshold": thr,
                     "score_type": results[name]["score_type"], "feature_names": FEATURE_COLUMNS},
                    models_dir / f"{name}.joblib")

    if run_experiments:  # class weighting vs none, evaluated on VALIDATION only
        for name in SUPERVISED:
            p = build_model(name, seed, rf_trees, class_weight=None).fit(s.X_train, s.y_train)
            sc = score_samples(name, p, s.X_val)
            t, _ = select_threshold(s.y_val, sc)
            experiments.setdefault("class_weighting_validation", {})[name] = {
                "no_weighting": _brief(compute_metrics(s.y_val, sc, t)),
                "balanced": _brief(results[name]["validation"]),
            }

    best = max(results, key=lambda n: results[n]["validation"]["average_precision"] or 0)
    ds = build_report(df).to_dict()
    metadata = {
        "model_version": MODEL_VERSION, "trained_at": datetime.now(timezone.utc).isoformat(),
        "random_seed": seed, "feature_names": FEATURE_COLUMNS, "models": MODEL_NAMES,
        "best_model": best, "thresholds": {n: r["threshold"] for n, r in results.items()},
        "selection_criterion": CRITERION, "dataset": ds, "split": s.info(),
        "split_scheme": "stratified 60/20/20 train/validation/test",
        "sklearn_version": sklearn.__version__, "python_version": sys.version.split()[0],
    }
    metrics = {"best_model": best, "selection_criterion": CRITERION, "models": results,
               "experiments": experiments, "split": s.info()}
    (models_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
    (models_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))
    return metrics


def _brief(m: dict) -> dict:
    return {k: m[k] for k in ("threshold", "precision", "recall", "f1", "average_precision")}


if __name__ == "__main__":
    try:
        out = train_all(load_dataset())
    except DatasetError as e:
        print(f"ERROR: {e}")
        raise SystemExit(1)
    print(f"Training complete. Best (validation AP): {out['best_model']}")
    for n, r in out["models"].items():
        t = r["test"]
        print(f"{n:20s} test P={t['precision']:.3f} R={t['recall']:.3f} F1={t['f1']:.3f} "
              f"AP={t['average_precision']:.3f}")
