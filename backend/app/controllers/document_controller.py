import os
import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException

from app.config import settings
from app.models.schemas import DocumentOut
from app.services import ingestion_service, document_service

router = APIRouter(prefix="/documents", tags=["documents"])
UPLOAD_DIR = "data/uploads"


@router.post("", response_model=DocumentOut)
async def upload(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    original = os.path.basename(file.filename)
    path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}_{original}")
    limit = settings.max_upload_mb * 1024 * 1024

    size, too_big = 0, False
    with open(path, "wb") as f:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > limit:
                too_big = True
                break
            f.write(chunk)
    if too_big:
        os.remove(path)
        raise HTTPException(413, f"File exceeds {settings.max_upload_mb} MB limit")

    try:
        return await ingestion_service.ingest_pdf(path, original)
    except ValueError as e:
        os.remove(path)
        raise HTTPException(422, str(e))
    except Exception as e:
        if os.path.exists(path):
            os.remove(path)
        raise HTTPException(502, f"Ingestion failed: {e}")


@router.get("", response_model=list[DocumentOut])
def list_documents():
    return document_service.list_documents()


@router.delete("/{doc_id}")
def delete_document(doc_id: int):
    if not document_service.delete_document(doc_id):
        raise HTTPException(404, "Document not found")
    return {"deleted": doc_id}
