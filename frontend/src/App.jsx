import { BarChart3, Database, GitCompare, ScanSearch, Shield } from "lucide-react";
import { useState } from "react";
import { useApi } from "./hooks/useApi.js";
import { api } from "./services/api.js";
import Analyze from "./pages/Analyze.jsx";
import Compare from "./pages/Compare.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Explorer from "./pages/Explorer.jsx";

const PAGES = [
  { id: "dashboard", label: "Dashboard", icon: BarChart3, el: <Dashboard /> },
  { id: "analyze", label: "Transaction analysis", icon: ScanSearch, el: <Analyze /> },
  { id: "compare", label: "Model comparison", icon: GitCompare, el: <Compare /> },
  { id: "explorer", label: "Data explorer", icon: Database, el: <Explorer /> },
];

export default function App() {
  const [page, setPage] = useState(() => PAGES.find((p) => p.id === window.location.hash.slice(1))?.id || "dashboard");
  const health = useApi(api.health);
  const go = (id) => { setPage(id); window.location.hash = id; };
  const cur = PAGES.find((p) => p.id === page);
  const up = health.data?.models_loaded;
  return (
    <div className="shell">
      <a className="skip" href="#main">Skip to content</a>
      <aside className="side">
        <div className="brand"><Shield size={22} aria-hidden /> <span>CyberSentinel</span></div>
        <nav aria-label="Primary">
          {PAGES.map((p) => (
            <button key={p.id} className={`nav ${page === p.id ? "active" : ""}`} aria-current={page === p.id ? "page" : undefined} onClick={() => go(p.id)}>
              <p.icon size={17} aria-hidden /> <span>{p.label}</span>
            </button>
          ))}
        </nav>
        <div className="api-status" role="status">
          <span className={`dot ${health.loading ? "" : up ? "dot-ok" : "dot-bad"}`} aria-hidden />
          {health.loading ? "Checking API…" : health.error ? "API unreachable" : up ? `Models ready: ${health.data.selected_model.replace(/_/g, " ")}` : "API up, models not trained"}
        </div>
      </aside>
      <main id="main">{cur.el}</main>
    </div>
  );
}
