from typing import Any, Literal
from pydantic import BaseModel


class AgentEvent(BaseModel):
    """Contract between backend and frontend. Streamed over SSE."""
    agent: Literal["planner", "retriever", "verifier", "writer", "summary"]
    status: Literal["started", "done", "error"]
    output: Any = None
    tokens: int = 0
