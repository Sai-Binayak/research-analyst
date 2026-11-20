import { useCallback, useEffect, useState } from "react";
import { getEvalResults, getEvalStatus, startEval } from "../api/client";
import EvalTable from "../components/EvalTable";
import EvalChart from "../components/EvalChart";
import QuestionSetCard from "../components/QuestionSetCard";

export default function EvalPage() {
  const [rows, setRows] = useState([]);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      setRows(await getEvalResults());
    } catch (e) {
      setError(e.message);
    }
  }, []);

  useEffect(() => {
    load();
    getEvalStatus().then(setStatus).catch(() => {});
  }, [load]);

  // Poll while an evaluation is running.
  useEffect(() => {
    if (!status?.running) return;
    const timer = setInterval(async () => {
      try {
        const s = await getEvalStatus();
        setStatus(s);
        if (!s.running) load();
      } catch (e) {
        setError(e.message);
      }
    }, 2000);
    return () => clearInterval(timer);
  }, [status?.running, load]);

  async function run(setup) {
    setError("");
    try {
      await startEval(setup);
      setStatus(await getEvalStatus());
    } catch (e) {
      setError(e.message);
    }
  }

  const running = status?.running;
  const pct = status?.total ? Math.round((status.done / status.total) * 100) : 0;

  return (
    <>
      <QuestionSetCard />

      <div className="card">
        <h3>Run evaluation</h3>
        <p className="muted">
          Runs every question in the question set above against all indexed documents.
        </p>
        <div className="row">
          <button className="btn" disabled={running} onClick={() => run("all")}>Run all three</button>
          <button className="btn secondary" disabled={running} onClick={() => run("naive")}>Naive</button>
          <button className="btn secondary" disabled={running} onClick={() => run("rerank")}>Reranker</button>
          <button className="btn secondary" disabled={running} onClick={() => run("agent")}>Multi-agent</button>
        </div>
        {running && (
          <>
            <p className="muted">
              Running {status.current}… {status.done}/{status.total} questions
            </p>
            <div className="progress"><div style={{ width: `${pct}%` }} /></div>
          </>
        )}
        {status?.error && <p className="error">Last run failed: {status.error}</p>}
        {error && <p className="error">{error}</p>}
      </div>

      <div className="card">
        <h3>Results</h3>
        <EvalTable rows={rows} />
        <EvalChart rows={rows} />
      </div>
    </>
  );
}
