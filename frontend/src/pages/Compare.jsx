import { useState } from 'react'
import { api } from '../services/api'
import { useApi } from '../hooks/useApi'
import { Card, ConfusionMatrix, Gate, int, num, pct, pretty } from '../components/ui'

const INFO = {
  logistic_regression: ['Interpretable linear baseline, fast, probability output.', 'Cannot capture nonlinear interactions; probabilities need calibration.'],
  random_forest: ['Captures nonlinear patterns; strong on tabular data.', 'Larger and slower; less interpretable; probabilities are not calibrated.'],
  isolation_forest: ['Unsupervised: needs no labels, can flag novel patterns.', 'Ignores labels during training, so it is usually weaker here; outputs an anomaly score, not a probability.'],
}

export default function Compare() {
  const st = useApi(api.metrics, [])
  const [sel, setSel] = useState(null)
  return (
    <Gate state={st}>{(m) => {
      const names = Object.keys(m.models)
      const cur = sel || m.best_model
      const r = m.models[cur]
      const ex = m.experiments || {}
      return (
        <div className="stack">
          <Card title="Select model">
            <div className="tabs-inline" role="tablist">
              {names.map((n) => <button key={n} role="tab" aria-selected={cur === n} className={cur === n ? 'on' : ''} onClick={() => setSel(n)}>{pretty(n)}{n === m.best_model && ' ★'}</button>)}
            </div>
            <p className="note">{m.selection_criterion}</p>
          </Card>
          <div className="grid2">
            <Card title={`${pretty(cur)} — confusion matrix (test)`}><ConfusionMatrix cm={r.test.confusion_matrix} /></Card>
            <Card title="Details">
              <dl className="dl">
                <dt>Type</dt><dd>{pretty(r.type)}</dd>
                <dt>Score type</dt><dd>{pretty(r.score_type)}</dd>
                <dt>Locked threshold (chosen on validation)</dt><dd>{num(r.threshold, 4)}</dd>
                <dt>Validation F1 / AP</dt><dd>{num(r.validation.f1)} / {num(r.validation.average_precision)}</dd>
                <dt>Test fraud prevalence</dt><dd>{pct(r.test.prevalence, 3)} (n={int(r.test.n_samples)})</dd>
              </dl>
              <p><b>Strengths:</b> {INFO[cur][0]}</p>
              <p><b>Weaknesses:</b> {INFO[cur][1]}</p>
            </Card>
          </div>
          <Card title="All models side by side (test)">
            <div className="table-wrap"><table>
              <thead><tr><th>Model</th><th>Threshold</th><th>Precision</th><th>Recall</th><th>F1</th><th>Avg precision</th><th>TP</th><th>FP</th><th>FN</th><th>TN</th></tr></thead>
              <tbody>{names.map((n) => { const t = m.models[n].test, c = t.confusion_matrix; return (
                <tr key={n} className={n === cur ? 'hl' : ''}><td>{pretty(n)}</td><td>{num(m.models[n].threshold, 4)}</td><td>{num(t.precision)}</td><td>{num(t.recall)}</td><td>{num(t.f1)}</td><td>{num(t.average_precision)}</td><td>{int(c.tp)}</td><td>{int(c.fp)}</td><td>{int(c.fn)}</td><td>{int(c.tn)}</td></tr>) })}</tbody>
            </table></div>
          </Card>
          {ex.class_weighting_validation && (
            <Card title="Experiment: class weighting (validation set)">
              <div className="table-wrap"><table>
                <thead><tr><th>Model</th><th>Setting</th><th>Precision</th><th>Recall</th><th>F1</th><th>Avg precision</th></tr></thead>
                <tbody>{Object.entries(ex.class_weighting_validation).flatMap(([n, v]) => Object.entries(v).map(([k, b]) => (
                  <tr key={n + k}><td>{pretty(n)}</td><td>{pretty(k)}</td><td>{num(b.precision)}</td><td>{num(b.recall)}</td><td>{num(b.f1)}</td><td>{num(b.average_precision)}</td></tr>)))}</tbody>
              </table></div>
              <p className="note">Each row uses its own validation-tuned threshold. Resampling (e.g. SMOTE) was not applied.</p>
            </Card>
          )}
        </div>
      )
    }}</Gate>
  )
}
