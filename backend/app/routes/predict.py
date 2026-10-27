import logging

from flask import Blueprint, current_app, request

from ..schemas.transaction import validate_transaction
from ..utils.errors import ApiError
from ..utils.responses import ok

bp = Blueprint("predict", __name__)
log = logging.getLogger("cybersentinel.api")
DISCLAIMER = "Model estimate only; not proof of fraud. Review flagged transactions with a human analyst."


def _json_body():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        raise ApiError("invalid_json", "Request body must be a JSON object (Content-Type: application/json).", 400)
    return body


def _predictor(model):
    p = current_app.extensions["store"].predictor()
    if p is None:
        raise ApiError("models_unavailable", "Models are not available. Run `python -m ml.train` first.", 503)
    if model is not None and (not isinstance(model, str) or model not in p.model_names):
        raise ApiError("unknown_model", f"Unknown model. Available: {p.model_names}", 400)
    return p


@bp.post("/predict")
def predict():
    body = _json_body()
    if set(body) - {"features", "model"}:
        raise ApiError("invalid_request", "Only 'features' and 'model' are allowed at the top level.", 400)
    clean, errors = validate_transaction(body.get("features"))
    if errors:
        raise ApiError("validation_error", "Invalid transaction features.", 422, errors)
    p = _predictor(body.get("model"))
    result = p.predict([clean], body.get("model"))[0]
    log.info("prediction model=%s label=%s", result["model"], result["label"])  # no feature values logged
    return ok({**result, "disclaimer": DISCLAIMER})


@bp.post("/predict/batch")
def predict_batch():
    body = _json_body()
    items = body.get("transactions")
    limit = current_app.config["MAX_BATCH_SIZE"]
    if not isinstance(items, list) or not items:
        raise ApiError("invalid_request", "'transactions' must be a non-empty list.", 400)
    if len(items) > limit:
        raise ApiError("batch_too_large", f"At most {limit} transactions per request.", 413)
    p = _predictor(body.get("model"))
    valid, results = [], [None] * len(items)
    for i, it in enumerate(items):
        clean, errors = validate_transaction(it)
        if errors:
            results[i] = {"index": i, "valid": False, "errors": errors}
        else:
            valid.append((i, clean))
    if valid:
        preds = p.predict([c for _, c in valid], body.get("model"))
        for (i, _), pr in zip(valid, preds):
            results[i] = {"index": i, "valid": True, "prediction": pr}
    log.info("batch prediction size=%d valid=%d", len(items), len(valid))
    return ok({"results": results, "valid_count": len(valid), "invalid_count": len(items) - len(valid),
               "disclaimer": DISCLAIMER})
