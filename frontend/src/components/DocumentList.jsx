import { useState } from "react";
import { uploadDocument, deleteDocument } from "../api/client";

export default function DocumentList({ docs, selected, onToggle, onChanged }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function handleFiles(e) {
    const files = Array.from(e.target.files);
    e.target.value = "";
    setBusy(true);
    setError("");
    for (const file of files) {
      try {
        await uploadDocument(file);
      } catch (err) {
        setError(`${file.name}: ${err.message}`);
      }
    }
    setBusy(false);
    onChanged();
  }

  async function remove(id) {
    try {
      await deleteDocument(id);
      onChanged();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <div className="card">
      <h3>Documents</h3>
      <input type="file" accept=".pdf" multiple onChange={handleFiles} disabled={busy} />
      {busy && <p className="muted">Parsing and embedding… this can take a minute for large PDFs.</p>}
      {error && <p className="error">{error}</p>}
      <p className="muted">
        Tick documents to restrict questions to them. With none ticked, all documents are searched.
      </p>
      {docs.length === 0 && <p className="muted">No documents yet.</p>}
      {docs.map((d) => (
        <div className="doc-item" key={d.id}>
          <label>
            <input
              type="checkbox"
              checked={selected.includes(d.id)}
              onChange={() => onToggle(d.id)}
            />{" "}
            {d.filename} <span className="muted">({d.pages} pages, {d.chunks} chunks)</span>
          </label>
          <button className="btn danger" onClick={() => remove(d.id)}>Delete</button>
        </div>
      ))}
    </div>
  );
}
