from app.services.agents.base_agent import BaseAgent
from app.services import retrieval_service


class Retriever(BaseAgent):
    name = "retriever"

    async def retrieve(self, sub_question: str, doc_ids=None):
        hits = await retrieval_service.hybrid_search(sub_question, doc_ids, rerank=True)
        return {"sub_question": sub_question, "passages": hits}
