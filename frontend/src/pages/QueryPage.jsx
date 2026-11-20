import { useState } from "react";
import { useAgentStream } from "../hooks/useAgentStream";
import { ragQuery } from "../api/client";
import AgentTimeline from "../components/AgentTimeline";
import ReportView from "../components/ReportView";
import CitationPanel from "../components/CitationPanel";
import StatsBar from "../components/StatsBar";

const MODES = [
  { id: "agent", label: "Multi-agent (plan → retrieve → verify → write)" },
  { id: "rerank", label: "RAG + reranker" },
  { id: "naive", label: "Naive RAG" },
];

export default function QueryPage({ selected }) {
  const [question, setQuestion] = useState("");
  const [mode, setMode] = useState("agent");
  const [ragResult, setRagResult] = useState(null);
  const [ragLoading, setRagLoading] = useState(false);
  const [ragError, setRagError] = useState("");
  const [activeId, setActiveId] = useState(null);
  const stream = useAgentStream();

  const summary = stream.events.find((e) => e.agent === "summary")?.output;
  const streamFailure = stream.events.find((e) => e.status === "error");
  const out = mode === "agent" ? summary : ragResult;
  const loading = mode === "agent" ? stream.running : ragLoading;
  const error = mode === "agent"
    ? stream.error || (streamFailure ? `${streamFailure.agent}: ${streamFailure.output}` : "")
    : ragError;

  async function submit() {
    if (!question.trim() || loading) return;
    const ids = selected.length ? selected : null;
    setActiveId(null);
    if (mode === "agent") {
      await stream.start(question, ids);
    } else {
      setRagLoading(true);
      setRagError("");
      setRagResult(null);
      try {
        setRagResult(await ragQuery(mode, question, ids));
      } catch (e) {
        setRagError(e.message);
      } finally {
        setRagLoading(false);
      }
    }
  }

  return (
    <>
      <div className="card">
        <textarea
          rows={3}
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) submit(); }}
          placeholder="Ask a question across your documents… (Ctrl+Enter to send)"
        />
        <div className="row">
          <select value={mode} onChange={(e) => setMode(e.target.value)}>
            {MODES.map((m) => <option key={m.id} value={m.id}>{m.label}</option>)}
          </select>
          <button className="btn" onClick={submit} disabled={loading || !question.trim()}>
            {loading ? "Working…" : "Ask"}
          </button>
          {mode === "agent" && stream.running && (
            <button className="btn secondary" onClick={stream.stop}>Stop</button>
          )}
        </div>
        <p className="muted">
          Searching {selected.length ? `${selected.length} selected document(s)` : "all documents"}.
        </p>
        {error && <p className="error">{error}</p>}
      </div>

      {mode === "agent" && <AgentTimeline events={stream.events} />}

      {out && (
        <>
          <ReportView
            report={out.report}
            citations={out.citations}
            onCitationClick={(id) => setActiveId(id)}
          />
          <StatsBar result={out} />
          <CitationPanel citations={out.citations} activeId={activeId} onSelect={setActiveId} />
        </>
      )}
    </>
  );
}
