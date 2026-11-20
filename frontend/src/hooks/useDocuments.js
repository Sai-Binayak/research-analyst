import { useEffect, useState, useCallback } from "react";
import { listDocuments } from "../api/client";

export function useDocuments() {
  const [docs, setDocs] = useState([]);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    try {
      setDocs(await listDocuments());
      setError("");
    } catch (e) {
      setError(`Could not reach the backend: ${e.message}`);
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);
  return { docs, refresh, error };
}
