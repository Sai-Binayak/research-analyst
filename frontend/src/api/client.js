export const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(path, options) {
  const res = await fetch(`${API}${path}`, options);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* ignore non-JSON error bodies */
    }
    throw new Error(detail);
  }
  return res.json();
}

const post = (body) => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});

export const listDocuments = () => request("/documents");

export function uploadDocument(file) {
  const form = new FormData();
  form.append("file", file);
  return request("/documents", { method: "POST", body: form });
}

export const deleteDocument = (id) => request(`/documents/${id}`, { method: "DELETE" });

// mode: "naive" | "rerank"
export const ragQuery = (mode, question, docIds) =>
  request(`/query/${mode}`, post({ question, doc_ids: docIds }));

export const startEval = (setup) => request(`/eval/run?setup=${setup}`, { method: "POST" });
export const getEvalStatus = () => request("/eval/status");
export const getEvalResults = () => request("/eval/results");
export const getRuns = () => request("/runs");

export const getQuestionSummary = () => request("/questions");
export const getQuestionStatus = () => request("/questions/status");
export const generateQuestions = (opts) => request("/questions/generate", post(opts));
