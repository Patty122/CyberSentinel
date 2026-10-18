"""Splitting and model pipelines. Scalers live inside sklearn Pipelines, so they are fit on
training data only (no leakage into validation/test)."""
from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml.data_loader import FEATURE_COLUMNS, TARGET_COLUMN

SEED = 42
MODEL_NAMES = ["logistic_regression", "random_forest", "isolation_forest"]
SUPERVISED = {"logistic_regression", "random_forest"}


@dataclass
class Splits:
    X_train: pd.DataFrame
    X_val: pd.DataFrame
    X_test: pd.DataFrame
    y_train: pd.Series
    y_val: pd.Series
    y_test: pd.Series

    def info(self) -> dict:
        return {k: {"rows": int(len(y)), "fraud": int(y.sum())}
                for k, y in [("train", self.y_train), ("validation", self.y_val), ("test", self.y_test)]}


def split_data(df: pd.DataFrame, seed: int = SEED, val_size: float = 0.2, test_size: float = 0.2) -> Splits:
    """Stratified train/validation/test split (default 60/20/20)."""
    X = df[FEATURE_COLUMNS].astype(float)
    y = df[TARGET_COLUMN].astype(int)
    X_tmp, X_test, y_tmp, y_test = train_test_split(X, y, test_size=test_size, stratify=y, random_state=seed)
    X_train, X_val, y_train, y_val = train_test_split(
        X_tmp, y_tmp, test_size=val_size / (1 - test_size), stratify=y_tmp, random_state=seed)
    return Splits(X_train, X_val, X_test, y_train, y_val, y_test)


def build_model(name: str, seed: int = SEED, rf_trees: int = 100, class_weight: str | None = "balanced"):
    if name == "logistic_regression":
        return Pipeline([("scale", StandardScaler()),
                         ("clf", LogisticRegression(max_iter=1000, class_weight=class_weight, random_state=seed))])
    if name == "random_forest":
        cw = "balanced_subsample" if class_weight else None
        return Pipeline([("clf", RandomForestClassifier(n_estimators=rf_trees, min_samples_leaf=2, n_jobs=-1,
                                                        class_weight=cw, random_state=seed))])
    if name == "isolation_forest":
        # Unsupervised: fit WITHOUT labels. Score threshold is later chosen on validation data.
        return Pipeline([("scale", StandardScaler()),
                         ("clf", IsolationForest(n_estimators=200, random_state=seed, n_jobs=-1))])
    raise ValueError(f"Unknown model: {name}")


def score_samples(name: str, pipe, X: pd.DataFrame):
    """Higher score = more likely fraud/anomalous. Probability for supervised, -score_samples for IF."""
    if name in SUPERVISED:
        return pipe.predict_proba(X)[:, 1]
    return -pipe.score_samples(X)
