import { useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Card } from "../components/Cards.jsx";
import ConfusionMatrix from "../components/ConfusionMatrix.jsx";
import StateView from "../components/StateView.jsx";
import { C, axisProps, tooltipStyle } from "../components/chartTheme.js";
import { useApi } from "../hooks/useApi.js";
import { CurveChart } from "./Dashboard.jsx";
import { api } from "../services/api.js";
import { fmt, fmtInt, pct } from "../services/format.js";

const NOTES = {
  dummy: ["Establishes the floor: always predicts the majority class.", "Catches no fraud; shows why accuracy alone is misleading."],
  logistic_regression: ["Fast, interpretable, coefficients can be inspected.", "Linear decision boundary; cannot capture feature interactions."],
  random_forest: ["Learns non-linear patterns and interactions, robust to scaling.", "Larger and slower; probabilities are not calibrated; less transparent."],
  xgboost: ["Strong on tabular data; handles imbalance via scale_pos_weight.", "More hyper-parameters to tune; easier to overfit a few hundred fraud cases."],
  isolation_forest: ["Needs no labels; can flag novel patterns.", "Anomalous is not the same as fraudulent; usually weaker than supervised models here."],
};

export default function Compare() {
  const metrics = useApi(api.metrics);
  const [pick, setPick] = useState(null);
  return (
    <div className="page">
      <h1>Model comparison</h1>
      <p className="lead muted">All models share one stratified split. Thresholds and the winner are chosen on validation data; the test set is evaluated once.</p>
      <StateView req={metrics} label="evaluation results">
        {(mt) => {
          const names = Object.keys(mt.models);
          const cur = pick || mt.selected_model;
          const r = mt.models[cur];
          return (
            <>
              <div className="tabs" role="tablist" aria-label="Choose model">
                {names.map((n) => (
                  <button key={n} role="tab" aria-selected={cur === n} className={`tab ${cur === n ? "active" : ""}`} onClick={() => setPick(n)}>
                    {mt.models[n].label}{n === mt.selected_model && " ★"}
                  </button>
                ))}
              </div>
              <div className="grid-2">
                <Card title={r.label} subtitle={r.score_meaning}>
                  <dl className="result-list">
                    <dt>Decision threshold</dt><dd>{fmt(r.threshold, 5)}</dd>
                    <dt>Threshold rule</dt><dd>{mt.threshold_rule}</dd>
                    <dt>Best hyper-parameters</dt><dd className="mono">{Object.keys(r.best_params).length ? JSON.stringify(r.best_params) : "none tuned"}</dd>
                    <dt>CV average precision (train)</dt><dd>{fmt(r.cv_average_precision)}</dd>
                    <dt>Probability supported</dt><dd>{r.supports_probability ? "Yes (uncalibrated)" : "No: anomaly score only"}</dd>
                  </dl>
                  <ul className="notes">
                    <li><strong>Strength:</strong> {NOTES[cur]?.[0]}</li>
                    <li><strong>Weakness:</strong> {NOTES[cur]?.[1]}</li>
                  </ul>
                </Card>
                <Card title="Confusion matrix (test)" subtitle={`Prevalence of fraud in test set: ${pct(100 * r.test.prevalence, 3)}`}>
                  <ConfusionMatrix cm={r.test.confusion_matrix} title={`${r.label} confusion matrix`} />
                  <p className="muted small">False positive rate {fmt(r.test.false_positive_rate, 5)} · False negative rate {fmt(r.test.false_negative_rate, 4)}</p>
                </Card>
              </div>

              <Card title="Metrics side by side" subtitle="Validation values were used for selection; test values are the final report.">
                <div className="table-wrap">
                  <table>
                    <thead><tr><th>Model</th><th>Split</th><th>Threshold</th><th>Precision</th><th>Recall</th><th>F1</th><th>PR-AUC</th><th>ROC-AUC</th><th>Balanced acc.</th><th>FPR</th><th>FNR</th></tr></thead>
                    <tbody>
                      {names.flatMap((n) => ["validation", "test"].map((sp) => {
                        const m = mt.models[n][sp];
                        return (
                          <tr key={n + sp} className={n === mt.selected_model && sp === "test" ? "row-selected" : ""}>
                            <td>{mt.models[n].label}</td><td>{sp}</td><td>{fmt(mt.models[n].threshold, 4)}</td>
                            <td>{fmt(m.precision)}</td><td>{fmt(m.recall)}</td><td>{fmt(m.f1)}</td><td>{fmt(m.pr_auc_average_precision)}</td>
                            <td>{fmt(m.roc_auc)}</td><td>{fmt(m.balanced_accuracy)}</td><td>{fmt(m.false_positive_rate, 5)}</td><td>{fmt(m.false_negative_rate)}</td>
                          </tr>
                        );
                      }))}
                    </tbody>
                  </table>
                </div>
              </Card>

              <div className="grid-2">
                <Card title="Precision-recall comparison" subtitle="Test set."><CurveChart mt={mt} kind="pr" xKey="recall" yKey="precision" xLabel="Recall" yLabel="Precision" /></Card>
                {r.threshold_tradeoff_validation?.length > 0 ? (
                  <Card title="Threshold trade-off" subtitle="Validation data: what each recall target costs in false alarms.">
                    <div className="table-wrap"><table>
                      <thead><tr><th>Recall target</th><th>Threshold</th><th>Precision</th><th>False alarms</th><th>Missed</th></tr></thead>
                      <tbody>{r.threshold_tradeoff_validation.map((t) => (
                        <tr key={t.target_recall}><td>{t.target_recall}</td><td>{fmt(t.threshold, 4)}</td><td>{fmt(t.precision, 3)}</td><td>{fmtInt(t.false_positives)}</td><td>{fmtInt(t.missed_fraud)}</td></tr>
                      ))}</tbody>
                    </table></div>
                    <p className="muted small">Lowering the threshold catches more fraud but raises false alarms. The locked threshold maximises validation F2.</p>
                  </Card>
                ) : <Card title="Threshold trade-off"><p className="muted">Not applicable to this model.</p></Card>}
              </div>

              {r.feature_importance && (
                <Card title="Feature importance" subtitle={`${r.feature_importance[0].basis}. V1-V28 are anonymised, so only their rank is informative.`}>
                  <ResponsiveContainer width="100%" height={320}>
                    <BarChart layout="vertical" data={r.feature_importance.slice(0, 12)} margin={{ left: 24 }}>
                      <CartesianGrid stroke={C.grid} horizontal={false} />
                      <XAxis type="number" {...axisProps} />
                      <YAxis type="category" dataKey="feature" {...axisProps} width={110} />
                      <Tooltip {...tooltipStyle} formatter={(v) => fmt(v)} />
                      <Bar dataKey="importance" fill={C.cyan} radius={[0, 6, 6, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </Card>
              )}

              <Card title="Error analysis (test set, aggregate)" subtitle="What do the missed frauds and false alarms look like?">
                <div className="table-wrap"><table>
                  <thead><tr><th>Outcome</th><th>Count</th><th>Median amount</th><th>Mean amount</th><th>Median score</th></tr></thead>
                  <tbody>{Object.entries(r.error_analysis).filter(([, v]) => typeof v === "object" && v).map(([k, v]) => (
                    <tr key={k}><td>{k.replace(/_/g, " ")}</td><td>{fmtInt(v.count)}</td><td>{fmt(v.amount_median, 2)}</td><td>{fmt(v.amount_mean, 2)}</td><td>{fmt(v.score_median, 4)}</td></tr>
                  ))}</tbody>
                </table></div>
              </Card>

              {mt.imbalance_experiment && (
                <Card title="Class-imbalance handling (Logistic Regression, validation)" subtitle="Training-only strategies compared at a validation-chosen threshold.">
                  <div className="table-wrap"><table>
                    <thead><tr><th>Strategy</th><th>Train rows</th><th>Precision</th><th>Recall</th><th>F1</th><th>PR-AUC</th><th>False positives</th></tr></thead>
                    <tbody>{Object.entries(mt.imbalance_experiment).map(([k, v]) => (
                      <tr key={k}><td>{k.replace(/_/g, " ")}</td><td>{fmtInt(v.train_rows)}</td><td>{fmt(v.precision)}</td><td>{fmt(v.recall)}</td><td>{fmt(v.f1)}</td><td>{fmt(v.pr_auc_average_precision)}</td><td>{fmtInt(v.false_positives)}</td></tr>
                    ))}</tbody>
                  </table></div>
                </Card>
              )}
            </>
          );
        }}
      </StateView>
    </div>
  );
}
