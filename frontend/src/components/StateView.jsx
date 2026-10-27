import { AlertTriangle, Database, Loader2, RefreshCw } from "lucide-react";

// Renders loading, error, "unavailable" (404) or the children(data). Never substitutes fake data.
export default function StateView({ req, children, label = "data" }) {
  if (req.loading) {
    return (
      <div className="state" role="status" aria-live="polite">
        <Loader2 className="spin" size={18} aria-hidden /> Loading {label}…
      </div>
    );
  }
  if (req.error) {
    const missing = req.error.status === 404 || req.error.status === 503;
    const Icon = missing ? Database : AlertTriangle;
    return (
      <div className={`state ${missing ? "state-empty" : "state-error"}`} role={missing ? "status" : "alert"}>
        <Icon size={18} aria-hidden />
        <div>
          <strong>{missing ? `${label} unavailable` : `Could not load ${label}`}</strong>
          <p>{req.error.message}</p>
          <button className="btn btn-ghost" onClick={req.reload}>
            <RefreshCw size={14} aria-hidden /> Retry
          </button>
        </div>
      </div>
    );
  }
  if (!req.data) return <div className="state state-empty">No {label} to show.</div>;
  return children(req.data);
}
