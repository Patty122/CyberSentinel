const BASE = import.meta.env.VITE_API_URL || ''
const TIMEOUT_MS = 15000

export class ApiError extends Error {
  constructor(message, fields) {
    super(message)
    this.fields = fields || null
  }
}

async function request(path, options = {}) {
  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), TIMEOUT_MS)
  try {
    const res = await fetch(`${BASE}${path}`, {
      ...options,
      signal: ctrl.signal,
      headers: { 'Content-Type': 'application/json' },
    })
    let body = null
    try { body = await res.json() } catch { /* non-JSON */ }
    if (!res.ok || !body || body.status === 'error') {
      throw new ApiError(body?.error?.message || `Request failed (${res.status})`, body?.error?.fields)
    }
    return body // {status: 'ok' | 'unavailable', data, message?}
  } catch (e) {
    if (e instanceof ApiError) throw e
    throw new ApiError(e.name === 'AbortError' ? 'Request timed out.' : 'Cannot reach the API. Is the backend running?')
  } finally {
    clearTimeout(timer)
  }
}

export const api = {
  health: () => request('/api/health'),
  summary: () => request('/api/summary'),
  models: () => request('/api/models'),
  metrics: () => request('/api/metrics'),
  predict: (features, model) => request('/api/predict', { method: 'POST', body: JSON.stringify({ features, model }) }),
  transactions: (params) => request(`/api/transactions?${new URLSearchParams(params)}`),
}
