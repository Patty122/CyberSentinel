"""Reproducible exploratory data analysis: summary.json, figures and a findings report.

Run from the project root:  python -m ml.eda
Findings are derived from the actual CSV; nothing here is hard-coded.
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from . import config
from .data_loader import load_dataset, quality_report

AMOUNT_EDGES = [0, 1, 5, 10, 25, 50, 100, 250, 500, 1000, 2500, 5000, np.inf]
PALETTE = {0: "#38bdf8", 1: "#f43f5e"}


def _amount_bins(df):
    labels = [f"{int(a)}-{int(b)}" if np.isfinite(b) else f"{int(a)}+" for a, b in zip(AMOUNT_EDGES[:-1], AMOUNT_EDGES[1:])]
    cut = pd.cut(df["Amount"], bins=AMOUNT_EDGES, labels=labels, right=False, include_lowest=True)
    t = pd.crosstab(cut, df[config.TARGET]).reindex(labels).fillna(0).astype(int)
    return [{"bin": l, "legitimate": int(t.loc[l].get(0, 0)), "fraud": int(t.loc[l].get(1, 0))} for l in labels]


def _hourly(df):
    hour = (df["Time"] // 3600).astype(int)
    g = df.groupby(hour)[config.TARGET].agg(total="size", fraud="sum")
    return [{"hour": int(h), "total": int(r.total), "fraud": int(r.fraud),
             "fraud_rate_percent": round(100 * r.fraud / r.total, 4)} for h, r in g.iterrows()]


def build_summary(df: pd.DataFrame) -> dict:
    q = quality_report(df)
    desc = df[config.FEATURES].describe().T
    feats = [{"feature": f, **{k: round(float(desc.loc[f, k]), 5) for k in ["mean", "std", "min", "25%", "50%", "75%", "max"]}}
             for f in config.FEATURES]
    corr = df.corr(numeric_only=True)[config.TARGET].drop(config.TARGET)
    top = corr.reindex(corr.abs().sort_values(ascending=False).index).head(10)
    amount_by_class = {str(c): {k: round(float(v), 4) for k, v in g["Amount"].describe().items()}
                       for c, g in df.groupby(config.TARGET)}
    return {
        "dataset": q,
        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
        "feature_statistics": feats,
        "amount_by_class": amount_by_class,
        "amount_distribution": _amount_bins(df),
        "time_distribution": _hourly(df),
        "time_range_hours": round(float(df["Time"].max() / 3600), 2),
        "top_correlations_with_class": [{"feature": k, "correlation": round(float(v), 4)} for k, v in top.items()],
        "note": "V1-V28 are PCA components; their original meaning is not provided by the dataset authors.",
    }


def make_figures(df: pd.DataFrame, out: Path) -> list[str]:
    out.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    names = []

    def save(fig, name):
        fig.tight_layout(); fig.savefig(out / name, dpi=130); plt.close(fig); names.append(name)

    counts = df[config.TARGET].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(5.5, 4))
    ax.bar(["Legitimate", "Fraud"], counts.values, color=[PALETTE[0], PALETTE[1]])
    ax.set_yscale("log"); ax.set_ylabel("Transactions (log scale)")
    ax.set_title(f"Class distribution (fraud = {100 * counts.get(1, 0) / len(df):.3f}%)")
    for i, v in enumerate(counts.values):
        ax.text(i, v, f"{v:,}", ha="center", va="bottom")
    save(fig, "class_distribution.png")

    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    for c, name in [(0, "Legitimate"), (1, "Fraud")]:
        axes[0].hist(np.log1p(df.loc[df[config.TARGET] == c, "Amount"]), bins=50, alpha=.6, density=True,
                     color=PALETTE[c], label=name)
    axes[0].set(title="log(1 + Amount) by class", xlabel="log1p(Amount)", ylabel="Density"); axes[0].legend()
    sns.boxplot(data=df, x=config.TARGET, y="Amount", ax=axes[1], palette=[PALETTE[0], PALETTE[1]], showfliers=False, hue=config.TARGET, legend=False)
    axes[1].set(title="Amount by class (outliers hidden)", xticklabels=["Legitimate", "Fraud"], xlabel="")
    save(fig, "amount_distribution.png")

    hours = pd.DataFrame(_hourly(df))
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(hours["hour"], hours["fraud"], color=PALETTE[1])
    ax.set(title="Fraud count per elapsed hour (Time / 3600)", xlabel="Hours since first transaction", ylabel="Fraud transactions")
    save(fig, "fraud_by_hour.png")

    fig, ax = plt.subplots(figsize=(11, 9))
    sns.heatmap(df.corr(numeric_only=True), cmap="vlag", center=0, ax=ax, cbar_kws={"shrink": .7})
    ax.set_title("Correlation matrix (all features and Class)")
    save(fig, "correlation_heatmap.png")

    corr = df.corr(numeric_only=True)[config.TARGET].drop(config.TARGET).sort_values()
    fig, ax = plt.subplots(figsize=(6, 8))
    ax.barh(corr.index, corr.values, color=np.where(corr.values >= 0, PALETTE[1], PALETTE[0]))
    ax.set(title="Pearson correlation with Class", xlabel="Correlation")
    save(fig, "feature_class_correlation.png")

    top = corr.abs().sort_values(ascending=False).head(6).index
    fig, axes = plt.subplots(2, 3, figsize=(12, 6))
    for ax, f in zip(axes.ravel(), top):
        sns.boxplot(data=df, x=config.TARGET, y=f, ax=ax, hue=config.TARGET, legend=False,
                    palette=[PALETTE[0], PALETTE[1]], showfliers=False)
        ax.set(title=f, xlabel="", xticklabels=["Legit", "Fraud"])
    save(fig, "top_features_by_class.png")
    return names


def findings_markdown(s: dict) -> str:
    d = s["dataset"]
    a0, a1 = s["amount_by_class"].get("0", {}), s["amount_by_class"].get("1", {})
    top = ", ".join(f"{t['feature']} ({t['correlation']:+.2f})" for t in s["top_correlations_with_class"][:5])
    peak = max(s["time_distribution"], key=lambda r: r["fraud_rate_percent"])
    return f"""# EDA findings (generated from the actual dataset)

