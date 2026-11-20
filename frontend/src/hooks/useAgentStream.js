import { useState, useRef } from "react";
import { API } from "../api/client";

export function useAgentStream() {
  const [events, setEvents] = useState([]);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const abortRef = useRef(null);

  async function start(question, docIds) {
    setEvents([]);
    setError("");
    setRunning(true);
    const controller = new AbortController();
    abortRef.current = controller;
    try {
      const res = await fetch(`${API}/query/agent`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question, doc_ids: docIds }),
        signal: controller.signal,
      });
      if (!res.ok) throw new Error(res.statusText);

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop(); // keep any incomplete trailing chunk
        for (const part of parts) {
          if (part.startsWith("data: ")) {
            setEvents((prev) => [...prev, JSON.parse(part.slice(6))]);
          }
        }
      }
    } catch (e) {
      if (e.name !== "AbortError") setError(e.message);
    } finally {
      setRunning(false);
    }
  }

  const stop = () => abortRef.current?.abort();

  return { events, running, error, start, stop };
}
