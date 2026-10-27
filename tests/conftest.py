"""Shared fixtures. All unit tests use SYNTHETIC data (clearly not the Kaggle dataset)."""
import numpy as np
import pandas as pd
import pytest

from ml import config
from ml.train import train


def make_synthetic(n=3000, frac=0.08, seed=0) -> pd.DataFrame:
    """Synthetic stand-in with the same schema as creditcard.csv. For tests only."""
    rng = np.random.default_rng(seed)
    y = (rng.random(n) < frac).astype(int)
    df = pd.DataFrame(rng.normal(size=(n, 28)), columns=[f"V{i}" for i in range(1, 29)])
    df.loc[y == 1, ["V1", "V2", "V3"]] += 2.5
    df.insert(0, "Time", np.sort(rng.uniform(0, 172_000, n)))
    df["Amount"] = rng.lognormal(3, 1, n).round(2)
    df["Class"] = y
    return df[config.ALL_COLUMNS]


@pytest.fixture(scope="session")
def synthetic_df():
    return make_synthetic()


@pytest.fixture(scope="session")
def artifacts(tmp_path_factory, synthetic_df):
    """Train tiny models once on synthetic data; returns (models_dir, reports_dir, data_csv)."""
    root = tmp_path_factory.mktemp("cs")
    models, reports = root / "models", root / "reports"
    train(synthetic_df, models, reports, quick=True, tune_rows=0, use_xgb=False, n_iter=2)
    csv = root / "synthetic.csv"
    synthetic_df.to_csv(csv, index=False)
    return models, reports, csv


@pytest.fixture()
def client(artifacts):
    from app import create_app
    models, reports, csv = artifacts
    app = create_app({"MODELS_DIR": models, "REPORTS_DIR": reports, "DATA_PATH": csv, "TESTING": True,
                      "CORS_ORIGINS": ["http://localhost:5173"], "MAX_BATCH_SIZE": 5})
    return app.test_client()


@pytest.fixture()
def empty_client(tmp_path):
    """App with NO artifacts: must stay up and report unavailability."""
    from app import create_app
    app = create_app({"MODELS_DIR": tmp_path / "m", "REPORTS_DIR": tmp_path / "r", "DATA_PATH": tmp_path / "none.csv", "TESTING": True})
    return app.test_client()


@pytest.fixture()
def valid_features(synthetic_df):
    return {k: float(v) for k, v in synthetic_df[config.FEATURES].iloc[0].items()}
