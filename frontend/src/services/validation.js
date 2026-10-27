// Client-side checks mirror the server schema (the server remains the source of truth).
export const FEATURES = ["Time", ...Array.from({ length: 28 }, (_, i) => `V${i + 1}`), "Amount"];
const BOUNDS = { Time: [0, 1e8], Amount: [0, 1e7] };
const NUMBER = /^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$/;

export function validateField(name, raw) {
  const s = String(raw ?? "").trim();
  if (s === "") return "Required.";
  if (!NUMBER.test(s)) return "Enter a finite number.";
  const v = Number(s);
  if (!Number.isFinite(v)) return "Enter a finite number.";
  const [lo, hi] = BOUNDS[name] || [-1000, 1000];
  if (v < lo || v > hi) return `Must be between ${lo} and ${hi}.`;
  return null;
}

export function validateAll(values) {
  const errors = {};
  FEATURES.forEach((f) => {
    const e = validateField(f, values[f]);
    if (e) errors[f] = e;
  });
  return errors;
}

export function toPayload(values) {
  return Object.fromEntries(FEATURES.map((f) => [f, Number(String(values[f]).trim())]));
}