- Rows x columns: **{d['rows']:,} x {d['columns']}**
- Missing values: **{d['missing_total']}**
- Exact duplicate rows: **{d['duplicate_rows']:,}** (removed before splitting during training)
- Legitimate: **{d['legitimate']:,}**, fraud: **{d['fraud']:,}** ({d['fraud_percent']}% of rows)
- Time spans about **{s['time_range_hours']} hours**; the highest hourly fraud rate is **{peak['fraud_rate_percent']}%** at elapsed hour {peak['hour']} (only {peak['total']:,} transactions in that hour).
- Median amount: legitimate **{a0.get('50%')}**, fraud **{a1.get('50%')}**; mean legitimate **{a0.get('mean')}**, fraud **{a1.get('mean')}**.
- Features most correlated with Class: {top}.

## Why accuracy is misleading here
A model that labels every transaction legitimate scores about {100 - d['fraud_percent']:.2f}% accuracy while catching zero fraud.
Precision, recall, F1, PR-AUC and the confusion matrix are used instead.

## Notes
V1-V28 are PCA components with undisclosed meaning, so no real-world interpretation is attached to them.
EDA is exploratory only: no modelling decision (feature removal, thresholds) is taken from it.
"""


def run(data_path=None, reports_dir=None) -> dict:
    reports = Path(reports_dir) if reports_dir else config.REPORTS_DIR
    df = load_dataset(data_path)
    summary = build_summary(df)
    reports.mkdir(parents=True, exist_ok=True)
    (reports / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    summary["figures"] = make_figures(df, reports / "figures")
    (reports / "eda_findings.md").write_text(findings_markdown(summary), encoding="utf-8")
    return summary


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Run exploratory data analysis")
    ap.add_argument("--data", default=None)
    args = ap.parse_args()
    s = run(args.data)
    print(f"EDA complete: {s['dataset']['rows']:,} rows, {s['dataset']['fraud']:,} fraud. Reports in {config.REPORTS_DIR}")
