from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.services import eval_service

router = APIRouter(prefix="/eval", tags=["eval"])

state = {"running": False, "current": None, "done": 0, "total": 0, "error": None}


def _progress(done: int, total: int):
    state["done"], state["total"] = done, total


async def _run(setups: list):
    try:
        for s in setups:
            state.update(current=s, done=0, total=0)
            result = await eval_service.run_eval(s, on_progress=_progress)
            eval_service.save_result(result)
    except Exception as e:
        state["error"] = str(e)
    finally:
        state.update(running=False, current=None)


@router.post("/run")
async def run(background: BackgroundTasks, setup: str = "all"):
    """setup = naive | rerank | agent | all. Runs in the background; poll /eval/status."""
    if state["running"]:
        raise HTTPException(409, "An evaluation is already running")
    setups = list(eval_service.SETUPS) if setup == "all" else [setup]
    if any(s not in eval_service.SETUPS for s in setups):
        raise HTTPException(400, "setup must be naive, rerank, agent or all")
    state.update(running=True, error=None, done=0, total=0, current=setups[0])
    background.add_task(_run, setups)
    return {"status": "started", "setups": setups}


@router.get("/status")
def status():
    return state


@router.get("/results")
def results():
    return eval_service.latest_results()
