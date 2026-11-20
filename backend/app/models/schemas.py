from typing import List, Optional
from pydantic import BaseModel


class QueryRequest(BaseModel):
    question: str
    doc_ids: Optional[List[int]] = None


class Citation(BaseModel):
    chunk_id: str
    doc_id: int
    filename: str
    page: int
    text: str


class QueryResponse(BaseModel):
    report: str
    citations: List[Citation]
    latency_s: float
    tokens: int
    cost_usd: float
    run_id: Optional[int] = None


class DocumentOut(BaseModel):
    id: int
    filename: str
    pages: int
    chunks: int
