import { FlaskConical, Info, Loader2, ScanSearch } from "lucide-react";
import { useMemo, useState } from "react";
import { Card } from "../components/Cards.jsx";
import StateView from "../components/StateView.jsx";
import { useApi } from "../hooks/useApi.js";
import { api } from "../services/api.js";
import { fmt } from "../services/format.js";
import { FEATURES, toPayload, validateAll, validateField } from "../services/validation.js";

const empty = () => Object.fromEntries(FEATURES.map((f) => [f, ""]));

export default function Analyze() {
  const models = useApi(api.models);
  const [values, setValues] = useState(empty);
  const [errors, setErrors] = useState({});
  const [model, setModel] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [apiError, setApiError] = useState(null);
  const [sample, setSample] = useState(null);

  const setField = (f, v) => {
    setValues((s) => ({ ...s, [f]: v }));
    setErrors((e) => ({ ...e, [f]: validateField(f, v) }));
  };

  async function loadSample(cls) {
    setApiError(null);
    try {
      const s = await api.sample(cls);
      setValues(Object.fromEntries(FEATURES.map((f) => [f, String(s.features[f])])));
      setErrors({});
      setSample({ id: s.id, label: s.label, source: s.source });
      setResult(null);
    } catch (e) {
      setApiError(e.message);
    }
  }

  async function submit(e) {
    e.preventDefault();
    const errs = validateAll(values);
    setErrors(errs);
    setApiError(null);
    if (Object.keys(errs).length) return;
    setBusy(true);
    try {
      setResult(await api.predict(toPayload(values), model || undefined));
    } catch (err) {
      setResult(null);
      if (err.details) setErrors((prev) => ({ ...prev, ...err.details }));
      setApiError(err.message);
    } finally {
      setBusy(false);
    }
  }

  const nErrors = useMemo(() => Object.values(errors).filter(Boolean).length, [errors]);

  return (
    <div className="page">
      <h1>Transaction analysis</h1>
      <p className="lead muted">Enter the 30 features of one transaction and the saved model returns an estimate.</p>
      <div className="notice" role="note">
        <Info size={16} aria-hidden />
        <span>V1 to V28 are anonymised PCA components from the Kaggle dataset; their real-world meaning is not published. Do not treat them as card or merchant attributes.</span>
      </div>

      <div className="analyze-layout">
        <form onSubmit={submit} noValidate className="card" aria-label="Transaction features">
          <div className="form-tools">
            <div>
              <label htmlFor="model">Model</label>
              <StateView req={models} label="models">
                {(m) => (
                  <select id="model" value={model} onChange={(e) => setModel(e.target.value)}>
                    <option value="">Selected model ({m.models.find((x) => x.selected)?.label})</option>
                    {m.models.filter((x) => x.name !== "dummy").map((x) => <option key={x.name} value={x.name}>{x.label}</option>)}
                  </select>
                )}
              </StateView>
            </div>
            <div className="sample-btns">
              <button type="button" className="btn btn-ghost" onClick={() => loadSample(0)}><FlaskConical size={14} aria-hidden /> Load real legitimate row</button>
              <button type="button" className="btn btn-ghost" onClick={() => loadSample(1)}><FlaskConical size={14} aria-hidden /> Load real fraud row</button>
            </div>
          </div>
          {sample && (
            <p className="muted small" role="status">
              Loaded dataset row #{sample.id} (true label: {sample.label ? "fraud" : "legitimate"}). {sample.source}
            </p>
          )}
          <div className="field-grid">
            {FEATURES.map((f) => (
              <div key={f} className={`field ${errors[f] ? "has-error" : ""}`}>
                <label htmlFor={`f-${f}`}>{f}</label>
                <input
                  id={`f-${f}`} inputMode="decimal" autoComplete="off" value={values[f]}
                  onChange={(e) => setField(f, e.target.value)}
                  aria-invalid={Boolean(errors[f])} aria-describedby={errors[f] ? `e-${f}` : undefined}
                />
                {errors[f] && <span id={`e-${f}`} className="field-error">{errors[f]}</span>}
              </div>
            ))}
          </div>
          <div className="form-actions">
            <button className="btn btn-primary" type="submit" disabled={busy}>
              {busy ? <Loader2 size={16} className="spin" aria-hidden /> : <ScanSearch size={16} aria-hidden />} Analyse transaction
            </button>
            <button type="button" className="btn btn-ghost" onClick={() => { setValues(empty()); setErrors({}); setResult(null); setSample(null); setApiError(null); }}>Clear</button>
            {nErrors > 0 && <span className="field-error" role="alert">{nErrors} field{nErrors > 1 ? "s" : ""} need attention.</span>}
          </div>
          {apiError && <div className="state state-error" role="alert">{apiError}</div>}
        </form>

        <Result result={result} sample={sample} />
      </div>
    </div>
  );
}

function Result({ result, sample }) {
  if (!result) return <Card title="Result" className="result-card"><p className="muted">No analysis yet. Submit a transaction to see the model's estimate.</p></Card>;
  const flagged = result.label === 1;
  const isProb = result.probability != null;
  const score = isProb ? result.probability : result.anomaly_score;
  const gauge = isProb ? Math.min(100, score * 100) : null;
  return (
    <Card title="Result" className={`result-card ${flagged ? "flagged" : "clear"}`}>
      <div className="verdict" role="status">{flagged ? "Flagged as likely fraudulent" : "Predicted legitimate"}</div>
      <dl className="result-list">
        <dt>Model</dt><dd>{result.model.replace(/_/g, " ")}</dd>
        <dt>{isProb ? "Fraud probability (uncalibrated)" : "Anomaly score"}</dt><dd>{fmt(score, isProb ? 4 : 4)}</dd>
        <dt>Decision threshold</dt><dd>{fmt(result.threshold, 4)}</dd>
      </dl>
      {isProb && (
        <div className="gauge" aria-hidden>
          <div className="gauge-fill" style={{ width: `${gauge}%` }} />
          <div className="gauge-mark" style={{ left: `${Math.min(100, result.threshold * 100)}%` }} />
        </div>
      )}
      {!isProb && <p className="muted small">Isolation Forest is unsupervised: its score is an anomaly measure, not a fraud probability.</p>}
      {sample && <p className="muted small">For reference, the loaded dataset row's true label is <strong>{sample.label ? "fraud" : "legitimate"}</strong>.</p>}
      <p className="small disclaimer">{result.disclaimer}</p>
    </Card>
  );
}
