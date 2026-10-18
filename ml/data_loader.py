"""Dataset loading and validation for the Kaggle creditcard.csv file.

Never fabricates data: if the file is missing or malformed a clear error is raised.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import pandas as pd

FEATURE_COLUMNS = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount"]
TARGET_COLUMN = "Class"
EXPECTED_COLUMNS = FEATURE_COLUMNS + [TARGET_COLUMN]
DEFAULT_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "creditcard.csv"


class DatasetError(Exception):
    """Raised when the dataset is missing, malformed, or fails validation."""


@dataclass
class DatasetReport:
    n_rows: int
    n_columns: int
    n_missing_values: int
    n_duplicate_rows: int
    n_legitimate: int
    n_fraud: int
    fraud_percentage: float

    def to_dict(self) -> dict:
        return asdict(self)


def validate_dataframe(df: pd.DataFrame) -> None:
    """Check schema and values. Raises DatasetError on any problem."""
    if df.empty:
        raise DatasetError("Dataset is empty.")
    missing = [c for c in EXPECTED_COLUMNS if c not in df.columns]
    if missing:
        raise DatasetError(f"Missing required columns: {missing}")
    extra = [c for c in df.columns if c not in EXPECTED_COLUMNS]
    if extra:
        raise DatasetError(f"Unexpected columns: {extra}")
    non_numeric = [c for c in EXPECTED_COLUMNS if not pd.api.types.is_numeric_dtype(df[c])]
    if non_numeric:
        raise DatasetError(f"Non-numeric columns: {non_numeric}")
    if not np.isfinite(df[EXPECTED_COLUMNS].to_numpy(dtype=float, na_value=np.nan)).all():
        # NaN or inf present in features/target; reported, but a missing target is fatal
        if df[TARGET_COLUMN].isna().any():
            raise DatasetError("Target column 'Class' contains missing values.")
    labels = set(df[TARGET_COLUMN].dropna().unique().tolist())
    if not labels <= {0, 1}:
        raise DatasetError(f"Class must contain only 0/1, found: {sorted(labels)}")
    if len(labels) < 2:
        raise DatasetError("Class column contains only one class; cannot train a classifier.")


def load_dataset(path: str | Path | None = None) -> pd.DataFrame:
    """Load and validate the dataset from disk."""
    path = Path(path) if path else DEFAULT_PATH
    if not path.is_file():
        raise DatasetError(
            f"Dataset not found at {path.name}. Download creditcard.csv from "
            "https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud and place it in data/raw/."
        )
    try:
        df = pd.read_csv(path)
    except Exception as exc:  # malformed CSV
        raise DatasetError(f"Could not parse CSV: {type(exc).__name__}") from exc
    validate_dataframe(df)
    return df


def build_report(df: pd.DataFrame) -> DatasetReport:
    """Compute actual dataset statistics (nothing assumed)."""
    n_fraud = int((df[TARGET_COLUMN] == 1).sum())
    n = len(df)
    return DatasetReport(
        n_rows=n,
        n_columns=df.shape[1],
        n_missing_values=int(df.isna().sum().sum()),
        n_duplicate_rows=int(df.duplicated().sum()),
        n_legitimate=n - n_fraud,
        n_fraud=n_fraud,
        fraud_percentage=round(100 * n_fraud / n, 4),
    )
