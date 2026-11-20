import { useState } from "react";
import UploadPage from "./pages/UploadPage";
import QueryPage from "./pages/QueryPage";
import EvalPage from "./pages/EvalPage";
import HistoryPage from "./pages/HistoryPage";

const TABS = [
  { id: "upload", label: "Documents" },
  { id: "query", label: "Ask" },
  { id: "eval", label: "Evaluation" },
  { id: "history", label: "History" },
];

export default function App() {
  const [tab, setTab] = useState("upload");
  const [selected, setSelected] = useState([]);

  return (
    <div className="container">
      <h1>Agentic Research Analyst</h1>
      <nav className="tabs">
        {TABS.map((t) => (
          <button
            key={t.id}
            className={`tab ${tab === t.id ? "active" : ""}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
            {t.id === "upload" && selected.length > 0 ? ` (${selected.length})` : ""}
          </button>
        ))}
      </nav>

      {tab === "upload" && <UploadPage selected={selected} setSelected={setSelected} />}
      {tab === "query" && <QueryPage selected={selected} />}
      {tab === "eval" && <EvalPage />}
      {tab === "history" && <HistoryPage />}
    </div>
  );
}
