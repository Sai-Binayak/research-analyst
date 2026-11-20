import { useCallback, useEffect, useState } from "react";
import { generateQuestions, getQuestionStatus, getQuestionSummary } from "../api/client";

export const CAT_LABELS = {
  specific: "Document-specific",
  generic: "Generic",
  cross: "Cross-document",
};

export default function QuestionSetCard() {
  const [summary, setSummary] = useState(null);
  const [status, setStatus] = useState(null);
  const [n, setN] = useState(30);
  const [generic, setGeneric] = useState(true);
  const [cross, setCross] = useState(true);
  const [error, setError] = useState("");

  const loadSummary = useCallback(async () => {
    try {
      setSummary(await getQuestionSummary());
    } catch (e) {
      setError(e.message);
    }
  }, []);

  useEffect(() => {
    loadSummary();
    getQuestionStatus().then(setStatus).catch(() => {});
  }, [loadSummary]);

  // Poll while generating.
  useEffect(() => {
    if (!status?.running) return;
    const timer = setInterval(async () => {
      try {
        const s = await getQuestionStatus();
        setStatus(s);
        if (!s.running) loadSummary();
      } catch (e) {
        setError(e.message);
      }
    }, 2000);
    return () => clearInterval(timer);
  }, [status?.running, loadSummary]);

  async function generate() {
    setError("");
    try {
      await generateQuestions({
        n_specific: Number(n),
        include_generic: generic,
        include_cross: cross,
      });
      setStatus(await getQuestionStatus());
    } catch (e) {
      setError(e.message);
    }
  }

  const running = status?.running;
  const pct = status?.total ? Math.round((status.done / status.total) * 100) : 0;

  return (
    <div className="card">
      <h3>Question set</h3>
      <p className="muted">
        Generates evaluation questions from your indexed documents. Document-specific questions
        get exact gold evidence for hit rate; generic and cross-document questions measure
        faithfulness only. Replaces questions.json (the old file is saved as a backup).
      </p>

      {summary && (
        <p>
          <strong>Current set: {summary.total} questions</strong>
          {Object.entries(summary.by_category).map(([cat, count]) => (
            <span key={cat} className="muted"> · {CAT_LABELS[cat] || cat}: {count}</span>
          ))}
        </p>
      )}

      <div className="row">
        <label>
          Document-specific questions{" "}
          <input
            type="number" min="1" max="100" value={n}
            onChange={(e) => setN(e.target.value)}
            style={{ width: 70, padding: 6 }}
          />
        </label>
        <label><input type="checkbox" checked={generic} onChange={(e) => setGeneric(e.target.checked)} /> Generic</label>
        <label><input type="checkbox" checked={cross} onChange={(e) => setCross(e.target.checked)} /> Cross-document</label>
        <button className="btn" disabled={running || !n} onClick={generate}>Generate</button>
      </div>

      {running && (
        <>
          <p className="muted">Generating… {status.done}/{status.total} (one AI call per question)</p>
          <div className="progress"><div style={{ width: `${pct}%` }} /></div>
        </>
      )}
      {!running && status?.last && (
        <p className="muted">
          Done: {status.last.total} questions saved.
          {status.last.cross_error ? ` Cross-document step failed: ${status.last.cross_error}` : ""}
        </p>
      )}
      {status?.error && <p className="error">Generation failed: {status.error}</p>}
      {error && <p className="error">{error}</p>}
    </div>
  );
}
