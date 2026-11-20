const ORDER = ["planner", "retriever", "verifier", "writer"];

function renderOutput(agent, output) {
  if (agent === "planner") {
    return <ul>{output.map((q, i) => <li key={i}>{q}</li>)}</ul>;
  }
  if (agent === "retriever") {
    return (
      <ul>
        {output.map((e, i) => (
          <li key={i}>{e.sub_question} — {e.passages.length} passages</li>
        ))}
      </ul>
    );
  }
  if (agent === "verifier") {
    return (
      <ul>
        {output.map((c, i) => (
          <li key={i}>
            {c.supported ? "✓" : "✗"} {c.claim}
            {c.note ? <span className="muted"> ({c.note})</span> : null}
          </li>
        ))}
      </ul>
    );
  }
  return null;
}

export default function AgentTimeline({ events }) {
  const latest = {};
  events.forEach((e) => {
    if (ORDER.includes(e.agent)) latest[e.agent] = e;
  });
  const shown = ORDER.filter((a) => latest[a]);
  if (shown.length === 0) return null;

  return (
    <div className="card">
      <h3>Agent activity</h3>
      {shown.map((agent) => {
        const e = latest[agent];
        const cls = e.status === "started" ? "running" : e.status;
        return (
          <div key={agent} className={`step ${cls}`}>
            <strong style={{ textTransform: "capitalize" }}>{agent}</strong>{" "}
            <span className="muted">
              {e.status === "started" ? "working…" : e.status === "error" ? "failed" : "done"}
              {e.tokens > 0 ? ` · ${e.tokens} tokens` : ""}
            </span>
            {e.status === "error" && <div className="error">{String(e.output)}</div>}
            {e.status === "done" && Array.isArray(e.output) && renderOutput(agent, e.output)}
          </div>
        );
      })}
    </div>
  );
}
