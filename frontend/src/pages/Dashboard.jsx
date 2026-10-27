import { Activity, BadgeCheck, Percent, ShieldAlert, ShieldCheck, Sigma } from "lucide-react";
import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Card, KpiCard } from "../components/Cards.jsx";
import ConfusionMatrix from "../components/ConfusionMatrix.jsx";
import StateView from "../components/StateView.jsx";
import { C, MODEL_COLORS, axisProps, tooltipStyle } from "../components/chartTheme.js";
import { useApi } from "../hooks/useApi.js";
import { api } from "../services/api.js";
import { fmt, fmtInt, pct } from "../services/format.js";

export default function Dashboard() {
  const summary = useApi(api.summary);
  const models = useApi(api.models);
  const metrics = useApi(api.metrics);

  return (
    <div className="page">
      <h1>Fraud analytics overview</h1>
      <p className="lead muted">Every figure below is read from the real dataset and the saved evaluation results. Nothing is placeholder data.</p>

      <StateView req={summary} label="dataset summary">
        {(s) => (
          <>
            <div className="kpi-grid">
              <KpiCard icon={Activity} label="Transactions analysed" value={fmtInt(s.dataset.rows)} hint={`${fmtInt(s.dataset.duplicate_rows)} exact duplicate rows`} />
              <KpiCard icon={ShieldAlert} tone="rose" label="Fraudulent" value={fmtInt(s.dataset.fraud)} />
              <KpiCard icon={ShieldCheck} label="Legitimate" value={fmtInt(s.dataset.legitimate)} />
              <KpiCard icon={Percent} tone="amber" label="Fraud share" value={pct(s.dataset.fraud_percent, 3)} hint="Highly imbalanced" />
              <ModelKpi req={models} />
            </div>
            <div className="grid-2">
              <Card title="Fraud versus legitimate" subtitle="Log scale: fraud is too rare to see on a linear axis.">
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={[{ name: "Legitimate", count: s.dataset.legitimate }, { name: "Fraud", count: s.dataset.fraud }]}>
                    <CartesianGrid stroke={C.grid} vertical={false} />
                    <XAxis dataKey="name" {...axisProps} />
                    <YAxis scale="log" domain={[1, "auto"]} allowDataOverflow {...axisProps} width={64} />
                    <Tooltip {...tooltipStyle} formatter={(v) => fmtInt(v)} />
                    <Bar dataKey="count" fill={C.cyan} radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
              <Card title="Transaction amount distribution" subtitle="Transactions per amount band (log scale).">
                <ResponsiveContainer width="100%" height={260}>
                  <BarChart data={s.amount_distribution}>
                    <CartesianGrid stroke={C.grid} vertical={false} />
                    <XAxis dataKey="bin" {...axisProps} interval={0} angle={-30} textAnchor="end" height={56} />
                    <YAxis scale="log" domain={[1, "auto"]} allowDataOverflow {...axisProps} width={64} />
                    <Tooltip {...tooltipStyle} formatter={(v) => fmtInt(v)} />
                    <Legend />
                    <Bar dataKey="legitimate" fill={C.cyan} />
                    <Bar dataKey="fraud" fill={C.rose} />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </div>
            <Card title="Fraud by transaction time" subtitle={`Each bar is one elapsed hour of the ${s.time_range_hours}-hour capture. Hours with few transactions give noisy rates.`}>
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={s.time_distribution}>
                  <CartesianGrid stroke={C.grid} vertical={false} />
                  <XAxis dataKey="hour" {...axisProps} label={{ value: "Hours since first transaction", fill: C.text, position: "insideBottom", offset: -2 }} height={48} />
                  <YAxis yAxisId="l" {...axisProps} width={48} />
                  <YAxis yAxisId="r" orientation="right" {...axisProps} width={56} unit="%" />
                  <Tooltip {...tooltipStyle} />
                  <Legend />
                  <Line yAxisId="l" type="monotone" dataKey="fraud" name="Fraud count" stroke={C.rose} dot={false} strokeWidth={2} />
                  <Line yAxisId="r" type="monotone" dataKey="fraud_rate_percent" name="Fraud rate (%)" stroke={C.amber} dot={false} strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </Card>
          </>
        )}
      </StateView>

      <StateView req={models} label="model results">
        {(m) => (
          <>
            <Card title="Model performance (held-out test set)" subtitle={`Selected on validation data: ${m.selection_criterion}.`}>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr><th>Model</th><th>Precision</th><th>Recall</th><th>F1</th><th>PR-AUC</th><th>ROC-AUC</th><th>Balanced acc.</th><th>False alarms</th><th>Missed fraud</th></tr>
                  </thead>
                  <tbody>
                    {m.models.map((r) => (
                      <tr key={r.name} className={r.selected ? "row-selected" : ""}>
                        <td>{r.label}{r.selected && <span className="badge">selected</span>}</td>
                        <td>{fmt(r.test.precision)}</td><td>{fmt(r.test.recall)}</td><td>{fmt(r.test.f1)}</td>
                        <td>{fmt(r.test.pr_auc_average_precision)}</td><td>{fmt(r.test.roc_auc)}</td><td>{fmt(r.test.balanced_accuracy)}</td>
                        <td>{fmtInt(r.test.confusion_matrix.fp)}</td><td>{fmtInt(r.test.confusion_matrix.fn)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="muted small">PR-AUC is average precision. A random classifier's PR-AUC equals the fraud prevalence ({pct(100 * m.models[0].test.prevalence, 3)} here), so compare against that, not against 0.5.</p>
            </Card>
            <div className="grid-2">
              <Card title="Precision, recall and F1" subtitle="Test set, at each model's validation-selected threshold.">
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={m.models.map((r) => ({ name: r.label, Precision: r.test.precision, Recall: r.test.recall, F1: r.test.f1 }))}>
                    <CartesianGrid stroke={C.grid} vertical={false} />
                    <XAxis dataKey="name" {...axisProps} interval={0} tick={{ fill: C.text, fontSize: 11 }} />
                    <YAxis domain={[0, 1]} {...axisProps} width={40} />
                    <Tooltip {...tooltipStyle} formatter={(v) => fmt(v)} />
                    <Legend />
                    <Bar dataKey="Precision" fill={C.cyan} /><Bar dataKey="Recall" fill={C.teal} /><Bar dataKey="F1" fill={C.amber} />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
              <StateView req={metrics} label="evaluation curves">
                {(mt) => <SelectedMatrix mt={mt} />}
              </StateView>
            </div>
          </>
        )}
      </StateView>

      <StateView req={metrics} label="ROC and precision-recall curves">
        {(mt) => (
          <div className="grid-2">
            <Card title="ROC curves" subtitle="Test set.">
              <CurveChart mt={mt} kind="roc" xKey="fpr" yKey="tpr" xLabel="False positive rate" yLabel="True positive rate" diagonal />
            </Card>
            <Card title="Precision-recall curves" subtitle="Test set. More informative than ROC when fraud is rare.">
              <CurveChart mt={mt} kind="pr" xKey="recall" yKey="precision" xLabel="Recall" yLabel="Precision" />
            </Card>
          </div>
        )}
      </StateView>
    </div>
  );
}

function ModelKpi({ req }) {
  if (req.loading) return <KpiCard icon={BadgeCheck} tone="violet" label="Best evaluated model" value="…" />;
  if (req.error) return <KpiCard icon={BadgeCheck} tone="violet" label="Best evaluated model" value="Not trained" hint="Run python -m ml.train" />;
  const sel = req.data.models.find((x) => x.selected);
  return <KpiCard icon={Sigma} tone="violet" label="Best evaluated model" value={sel.label} hint={`Validation PR-AUC ${fmt(sel.validation.pr_auc_average_precision, 3)}`} />;
}

function SelectedMatrix({ mt }) {
  const sel = mt.models[mt.selected_model];
  return (
    <Card title={`Confusion matrix: ${sel.label}`} subtitle="Held-out test set.">
      <ConfusionMatrix cm={sel.test.confusion_matrix} title={`Confusion matrix for ${sel.label}`} />
    </Card>
  );
}

export function CurveChart({ mt, kind, xKey, yKey, xLabel, yLabel, diagonal }) {
  const entries = Object.entries(mt.models).filter(([, r]) => r.curves);
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart margin={{ left: 4, right: 12, top: 8 }}>
        <CartesianGrid stroke={C.grid} />
        <XAxis type="number" dataKey="x" domain={[0, 1]} {...axisProps} label={{ value: xLabel, fill: C.text, position: "insideBottom", offset: -4 }} height={44} />
        <YAxis type="number" dataKey="y" domain={[0, 1]} {...axisProps} width={44} label={{ value: yLabel, fill: C.text, angle: -90, position: "insideLeft" }} />
        <Tooltip {...tooltipStyle} formatter={(v) => fmt(v, 3)} />
        <Legend />
        {diagonal && <Line data={[{ x: 0, y: 0 }, { x: 1, y: 1 }]} dataKey="y" name="Chance" stroke="#475569" strokeDasharray="4 4" dot={false} />}
        {entries.map(([name, r]) => {
          const cu = r.curves[kind];
          const data = cu[xKey].map((x, i) => ({ x, y: cu[yKey][i] }));
          return <Line key={name} data={data} dataKey="y" name={r.label} stroke={MODEL_COLORS[name]} dot={false} strokeWidth={2} isAnimationActive={false} />;
        })}
      </LineChart>
    </ResponsiveContainer>
  );
}
