// Thin client for the Flask API. All responses use {status, data} / {status, error}.
const BASE = (import.meta.env.VITE_API_URL || "/api").replace(/\/$/, "");
const TIMEOUT_MS = 20000;

export class ApiError extends Error {
  constructor(message, { status, code, details } = {}) {
    super(message);
    this.status = status;
    this.code = code;
    this.details = details;
  }
}

async function request(path, options = {}) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS);
  try {
    const res = await fetch(`${BASE}${path}`, { ...options, signal: ctrl.signal });
    let body = null;
    try {
      body = await res.json();
    } catch {
      /* non-JSON response */
    }
    if (!res.ok || !body || body.status !== "ok") {
      const e = body?.error;
      throw new ApiError(e?.message || `Request failed (${res.status})`, { status: res.status, code: e?.code, details: e?.details });
    }
    return body.data;
  } catch (err) {
    if (err instanceof ApiError) throw err;
    if (err.name === "AbortError") throw new ApiError("The server took too long to respond.", { code: "timeout" });
    throw new ApiError("Cannot reach the API. Is the Flask backend running on port 5000?", { code: "network" });
  } finally {
    clearTimeout(timer);
  }
}

const qs = (params) => {
  const p = new URLSearchParams();
  Object.entries(params || {}).forEach(([k, v]) => v !== "" && v != null && p.set(k, v));
  const s = p.toString();
  return s ? `?${s}` : "";
};

export const api = {
  health: () => request("/health"),
  summary: () => request("/summary"),
  models: () => request("/models"),
  metrics: () => request("/metrics"),
  transactions: (params) => request(`/transactions${qs(params)}`),
  sample: (cls) => request(`/transactions/sample${qs({ class: cls })}`),
  predict: (features, model) =>
    request("/predict", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ features, model }) }),
};
