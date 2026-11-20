import re
from rank_bm25 import BM25Okapi

from app.config import settings
from app.models import vector_store
from app.services import llm_service
from app.utils.prompts import RERANK_SYSTEM

RRF_K = 60
_bm25_cache = {}


def invalidate_cache():
    """Call after documents are added or deleted."""
    _bm25_cache.clear()


def _tokenize(text: str):
    return re.findall(r"\w+", text.lower())


def _get_bm25(doc_ids):
    key = tuple(sorted(doc_ids)) if doc_ids else None
    if key not in _bm25_cache:
        corpus = vector_store.get_all(doc_ids)
        bm25 = BM25Okapi([_tokenize(c["text"]) for c in corpus]) if corpus else None
        _bm25_cache[key] = (bm25, corpus)
    return _bm25_cache[key]


async def hybrid_search(query: str, doc_ids=None, k: int = None, rerank: bool = True):
    """Vector + BM25 search fused with reciprocal rank fusion, optionally reranked."""
    k = k or settings.top_k
    pool = max(settings.rerank_candidates, k) if rerank else k

    q_emb = (await llm_service.embed([query]))[0]
    vec_hits = vector_store.search(q_emb, k=pool * 2, doc_ids=doc_ids)

    bm25, corpus = _get_bm25(doc_ids)
    bm25_hits = []
    if bm25:
        scores = bm25.get_scores(_tokenize(query))
        order = sorted(range(len(corpus)), key=lambda i: -scores[i])[: pool * 2]
        bm25_hits = [corpus[i] for i in order if scores[i] > 0]

    fused = {}
    for hits in (vec_hits, bm25_hits):
        for rank, h in enumerate(hits):
            entry = fused.setdefault(h["chunk_id"], {"item": h, "score": 0.0})
            entry["score"] += 1.0 / (RRF_K + rank)

    ranked = [e["item"] for e in sorted(fused.values(), key=lambda e: -e["score"])]
    candidates = ranked[:pool]
    if rerank:
        candidates = await _rerank(query, candidates)
    return candidates[:k]


async def _rerank(query: str, items: list):
    """LLM-based reranker: scores each candidate 0-10 for relevance.
    Swap for a cross-encoder (sentence-transformers) or Cohere Rerank if you prefer.
    Falls back to the fused order if the model output is unusable."""
    if len(items) <= 1:
        return items
    listing = "\n\n".join(f"[{i}] {it['text'][:600]}" for i, it in enumerate(items))
    try:
        data, _ = await llm_service.chat(
            RERANK_SYSTEM, f"Query: {query}\n\nPassages:\n{listing}", json_mode=True
        )
        scores = {int(s["id"]): float(s["score"]) for s in data.get("scores", [])}
    except Exception:
        return items
    order = sorted(range(len(items)), key=lambda i: (-scores.get(i, 0.0), i))
    return [items[i] for i in order]
