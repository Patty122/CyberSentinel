"""Dataset loading, validation, quality report and stratified splitting."""
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from . import config


class DatasetError(Exception):
    """Raised when the dataset is missing or does not match the expected schema."""


def validate_dataframe(df: pd.DataFrame) -> None:
    """Check columns, numeric types and a binary 0/1 target. Raises DatasetError."""
    missing = [c for c in config.ALL_COLUMNS if c not in df.columns]
    if missing:
        raise DatasetError(f"Missing required columns: {missing}")
    extra = [c for c in df.columns if c not in config.ALL_COLUMNS]
    if extra:
        raise DatasetError(f"Unexpected columns: {extra}")
    non_numeric = [c for c in config.ALL_COLUMNS if not pd.api.types.is_numeric_dtype(df[c])]
    if non_numeric:
        raise DatasetError(f"Non-numeric columns: {non_numeric}")
    if df.empty:
        raise DatasetError("Dataset is empty")
    if df[config.TARGET].isna().any():
        raise DatasetError("Target column contains missing values")
    labels = set(df[config.TARGET].unique().tolist())
    if not labels <= {0, 1}:
        raise DatasetError(f"Target must be binary 0/1, found {sorted(labels)}")
    if len(labels) < 2:
        raise DatasetError("Target contains only one class; cannot train a classifier")


def load_dataset(path: Path | str | None = None) -> pd.DataFrame:
    """Load creditcard.csv and validate it. Never fabricates or substitutes data."""
    path = Path(path) if path else config.DATA_PATH
    if not path.exists():
        raise DatasetError(
            f"Dataset not found at {path}. Download creditcard.csv from "
            "https://www.kaggle.com/datasets/mlg-ulb/creditcardfraud and place it in data/raw/."
        )
    try:
        df = pd.read_csv(path)
    except Exception as exc:  # malformed CSV
        raise DatasetError(f"Could not parse CSV: {exc}") from exc
    validate_dataframe(df)
    return df


def quality_report(df: pd.DataFrame) -> dict:
    """Actual dimensions, missing values, duplicates and class distribution."""
    counts = df[config.TARGET].value_counts().to_dict()
    n = len(df)
    fraud = int(counts.get(1, 0))
    return {
        "rows": n,
        "columns": df.shape[1],
        "missing_total": int(df.isna().sum().sum()),
        "missing_by_column": {c: int(v) for c, v in df.isna().sum().items() if v > 0},
        "duplicate_rows": int(df.duplicated().sum()),
        "legitimate": int(counts.get(0, 0)),
        "fraud": fraud,
        "fraud_percent": round(100 * fraud / n, 4),
    }


def drop_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Exact duplicate rows are removed so identical rows cannot sit in both train and test."""
    return df.drop_duplicates().reset_index(drop=True)


def split_data(df: pd.DataFrame, seed: int = config.SEED,
               val_size: float = config.VAL_SIZE, test_size: float = config.TEST_SIZE):
    """Stratified train/validation/test split. Returns dict of (X, y) tuples."""
    X, y = df[config.FEATURES], df[config.TARGET].astype(int)
    X_tmp, X_test, y_tmp, y_test = train_test_split(
        X, y, test_size=test_size, stratify=y, random_state=seed)
    rel_val = val_size / (1 - test_size)
    X_train, X_val, y_train, y_val = train_test_split(
        X_tmp, y_tmp, test_size=rel_val, stratify=y_tmp, random_state=seed)
    return {"train": (X_train, y_train), "val": (X_val, y_val), "test": (X_test, y_test)}


def split_info(splits: dict) -> dict:
    return {
        name: {"rows": int(len(y)), "fraud": int(y.sum()),
               "fraud_percent": round(100 * float(y.mean()), 4)}
        for name, (_, y) in splits.items()
    }
