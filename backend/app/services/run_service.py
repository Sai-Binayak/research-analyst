from app.models.db_models import SessionLocal, Run


def save_run(mode, question, report, citations, latency_s, tokens, cost_usd) -> int:
    db = SessionLocal()
    try:
        run = Run(mode=mode, question=question, report=report, citations=citations,
                  latency_s=latency_s, tokens=tokens, cost_usd=cost_usd)
        db.add(run)
        db.commit()
        db.refresh(run)
        return run.id
    finally:
        db.close()


def list_runs(limit: int = 50) -> list:
    db = SessionLocal()
    try:
        rows = db.query(Run).order_by(Run.created_at.desc()).limit(limit).all()
        return [
            {"id": r.id, "mode": r.mode, "question": r.question, "report": r.report,
             "latency_s": r.latency_s, "tokens": r.tokens, "cost_usd": r.cost_usd,
             "created_at": r.created_at.isoformat()}
            for r in rows
        ]
    finally:
        db.close()
