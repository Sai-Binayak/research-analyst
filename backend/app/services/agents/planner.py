from app.config import settings
from app.services.agents.base_agent import BaseAgent
from app.utils.prompts import PLANNER_SYSTEM


class Planner(BaseAgent):
    name = "planner"
    system_prompt = PLANNER_SYSTEM

    async def plan(self, question: str):
        data, usage = await self.run_llm(question, json_mode=True)
        subs = data.get("sub_questions") or []
        subs = [s.strip() for s in subs if isinstance(s, str) and s.strip()][:settings.max_sub_questions]
        return (subs or [question]), usage
