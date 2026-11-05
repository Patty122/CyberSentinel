<<<<<<< HEAD
import { FlaskConical, Info, Loader2, ScanSearch, Sparkles } from "lucide-react";
=======

import { Info, Loader2, ScanSearch, Sparkles } from "lucide-react";
>>>>>>> 4ae8762 (Update transaction analysis for multi-model predictions)
import { useMemo, useState } from "react";
import { Card } from "../components/Cards.jsx";
import StateView from "../components/StateView.jsx";
import { useApi } from "../hooks/useApi.js";
import { api } from "../services/api.js";
import { fmt } from "../services/format.js";
import {
  FEATURES,
  toPayload,
  validateAll,
  validateField,
} from "../services/validation.js";

const empty = () =>
  Object.fromEntries(FEATURES.map((feature) => [feature, ""]));

export default function Analyze() {
  const models = useApi(api.models);

  const [values, setValues] = useState(empty);
  const [errors, setErrors] = useState({});
  const [busy, setBusy] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState(null);
  const [apiError, setApiError] = useState(null);
  const [sample, setSample] = useState(null);

<<<<<<< HEAD
  const setField = (f, v) => {
    setValues((s) => ({ ...s, [f]: v }));
    setErrors((e) => ({ ...e, [f]: validateField(f, v) }));
=======
  const setField = (feature, value) => {
    setValues((previous) => ({
      ...previous,
      [feature]: value,
    }));

    setErrors((previous) => ({
      ...previous,
      [feature]: validateField(feature, value),
    }));

>>>>>>> 4ae8762 (Update transaction analysis for multi-model predictions)
    setResult(null);
  };

  async function generateRandomData() {
    if (busy || generating) return;
<<<<<<< HEAD
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
=======

    setGenerating(true);
    setApiError(null);
    setResult(null);

    try {
      // Load one real row from the local dataset.
      // The model prediction happens when Analyse is clicked.
      const trueClass = Math.random() < 0.5 ? 0 : 1;
      const row = await api.sample(trueClass);

      setValues(
        Object.fromEntries(
          FEATURES.map((feature) => [
            feature,
            String(row.features[feature]),
          ])
        )
      );

      setErrors({});
      setSample({
        id: row.id,
        label: row.label,
        source: row.source,
      });
    } catch (error) {
      setApiError(error.message);
>>>>>>> 4ae8762 (Update transaction analysis for multi-model predictions)
    } finally {
      setGenerating(false);
    }
  }

  async function submit(event) {
    event.preventDefault();

    const validationErrors = validateAll(values);
    setErrors(validationErrors);
    setApiError(null);
<<<<<<< HEAD
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
=======

    if (Object.keys(validationErrors).length > 0) return;

    setBusy(true);
    setResult(null);

    try {
      const payload = toPayload(values);
      const modelData = models.data;
      const listedModels = modelData?.models;

      // Support either an array of model objects or the
      // backend's object keyed by model name.
      const modelNames = Array.isArray(listedModels)
        ? listedModels
            .filter((item) => item.name !== "dummy")
            .map((item) => item.name)
        : listedModels && typeof listedModels === "object"
          ? Object.keys(listedModels).filter(
              (name) => name !== "dummy"
            )
          : [];

      if (modelNames.length === 0) {
        // Fallback to the backend's selected model.
        const prediction = await api.predict(payload);

        setResult({
          predictions: [prediction],
          disclaimer: prediction.disclaimer,
        });
      } else {
        // Run every available model against the SAME input.
        const responses = await Promise.allSettled(
          modelNames.map((name) => api.predict(payload, name))
        );

        const predictions = responses
          .filter((response) => response.status === "fulfilled")
          .map((response) => response.value);

        const failures = responses.filter(
          (response) => response.status === "rejected"
        );

        if (predictions.length === 0) {
          throw (
            failures[0]?.reason ||
            new Error("No models returned a prediction.")
          );
        }

        setResult({
          predictions,
          disclaimer:
            predictions[0]?.disclaimer ||
            "Model estimates only, not proof of fraud.",
          failedModels: failures.length,
        });
      }
    } catch (error) {
>>>>>>> 4ae8762 (Update transaction analysis for multi-model predictions)
      setResult(null);

      if (error.details) {
        setErrors((previous) => ({
          ...previous,
          ...error.details,
        }));
      }

      setApiError(error.message);
    } finally {
      setBusy(false);
    }
  }

  const errorCount = useMemo(
    () => Object.values(errors).filter(Boolean).length,
    [errors]
  );

  return (
    <div className="page">
      <h1>Transaction analysis</h1>
<<<<<<< HEAD
      <p className="lead muted">Enter one transaction once. CyberSentinel evaluates that same input across the available models and shows legitimate and fraud scores where supported.</p>
=======

      <p className="lead muted">
        Enter one transaction once. CyberSentinel evaluates the
        same input across available models and displays legitimate
        and fraud scores where supported.
      </p>

>>>>>>> 4ae8762 (Update transaction analysis for multi-model predictions)
      <div className="notice" role="note">
        <Info size={16} aria-hidden />
        <span>
          V1 to V28 are anonymised PCA components from the Kaggle
          dataset. Their real-world meaning is not published.
          Do not treat them as card or merchant attributes.
        </span>
      </div>

      <div className="analyze-layout">
        <form
          onSubmit={submit}
          noValidate
          className="card"
          aria-label="Transaction features"
        >
          <div className="form-tools">
            <div>
              <strong>Transaction features</strong>
<<<<<<< HEAD
              <p className="muted small">Generate a sample or enter the 30 values manually.</p>
=======
              <p className="muted small">
                Generate a sample or enter the 30 values manually.
              </p>
>>>>>>> 4ae8762 (Update transaction analysis for multi-model predictions)
            </div>

            <div className="sample-btns">
<<<<<<< HEAD
              <button type="button" className="btn btn-ghost" onClick={generateRandomData} disabled={busy || generating}>
                {generating ? <Loader2 size={14} className="spin" aria-hidden /> : <Sparkles size={14} aria-hidden />}
                {generating ? "Generating..." : "Generate Random Data"}
=======
              <button
                type="button"
                className="btn btn-ghost"
                onClick={generateRandomData}
                disabled={busy || generating}
              >
                {generating ? (
                  <Loader2
                    size={14}
                    className="spin"
                    aria-hidden
                  />
                ) : (
                  <Sparkles size={14} aria-hidden />
                )}
                {generating
                  ? "Generating..."
                  : "Generate Random Data"}
>>>>>>> 4ae8762 (Update transaction analysis for multi-model predictions)
              </button>
            </div>
          </div>

          {sample && (
            <p className="muted small" role="status">
<<<<<<< HEAD
              Loaded dataset row #{sample.id} (reference label: {sample.label ? "fraud" : "legitimate"}). {sample.source}
=======
              Loaded dataset row #{sample.id} (reference label:{" "}
              {sample.label ? "fraud" : "legitimate"}).{" "}
              {sample.source}
>>>>>>> 4ae8762 (Update transaction analysis for multi-model predictions)
            </p>
          )}

          <div className="field-grid">
            {FEATURES.map((feature) => (
              <div
                key={feature}
                className={`field ${
                  errors[feature] ? "has-error" : ""
                }`}
              >
                <label htmlFor={`f-${feature}`}>
                  {feature}
                </label>

                <input
                  id={`f-${feature}`}
                  inputMode="decimal"
                  autoComplete="off"
                  value={values[feature]}
                  onChange={(event) =>
                    setField(feature, event.target.value)
                  }
                  aria-invalid={Boolean(errors[feature])}
                  aria-describedby={
                    errors[feature]
                      ? `e-${feature}`
                      : undefined
                  }
                />

                {errors[feature] && (
                  <span
                    id={`e-${feature}`}
                    className="field-error"
                  >
                    {errors[feature]}
                  </span>
                )}
              </div>
            ))}
          </div>

          <div className="form-actions">
<<<<<<< HEAD
            <button className="btn btn-primary" type="submit" disabled={busy || generating}>
              {busy ? <Loader2 size={16} className="spin" aria-hidden /> : <ScanSearch size={16} aria-hidden />}
              {busy ? "Analysing..." : "Analyse Transaction"}
            </button>
            <button type="button" className="btn btn-ghost" onClick={() => { setValues(empty()); setErrors({}); setResult(null); setSample(null); setApiError(null); }} disabled={busy || generating}>Clear</button>
            {nErrors > 0 && <span className="field-error" role="alert">{nErrors} field{nErrors > 1 ? "s" : ""} need attention.</span>}
=======
            <button
              className="btn btn-primary"
              type="submit"
              disabled={busy || generating}
            >
              {busy ? (
                <Loader2
                  size={16}
                  className="spin"
                  aria-hidden
                />
              ) : (
                <ScanSearch size={16} aria-hidden />
              )}
              {busy ? "Analysing..." : "Analyse Transaction"}
            </button>

            <button
              type="button"
              className="btn btn-ghost"
              disabled={busy || generating}
              onClick={() => {
                setValues(empty());
                setErrors({});
                setResult(null);
                setSample(null);
                setApiError(null);
              }}
            >
              Clear
            </button>

            {errorCount > 0 && (
              <span className="field-error" role="alert">
                {errorCount} field
                {errorCount > 1 ? "s" : ""} need attention.
              </span>
            )}
>>>>>>> 4ae8762 (Update transaction analysis for multi-model predictions)
          </div>

          {apiError && (
            <div className="state state-error" role="alert">
              {apiError}
            </div>
          )}
        </form>

        <Results result={result} sample={sample} />
      </div>
    </div>
  );
}

