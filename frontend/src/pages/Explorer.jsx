import { useState } from 'react'
import { api } from '../services/api'
import { useApi } from '../hooks/useApi'
import { Card, Gate, Kpi, int, num } from '../components/ui'

const COLS = ['id', 'Time', 'Amount', 'V1', 'V2', 'V3', 'V4', 'V5', 'Class']

export default function Explorer() {
  const summary = useApi(api.summary, [])
  const [f, setF] = useState({ class: '', min_amount: '', max_amount: '' })
  const [applied, setApplied] = useState(f)
  const [page, setPage] = useState(1)
  const params = { page, page_size: 20, ...Object.fromEntries(Object.entries(applied).filter(([, v]) => v !== '')) }
  const tx = useApi(() => api.transactions(params), [page, applied])

  return (
    <div className="stack">
      <Gate state={summary}>{(s) => (<>
        <div className="kpis">
          <Kpi label="Rows" value={int(s.dataset.n_rows)} />
          <Kpi label="Columns" value={s.dataset.n_columns} />
          <Kpi label="Missing values" value={int(s.dataset.n_missing_values)} />
          <Kpi label="Duplicate rows" value={int(s.dataset.n_duplicate_rows)} />
        </div>
        <div className="grid2">
          <Card title="Amount statistics by class">
            <div className="table-wrap"><table>
              <thead><tr><th>Stat</th><th>All</th><th>Legitimate</th><th>Fraud</th></tr></thead>
              <tbody>{['mean', 'std', 'min', '50%', '75%', 'max'].map((k) => (
                <tr key={k}><td>{k}</td><td>{num(s.amount_stats.all[k], 2)}</td><td>{num(s.amount_stats.legitimate[k], 2)}</td><td>{num(s.amount_stats.fraud[k], 2)}</td></tr>))}</tbody>
            </table></div>
          </Card>
          <Card title="Top correlations with Class">
            <div className="table-wrap"><table><thead><tr><th>Feature</th><th>Pearson r</th></tr></thead>
              <tbody>{Object.entries(s.top_correlations_with_class).map(([k, v]) => <tr key={k}><td>{k}</td><td>{num(v)}</td></tr>)}</tbody></table></div>
            <p className="note">V1–V28 are anonymised; correlation does not imply meaning.</p>
          </Card>
        </div>
      </>)}</Gate>

      <Card title="Transactions (bounded, paginated)">
        <form className="filters" onSubmit={(e) => { e.preventDefault(); setPage(1); setApplied(f) }}>
          <label className="field">Class
            <select value={f.class} onChange={(e) => setF({ ...f, class: e.target.value })}>
              <option value="">Any</option><option value="0">Legitimate</option><option value="1">Fraud</option></select></label>
          <label className="field">Min amount<input inputMode="decimal" value={f.min_amount} onChange={(e) => setF({ ...f, min_amount: e.target.value })} /></label>
          <label className="field">Max amount<input inputMode="decimal" value={f.max_amount} onChange={(e) => setF({ ...f, max_amount: e.target.value })} /></label>
          <button className="btn" type="submit">Apply</button>
        </form>
        <Gate state={tx}>{(d) => (<>
          <div className="table-wrap"><table>
            <thead><tr>{COLS.map((c) => <th key={c}>{c}</th>)}</tr></thead>
            <tbody>{d.rows.map((r) => <tr key={r.id}>{COLS.map((c) => <td key={c}>{c === 'id' || c === 'Class' ? r[c] : num(r[c], 3)}</td>)}</tr>)}</tbody>
          </table></div>
          <div className="row pager">
            <button className="btn ghost" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</button>
            <span>Page {d.page} of {Math.max(1, Math.ceil(d.total / d.page_size))} · {int(d.total)} rows</span>
            <button className="btn ghost" disabled={page * d.page_size >= d.total} onClick={() => setPage(page + 1)}>Next</button>
          </div>
        </>)}</Gate>
      </Card>
    </div>
  )
}
