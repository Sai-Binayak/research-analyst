import os

from app.models import vector_store
from app.models.db_models import SessionLocal, Document
from app.services import retrieval_service


def list_documents() -> list:
    db = SessionLocal()
    try:
        return [
            {"id": d.id, "filename": d.filename, "pages": d.pages, "chunks": d.chunks}
            for d in db.query(Document).order_by(Document.id).all()
        ]
    finally:
        db.close()


def delete_document(doc_id: int) -> bool:
    db = SessionLocal()
    try:
        doc = db.get(Document, doc_id)
        if not doc:
            return False
        path = doc.path
        db.delete(doc)
        db.commit()
    finally:
        db.close()
    vector_store.delete_doc(doc_id)
    retrieval_service.invalidate_cache()
    if path and os.path.exists(path):
        os.remove(path)
    return True
