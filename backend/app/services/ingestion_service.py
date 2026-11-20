import asyncio

from app.config import settings
from app.models import vector_store
from app.models.db_models import SessionLocal, Document
from app.services import llm_service, retrieval_service
from app.utils.chunking import chunk_text
from app.utils.pdf_parser import parse_pdf

BATCH = 64


async def ingest_pdf(path: str, filename: str) -> dict:
    pages = await asyncio.to_thread(parse_pdf, path)

    chunks = []  # (page_no, index, text)
    for page_no, text in pages:
        for j, c in enumerate(chunk_text(text, settings.chunk_size, settings.chunk_overlap)):
            chunks.append((page_no, j, c))
    if not chunks:
        raise ValueError("No extractable text found (is this a scanned PDF?)")

    db = SessionLocal()
    try:
        doc = Document(filename=filename, path=path, pages=len(pages), chunks=len(chunks))
        db.add(doc)
        db.commit()
        db.refresh(doc)
        result = {"id": doc.id, "filename": doc.filename, "pages": doc.pages, "chunks": doc.chunks}

        try:
            for i in range(0, len(chunks), BATCH):
                batch = chunks[i:i + BATCH]
                embs = await llm_service.embed([c[2] for c in batch])
                vector_store.add_chunks(
                    ids=[f"d{doc.id}-p{c[0]}-c{c[1]}" for c in batch],
                    texts=[c[2] for c in batch],
                    embeddings=embs,
                    metadatas=[{"doc_id": doc.id, "filename": filename, "page": c[0]} for c in batch],
                )
        except Exception:
            vector_store.delete_doc(doc.id)
            db.delete(doc)
            db.commit()
            raise

        retrieval_service.invalidate_cache()
        return result
    finally:
        db.close()
