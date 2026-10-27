from flask import Blueprint, current_app

from ..utils.errors import ApiError
from ..utils.responses import ok

bp = Blueprint("analysis", __name__)
HINT_EDA = "Run `python -m ml.eda` from the project root."
HINT_TRAIN = "Run `python -m ml.train` from the project root."


def _store():
    return current_app.extensions["store"]


@bp.get("/summary")
def summary():
    s = _store().summary
    if s is None:
        raise ApiError("summary_unavailable", "EDA summary not generated yet. " + HINT_EDA, 404)
    return ok(s)


@bp.get("/models")
def models():
    m, meta = _store().metrics, _store().metadata
    if m is None or meta is None:
        raise ApiError("models_unavailable", "No trained models found. " + HINT_TRAIN, 404)
    out = []
    for name, r in m["models"].items():
        out.append({"name": name, "label": r["label"], "kind": r["kind"], "supports_probability": r["supports_probability"],
                    "score_meaning": r["score_meaning"], "threshold": r["threshold"], "best_params": r["best_params"],
                    "cv_average_precision": r["cv_average_precision"],
                    "validation": {k: v for k, v in r["validation"].items() if k != "classification_report"},
                    "test": {k: v for k, v in r["test"].items() if k != "classification_report"},
                    "selected": name == m["selected_model"]})
    return ok({"selected_model": m["selected_model"], "selection_criterion": m["selection_criterion"],
               "trained_at_utc": meta["trained_at_utc"], "model_version": meta["model_version"], "models": out})


@bp.get("/metrics")
def metrics():
    m, meta = _store().metrics, _store().metadata
    if m is None:
        raise ApiError("metrics_unavailable", "No evaluation metrics found. " + HINT_TRAIN, 404)
    return ok({**m, "imbalance_experiment": (meta or {}).get("imbalance_experiment"),
               "tuning": (meta or {}).get("tuning"), "threshold_rule": (meta or {}).get("threshold_rule")})
