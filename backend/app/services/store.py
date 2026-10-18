"""Loads read-only artifacts (models, reports, dataset) lazily and tolerates their absence."""
import json
import logging
from pathlib import Path

import pandas as pd

from ml.data_loader import DatasetError, load_dataset
from ml.predict import ModelsUnavailable, Predictor

log = logging.getLogger("cybersentinel")


class Store:
    def __init__(self, cfg):
        self.cfg = cfg
        self.predictor = Predictor(cfg["MODELS_DIR"])
        self._df = None

    def models_ready(self) -> bool:
        if not self.predictor.loaded:
            try:
                self.predictor.load()
            except (ModelsUnavailable, Exception) as exc:  # noqa: BLE001
                log.warning("Models unavailable: %s", type(exc).__name__)
                return False
        return True

    def read_json(self, path: Path):
        try:
            return json.loads(path.read_text())
        except (OSError, ValueError):
            return None

    def metrics(self):
        return self.read_json(Path(self.cfg["MODELS_DIR"]) / "metrics.json")

    def metadata(self):
        return self.read_json(Path(self.cfg["MODELS_DIR"]) / "metadata.json")

    def eda(self):
        return self.read_json(Path(self.cfg["REPORTS_DIR"]) / "eda_summary.json")

    def dataframe(self):
        if self._df is None:
            try:
                self._df = load_dataset(self.cfg["DATA_PATH"])
            except DatasetError:
                return None
        return self._df

    def transactions(self, page, size, cls, min_amt, max_amt):
        df = self.dataframe()
        if df is None:
            return None
        if cls is not None:
            df = df[df["Class"] == cls]
        if min_amt is not None:
            df = df[df["Amount"] >= min_amt]
        if max_amt is not None:
            df = df[df["Amount"] <= max_amt]
        total = len(df)
        part = df.iloc[(page - 1) * size: page * size]
        rows = [{"id": int(i), **{k: (None if pd.isna(v) else float(v)) for k, v in r.items()}}
                for i, r in part.iterrows()]
        return {"rows": rows, "total": total, "page": page, "page_size": size}
