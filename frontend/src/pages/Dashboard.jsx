import { Bar, BarChart, CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { api } from '../services/api'
import { useApi } from '../hooks/useApi'
import { Card, ConfusionMatrix, Gate, Kpi, MODEL_COLORS, chartTheme as T, int, num, pct, pretty } from '../components/ui'

const axis = { stroke: T.axis, fontSize: 12 }

function Curves({ metrics, kind }) {
  const isRoc = kind === 'roc'
  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart margin={{ left: 0, right: 12, top: 8 }}>
        <CartesianGrid stroke={T.grid} />
        <XAxis type="number" dataKey="x" domain={[0, 1]} {...axis} label={{ value: isRoc ? 'False positive rate' : 'Recall', fill: T.axis, dy: 14, fontSize: 12 }} />
        <YAxis type="number" dataKey="y" domain={[0, 1]} {...axis} />
        <Tooltip contentStyle={T.tooltip} formatter={(v) => Number(v).toFixed(3)} />
        <Legend wrapperStyle={{ paddingTop: 12 }} />
        {Object.entries(metrics.models).map(([n, m]) => {
          const c = m.test.curves?.[kind]
          if (!c) return null
          const xs = isRoc ? c.fpr : c.recall, ys = isRoc ? c.tpr : c.precision
          return <Line key={n} name={pretty(n)} data={xs.map((x, i) => ({ x, y: ys[i] }))} dataKey="y"
            stroke={MODEL_COLORS[n]} dot={false} strokeWidth={2} isAnimationActive={false} />
        })}
      </LineChart>
    </ResponsiveContainer>
  )
}

export default function Dashboard() {
  const summary = useApi(api.summary, [])
  const metrics = useApi(api.metrics, [])
  const best = metrics.data?.best_model
  const bestTest = best && metrics.data.models[best].test

  return (
    <div className="stack">
      <Gate state={summary}>{(s) => {
        const d = s.dataset
        const classData = [{ name: 'Legitimate', count: d.n_legitimate }, { name: 'Fraud', count: d.n_fraud }]
        const hist = s.amount_histogram.edges.slice(0, -1).map((e, i) => ({
          bin: `${e.toFixed(0)}–${s.amount_histogram.edges[i + 1].toFixed(0)}`,
          all: s.amount_histogram.all[i], fraud: s.amount_histogram.fraud[i] }))
        return (<>
          <div className="kpis">
            <Kpi label="Transactions analysed" value={int(d.n_rows)} />
            <Kpi label="Fraudulent" value={int(d.n_fraud)} tone="rose" />
            <Kpi label="Legitimate" value={int(d.n_legitimate)} tone="teal" />
            <Kpi label="Fraud percentage" value={`${d.fraud_percentage}%`} hint="Highly imbalanced" />
            <Kpi label="Best model (validation AP)" value={best ? pretty(best) : 'Pending'}
              hint={bestTest ? `Test AP ${num(bestTest.average_precision)}` : 'Train models first'} />
          </div>
          <div className="grid2">
            <Card title="Fraud vs legitimate (log scale)">
              <ResponsiveContainer width="100%" height={260}><BarChart data={classData}>
                <CartesianGrid stroke={T.grid} /><XAxis dataKey="name" {...axis} /><YAxis scale="log" domain={[1, 'auto']} allowDataOverflow {...axis} />
                <Tooltip contentStyle={T.tooltip} /><Bar dataKey="count" fill={T.cyan} isAnimationActive={false} />
              </BarChart></ResponsiveContainer>
            </Card>
            <Card title="Transaction amount distribution (up to 99th percentile)">
              <ResponsiveContainer width="100%" height={260}><BarChart data={hist}>
                <CartesianGrid stroke={T.grid} /><XAxis dataKey="bin" {...axis} interval={3} /><YAxis scale="log" domain={[1, 'auto']} allowDataOverflow {...axis} />
                <Tooltip contentStyle={T.tooltip} /><Legend />
                <Bar dataKey="all" name="All" fill={T.cyan} isAnimationActive={false} />
                <Bar dataKey="fraud" name="Fraud" fill={T.rose} isAnimationActive={false} />
              </BarChart></ResponsiveContainer>
            </Card>
          </div>
          <Card title="Fraud count by transaction time (seconds since first transaction)">
            <ResponsiveContainer width="100%" height={240}><LineChart data={s.time_trend}>
              <CartesianGrid stroke={T.grid} /><XAxis dataKey="bin" {...axis} interval={3} /><YAxis {...axis} />
              <Tooltip contentStyle={T.tooltip} />
              <Line dataKey="fraud" name="Fraud" stroke={T.rose} dot={false} strokeWidth={2} isAnimationActive={false} />
            </LineChart></ResponsiveContainer>
          </Card>
        </>)
      }}</Gate>

      <Gate state={metrics}>{(m) => {
        const rows = Object.entries(m.models)
        const cmp = ['precision', 'recall', 'f1'].map((k) => ({ metric: pretty(k), ...Object.fromEntries(rows.map(([n, r]) => [n, r.test[k]])) }))
        return (<>
          <div className="grid2">
            <Card title="Precision, recall and F1 (test set)">
              <ResponsiveContainer width="100%" height={260}><BarChart data={cmp}>
                <CartesianGrid stroke={T.grid} /><XAxis dataKey="metric" {...axis} /><YAxis domain={[0, 1]} {...axis} />
                <Tooltip contentStyle={T.tooltip} formatter={(v) => Number(v).toFixed(3)} /><Legend />
                {rows.map(([n]) => <Bar key={n} dataKey={n} name={pretty(n)} fill={MODEL_COLORS[n]} isAnimationActive={false} />)}
              </BarChart></ResponsiveContainer>
            </Card>
            <Card title={`Confusion matrix — ${pretty(m.best_model)} (test)`}>
              <ConfusionMatrix cm={m.models[m.best_model].test.confusion_matrix} />
            </Card>
          </div>
          <div className="grid2">
            <Card title="ROC curves (test)"><Curves metrics={m} kind="roc" /></Card>
            <Card title="Precision–recall curves (test)"><Curves metrics={m} kind="pr" /></Card>
          </div>
          <Card title="Model performance (held-out test set)">
            <div className="table-wrap"><table>
              <thead><tr><th>Model</th><th>Precision</th><th>Recall</th><th>F1</th><th>ROC-AUC</th><th>Avg precision</th><th>Balanced acc.</th><th>FPR</th><th>FNR</th><th>Fraud prevalence</th></tr></thead>
              <tbody>{rows.map(([n, r]) => { const t = r.test; return (
                <tr key={n} className={n === m.best_model ? 'hl' : ''}><td>{pretty(n)}{n === m.best_model && ' ★'}</td>
                  <td>{num(t.precision)}</td><td>{num(t.recall)}</td><td>{num(t.f1)}</td><td>{num(t.roc_auc)}</td>
                  <td>{num(t.average_precision)}</td><td>{num(t.balanced_accuracy)}</td>
                  <td>{pct(t.false_positive_rate, 3)}</td><td>{pct(t.false_negative_rate)}</td><td>{pct(t.prevalence, 3)}</td></tr>) })}</tbody>
            </table></div>
            <p className="note">★ chosen by validation average precision. Average precision is scikit-learn's step-wise PR-AUC; a no-skill model scores about the fraud prevalence.</p>
          </Card>
        </>)
      }}</Gate>
    </div>
  )
}
