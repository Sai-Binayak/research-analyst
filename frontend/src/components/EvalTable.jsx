import { CAT_LABELS } from "./QuestionSetCard";

const LABELS = { naive: "Naive RAG", rerank: "RAG + reranker", agent: "Multi-agent + verifier" };
const pct = (v) => (v === null || v === undefined ? "—" : v.toFixed(2));

export default function EvalTable({ rows }) {
  if (rows.length === 0) return <p className="muted">No evaluation results yet.</p>;

  const categories = [...new Set(rows.flatMap((r) => Object.keys(r.by_category || {})))];

  return (
    <>
      <table>
        <thead>
          <tr>
            <th>Setup</th><th>Hit rate</th><th>Faithfulness</th>
            <th>Latency (s)</th><th>Cost / query</th><th>Questions</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r.setup}>
              <td>{LABELS[r.setup] || r.setup}</td>
              <td>{pct(r.hit_rate)}</td>
              <td>{pct(r.faithfulness)}</td>
              <td>{r.avg_latency_s.toFixed(2)}</td>
              <td>${r.avg_cost_usd.toFixed(5)}</td>
              <td>{r.n_questions}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {categories.length > 0 && (
        <>
          <h3 style={{ marginTop: 20 }}>By question type</h3>
          <table>
            <thead>
              <tr>
                <th>Setup</th>
                {categories.map((c) => (
                  <th key={c}>{CAT_LABELS[c] || c}<br /><span className="muted">hit / faithfulness (n)</span></th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.setup}>
                  <td>{LABELS[r.setup] || r.setup}</td>
                  {categories.map((c) => {
                    const b = (r.by_category || {})[c];
                    return (
                      <td key={c}>
                        {b ? `${pct(b.hit_rate)} / ${pct(b.faithfulness)} (${b.n})` : "—"}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}
    </>
  );
}
