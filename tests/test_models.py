import json

import pytest

from ml.evaluate import compute_metrics, select_threshold
from ml.predict import ModelsUnavailable, Predictor
from ml.train import train_all


@pytest.fixture(scope="module")
def trained(tmp_path_factory, request):
    import numpy as np, pandas as pd
    from ml.data_loader import EXPECTED_COLUMNS
    rng = np.random.default_rng(7)
    n = 3000
    df = pd.DataFrame(rng.normal(size=(n, 28)), columns=[f"V{i}" for i in range(1, 29)])
    df.insert(0, "Time", np.sort(rng.uniform(0, 172800, n)))
    df["Amount"] = rng.exponential(80, n)
    df["Class"] = 0
    f = rng.choice(n, 90, replace=False)
    df.loc[f, "Class"] = 1
    df.loc[f, ["V1", "V2", "V3", "V4"]] += 4
    d = tmp_path_factory.mktemp("models")
    return d, train_all(df[EXPECTED_COLUMNS], d, rf_trees=20), df


def test_metrics_math():
    m = compute_metrics([0, 0, 1, 1], [0.1, 0.6, 0.4, 0.9], 0.5)
    assert m["confusion_matrix"] == {"tn": 1, "fp": 1, "fn": 1, "tp": 1}
    assert m["precision"] == 0.5 and m["recall"] == 0.5 and m["prevalence"] == 0.5


def test_threshold_from_validation_only():
    t, f1 = select_threshold([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9])
    assert 0.2 < t <= 0.8 and f1 == 1.0


def test_training_artifacts_and_metrics(trained):
    d, metrics, _ = trained
    assert set(metrics["models"]) == {"logistic_regression", "random_forest", "isolation_forest"}
    meta = json.loads((d / "metadata.json").read_text())
    assert meta["feature_names"][0] == "Time" and len(meta["feature_names"]) == 30
    assert metrics["models"]["random_forest"]["test"]["recall"] > 0.5
    assert metrics["best_model"] == meta["best_model"]
    assert "curves" in metrics["models"]["logistic_regression"]["test"]


def test_predictor_supervised_and_iforest(trained):
    d, _, df = trained
    p = Predictor(d); p.load()
    row = df.drop(columns="Class").iloc[0].to_dict()
    r = p.predict([row], "random_forest")[0]
    assert 0 <= r["fraud_probability"] <= 1
    a = p.predict([row], "isolation_forest")[0]
    assert a["fraud_probability"] is None and "anomaly_score" in a


def test_predictor_missing_artifacts(tmp_path):
    with pytest.raises(ModelsUnavailable):
        Predictor(tmp_path).load()
