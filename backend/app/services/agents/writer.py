import json
from app.services.agents.base_agent import BaseAgent
from app.utils.prompts import WRITER_SYSTEM

NO_EVIDENCE = "The indexed documents do not contain evidence that answers this question."


class Writer(BaseAgent):
    name = "writer"
    system_prompt = WRITER_SYSTEM

    async def write(self, question: str, claims: list):
        supported = [c for c in claims if c.get("supported")]
        if not supported:
            return NO_EVIDENCE, {"tokens": 0, "cost_usd": 0.0}
        user = f"Question: {question}\n\nVerified claims:\n{json.dumps(supported, indent=2)}"
        return await self.run_llm(user)
