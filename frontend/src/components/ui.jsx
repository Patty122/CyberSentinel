import { AlertTriangle, Database, Loader2 } from 'lucide-react'

export const pct = (v, d = 1) => (v == null ? '—' : `${(v * 100).toFixed(d)}%`)
export const num = (v, d = 3) => (v == null ? '—' : Number(v).toFixed(d))
export const int = (v) => (v == null ? '—' : Number(v).toLocaleString())
export const pretty = (n) => n.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())

export function Card({ title, children, className = '', aside }) {
  return (
    <section className={`card ${className}`}>
      {title && <header className="card-head"><h3>{title}</h3>{aside}</header>}
      {children}
    </section>
  )
}

export function Kpi({ label, value, hint, tone }) {
  return (
    <div className={`kpi ${tone || ''}`}>
      <span className="kpi-label">{label}</span>
      <strong className="kpi-value">{value}</strong>
      {hint && <span className="kpi-hint">{hint}</span>}
    </div>
  )
}

/** Handles loading / error / unavailable states uniformly. */
export function Gate({ state, children }) {
  if (state.loading) return <div className="state" role="status"><Loader2 className="spin" size={18} /> Loading…</div>
  if (state.error) return <div className="state err" role="alert"><AlertTriangle size={18} /> {state.error}</div>
  if (state.unavailable || state.data == null)
    return <div className="state"><Database size={18} /> {state.unavailable || 'No data available.'}</div>
  return children(state.data)
}

export function ConfusionMatrix({ cm }) {
  const cells = [
    ['True negative', cm.tn, 'ok'], ['False positive', cm.fp, 'bad'],
    ['False negative', cm.fn, 'bad'], ['True positive', cm.tp, 'ok'],
  ]
  return (
    <div className="cm" role="table" aria-label="Confusion matrix">
      <div className="cm-axis" />
      <div className="cm-axis">Predicted legitimate</div>
      <div className="cm-axis">Predicted fraud</div>
      <div className="cm-axis">Actual legitimate</div>
      <div className={`cm-cell ${cells[0][2]}`}><b>{int(cells[0][1])}</b><span>{cells[0][0]}</span></div>
      <div className={`cm-cell ${cells[1][2]}`}><b>{int(cells[1][1])}</b><span>{cells[1][0]}</span></div>
      <div className="cm-axis">Actual fraud</div>
      <div className={`cm-cell ${cells[2][2]}`}><b>{int(cells[2][1])}</b><span>{cells[2][0]}</span></div>
      <div className={`cm-cell ${cells[3][2]}`}><b>{int(cells[3][1])}</b><span>{cells[3][0]}</span></div>
    </div>
  )
}

export const chartTheme = {
  grid: '#1e3a52', axis: '#7f9bb3', cyan: '#22d3ee', rose: '#fb7185', amber: '#fbbf24', teal: '#2dd4bf',
  tooltip: { background: '#0b1b2b', border: '1px solid #1e3a52', borderRadius: 8, color: '#e6f1fa' },
}
export const MODEL_COLORS = { logistic_regression: '#22d3ee', random_forest: '#fbbf24', isolation_forest: '#fb7185' }
