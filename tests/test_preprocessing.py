import numpy as np

from ml.data_loader import FEATURE_COLUMNS
from ml.preprocess import build_model, split_data


def test_split_is_disjoint_stratified_and_ordered(signal_df):
    s = split_data(signal_df)
    tr, va, te = set(s.X_train.index), set(s.X_val.index), set(s.X_test.index)
    assert not (tr & va) and not (tr & te) and not (va & te)
    assert len(tr) + len(va) + len(te) == len(signal_df)
    assert list(s.X_train.columns) == FEATURE_COLUMNS
    prev = signal_df["Class"].mean()
    for y in (s.y_train, s.y_val, s.y_test):
        assert abs(y.mean() - prev) < 0.01


def test_split_reproducible(signal_df):
    a, b = split_data(signal_df), split_data(signal_df)
    assert a.X_test.index.equals(b.X_test.index)


def test_scaler_fit_on_train_only(signal_df):
    s = split_data(signal_df)
    pipe = build_model("logistic_regression").fit(s.X_train, s.y_train)
    assert np.allclose(pipe["scale"].mean_, s.X_train.mean().to_numpy())
    assert not np.allclose(pipe["scale"].mean_, s.X_test.mean().to_numpy())
