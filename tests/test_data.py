import pytest

from ml.data_loader import DatasetError, build_report, load_dataset, validate_dataframe
from ml.eda import compute_summary, run_eda


def test_valid_synthetic_passes(synthetic_df):
    validate_dataframe(synthetic_df)


def test_missing_column_rejected(synthetic_df):
    with pytest.raises(DatasetError, match="Missing required"):
        validate_dataframe(synthetic_df.drop(columns=["V5"]))


def test_unexpected_column_rejected(synthetic_df):
    synthetic_df["extra"] = 1
    with pytest.raises(DatasetError, match="Unexpected"):
        validate_dataframe(synthetic_df)


def test_bad_labels_rejected(synthetic_df):
    synthetic_df.loc[0, "Class"] = 2
    with pytest.raises(DatasetError, match="0/1"):
        validate_dataframe(synthetic_df)


def test_single_class_rejected(synthetic_df):
    synthetic_df["Class"] = 0
    with pytest.raises(DatasetError, match="only one class"):
        validate_dataframe(synthetic_df)


def test_missing_target_rejected(synthetic_df):
    synthetic_df.loc[3, "Class"] = None
    with pytest.raises(DatasetError, match="missing"):
        validate_dataframe(synthetic_df)


def test_missing_file_has_helpful_message(tmp_path):
    with pytest.raises(DatasetError, match="Kaggle|kaggle"):
        load_dataset(tmp_path / "nope.csv")


def test_non_numeric_rejected(synthetic_df):
    synthetic_df["Amount"] = "abc"
    with pytest.raises(DatasetError, match="Non-numeric"):
        validate_dataframe(synthetic_df)


def test_load_roundtrip_and_report(tmp_path, synthetic_df):
    p = tmp_path / "creditcard.csv"
    synthetic_df.to_csv(p, index=False)
    df = load_dataset(p)
    r = build_report(df)
    assert r.n_rows == 600 and r.n_fraud == 30 and r.n_legitimate == 570
    assert r.fraud_percentage == 5.0


def test_eda_outputs_from_actual_data(tmp_path, synthetic_df):
    p = tmp_path / "creditcard.csv"
    synthetic_df.to_csv(p, index=False)
    s = run_eda(p, report_dir=tmp_path / "reports")
    assert s["dataset"]["n_rows"] == 600
    assert (tmp_path / "reports" / "eda_findings.md").exists()
    assert len(s["figures"]) == 4
    assert sum(s["amount_histogram"]["all"]) > 0


def test_summary_time_trend_counts(synthetic_df):
    s = compute_summary(synthetic_df)
    assert sum(t["transactions"] for t in s["time_trend"]) == 600
