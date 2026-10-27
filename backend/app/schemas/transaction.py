"""Strict input schema for one transaction: exactly the 30 expected features, finite numbers only."""
from pydantic import ConfigDict, Field, ValidationError, create_model

from ml.config import FEATURES

# Plausible bounds (the real dataset: Time <= 172,792 s, Amount <= 25,691, |V| < 120).
_BOUNDS = {"Time": (0, 1e8), "Amount": (0, 1e7)}


def _field(name):
    lo, hi = _BOUNDS.get(name, (-1000.0, 1000.0))
    return (float, Field(..., strict=True, allow_inf_nan=False, ge=lo, le=hi))


TransactionIn = create_model(
    "TransactionIn", __config__=ConfigDict(extra="forbid"), **{n: _field(n) for n in FEATURES})


def validate_transaction(payload) -> tuple[dict | None, dict | None]:
    """Return (clean_features, None) or (None, {field: message})."""
    if not isinstance(payload, dict):
        return None, {"_": "Transaction must be a JSON object of feature values."}
    try:
        return TransactionIn(**payload).model_dump(), None
    except ValidationError as exc:
        errors = {}
        for e in exc.errors():
            field = ".".join(str(p) for p in e["loc"]) or "_"
            errors[field] = {"missing": "Required.", "extra_forbidden": "Unexpected field."}.get(e["type"], e["msg"])
        return None, errors
