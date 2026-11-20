# Agentic Research Analyst

Upload PDFs, ask complex questions, and a team of agents (planner, retriever, verifier,
writer) answers with cited evidence. Includes two single-shot RAG baselines and an
evaluation harness that compares all three approaches on hit rate, faithfulness,
latency and cost.

## Architecture (MVC + service layer)
- Model: backend/app/models (DB tables, schemas, SSE event contract, vector store)
- View: frontend/src (React)
- Controller: backend/app/controllers (thin FastAPI routers)
- Services: backend/app/services (ingestion, retrieval, agents, evaluation)

Dependencies point downward only: controllers -> services -> models.

## Features
- Hybrid retrieval: vector search + BM25 fused with reciprocal rank fusion
- LLM-based reranker (swappable for a cross-encoder)
- Multi-agent pipeline: planner -> parallel retrievers -> verifier -> writer, streamed over SSE
- Verifier extracts atomic claims and checks each against retrieved passages
- Cost, token and latency tracking for every LLM call (contextvar-based tracker)
- Evaluation: naive vs reranker vs multi-agent, run in the background with progress
- Run history stored in SQLite
- React UI: upload/delete docs, agent timeline, numbered citations, evaluation chart

## Run locally
Backend (always start from inside backend/, paths are relative):
    cd backend
    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env        # add OPENAI_API_KEY
    uvicorn app.main:app --reload

Frontend:
    cd frontend
    cp .env.example .env
    npm install
    npm run dev                 # http://localhost:5173

Tests (from backend/):
    pytest

API docs: http://localhost:8000/docs

## Suggested workflow
1. Upload 1-2 PDFs on the Documents tab
2. Ask the same question in Naive, Reranker and Multi-agent modes
3. Write 30-50 real questions in backend/eval_data/questions.json
4. Evaluation tab -> "Run all three" and paste the table below into this README

## Evaluation table (fill in after running)
| Setup | Hit rate | Faithfulness | Latency | Cost/query |
|---|---|---|---|---|
| Naive RAG | | | | |
| RAG + reranker | | | | |
| Multi-agent + verifier | | | | |

## Evaluation questions
Three kinds of questions, scored differently:
- specific: generated from a real chunk, so the chunk id is the gold evidence.
  Scored on hit rate AND faithfulness.
- generic ("What are the limitations?"): work on any paper. Faithfulness only.
- cross: need two or more documents (needs 2+ PDFs). Faithfulness only.

Generate them from your indexed PDFs: Evaluation tab -> "Question set" -> Generate
(or POST /questions/generate). The previous set is saved to eval_data/questions.backup.json.
Generated questions are told to avoid copying the passage wording, and any that reuse
5+ consecutive words are rejected, so keyword search is not unfairly favoured.

You can also write questions by hand in eval_data/questions.json:
    {"question": "...", "gold_phrases": ["short exact phrase"], "gold_chunk_ids": [],
     "category": "specific"}
A retrieval counts as a hit if any gold chunk id or gold phrase appears in the retrieved
passages. Results are reported overall and per category.

## Known limitations
- Sliding-window chunking (not section-aware)
- LLM reranker adds cost/latency; a cross-encoder would be cheaper at scale
- No authentication: do not expose publicly with your API key
- Scanned PDFs (no extractable text) are rejected; add OCR to support them
- Evaluation state is in-memory, so it assumes a single backend process

## Free-tier setup (no paid API needed)
The backend talks to any OpenAI-compatible API. Copy backend/.env.example to .env and
uncomment ONE provider block:
- Gemini free tier: key from aistudio.google.com. Rate limits are low, so
  REQUESTS_PER_MINUTE throttles requests and EVAL_MAX_QUESTIONS keeps evaluation runs small.
- Ollama: fully local and unlimited, but quality and speed depend on your hardware.

IMPORTANT: vectors from different embedding models are incompatible. If you change
EMBED_MODEL, delete backend/data and re-upload your PDFs.
