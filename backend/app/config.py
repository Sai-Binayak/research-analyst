from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- LLM provider (any OpenAI-compatible API: OpenAI, Gemini, Ollama, Groq, ...) ---
    openai_api_key: str = ""
    openai_base_url: str = ""          # empty = official OpenAI endpoint
    chat_model: str = "gpt-4o-mini"
    embed_model: str = "text-embedding-3-small"

    # --- Free-tier friendliness ---
    requests_per_minute: int = 0       # 0 = unlimited. Gemini free tier: ~10
    max_concurrent_requests: int = 4   # use 1 for a local Ollama model
    llm_max_retries: int = 5
    max_sub_questions: int = 3         # fewer sub-questions = fewer API calls per agent run
    eval_max_questions: int = 0        # 0 = use every question in questions.json

    # --- Storage / retrieval ---
    database_url: str = "sqlite:///./data/app.db"
    chroma_path: str = "./data/chroma"
    cors_origins: str = "http://localhost:5173"
    chunk_size: int = 800
    chunk_overlap: int = 120
    top_k: int = 6
    rerank_candidates: int = 15
    max_upload_mb: int = 20


settings = Settings()
