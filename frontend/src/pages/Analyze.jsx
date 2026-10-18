import { useState } from 'react'
import { Dices, ShieldAlert, ShieldCheck } from 'lucide-react'
import { api } from '../services/api'
import { Card, pretty, num } from '../components/ui'

const FEATURES = ['Time', ...Array.from({ length: 28 }, (_, i) => `V${i + 1}`), 'Amount']
const empty = () => Object.fromEntries(FEATURES.map((f) => [f, '']))
const MODELS = ['', 'logistic_regression', 'random_forest', 'isolation_forest']

export default function Analyze() {
  const [vals, setVals] = useState(empty())
  const [model, setModel] = useState('')
  const [errors, setErrors] = useState({})
  const [result, setResult] = useState(null)
  const [msg, setMsg] = useState(null)
  const [sample, setSample] = useState(null)
  const [busy, setBusy] = useState(false)

  function validate() {
    const e = {}
    for (const f of FEATURES) {
      const v = vals[f].trim()
      if (v === '') e[f] = 'Required'
      else if (!Number.isFinite(Number(v))) e[f] = 'Must be a finite number'
    }
    return e
  }

  async function submit(ev) {
    ev.preventDefault()
    setMsg(null); setResult(null)
    const e = validate()
    setErrors(e)
    if (Object.keys(e).length) { setMsg({ err: 'Please fix the highlighted fields.' }); return }
    setBusy(true)
    try {
      const features = Object.fromEntries(FEATURES.map((f) => [f, Number(vals[f])]))
      const r = await api.predict(features, model || undefined)
      setResult(r.data)
    } catch (x) {
      setErrors(x.fields || {})
      setMsg({ err: x.message })
    } finally { setBusy(false) }
  }

  async function loadSample() {
    setMsg(null); setBusy(true)
    try {
      const first = await api.transactions({ page: 1, page_size: 1 })
      if (first.status === 'unavailable') { setMsg({ err: first.message }); return }
      const page = 1 + Math.floor(Math.random() * first.data.total)
      const r = await api.transactions({ page, page_size: 1 })
      const row = r.data.rows[0]
      setVals(Object.fromEntries(FEATURES.map((f) => [f, String(row[f])])))
      setSample({ id: row.id, cls: row.Class })
      setErrors({}); setResult(null)
    } catch (x) { setMsg({ err: x.message }) } finally { setBusy(false) }
  }

  const isAnom = result && result.anomaly_score !== undefined
  return (
    <div className="stack">
      <Card title="Transaction analysis"
        aside={<button type="button" className="btn ghost" onClick={loadSample} disabled={busy}><Dices size={16} /> Load real sample row</button>}>
        <p className="note">
          Features <code>V1–V28</code> are anonymised PCA-style components from the public dataset; their real-world meaning is not available,
          so none is implied. Enter values manually, or load a genuine row from your local copy of the dataset.
        </p>
        {sample && <p className="banner">Loaded dataset row #{sample.id} (true label: {sample.cls === 1 ? 'fraud' : 'legitimate'}). This is a real record from your local CSV, shown for demonstration only.</p>}
        <form onSubmit={submit} noValidate>
          <label className="field wide">Model
            <select value={model} onChange={(e) => setModel(e.target.value)}>
              {MODELS.map((m) => <option key={m} value={m}>{m ? pretty(m) : 'Default (best on validation)'}</option>)}
            </select>
          </label>
          <div className="fields">
            {FEATURES.map((f) => (
              <label key={f} className={`field ${errors[f] ? 'invalid' : ''}`}>{f}
                <input inputMode="decimal" value={vals[f]} aria-invalid={!!errors[f]} aria-describedby={errors[f] ? `e-${f}` : undefined}
                  onChange={(e) => setVals({ ...vals, [f]: e.target.value })} />
                {errors[f] && <span id={`e-${f}`} className="field-err">{errors[f]}</span>}
              </label>
            ))}
          </div>
          {msg?.err && <div className="state err" role="alert">{msg.err}</div>}
          <div className="row">
            <button className="btn" type="submit" disabled={busy}>{busy ? 'Working…' : 'Analyse transaction'}</button>
            <button className="btn ghost" type="button" onClick={() => { setVals(empty()); setErrors({}); setResult(null); setSample(null) }}>Clear</button>
          </div>
        </form>
      </Card>

      {result && (
        <Card title="Result">
          <div className={`verdict ${result.prediction ? 'bad' : 'ok'}`} role="status">
            {result.prediction ? <ShieldAlert size={28} /> : <ShieldCheck size={28} />}
            <div>
              <strong>{isAnom ? (result.is_anomaly ? 'Flagged as anomalous' : 'Not flagged') : (result.prediction ? 'Predicted fraud' : 'Predicted legitimate')}</strong>
              <span>Model: {pretty(result.model)}</span>
            </div>
          </div>
          <dl className="dl">
            {result.fraud_probability != null && <><dt>Fraud probability (uncalibrated)</dt><dd>{num(result.fraud_probability, 4)}</dd></>}
            {isAnom && <><dt>Anomaly score (not a probability)</dt><dd>{num(result.anomaly_score, 4)}</dd></>}
            <dt>Decision threshold</dt><dd>{num(result.threshold, 4)}</dd>
          </dl>
          <p className="note">This is a model estimate, not proof of fraud. Scores are not calibrated probabilities, and false positives and false negatives are both expected.</p>
        </Card>
      )}
    </div>
  )
}
