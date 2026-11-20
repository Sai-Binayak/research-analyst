import DocumentList from "../components/DocumentList";
import { useDocuments } from "../hooks/useDocuments";

export default function UploadPage({ selected, setSelected }) {
  const { docs, refresh, error } = useDocuments();

  const toggle = (id) =>
    setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));

  // Refresh the list, and drop selections for documents that no longer exist.
  const onChanged = async () => {
    await refresh();
  };

  return (
    <>
      {error && <p className="error">{error}</p>}
      <DocumentList docs={docs} selected={selected} onToggle={toggle} onChanged={onChanged} />
    </>
  );
}
