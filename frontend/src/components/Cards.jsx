export function KpiCard({ icon: Icon, label, value, hint, tone = "cyan" }) {
  return (
    <div className={`kpi kpi-${tone}`}>
      <div className="kpi-top">
        {Icon && <Icon size={16} aria-hidden />}
        <span>{label}</span>
      </div>
      <div className="kpi-value">{value}</div>
      {hint && <div className="kpi-hint">{hint}</div>}
    </div>
  );
}

export function Card({ title, subtitle, children, className = "", actions }) {
  return (
    <section className={`card ${className}`}>
      {(title || actions) && (
        <header className="card-head">
          <div>
            <h2>{title}</h2>
            {subtitle && <p className="muted">{subtitle}</p>}
          </div>
          {actions}
        </header>
      )}
      {children}
    </section>
  );
}
