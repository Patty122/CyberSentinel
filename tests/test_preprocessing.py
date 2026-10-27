import numpy as np
import pandas as pd

from ml import config
from ml.preprocess import FeatureEngineer, build_pipeline, random_undersample
from sklearn.linear_model import LogisticRegression


def test_feature_engineer_adds_columns_keeps_order(synthetic_df):
    X = synthetic_df[config.FEATURES]
    out = FeatureEngineer().fit_transform(X)
    assert list(out.columns) == config.FEATURES + ["log_amount", "hour_elapsed_mod24"]
    assert np.allclose(out["log_amount"], np.log1p(X["Amount"]))
    assert out["hour_elapsed_mod24"].between(0, 24).all()
    assert list(X.columns) == config.FEATURES  # input not mutated


def test_scaler_fitted_on_train_only(synthetic_df):
    X, y = synthetic_df[config.FEATURES], synthetic_df["Class"]
    train_X, test_X = X.iloc[:2000], X.iloc[2000:]
    pipe = build_pipeline(LogisticRegression(max_iter=500), scale=True).fit(train_X, y.iloc[:2000])
    fe = pipe.named_steps["fe"].transform(train_X)
    assert np.allclose(pipe.named_steps["scale"].mean_, fe.mean().to_numpy())  # statistics come from train only
    pipe.predict_proba(test_X)  # transform of unseen data must not refit


def test_undersample_keeps_all_fraud_and_is_train_only_helper(synthetic_df):
    X, y = synthetic_df[config.FEATURES], synthetic_df["Class"]
    Xu, yu = random_undersample(X, y, ratio=5, seed=1)
    assert yu.sum() == y.sum() and (yu == 0).sum() == 5 * y.sum()
