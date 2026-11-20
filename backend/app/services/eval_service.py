import json

from app.config import settings
from app.models.db_models import SessionLocal, EvalResult
from app.services import llm_service, naive_rag_service
from app.services.agents.orchestrator import run_pipeline
from app.utils.metrics import is_hit, mean
from app.utils.prompts import JUDGE_SYSTEM
from app.utils.question_utils import QUESTIONS_PATH, category_of, select_questions

SETUPS = ("naive", "rerank", "agent")


def load_questions() -> list:
    with open(QUESTIONS_PATH, encoding="utf-8") as f:
        return json.load(f)


async def judge_faithfulness(answer: str, passages: list) -> float:
    sources = "\n\n".join(p["text"] for p in passages) or "(no sources)"
    data, _ = await llm_service.chat(
        JUDGE_SYSTEM, f"ANSWER:\n{answer}\n\nSOURCES:\n{sources}", json_mode=True
    )
    return max(0.0, min(1.0, float(data.get("score", 0))))


async def _run_one(setup: str, question: str) -> dict:
    if setup in ("naive", "rerank"):
        res = await naive_rag_service.answer(question, rerank=(setup == "rerank"))
        return {"report": res["report"], "passages": res["citations"],
                "latency_s": res["latency_s"], "cost_usd": res["cost_usd"]}

    passages, summary = [], None
    async for ev in run_pipeline(question, None, persist=False):
        if ev.status == "error":
            raise RuntimeError(f"{ev.agent}: {ev.output}")
        if ev.agent == "retriever" and ev.status == "done":
            seen = {}
            for item in ev.output:
                for p in item["passages"]:
                    seen[p["chunk_id"]] = p
            passages = list(seen.values())
        if ev.agent == "summary":
            summary = ev.output
    if summary is None:
        raise RuntimeError("pipeline produced no summary")
    return {"report": summary["report"], "passages": passages,
            "latency_s": summary["latency_s"], "cost_usd": summary["cost_usd"]}


async def run_eval(setup: str, limit: int = None, on_progress=None) -> dict:
    if setup not in SETUPS:
        raise ValueError(f"Unknown setup: {setup}")
    questions = select_questions(load_questions(), limit or settings.eval_max_questions)

    hits, faith, lat, cost = [], [], [], []
    cats = {}
    errors, last_error = 0, None
    for i, q in enumerate(questions):
        bucket = cats.setdefault(category_of(q), {"hits": [], "faith": []})
        try:
            r = await _run_one(setup, q["question"])
            hit = is_hit(r["passages"], q.get("gold_chunk_ids", []), q.get("gold_phrases", []))
            f = await judge_faithfulness(r["report"], r["passages"])
            lat.append(r["latency_s"])
            cost.append(r["cost_usd"])
            faith.append(f)
            bucket["faith"].append(f)
            if hit is not None:  # hit rate only exists for questions with gold evidence
                hits.append(1.0 if hit else 0.0)
                bucket["hits"].append(1.0 if hit else 0.0)
        except Exception as e:
            errors += 1
            last_error = e
        if on_progress:
            on_progress(i + 1, len(questions))

    if questions and errors == len(questions):
        raise RuntimeError(f"All questions failed. Last error: {last_error}")

    by_category = {
        cat: {"hit_rate": mean(b["hits"]) if b["hits"] else None,
              "faithfulness": mean(b["faith"]), "n": len(b["faith"])}
        for cat, b in cats.items() if b["faith"]
    }
    return {
        "setup": setup,
        "hit_rate": mean(hits) if hits else None,
        "faithfulness": mean(faith),
        "avg_latency_s": mean(lat),
        "avg_cost_usd": mean(cost),
        "n_questions": len(faith),
        "by_category": by_category,
    }


def save_result(result: dict):
    db = SessionLocal()
    try:
        db.add(EvalResult(**result))
        db.commit()
    finally:
        db.close()


def latest_results() -> list:
    db = SessionLocal()
    try:
        rows = db.query(EvalResult).order_by(EvalResult.created_at.desc()).all()
    finally:
        db.close()
    latest = {}
    for r in rows:
        latest.setdefault(r.setup, r)
    out = []
    for s in SETUPS:
        r = latest.get(s)
        if r:
            out.append({"setup": r.setup, "hit_rate": r.hit_rate, "faithfulness": r.faithfulness,
                        "avg_latency_s": r.avg_latency_s, "avg_cost_usd": r.avg_cost_usd,
                        "n_questions": r.n_questions, "by_category": r.by_category or {}})
    return out
