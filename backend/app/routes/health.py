from flask import Blueprint, current_app

from ..utils.responses import ok

bp = Blueprint("health", __name__)


@bp.get("/health")
def health():
    s, t = current_app.extensions["store"], current_app.extensions["transactions"]
    pred = s.predictor()
    return ok({
        "service": "cybersentinel-api",
        "models_loaded": pred is not None,
        "selected_model": pred.selected if pred else None,
        "artifacts": {"model_metadata": s.metadata is not None, "metrics": s.metrics is not None,
                      "eda_summary": s.summary is not None, "dataset_present": t.available},
    })
