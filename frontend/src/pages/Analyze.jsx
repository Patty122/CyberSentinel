import { useMemo, useState } from "react";
import { Info, Loader2, ScanSearch, Sparkles } from "lucide-react";
import { Card } from "../components/Cards.jsx";
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

  const setField = (feature, value) => {
    setValues((previous) => ({
      ...previous,
      [feature]: value,
    }));

    setErrors((previous) => ({
      ...previous,
      [feature]: validateField(feature, value),
    }));

    setResult(null);
  };

  async function generateRandomData() {
    if (busy || generating) return;

    setGenerating(true);
    setApiError(null);
    setResult(null);

    try {
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
    } finally {
      setGenerating(false);
    }
  }

  async function submit(event) {
    event.preventDefault();

    const validationErrors = validateAll(values);
    setErrors(validationErrors);
    setApiError(null);

    if (Object.keys(validationErrors).length > 0) return;

    setBusy(true);
    setResult(null);

    try {
      const payload = toPayload(values);
      const modelData = models.data;
      const listedModels = modelData?.models;

      const modelNames = Array.isArray(listedModels)
        ? listedModels
            .filter((item) => item?.name && item.name !== "dummy")
            .map((item) => item.name)
        : listedModels && typeof listedModels === "object"
          ? Object.keys(listedModels).filter(
              (name) => name !== "dummy"
            )
          : [];

      if (modelNames.length === 0) {
        const prediction = await api.predict(payload);

        setResult({
          predictions: [prediction],
          disclaimer: prediction.disclaimer,
          failedModels: 0,
        });
      } else {
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

  function clearForm() {
    setValues(empty());
    setErrors({});
    setResult(null);
    setSample(null);
    setApiError(null);
  }

  return (
    <div className="page">
      <h1>Transaction analysis</h1>

      <p className="lead muted">
        Enter one transaction once. CyberSentinel evaluates the same input
        across available models and displays legitimate and fraud scores
        where supported.
      </p>

      <div className="notice" role="note">
        <Info size={16} aria-hidden="true" />
        <span>
          V1 to V28 are anonymised PCA components from the Kaggle dataset.
          Their real-world meaning is not published. Do not treat them as
          card or merchant attributes.
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
              <p className="muted small">
                Generate a sample or enter the 30 values manually.
              </p>
            </div>

            <div className="sample-btns">
              <button
                type="button"
                className="btn btn-ghost"
                onClick={generateRandomData}
                disabled={busy || generating}
              >
                {generating ? (
                  <Loader2 size={14} className="spin" aria-hidden="true" />
                ) : (
                  <Sparkles size={14} aria-hidden="true" />
                )}
                {generating ? "Generating..." : "Generate Random Data"}
              </button>
            </div>
          </div>

          {sample && (
            <p className="muted small" role="status">
              Loaded dataset row #{sample.id} (reference label:{" "}
              {sample.label ? "fraud" : "legitimate"}). {sample.source}
            </p>
          )}

          <div className="field-grid">
            {FEATURES.map((feature) => (
              <div
                key={feature}
                className={`field ${errors[feature] ? "has-error" : ""}`}
              >
                <label htmlFor={`f-${feature}`}>{feature}</label>

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
                    errors[feature] ? `e-${feature}` : undefined
                  }
                />

                {errors[feature] && (
                  <span id={`e-${feature}`} className="field-error">
                    {errors[feature]}
                  </span>
                )}
              </div>
            ))}
          </div>

          <div className="form-actions">
            <button
              className="btn btn-primary"
              type="submit"
              disabled={busy || generating}
            >
              {busy ? (
                <Loader2 size={16} className="spin" aria-hidden="true" />
              ) : (
                <ScanSearch size={16} aria-hidden="true" />
              )}
              {busy ? "Analysing..." : "Analyse Transaction"}
            </button>

            <button
              type="button"
              className="btn btn-ghost"
              disabled={busy || generating}
              onClick={clearForm}
            >
              Clear
            </button>

            {errorCount > 0 && (
              <span className="field-error" role="alert">
                {errorCount} field{errorCount > 1 ? "s" : ""} need attention.
              </span>
            )}
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
    return (
      <Card title="Analysis results" className="result-card">
        <p className="muted">
          No analysis yet. Generate or enter a transaction, then click
          Analyse Transaction to see the scores and model decisions.
        </p>
      </Card>
    );
  }

  const predictions = result.predictions || [];

  return (
    <Card title="Analysis results" className="result-card">
      <div className="model-results">
        {predictions.map((prediction, index) => {
          const flagged = prediction.label === 1;

          const numericProbability =
            prediction.probability != null
              ? Number(prediction.probability)
              : null;

          const fraudProbability =
            numericProbability !== null &&
            Number.isFinite(numericProbability)
              ? Math.max(0, Math.min(1, numericProbability))
              : null;

          const legitimateProbability =
            fraudProbability === null
              ? null
              : 1 - fraudProbability;

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
              key={prediction.model || `model-${index}`}
              className={`model-result ${flagged ? "flagged" : "clear"}`}
            >
              <div className="verdict" role="status">
                {(prediction.model || "Model").replace(/_/g, " ")}:{" "}
                {flagged
                  ? "Flagged as likely fraudulent"
                  : "Predicted legitimate"}
              </div>

              {fraudProbability !== null ? (
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
                      aria-label={`Legitimate score ${legitimatePercent.toFixed(2)}%`}
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
                      aria-label={`Fraud probability ${fraudPercent.toFixed(2)}%`}
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
                </>
              ) : (
                <>
                  <dl className="result-list">
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
                    This model produces an anomaly score, not calibrated
                    fraud or legitimate probabilities.
                  </p>
                </>
              )}
            </section>
          );
        })}
      </div>

      {result.failedModels > 0 && (
        <p className="muted small">
          {result.failedModels} model(s) could not return a result.
          Successful predictions are shown above.
        </p>
      )}

      {sample && (
        <p className="muted small">
          Dataset reference label:{" "}
          <strong>
            {sample.label ? "fraud" : "legitimate"}
          </strong>
          . This is the row's original label, not a forced model output.
        </p>
      )}

      <p className="small disclaimer">
        {result.disclaimer}
      </p>

      <p className="muted small">
        The legitimate score is calculated as 1 minus the supervised
        model's fraud probability. These are model estimates, not proof
        of a transaction's true class.
      </p>
    </Card>
  );
}