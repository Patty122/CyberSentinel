"""Bounded, read-only access to the local dataset for the Data Explorer. No uploads, no raw dumps."""
import logging
from pathlib import Path

import pandas as pd

from ml import config as mlcfg
from ml.data_loader import DatasetError, load_dataset

log = logging.getLogger("cybersentinel.api")


class TransactionStore:
    def __init__(self, path: Path):
        self.path, self._df = Path(path), None

    @property
    def available(self) -> bool:
        return self.path.exists()

    def df(self):
        if self._df is None:
            try:
                d = load_dataset(self.path)
            except DatasetError:
                return None
            d.insert(0, "id", range(len(d)))
            self._df = d
        return self._df

    def page(self, page, page_size, cls=None, min_amount=None, max_amount=None, row_id=None):
        d = self.df()
        if d is None:
            return None
        m = pd.Series(True, index=d.index)
        if cls is not None: m &= d[mlcfg.TARGET] == cls
        if min_amount is not None: m &= d["Amount"] >= min_amount
        if max_amount is not None: m &= d["Amount"] <= max_amount
        if row_id is not None: m &= d["id"] == row_id
        sub = d[m]
        total = int(len(sub))
        chunk = sub.iloc[(page - 1) * page_size: page * page_size].round(4)
        return {"total": total, "page": page, "page_size": page_size,
                "pages": max(1, -(-total // page_size)), "rows": chunk.to_dict(orient="records")}

    def sample(self, cls=None, seed=None):
        d = self.df()
        if d is None:
            return None
        sub = d if cls is None else d[d[mlcfg.TARGET] == cls]
        if sub.empty:
            return None
        row = sub.sample(1, random_state=seed).iloc[0]
        return {"id": int(row["id"]), "label": int(row[mlcfg.TARGET]),
                "features": {f: float(row[f]) for f in mlcfg.FEATURES}}
