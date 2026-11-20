from app.services import llm_service


class BaseAgent:
    name = "base"
    system_prompt = ""

    async def run_llm(self, user: str, json_mode: bool = False):
        return await llm_service.chat(self.system_prompt, user, json_mode=json_mode)
