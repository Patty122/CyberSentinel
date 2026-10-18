"""Inference from saved artifacts. Only loads files from our own models/ directory."""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import pandas as pd

from ml.data_loader import FEATURE_COLUMNS
from ml.preprocess import MODEL_NAMES, SUPERVISED, score_samples


class ModelsUnavailable(Exception):
    pass


class Predictor:
    def __init__(self, models_dir: Path):
        self.models_dir = Path(models_dir)
        self.artifacts: dict = {}
        self.metadata: dict = {}

    def artifacts_present(self) -> bool:
        d = self.models_dir
        return (d / "metadata.json").is_file() and all((d / f"{n}.joblib").is_file() for n in MODEL_NAMES)

    def load(self) -> None:
        if not self.artifacts_present():
            raise ModelsUnavailable("Model artifacts not found. Run training first.")
        self.metadata = json.loads((self.models_dir / "metadata.json").read_text())
        if self.metadata["feature_names"] != FEATURE_COLUMNS:
            raise ModelsUnavailable("Feature schema mismatch between artifacts and code.")
        self.artifacts = {n: joblib.load(self.models_dir / f"{n}.joblib") for n in MODEL_NAMES}

    @property
    def loaded(self) -> bool:
        return bool(self.artifacts)

    @property
    def default_model(self) -> str:
        return self.metadata["best_model"]

    def predict(self, rows: list[dict], model_name: str | None = None) -> list[dict]:
        if not self.loaded:
            raise ModelsUnavailable("Models not loaded.")
        name = model_name or self.default_model
        if name not in self.artifacts:
            raise KeyError(name)
        art = self.artifacts[name]
        X = pd.DataFrame(rows, columns=FEATURE_COLUMNS).astype(float)
        scores = score_samples(name, art["model"], X)
        thr = art["threshold"]
        out = []
        for sc in scores:
            pred = int(sc >= thr)
            r = {"model": name, "prediction": pred, "label": "fraud" if pred else "legitimate",
                 "threshold": thr}
            if name in SUPERVISED:
                r["fraud_probability"] = float(sc)  # uncalibrated model estimate
            else:  # Isolation Forest: anomaly score, NOT a probability
                r["fraud_probability"] = None
                r["anomaly_score"] = float(sc)
                r["is_anomaly"] = bool(pred)
            out.append(r)
        return out
