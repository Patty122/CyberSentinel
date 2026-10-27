import json

import pytest

from ml import config
from ml.data_loader import split_data
from ml.predict import ArtifactError, Predictor


def test_artifacts_created(artifacts):
    models, reports, _ = artifacts
    for f in ["metadata.json", "metrics.json", "dummy.joblib", "logistic_regression.joblib",
              "random_forest.joblib", "isolation_forest.joblib"]:
        assert (models / f).exists()
    assert (reports / "model_comparison.md").exists()


def test_metadata_contents(artifacts):
    meta = json.loads((artifacts[0] / "metadata.json").read_text())
    assert meta["feature_names"] == config.FEATURES
    assert {"trained_at_utc", "model_version", "selected_model", "threshold_rule", "dataset"} <= set(meta)
    assert meta["selected_model"] != "dummy"
    assert set(meta["dataset"]["split"]) == {"train", "val", "test"}


def test_metrics_have_required_fields(artifacts):
    m = json.loads((artifacts[0] / "metrics.json").read_text())
    t = m["models"]["logistic_regression"]["test"]
    for k in ["precision", "recall", "f1", "roc_auc", "pr_auc_average_precision", "balanced_accuracy",
              "false_positive_rate", "false_negative_rate", "prevalence", "confusion_matrix", "classification_report"]:
        assert k in t
    cm = t["confusion_matrix"]
    assert cm["tn"] + cm["fp"] + cm["fn"] + cm["tp"] > 0


def test_selection_and_thresholds_use_validation_only(artifacts):
    m = json.loads((artifacts[0] / "metrics.json").read_text())
    cand = {n: r for n, r in m["models"].items() if n != "dummy"}
    best_val = max(r["validation"]["pr_auc_average_precision"] for r in cand.values())
    assert round(cand[m["selected_model"]]["validation"]["pr_auc_average_precision"], 4) == round(best_val, 4)
    assert "test set not used" in m["selection_criterion"]


def test_predictor_loads_and_scores(artifacts, synthetic_df):
    p = Predictor(artifacts[0])
    rows = synthetic_df[config.FEATURES].head(3).to_dict("records")
    for name in p.model_names:
        out = p.predict(rows, name)
        assert len(out) == 3 and all(o["label"] in (0, 1) for o in out)
    sup = p.predict(rows, "logistic_regression")[0]
    assert 0 <= sup["probability"] <= 1 and sup["anomaly_score"] is None
    iso = p.predict(rows, "isolation_forest")[0]
    assert iso["probability"] is None and iso["anomaly_score"] is not None  # IF never reports a probability


def test_predictor_missing_artifacts(tmp_path):
    with pytest.raises(ArtifactError):
        Predictor(tmp_path)


@pytest.mark.integration
def test_real_dataset_split_if_available():
    if not config.DATA_PATH.exists():
        pytest.skip("creditcard.csv not present")
    from ml.data_loader import load_dataset
    df = load_dataset()
    assert df.shape[1] == 31 and df["Class"].sum() == 492
    s = split_data(df)
    assert sum(len(v[1]) for v in s.values()) == len(df)
