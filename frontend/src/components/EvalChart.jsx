import {
  BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer, CartesianGrid,
} from "recharts";

const LABELS = { naive: "Naive", rerank: "Reranker", agent: "Multi-agent" };

export default function EvalChart({ rows }) {
  if (rows.length === 0) return null;
  const data = rows.map((r) => ({
    setup: LABELS[r.setup] || r.setup,
    "Hit rate": r.hit_rate === null || r.hit_rate === undefined ? null : Number(r.hit_rate.toFixed(3)),
    Faithfulness: Number(r.faithfulness.toFixed(3)),
  }));
  return (
    <div style={{ width: "100%", height: 280, marginTop: 16 }}>
      <ResponsiveContainer>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="setup" />
          <YAxis domain={[0, 1]} />
          <Tooltip />
          <Legend />
          <Bar dataKey="Hit rate" fill="#4f46e5" />
          <Bar dataKey="Faithfulness" fill="#16a34a" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
