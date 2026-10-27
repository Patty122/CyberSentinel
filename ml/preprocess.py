"""Feature engineering and preprocessing pipelines (all fitted on training data only)."""
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


class FeatureEngineer(BaseEstimator, TransformerMixin):
    """Adds two stateless engineered features to the 30 raw inputs.

    log_amount: log1p(Amount) reduces the heavy right skew of transaction amounts.
    hour_elapsed_mod24: (Time / 3600) mod 24. Time is seconds since the first transaction in the
        dataset, so this is a relative hour-of-day proxy, not a real clock time.
    """

    def fit(self, X, y=None):
        self.input_columns_ = list(X.columns)
        return self

    def transform(self, X):
        X = pd.DataFrame(X).copy()
        X["log_amount"] = np.log1p(X["Amount"].clip(lower=0))
        X["hour_elapsed_mod24"] = (X["Time"] / 3600.0) % 24
        return X


def build_pipeline(estimator, scale: bool) -> Pipeline:
    """FeatureEngineer -> optional StandardScaler -> estimator.

    Scaling is used for Logistic Regression and Isolation Forest; tree ensembles do not need it.
    Because everything lives inside one Pipeline, scalers are fitted on training data only
    (and inside each CV fold during hyper-parameter search), which prevents leakage.
    """
    steps = [("fe", FeatureEngineer())]
    if scale:
        steps.append(("scale", StandardScaler()))
    steps.append(("clf", estimator))
    return Pipeline(steps)


def random_undersample(X, y, ratio: int = 10, seed: int = 42):
    """Training-only random under-sampling: keep all fraud, ratio x as many legitimate rows."""
    rng = np.random.default_rng(seed)
    pos = np.flatnonzero(y.to_numpy() == 1)
    neg = np.flatnonzero(y.to_numpy() == 0)
    keep_neg = rng.choice(neg, size=min(len(neg), ratio * len(pos)), replace=False)
    idx = np.sort(np.concatenate([pos, keep_neg]))
    return X.iloc[idx], y.iloc[idx]
