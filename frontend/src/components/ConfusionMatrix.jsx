import { fmtInt } from "../services/format.js";

// 2x2 confusion matrix with plain-language meanings. Counts come straight from the evaluation file.
export default function ConfusionMatrix({ cm, title }) {
  const cells = [
    { k: "tn", name: "True negative", note: "Legitimate, passed", tone: "ok", v: cm.tn },
    { k: "fp", name: "False positive", note: "Legitimate, flagged (false alarm)", tone: "warn", v: cm.fp },
    { k: "fn", name: "False negative", note: "Fraud, missed", tone: "bad", v: cm.fn },
    { k: "tp", name: "True positive", note: "Fraud, caught", tone: "ok", v: cm.tp },
  ];
  return (
    <figure className="cm" aria-label={title || "Confusion matrix"}>
      <div className="cm-grid">
        <span />
        <span className="cm-axis">Predicted legitimate</span>
        <span className="cm-axis">Predicted fraud</span>
        <span className="cm-axis cm-row">Actually legitimate</span>
        <Cell c={cells[0]} />
        <Cell c={cells[1]} />
        <span className="cm-axis cm-row">Actually fraud</span>
        <Cell c={cells[2]} />
        <Cell c={cells[3]} />
      </div>
    </figure>
  );
}

function Cell({ c }) {
  return (
    <div className={`cm-cell cm-${c.tone}`}>
      <strong>{fmtInt(c.v)}</strong>
      <span>{c.name}</span>
      <small>{c.note}</small>
    </div>
  );
}
