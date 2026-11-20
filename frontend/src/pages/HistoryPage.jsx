import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { getRuns } from "../api/client";

export default function HistoryPage() {
  const [runs, setRuns] = useState([]);
  const [open, setOpen] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getRuns().then(setRuns).catch((e) => setError(e.message));
  }, []);

  return (
    <div className="card">
      <h3>Run history</h3>
      {error && <p className="error">{error}</p>}
      {runs.length === 0 && !error && <p className="muted">No runs yet.</p>}
      {runs.map((r) => (
        <div key={r.id} className="source">
          <div className="source-head" onClick={() => setOpen(open === r.id ? null : r.id)}>
            <strong>{r.mode}</strong>
            <span>{r.question}</span>
          </div>
          <div className="stats">
            <span>{r.latency_s}s</span>
            <span>{r.tokens} tokens</span>
            <span>${Number(r.cost_usd).toFixed(5)}</span>
            <span>{new Date(r.created_at + "Z").toLocaleString()}</span>
          </div>
          {open === r.id && <ReactMarkdown>{r.report}</ReactMarkdown>}
        </div>
      ))}
    </div>
  );
}
