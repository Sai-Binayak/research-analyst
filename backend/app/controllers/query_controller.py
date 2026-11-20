from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.models.schemas import QueryRequest, QueryResponse
from app.services import naive_rag_service, run_service
from app.services.agents.orchestrator import run_pipeline

router = APIRouter(prefix="/query", tags=["query"])


async def _rag(req: QueryRequest, rerank: bool, mode: str) -> dict:
    try:
        result = await naive_rag_service.answer(req.question, req.doc_ids, rerank=rerank)
    except Exception as e:
        raise HTTPException(502, f"Query failed: {e}")
    result["run_id"] = run_service.save_run(
        mode, req.question, result["report"], result["citations"],
        result["latency_s"], result["tokens"], result["cost_usd"],
    )
    return result


@router.post("/naive", response_model=QueryResponse)
async def naive_query(req: QueryRequest):
    return await _rag(req, rerank=False, mode="naive")


@router.post("/rerank", response_model=QueryResponse)
async def rerank_query(req: QueryRequest):
    return await _rag(req, rerank=True, mode="rerank")


@router.post("/agent")
async def agent_query(req: QueryRequest):
    async def event_stream():
        async for event in run_pipeline(req.question, req.doc_ids):
            yield f"data: {event.model_dump_json()}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
