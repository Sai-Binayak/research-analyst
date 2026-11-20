def chunk_text(text: str, size: int = 800, overlap: int = 120):
    """Simple sliding-window chunker. TODO: upgrade to section-aware chunking."""
    text = " ".join(text.split())
    if not text:
        return []
    chunks, start = [], 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = end - overlap
    return chunks
