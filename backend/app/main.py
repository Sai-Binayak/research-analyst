from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.controllers import (
    document_controller, query_controller, eval_controller, runs_controller, questions_controller,
)
from app.models.db_models import init_db

app = FastAPI(title="Agentic Research Analyst")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)

init_db()

app.include_router(document_controller.router)
app.include_router(query_controller.router)
app.include_router(eval_controller.router)
app.include_router(runs_controller.router)
app.include_router(questions_controller.router)


@app.get("/health")
def health():
    return {"status": "ok"}
