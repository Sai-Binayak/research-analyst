import asyncio
import re
import time

from app.models.events import AgentEvent
from app.services import llm_service, run_service
from app.services.agents.planner import Planner
from app.services.agents.retriever import Retriever
from app.services.agents.verifier import Verifier
from app.services.agents.writer import Writer

planner, retriever, verifier, writer = Planner(), Retriever(), Verifier(), Writer()
CITE_RE = re.compile(r"\[(d\d+-p\d+-c\d+)\]")


def _citation(p: dict) -> dict:
    return {"chunk_id": p["chunk_id"], "doc_id": p["meta"]["doc_id"],
            "filename": p["meta"]["filename"], "page": p["meta"]["page"], "text": p["text"]}


async def run_pipeline(question: str, doc_ids=None, persist: bool = True):
    """Async generator: yields an AgentEvent after each step so the UI can stream.
    The last event is a 'summary' with the report, citations, latency, tokens and cost."""
    tracker = llm_service.start_tracking()
    start = time.time()
    stage = "planner"
    try:
        yield AgentEvent(agent="planner", status="started")
        sub_questions, u = await planner.plan(question)
        yield AgentEvent(agent="planner", status="done", output=sub_questions, tokens=u["tokens"])

        stage = "retriever"
        yield AgentEvent(agent="retriever", status="started")
        before = tracker.tokens
        evidence = list(await asyncio.gather(*[retriever.retrieve(sq, doc_ids) for sq in sub_questions]))
        yield AgentEvent(agent="retriever", status="done", output=evidence,
                         tokens=tracker.tokens - before)

        stage = "verifier"
        yield AgentEvent(agent="verifier", status="started")
        claims, u = await verifier.check(evidence)
        yield AgentEvent(agent="verifier", status="done", output=claims, tokens=u["tokens"])

        stage = "writer"
        yield AgentEvent(agent="writer", status="started")
        report, u = await writer.write(question, claims)
        yield AgentEvent(agent="writer", status="done", output=report, tokens=u["tokens"])

        passages = {p["chunk_id"]: p for e in evidence for p in e["passages"]}
        cited = list(dict.fromkeys(CITE_RE.findall(report)))
        citations = [_citation(passages[c]) for c in cited if c in passages]
        if not citations:
            citations = [_citation(p) for p in passages.values()]

        latency = round(time.time() - start, 2)
        tokens = tracker.tokens
        cost = round(tracker.cost_usd, 6)
        run_id = None
        if persist:
            run_id = run_service.save_run("agent", question, report, citations, latency, tokens, cost)

        yield AgentEvent(agent="summary", status="done", output={
            "report": report, "citations": citations, "latency_s": latency,
            "tokens": tokens, "cost_usd": cost, "run_id": run_id,
        })
    except Exception as e:
        yield AgentEvent(agent=stage, status="error", output=str(e))
