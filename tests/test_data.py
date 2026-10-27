import pandas as pd
import pytest

from ml import config
from ml.data_loader import DatasetError, drop_duplicates, load_dataset, quality_report, split_data, validate_dataframe


def test_valid_dataframe_passes(synthetic_df):
    validate_dataframe(synthetic_df)


def test_missing_column_rejected(synthetic_df):
    with pytest.raises(DatasetError, match="Missing"):
        validate_dataframe(synthetic_df.drop(columns=["V5"]))


def test_unexpected_column_rejected(synthetic_df):
    with pytest.raises(DatasetError, match="Unexpected"):
        validate_dataframe(synthetic_df.assign(extra=1))


def test_non_binary_target_rejected(synthetic_df):
    bad = synthetic_df.copy(); bad.loc[0, "Class"] = 2
    with pytest.raises(DatasetError, match="binary"):
        validate_dataframe(bad)


def test_non_numeric_rejected(synthetic_df):
    bad = synthetic_df.copy(); bad["Amount"] = bad["Amount"].astype(str)
    with pytest.raises(DatasetError, match="Non-numeric"):
        validate_dataframe(bad)


def test_missing_file_gives_clear_error(tmp_path):
    with pytest.raises(DatasetError, match="not found"):
        load_dataset(tmp_path / "nope.csv")


def test_malformed_csv_rejected(tmp_path):
    p = tmp_path / "bad.csv"; p.write_text("a,b\n1,2\n")
    with pytest.raises(DatasetError):
        load_dataset(p)


def test_quality_report_counts(synthetic_df):
    q = quality_report(synthetic_df)
    assert q["rows"] == len(synthetic_df) and q["fraud"] + q["legitimate"] == q["rows"]
    assert q["missing_total"] == 0


def test_duplicates_removed(synthetic_df):
    doubled = pd.concat([synthetic_df, synthetic_df.head(10)])
    assert len(drop_duplicates(doubled)) == len(synthetic_df)


def test_split_is_disjoint_stratified_and_reproducible(synthetic_df):
    a, b = split_data(synthetic_df), split_data(synthetic_df)
    idx = {k: set(v[0].index) for k, v in a.items()}
    assert not (idx["train"] & idx["test"]) and not (idx["train"] & idx["val"]) and not (idx["val"] & idx["test"])
    assert sum(len(v) for v in idx.values()) == len(synthetic_df)
    assert idx["test"] == set(b["test"][0].index)  # same seed, same split
    rates = [y.mean() for _, y in a.values()]
    assert max(rates) - min(rates) < 0.01  # stratified
