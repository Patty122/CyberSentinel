"""Strict request schemas built from the single source of truth: ml.data_loader.FEATURE_COLUMNS."""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError, create_model

from ml.data_loader import FEATURE_COLUMNS

_Strict = ConfigDict(extra="forbid")

Features = create_model(
    "Features", __config__=_Strict,
    **{c: (float, Field(strict=True, allow_inf_nan=False)) for c in FEATURE_COLUMNS})


class PredictRequest(BaseModel):
    model_config = _Strict
    features: Features
    model: Optional[str] = None


class BatchRequest(BaseModel):
    model_config = _Strict
    transactions: list[Features]
    model: Optional[str] = None


def field_errors(exc: ValidationError) -> dict:
    """Flatten pydantic errors into {field: message}. Never echoes submitted values."""
    out = {}
    for e in exc.errors(include_input=False, include_url=False):
        loc = [str(p) for p in e["loc"] if p not in ("features", "transactions")]
        out[".".join(loc) or "body"] = e["msg"]
    return out
