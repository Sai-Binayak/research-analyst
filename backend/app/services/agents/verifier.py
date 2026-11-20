import json
from app.services.agents.base_agent import BaseAgent
from app.utils.prompts import VERIFIER_SYSTEM


class Verifier(BaseAgent):
    name = "verifier"
    system_prompt = VERIFIER_SYSTEM

    async def check(self, evidence: list):
        if not any(e["passages"] for e in evidence):
            return [], {"tokens": 0, "cost_usd": 0.0}
        payload = json.dumps([
            {"sub_question": e["sub_question"],
             "passages": [{"chunk_id": p["chunk_id"], "text": p["text"]} for p in e["passages"]]}
            for e in evidence
        ])
        data, usage = await self.run_llm(payload, json_mode=True)
        return data.get("claims", []), usage
