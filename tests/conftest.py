import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))
from ml.data_loader import EXPECTED_COLUMNS  # noqa: E402


@pytest.fixture
def synthetic_df() -> pd.DataFrame:
    """SYNTHETIC data for tests only. Not real transactions."""
    rng = np.random.default_rng(42)
    n = 600
    df = pd.DataFrame(rng.normal(size=(n, 28)), columns=[f"V{i}" for i in range(1, 29)])
    df.insert(0, "Time", np.sort(rng.uniform(0, 172800, n)))
    df["Amount"] = rng.exponential(80, n)
    df["Class"] = 0
    df.loc[rng.choice(n, 30, replace=False), "Class"] = 1
    return df[EXPECTED_COLUMNS]


@pytest.fixture
def signal_df() -> pd.DataFrame:
    """SYNTHETIC data with a learnable fraud signal. Tests only; not real transactions."""
    rng = np.random.default_rng(7)
    n = 3000
    df = pd.DataFrame(rng.normal(size=(n, 28)), columns=[f"V{i}" for i in range(1, 29)])
    df.insert(0, "Time", np.sort(rng.uniform(0, 172800, n)))
    df["Amount"] = rng.exponential(80, n)
    df["Class"] = 0
    fraud = rng.choice(n, 90, replace=False)
    df.loc[fraud, "Class"] = 1
    df.loc[fraud, ["V1", "V2", "V3", "V4"]] += 4
    return df[EXPECTED_COLUMNS]


@pytest.fixture(scope="session")
def api_env(tmp_path_factory):
    """Trains on SYNTHETIC data into a temp dir and returns config overrides for the Flask app."""
    from ml.train import train_all
    rng = np.random.default_rng(7)
    n = 3000
    df = pd.DataFrame(rng.normal(size=(n, 28)), columns=[f"V{i}" for i in range(1, 29)])
    df.insert(0, "Time", np.sort(rng.uniform(0, 172800, n)))
    df["Amount"] = rng.exponential(80, n)
    df["Class"] = 0
    f = rng.choice(n, 90, replace=False)
    df.loc[f, "Class"] = 1
    df.loc[f, ["V1", "V2", "V3", "V4"]] += 4
    df = df[EXPECTED_COLUMNS]
    d = tmp_path_factory.mktemp("api")
    (d / "models").mkdir(); (d / "reports").mkdir()
    df.to_csv(d / "creditcard.csv", index=False)
    train_all(df, d / "models", rf_trees=20, run_experiments=False)
    return {"MODELS_DIR": d / "models", "REPORTS_DIR": d / "reports", "DATA_PATH": d / "creditcard.csv"}, df
