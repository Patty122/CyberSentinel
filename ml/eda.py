"""Reproducible exploratory data analysis. Outputs come only from the real data passed in."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from ml.data_loader import FEATURE_COLUMNS, TARGET_COLUMN, build_report, load_dataset

ROOT = Path(__file__).resolve().parents[1]
FIG_DIR = ROOT / "reports" / "figures"
REPORT_DIR = ROOT / "reports"


def compute_summary(df: pd.DataFrame, n_time_bins: int = 24) -> dict:
    """Return a JSON-serialisable summary computed from the data."""
    report = build_report(df).to_dict()
    amount = df["Amount"]
    fraud = df[df[TARGET_COLUMN] == 1]
    legit = df[df[TARGET_COLUMN] == 0]

    def _amount_stats(s: pd.Series) -> dict:
        if s.empty:
            return {}
        return {k: float(v) for k, v in s.describe().items()}

    hist_edges = np.quantile(amount, np.linspace(0, 0.99, 21))
    hist_edges = np.unique(hist_edges)
    if len(hist_edges) < 2:
        hist_edges = np.array([float(amount.min()), float(amount.max()) + 1.0])
    counts_all, _ = np.histogram(amount, bins=hist_edges)
    counts_fraud, _ = np.histogram(fraud["Amount"], bins=hist_edges)

    time_bins = pd.cut(df["Time"], bins=n_time_bins)
    by_time = df.groupby(time_bins, observed=True)[TARGET_COLUMN].agg(["count", "sum"])
    time_trend = [
        {"bin": f"{iv.left:.0f}-{iv.right:.0f}", "transactions": int(r["count"]), "fraud": int(r["sum"]),
         "fraud_rate": float(r["sum"] / r["count"]) if r["count"] else 0.0}
        for iv, r in by_time.iterrows()
    ]

    corr = df[FEATURE_COLUMNS + [TARGET_COLUMN]].corr()[TARGET_COLUMN].drop(TARGET_COLUMN)
    top_corr = corr.reindex(corr.abs().sort_values(ascending=False).index).head(10)

    return {
        "dataset": report,
        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
        "amount_stats": {"all": _amount_stats(amount), "fraud": _amount_stats(fraud["Amount"]),
                         "legitimate": _amount_stats(legit["Amount"])},
        "amount_histogram": {"edges": [float(e) for e in hist_edges],
                             "all": counts_all.tolist(), "fraud": counts_fraud.tolist()},
        "time_trend": time_trend,
        "top_correlations_with_class": {k: float(v) for k, v in top_corr.items()},
        "naive_accuracy_baseline": round(1 - report["fraud_percentage"] / 100, 6),
    }


def make_figures(df: pd.DataFrame, out_dir: Path = FIG_DIR) -> list[str]:
    out_dir.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="darkgrid")
    files = []

    fig, ax = plt.subplots(figsize=(5, 4))
    counts = df[TARGET_COLUMN].value_counts().sort_index()
    ax.bar(["Legitimate", "Fraud"], [counts.get(0, 0), counts.get(1, 0)], color=["#2dd4bf", "#f43f5e"])
    ax.set_yscale("log"); ax.set_title("Class distribution (log scale)")
    fig.tight_layout(); fig.savefig(out_dir / "class_distribution.png", dpi=120); plt.close(fig)
    files.append("class_distribution.png")

    fig, ax = plt.subplots(figsize=(7, 4))
    for label, name, color in [(0, "Legitimate", "#2dd4bf"), (1, "Fraud", "#f43f5e")]:
        ax.hist(np.log1p(df.loc[df[TARGET_COLUMN] == label, "Amount"]), bins=40, alpha=0.6,
                label=name, color=color, density=True)
    ax.set_xlabel("log(1 + Amount)"); ax.set_title("Amount distribution by class"); ax.legend()
    fig.tight_layout(); fig.savefig(out_dir / "amount_distribution.png", dpi=120); plt.close(fig)
    files.append("amount_distribution.png")

    fig, ax = plt.subplots(figsize=(7, 4))
    for label, name, color in [(0, "Legitimate", "#2dd4bf"), (1, "Fraud", "#f43f5e")]:
        ax.hist(df.loc[df[TARGET_COLUMN] == label, "Time"], bins=48, alpha=0.6, label=name,
                color=color, density=True)
    ax.set_xlabel("Time (seconds from first transaction)"); ax.set_title("Transaction time by class"); ax.legend()
    fig.tight_layout(); fig.savefig(out_dir / "time_distribution.png", dpi=120); plt.close(fig)
    files.append("time_distribution.png")

    corr = df[FEATURE_COLUMNS + [TARGET_COLUMN]].corr()[TARGET_COLUMN].drop(TARGET_COLUMN).sort_values()
    fig, ax = plt.subplots(figsize=(6, 7))
    ax.barh(corr.index, corr.values, color="#22d3ee")
    ax.set_title("Pearson correlation of each feature with Class")
    fig.tight_layout(); fig.savefig(out_dir / "correlation_with_class.png", dpi=120); plt.close(fig)
    files.append("correlation_with_class.png")
    return files


def findings_markdown(summary: dict) -> str:
    d = summary["dataset"]
    return (
        "# EDA Findings (generated from the actual dataset)\n\n"
        f"- Rows: {d['n_rows']:,}; columns: {d['n_columns']}\n"
        f"- Missing values: {d['n_missing_values']:,}\n"
        f"- Duplicate rows: {d['n_duplicate_rows']:,}\n"
        f"- Legitimate: {d['n_legitimate']:,}; fraud: {d['n_fraud']:,} ({d['fraud_percentage']}%)\n\n"
        "## Why accuracy is misleading\n"
        f"A model that labels every transaction legitimate scores {summary['naive_accuracy_baseline']:.4%} "
        "accuracy while catching zero fraud. This project therefore reports precision, recall, F1, "
        "PR-AUC, ROC-AUC, and balanced accuracy instead.\n\n"
        "## Features most correlated with Class (V1-V28 are anonymised; no meaning is assumed)\n"
        + "\n".join(f"- {k}: {v:+.3f}" for k, v in summary["top_correlations_with_class"].items())
        + "\n"
    )


def run_eda(csv_path: str | Path | None = None, report_dir: Path = REPORT_DIR) -> dict:
    df = load_dataset(csv_path)
    summary = compute_summary(df)
    report_dir.mkdir(parents=True, exist_ok=True)
    summary["figures"] = make_figures(df, report_dir / "figures")
    (report_dir / "eda_summary.json").write_text(json.dumps(summary, indent=2))
    (report_dir / "eda_findings.md").write_text(findings_markdown(summary))
    return summary


if __name__ == "__main__":
    from ml.data_loader import DatasetError
    try:
        s = run_eda()
        print(f"EDA complete: {s['dataset']['n_rows']:,} rows, {s['dataset']['n_fraud']:,} fraud.")
    except DatasetError as e:
        print(f"ERROR: {e}")
        raise SystemExit(1)
