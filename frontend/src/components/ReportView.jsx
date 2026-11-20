import ReactMarkdown from "react-markdown";

const CITE_RE = /\[(d\d+-p\d+-c\d+)\]/g;

export default function ReportView({ report, citations = [], onCitationClick }) {
  if (!report) return null;

  const numbers = {};
  citations.forEach((c, i) => { numbers[c.chunk_id] = i + 1; });

  // Turn [chunk_id] markers into numbered, clickable links.
  const linked = report.replace(CITE_RE, (match, id) =>
    numbers[id] ? `[${numbers[id]}](#cite-${id})` : match
  );

  return (
    <div className="card">
      <h3>Report</h3>
      <ReactMarkdown
        components={{
          a: ({ href, children }) =>
            href?.startsWith("#cite-") ? (
              <button className="cite" onClick={() => onCitationClick(href.slice(6))}>
                {children}
              </button>
            ) : (
              <a href={href} target="_blank" rel="noreferrer">{children}</a>
            ),
        }}
      >
        {linked}
      </ReactMarkdown>
    </div>
  );
}
