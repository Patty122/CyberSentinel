import { ChevronLeft, ChevronRight, Search } from "lucide-react";
import { useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Card } from "../components/Cards.jsx";
import StateView from "../components/StateView.jsx";
import { C, axisProps, tooltipStyle } from "../components/chartTheme.js";
import { useApi } from "../hooks/useApi.js";
import { api } from "../services/api.js";
import { fmt, fmtInt, pct } from "../services/format.js";

const SHOW = ["id", "Time", "Amount", "Class", "V1", "V2", "V3", "V4", "V5"];

export default function Explorer() {
  const summary = useApi(api.summary);
  return (
    <div className="page">
      <h1>Data explorer</h1>
      <p className="lead muted">Dataset overview and a bounded, read-only view of rows from the local file.</p>
      <StateView req={summary} label="dataset summary">
        {(s) => (
          <>
            <div className="grid-2">
              <Card title="Overview">
                <dl className="result-list">
                  <dt>Rows × columns</dt><dd>{fmtInt(s.dataset.rows)} × {s.dataset.columns}</dd>
                  <dt>Missing values</dt><dd>{fmtInt(s.dataset.missing_total)}{s.dataset.missing_total === 0 && " (none)"}</dd>
                  <dt>Duplicate rows</dt><dd>{fmtInt(s.dataset.duplicate_rows)}</dd>
                  <dt>Fraud / legitimate</dt><dd>{fmtInt(s.dataset.fraud)} / {fmtInt(s.dataset.legitimate)} ({pct(s.dataset.fraud_percent, 3)})</dd>
                  <dt>Time span</dt><dd>{s.time_range_hours} hours</dd>
                </dl>
                <p className="muted small">{s.note}</p>
              </Card>
              <Card title="Strongest linear correlations with Class" subtitle="Pearson, whole dataset. Exploratory only; not used to select features.">
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart layout="vertical" data={s.top_correlations_with_class} margin={{ left: 8 }}>
                    <CartesianGrid stroke={C.grid} horizontal={false} />
                    <XAxis type="number" domain={[-0.5, 0.5]} {...axisProps} />
                    <YAxis type="category" dataKey="feature" {...axisProps} width={48} />
                    <Tooltip {...tooltipStyle} formatter={(v) => fmt(v, 3)} />
                    <Bar dataKey="correlation" fill={C.violet} radius={4} />
                  </BarChart>
                </ResponsiveContainer>
              </Card>
            </div>
            <Card title="Feature summaries">
              <div className="table-wrap tall"><table>
                <thead><tr><th>Feature</th><th>Mean</th><th>Std</th><th>Min</th><th>25%</th><th>Median</th><th>75%</th><th>Max</th></tr></thead>
                <tbody>{s.feature_statistics.map((f) => (
                  <tr key={f.feature}><td>{f.feature}</td><td>{fmt(f.mean, 3)}</td><td>{fmt(f.std, 3)}</td><td>{fmt(f.min, 3)}</td><td>{fmt(f["25%"], 3)}</td><td>{fmt(f["50%"], 3)}</td><td>{fmt(f["75%"], 3)}</td><td>{fmt(f.max, 3)}</td></tr>
                ))}</tbody>
              </table></div>
            </Card>
          </>
        )}
      </StateView>
      <TransactionTable />
    </div>
  );
}

function TransactionTable() {
  const [f, setF] = useState({ class: "", min_amount: "", max_amount: "", id: "" });
  const [applied, setApplied] = useState(f);
  const [page, setPage] = useState(1);
  const req = useApi(() => api.transactions({ ...applied, page, page_size: 20 }), [applied, page]);
  const upd = (k) => (e) => setF({ ...f, [k]: e.target.value });
  return (
    <Card title="Transactions" subtitle="Anonymised rows from your local copy of the dataset. Page size is capped by the server.">
      <form className="filters" onSubmit={(e) => { e.preventDefault(); setPage(1); setApplied(f); }}>
        <div><label htmlFor="fc">Class</label>
          <select id="fc" value={f.class} onChange={upd("class")}><option value="">All</option><option value="0">Legitimate</option><option value="1">Fraud</option></select></div>
        <div><label htmlFor="fmin">Min amount</label><input id="fmin" inputMode="decimal" value={f.min_amount} onChange={upd("min_amount")} /></div>
        <div><label htmlFor="fmax">Max amount</label><input id="fmax" inputMode="decimal" value={f.max_amount} onChange={upd("max_amount")} /></div>
        <div><label htmlFor="fid">Row id</label><input id="fid" inputMode="numeric" value={f.id} onChange={upd("id")} /></div>
        <button className="btn btn-primary" type="submit"><Search size={14} aria-hidden /> Apply</button>
      </form>
      <StateView req={req} label="transactions">
        {(d) => (
          <>
            <div className="table-wrap"><table>
              <thead><tr>{SHOW.map((c) => <th key={c}>{c}</th>)}</tr></thead>
              <tbody>
                {d.rows.length === 0 && <tr><td colSpan={SHOW.length} className="muted">No rows match these filters.</td></tr>}
                {d.rows.map((r) => (
                  <tr key={r.id} className={r.Class === 1 ? "row-fraud" : ""}>{SHOW.map((c) => <td key={c}>{c === "Class" ? (r.Class ? "Fraud" : "Legit") : r[c]}</td>)}</tr>
                ))}
              </tbody>
            </table></div>
            <div className="pager">
              <button className="btn btn-ghost" disabled={page <= 1} onClick={() => setPage(page - 1)} aria-label="Previous page"><ChevronLeft size={16} /></button>
              <span>Page {fmtInt(d.page)} of {fmtInt(d.pages)} · {fmtInt(d.total)} rows</span>
              <button className="btn btn-ghost" disabled={page >= d.pages} onClick={() => setPage(page + 1)} aria-label="Next page"><ChevronRight size={16} /></button>
            </div>
          </>
        )}
      </StateView>
    </Card>
  );
}
