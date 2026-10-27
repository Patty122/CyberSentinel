from flask import Blueprint, current_app, request

from ..utils.errors import ApiError
from ..utils.responses import ok

bp = Blueprint("transactions", __name__)


def _num(name, cast, lo=None, hi=None):
    raw = request.args.get(name)
    if raw in (None, ""):
        return None
    try:
        v = cast(raw)
    except ValueError:
        raise ApiError("invalid_query", f"'{name}' must be a valid {cast.__name__}.", 400)
    if v != v or (lo is not None and v < lo) or (hi is not None and v > hi):
        raise ApiError("invalid_query", f"'{name}' is out of range.", 400)
    return v


def _store():
    t = current_app.extensions["transactions"]
    if not t.available:
        raise ApiError("dataset_unavailable", "Dataset not found. Place creditcard.csv in data/raw/ (see README).", 404)
    return t


@bp.get("/transactions")
def transactions():
    t = _store()
    page = _num("page", int, 1, 10**7) or 1
    size = _num("page_size", int, 1, current_app.config["MAX_PAGE_SIZE"]) or 25
    cls = _num("class", int, 0, 1)
    res = t.page(page, size, cls, _num("min_amount", float, 0, 1e9), _num("max_amount", float, 0, 1e9), _num("id", int, 0, 10**9))
    if res is None:
        raise ApiError("dataset_invalid", "Dataset could not be loaded or failed validation.", 500)
    return ok(res)


@bp.get("/transactions/sample")
def sample():
    """A real row from the local dataset, clearly labelled, for trying the prediction form."""
    row = _store().sample(_num("class", int, 0, 1))
    if row is None:
        raise ApiError("dataset_invalid", "Dataset could not be loaded or failed validation.", 500)
    return ok({**row, "source": "Row from the local Kaggle creditcard.csv (the model may have seen it during training)."})
