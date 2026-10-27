"""Loading saved artifacts and scoring transactions (used by training, evaluation and the Flask API)."""
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from . import config


class ArtifactError(Exception):
    """Raised when required model artifacts are missing or inconsistent."""


def score_pipeline(pipe, kind: str, X: pd.DataFrame) -> np.ndarray:
    """Return a 'higher = more suspicious' score.

    supervised: predicted probability of Class 1 (not guaranteed to be calibrated).
    anomaly (Isolation Forest): negated score_samples, so larger = more anomalous. NOT a probability.
    """
    if kind == "supervised":
        return pipe.predict_proba(X)[:, 1]
    if kind == "anomaly":
        return -pipe.score_samples(X)
    raise ValueError(f"Unknown model kind: {kind}")


class Predictor:
    """Loads metadata + fitted pipelines once and serves predictions."""

    def __init__(self, models_dir: Path | str | None = None):
        self.models_dir = Path(models_dir) if models_dir else config.MODELS_DIR
        meta_path = self.models_dir / "metadata.json"
        if not meta_path.exists():
            raise ArtifactError("Model metadata not found. Run the training command first.")
        self.metadata = json.loads(meta_path.read_text(encoding="utf-8"))
        self.features = self.metadata["feature_names"]
        self.selected = self.metadata["selected_model"]
        self._pipes = {}
        for name, info in self.metadata["models"].items():
            f = self.models_dir / info["file"]
            if not f.exists():
                raise ArtifactError(f"Model file missing for '{name}'")
            # Only files produced by our own training run and located in models/ are loaded.
            self._pipes[name] = joblib.load(f)

    @property
    def model_names(self):
        return list(self._pipes)

    def predict(self, rows: list[dict], model: str | None = None) -> list[dict]:
        name = model or self.selected
        if name not in self._pipes:
            raise KeyError(name)
        info = self.metadata["models"][name]
        X = pd.DataFrame(rows, columns=self.features).astype(float)  # enforces feature order
        scores = score_pipeline(self._pipes[name], info["kind"], X)
        out = []
        for s in scores:
            s = float(s)
            label = int(s >= info["threshold"])
            out.append({
                "model": name,
                "kind": info["kind"],
                "label": label,
                "label_name": "fraudulent" if label else "legitimate",
                "probability": s if info["kind"] == "supervised" else None,
                "anomaly_score": s if info["kind"] == "anomaly" else None,
                "threshold": info["threshold"],
            })
        return out
