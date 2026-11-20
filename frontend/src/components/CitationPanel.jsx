export default function CitationPanel({ citations = [], activeId, onSelect }) {
  if (citations.length === 0) return null;
  return (
    <div className="card">
      <h3>Sources</h3>
      {citations.map((c, i) => (
        <div key={c.chunk_id} className={`source ${activeId === c.chunk_id ? "active" : ""}`}>
          <div className="source-head" onClick={() => onSelect(activeId === c.chunk_id ? null : c.chunk_id)}>
            <strong>[{i + 1}]</strong>
            <span>{c.filename}</span>
            <span className="muted">page {c.page}</span>
          </div>
          {activeId === c.chunk_id && <p>{c.text}</p>}
        </div>
      ))}
    </div>
  );
}
