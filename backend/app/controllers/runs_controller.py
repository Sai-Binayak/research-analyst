from fastapi import APIRouter
from app.services import run_service

router = APIRouter(prefix="/runs", tags=["runs"])


@router.get("")
def list_runs(limit: int = 50):
    return run_service.list_runs(limit)
