import { useState } from 'react'
import { Activity, BarChart3, Database, ScanSearch, ShieldCheck } from 'lucide-react'
import { api } from './services/api'
import { useApi } from './hooks/useApi'
import Dashboard from './pages/Dashboard.jsx'
import Analyze from './pages/Analyze.jsx'
import Compare from './pages/Compare.jsx'
import Explorer from './pages/Explorer.jsx'

const PAGES = [
  ['dashboard', 'Dashboard', Activity, Dashboard],
  ['analyze', 'Transaction Analysis', ScanSearch, Analyze],
  ['compare', 'Model Comparison', BarChart3, Compare],
  ['explorer', 'Data Explorer', Database, Explorer],
]

export default function App() {
  const [page, setPage] = useState('dashboard')
  const health = useApi(api.health, [])
  const Page = PAGES.find((p) => p[0] === page)[3]
  const ok = health.data?.models_available
  return (
    <div className="shell">
      <aside className="side">
        <div className="brand"><ShieldCheck size={22} /> <span>CyberSentinel</span></div>
        <nav aria-label="Main">
          {PAGES.map(([id, label, Icon]) => (
            <button key={id} className={page === id ? 'on' : ''} aria-current={page === id ? 'page' : undefined} onClick={() => setPage(id)}>
              <Icon size={18} /> <span>{label}</span>
            </button>
          ))}
        </nav>
        <div className="status" role="status">
          <i className={health.error ? 'dot bad' : ok ? 'dot ok' : 'dot warn'} />
          {health.loading ? 'Checking API…' : health.error ? 'API offline' : ok ? 'Models loaded' : 'Models not trained'}
        </div>
      </aside>
      <main>
        <header className="top"><h1>{PAGES.find((p) => p[0] === page)[1]}</h1>
          <span className="tag">Educational prototype — not a production banking system</span></header>
        <Page />
      </main>
    </div>
  )
}
