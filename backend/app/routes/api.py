import logging

from flask import Blueprint, current_app, request
from pydantic import ValidationError

from app.schemas.prediction import BatchRequest, PredictRequest, field_errors
from app.utils.responses import error, ok, unavailable

bp = Blueprint("api", __name__, url_prefix="/api")
log = logging.getLogger("cybersentinel")


def store():
    return current_app.extensions["store"]


@bp.get("/health")
def health():
    s = store()
    ready = s.models_ready()
    return ok({"service": "cybersentinel", "models_available": ready,
               "dataset_available": s.dataframe() is not None,
               "eda_available": s.eda() is not None})


@bp.get("/summary")
def summary():
    eda = store().eda()
    if eda is None:
        return unavailable("EDA report not found. Run: python -m ml.eda")
    return ok(eda)


@bp.get("/models")
def models():
    m, meta = store().metrics(), store().metadata()
    if m is None:
        return unavailable("Models not trained. Run: python -m ml.train")
    out = {"best_model": m["best_model"], "selection_criterion": m["selection_criterion"],
           "models": {n: {"type": r["type"], "score_type": r["score_type"], "threshold": r["threshold"],
                          "test": {k: v for k, v in r["test"].items() if k != "curves"}}
                      for n, r in m["models"].items()},
           "metadata": {k: meta.get(k) for k in ("model_version", "trained_at", "split", "random_seed")}
           if meta else None}
    return ok(out)


@bp.get("/metrics")
def metrics():
    m = store().metrics()
    if m is None:
        return unavailable("Models not trained. Run: python -m ml.train")
    return ok(m)


def _run(rows, model, many):
    s = store()
    if not s.models_ready():
        return error("models_unavailable", "Models not trained yet.", 503)
    try:
        res = s.predictor.predict(rows, model)
    except KeyError:
        return error("unknown_model", "Unknown model name.", 400)
    return ok({"predictions": res} if many else res[0],
              disclaimer="Model estimate only; not proof of fraud.")


@bp.post("/predict")
def predict():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return error("invalid_json", "Body must be a JSON object.", 400)
    try:
        req = PredictRequest.model_validate(body)
    except ValidationError as e:
        return error("validation_error", "Invalid transaction features.", 422, field_errors(e))
    return _run([req.features.model_dump()], req.model, many=False)


@bp.post("/predict/batch")
def predict_batch():
    body = request.get_json(silent=True)
    if not isinstance(body, dict) or not isinstance(body.get("transactions"), list):
        return error("invalid_json", "Body must be an object with a 'transactions' list.", 400)
    limit = current_app.config["MAX_BATCH_SIZE"]
    if not body["transactions"]:
        return error("empty_batch", "Batch is empty.", 422)
    if len(body["transactions"]) > limit:
        return error("batch_too_large", f"Batch exceeds the limit of {limit}.", 413)
    try:
        req = BatchRequest.model_validate(body)
    except ValidationError as e:
        return error("validation_error", "Invalid transaction in batch.", 422, field_errors(e))
    return _run([t.model_dump() for t in req.transactions], req.model, many=True)


def _int(name, default, lo, hi):
    raw = request.args.get(name)
    if raw is None:
        return default
    v = int(raw)
    return max(lo, min(hi, v))


@bp.get("/transactions")
def transactions():
    try:
        page = _int("page", 1, 1, 10**9)
        size = _int("page_size", 25, 1, current_app.config["MAX_PAGE_SIZE"])
        cls = request.args.get("class")
        cls = None if cls in (None, "") else int(cls)
        if cls not in (None, 0, 1):
            raise ValueError
        lo = request.args.get("min_amount"); hi = request.args.get("max_amount")
        lo = float(lo) if lo else None; hi = float(hi) if hi else None
        if any(v is not None and v != v for v in (lo, hi)):
            raise ValueError
    except ValueError:
        return error("invalid_query", "Invalid query parameter.", 400)
    res = store().transactions(page, size, cls, lo, hi)
    if res is None:
        return unavailable("Dataset not found. Place creditcard.csv in data/raw/.")
    return ok(res)
