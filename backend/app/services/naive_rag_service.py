import time

from app.services import llm_service, retrieval_service
from app.utils.prompts import NAIVE_RAG_SYSTEM


def _citation(h: dict) -> dict:
    return {"chunk_id": h["chunk_id"], "doc_id": h["meta"]["doc_id"],
            "filename": h["meta"]["filename"], "page": h["meta"]["page"], "text": h["text"]}


async def answer(question: str, doc_ids=None, rerank: bool = False) -> dict:
    """Single-shot RAG. rerank=False is the naive baseline, rerank=True adds the reranker."""
    tracker = llm_service.start_tracking()
    start = time.time()
    hits = await retrieval_service.hybrid_search(question, doc_ids, rerank=rerank)

    if not hits:
        return {"report": "No indexed documents matched. Upload a PDF first.",
                "citations": [], "latency_s": round(time.time() - start, 2),
                "tokens": tracker.tokens, "cost_usd": round(tracker.cost_usd, 6)}

    context = "\n\n".join(f"[{h['chunk_id']}] {h['text']}" for h in hits)
    text, _ = await llm_service.chat(
        NAIVE_RAG_SYSTEM, f"Context:\n{context}\n\nQuestion: {question}"
    )
    return {
        "report": text,
        "citations": [_citation(h) for h in hits],
        "latency_s": round(time.time() - start, 2),
        "tokens": tracker.tokens,
        "cost_usd": round(tracker.cost_usd, 6),
    }
