import { FlaskConical, Info, Loader2, ScanSearch, Sparkles } from "lucide-react";
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
  const [busy, setBusy] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState(null);
  const [apiError, setApiError] = useState(null);
  const [sample, setSample] = useState(null);

  const setField = (f, v) => {
    setValues((s) => ({ ...s, [f]: v }));
    setErrors((e) => ({ ...e, [f]: validateField(f, v) }));
    setResult(null);
  };

  async function generateRandomData() {
    if (busy || generating) return;
    setGenerating(true);
    setApiError(null);
    setResult(null);
    try {
      // Fill the form with one real dataset row. The model's prediction is still
      // calculated separately when the user clicks Analyse transaction.
      const trueClass = Math.random() < 0.5 ? 0 : 1;
      const s = await api.sample(trueClass);
      setValues(Object.fromEntries(FEATURES.map((f) => [f, String(s.features[f])])));
      setErrors({});
      setSample({ id: s.id, label: s.label, source: s.source });
    } catch (e) {
      setApiError(e.message);
    } finally {
      setGenerating(false);
    }
  }

  async function submit(e) {
    e.preventDefault();
    const errs = validateAll(values);
    setErrors(errs);
    setApiError(null);
    if (Object.keys(errs).length) return;

    setBusy(true);
    setResult(null);
    try {
      const payload = toPayload(values);
      const modelData = models.data;
      const listed = modelData?.models;
      const modelNames = Array.isArray(listed)
        ? listed.filter((m) => m.name !== "dummy").map((m) => m.name)
        : listed && typeof listed === "object"
          ? Object.keys(listed).filter((name) => name !== "dummy")
          : [];

      if (!modelNames.length) {
        // Fallback to the backend's selected model if the model list is unavailable.
        const single = await api.predict(payload);
        setResult({ predictions: [single], disclaimer: single.disclaimer });
      } else {
        const settled = await Promise.allSettled(
          modelNames.map((name) => api.predict(payload, name))
        );
        const predictions = settled
          .filter((item) => item.status === "fulfilled")
          .map((item) => item.value);
        const failures = settled.filter((item) => item.status === "rejected");
        if (!predictions.length) {
          throw failures[0]?.reason || new Error("No models returned a prediction.");
        }
        setResult({
          predictions,
          disclaimer: predictions[0]?.disclaimer || "Model estimates only, not proof of fraud.",
          failedModels: failures.length,
        });
      }
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
      <p className="lead muted">Enter one transaction once. CyberSentinel evaluates that same input across the available models and shows legitimate and fraud scores where supported.</p>
      <div className="notice" role="note">
        <Info size={16} aria-hidden />
        <span>V1 to V28 are anonymised PCA components from the Kaggle dataset; their real-world meaning is not published. Do not treat them as card or merchant attributes.</span>
      </div>

      <div className="analyze-layout">
        <form onSubmit={submit} noValidate className="card" aria-label="Transaction features">
          <div className="form-tools">
            <div>
              <strong>Transaction features</strong>
              <p className="muted small">Generate a sample or enter the 30 values manually.</p>
            </div>
            <div className="sample-btns">
              <button type="button" className="btn btn-ghost" onClick={generateRandomData} disabled={busy || generating}>
                {generating ? <Loader2 size={14} className="spin" aria-hidden /> : <Sparkles size={14} aria-hidden />}
                {generating ? "Generating..." : "Generate Random Data"}
              </button>
            </div>
          </div>
          {sample && (
            <p className="muted small" role="status">
              Loaded dataset row #{sample.id} (reference label: {sample.label ? "fraud" : "legitimate"}). {sample.source}
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
            <button className="btn btn-primary" type="submit" disabled={busy || generating}>
              {busy ? <Loader2 size={16} className="spin" aria-hidden /> : <ScanSearch size={16} aria-hidden />}
              {busy ? "Analysing..." : "Analyse Transaction"}
            </button>
            <button type="button" className="btn btn-ghost" onClick={() => { setValues(empty()); setErrors({}); setResult(null); setSample(null); setApiError(null); }} disabled={busy || generating}>Clear</button>
            {nErrors > 0 && <span className="field-error" role="alert">{nErrors} field{nErrors > 1 ? "s" : ""} need attention.</span>}
          </div>
          {apiError && <div className="state state-error" role="alert">{apiError}</div>}
        </form>

        <Results result={result} sample={sample} />
      </div>
    </div>
  );
}

function Results({ result, sample }) {
  if (!result) {
    return <Card title="Analysis results" className="result-card"><p className="muted">No analysis yet. Generate or enter a transaction, then click Analyse Transaction to see both scores and each model's decision.</p></Card>;
  }

  const predictions = result.predictions || [];
  return (
    <Card title="Analysis results" className="result-card">
      <div className="model-results">
        {predictions.map((prediction) => {
          const flagged = prediction.label === 1;
          const isProbability = prediction.probability != null;
          const fraudProbability = isProbability ? prediction.probability : null;
          const legitimateProbability = isProbability ? 1 - fraudProbability : null;
          const fraudPercent = isProbability ? Math.max(0, Math.min(100, fraudProbability * 100)) : null;
          const legitimatePercent = isProbability ? Math.max(0, Math.min(100, legitimateProbability * 100)) : null;

          return (
            <section key={prediction.model} className={`model-result ${flagged ? "flagged" : "clear"}`}>
              <div className="verdict" role="status">
                {prediction.model.replace(/_/g, " ")}: {flagged ? "Flagged as likely fraudulent" : "Predicted legitimate"}
              </div>
              {isProbability ? (
                <>
                  <div className="result-list">
                    <div className="result-score-row">
                      <span>Legitimate score</span><strong>{fmt(legitimatePercent, 2)}%</strong>
                    </div>
                    <div className="probability-track" aria-label={`Legitimate score ${legitimatePercent.toFixed(2)} percent`}>
                      <div className="probability-fill legitimate-fill" style={{ width: `${legitimatePercent}%` }} />
                    </div>
                    <div className="result-score-row">
                      <span>Fraud probability (uncalibrated)</span><strong>{fmt(fraudPercent, 2)}%</strong>
                    </div>
                    <div className="probability-track" aria-label={`Fraud probability ${fraudPercent.toFixed(2)} percent`}>
                      <div className="probability-fill fraud-fill" style={{ width: `${fraudPercent}%` }} />
                    </div>
                  </div>
                  <p className="muted small">Decision threshold: {fmt(prediction.threshold, 4)}</p>
                </>
              ) : (
                <>
                  <dl className="result-list">
                    <dt>Anomaly score</dt><dd>{fmt(prediction.anomaly_score, 4)}</dd>
                    <dt>Decision threshold</dt><dd>{fmt(prediction.threshold, 4)}</dd>
                  </dl>
                  <p className="muted small">This model produces an anomaly score, not a calibrated fraud/legitimate probability.</p>
                </>
              )}
            </section>
          );
        })}
      </div>
      {result.failedModels > 0 && <p className="muted small">{result.failedModels} model(s) could not return a result. The successful predictions are shown above.</p>}
      {sample && <p className="muted small">Dataset reference label: <strong>{sample.label ? "fraud" : "legitimate"}</strong>. This is the row's original label, not a forced model output.</p>}
      <p className="small disclaimer">{result.disclaimer}</p>
      <p className="muted small">The legitimate score is calculated as 1 minus the supervised model's fraud probability. These are model estimates, not proof of a transaction's true class.</p>
    </Card>
  );
}
