from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

from app.controllers import eval_controller
from app.services import document_service, question_gen_service

router = APIRouter(prefix="/questions", tags=["questions"])

state = {"running": False, "done": 0, "total": 0, "error": None, "last": None}


class GenerateRequest(BaseModel):
    n_specific: int = Field(30, ge=1, le=100)
    include_generic: bool = True
    include_cross: bool = True
    doc_ids: Optional[List[int]] = None


def _progress(done: int, total: int):
    state["done"], state["total"] = done, total


async def _run(req: GenerateRequest):
    try:
        state["last"] = await question_gen_service.generate(
            n_specific=req.n_specific, include_generic=req.include_generic,
            include_cross=req.include_cross, doc_ids=req.doc_ids, on_progress=_progress,
        )
    except Exception as e:
        state["error"] = str(e)
    finally:
        state["running"] = False


@router.post("/generate")
async def generate(req: GenerateRequest, background: BackgroundTasks):
    """Builds eval_data/questions.json from the indexed documents (runs in the background)."""
    if state["running"]:
        raise HTTPException(409, "Question generation is already running")
    if eval_controller.state["running"]:
        raise HTTPException(409, "An evaluation is running; wait for it to finish")
    if not document_service.list_documents():
        raise HTTPException(400, "Upload at least one PDF first")
    state.update(running=True, error=None, done=0, total=req.n_specific, last=None)
    background.add_task(_run, req)
    return {"status": "started"}


@router.get("/status")
def status():
    return state


@router.get("")
def summary():
    return question_gen_service.load_summary()
