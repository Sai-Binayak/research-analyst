export default function StatsBar({ result }) {
  if (!result) return null;
  return (
    <div className="stats">
      <span>Latency: {result.latency_s}s</span>
      <span>Tokens: {result.tokens}</span>
      <span>Cost: ${Number(result.cost_usd).toFixed(5)}</span>
    </div>
  );
}