function Results({ result, sample }) {
  if (!result) {
<<<<<<< HEAD
    return <Card title="Analysis results" className="result-card"><p className="muted">No analysis yet. Generate or enter a transaction, then click Analyse Transaction to see both scores and each model's decision.</p></Card>;
  }

  const predictions = result.predictions || [];
=======
    return (
      <Card title="Analysis results" className="result-card">
        <p className="muted">
          No analysis yet. Generate or enter a transaction, then
          click Analyse Transaction to see the scores and model
          decisions.
        </p>
      </Card>
    );
  }

  const predictions = result.predictions || [];

>>>>>>> 4ae8762 (Update transaction analysis for multi-model predictions)
  return (
    <Card title="Analysis results" className="result-card">
      <div className="model-results">
        {predictions.map((prediction) => {
          const flagged = prediction.label === 1;
<<<<<<< HEAD
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
=======
          const hasProbability =
            prediction.probability != null;

          const fraudProbability = hasProbability
            ? Math.max(
                0,
                Math.min(1, Number(prediction.probability))
              )
            : null;

          const legitimateProbability = hasProbability
            ? 1 - fraudProbability
            : null;

          const fraudPercent =
            fraudProbability === null
              ? null
              : fraudProbability * 100;

          const legitimatePercent =
            legitimateProbability === null
              ? null
              : legitimateProbability * 100;

          return (
            <section
              key={prediction.model}
              className={`model-result ${
                flagged ? "flagged" : "clear"
              }`}
            >
              <div className="verdict" role="status">
                {prediction.model.replace(/_/g, " ")}:{" "}
                {flagged
                  ? "Flagged as likely fraudulent"
                  : "Predicted legitimate"}
              </div>

              {hasProbability ? (
                <>
                  <div className="result-list">
                    <div className="result-score-row">
                      <span>Legitimate score</span>
                      <strong>
                        {fmt(legitimatePercent, 2)}%
                      </strong>
                    </div>

                    <div
                      className="probability-track"
                      role="img"
                      aria-label={`Legitimate score ${legitimatePercent.toFixed(
                        2
                      )}%`}
                    >
                      <div
                        className="probability-fill legitimate-fill"
                        style={{
                          width: `${legitimatePercent}%`,
                        }}
                      />
                    </div>

                    <div className="result-score-row">
                      <span>
                        Fraud probability (uncalibrated)
                      </span>
                      <strong>{fmt(fraudPercent, 2)}%</strong>
                    </div>

                    <div
                      className="probability-track"
                      role="img"
                      aria-label={`Fraud probability ${fraudPercent.toFixed(
                        2
                      )}%`}
                    >
                      <div
                        className="probability-fill fraud-fill"
                        style={{
                          width: `${fraudPercent}%`,
                        }}
                      />
                    </div>
                  </div>

                  <p className="muted small">
                    Decision threshold:{" "}
                    {fmt(prediction.threshold, 4)}
                  </p>
>>>>>>> 4ae8762 (Update transaction analysis for multi-model predictions)
                </>
              ) : (
                <>
                  <dl className="result-list">
<<<<<<< HEAD
                    <dt>Anomaly score</dt><dd>{fmt(prediction.anomaly_score, 4)}</dd>
                    <dt>Decision threshold</dt><dd>{fmt(prediction.threshold, 4)}</dd>
                  </dl>
                  <p className="muted small">This model produces an anomaly score, not a calibrated fraud/legitimate probability.</p>
=======
                    <dt>Anomaly score</dt>
                    <dd>
                      {fmt(prediction.anomaly_score, 4)}
                    </dd>
                    <dt>Decision threshold</dt>
                    <dd>
                      {fmt(prediction.threshold, 4)}
                    </dd>
                  </dl>

                  <p className="muted small">
                    This model produces an anomaly score, not
                    calibrated fraud or legitimate probabilities.
                  </p>
>>>>>>> 4ae8762 (Update transaction analysis for multi-model predictions)
                </>
              )}
            </section>
          );
        })}
      </div>
<<<<<<< HEAD
      {result.failedModels > 0 && <p className="muted small">{result.failedModels} model(s) could not return a result. The successful predictions are shown above.</p>}
      {sample && <p className="muted small">Dataset reference label: <strong>{sample.label ? "fraud" : "legitimate"}</strong>. This is the row's original label, not a forced model output.</p>}
      <p className="small disclaimer">{result.disclaimer}</p>
      <p className="muted small">The legitimate score is calculated as 1 minus the supervised model's fraud probability. These are model estimates, not proof of a transaction's true class.</p>
=======

      {result.failedModels > 0 && (
        <p className="muted small">
          {result.failedModels} model(s) could not return a
          result. Successful predictions are shown above.
        </p>
      )}

      {sample && (
        <p className="muted small">
          Dataset reference label:{" "}
          <strong>
            {sample.label ? "fraud" : "legitimate"}
          </strong>
          . This is the row's original label, not a forced model
          output.
        </p>
      )}

      <p className="small disclaimer">{result.disclaimer}</p>

      <p className="muted small">
        The legitimate score is calculated as 1 minus the
        supervised model's fraud probability. These are model
        estimates, not proof of a transaction's true class.
      </p>
>>>>>>> 4ae8762 (Update transaction analysis for multi-model predictions)
    </Card>
  );
}
