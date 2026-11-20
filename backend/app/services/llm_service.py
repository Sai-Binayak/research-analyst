import json
import time
import asyncio
import contextvars
from openai import AsyncOpenAI, APIConnectionError, APIStatusError, RateLimitError

from app.config import settings

# max_retries=0: we do our own retrying so we can respect free-tier rate limits.
client = AsyncOpenAI(
    api_key=settings.openai_api_key or "not-needed",
    base_url=settings.openai_base_url or None,
    max_retries=0,
)

# USD per 1M tokens. Unknown models (Gemini free tier, Ollama, ...) cost $0.
CHAT_PRICING = {"gpt-4o-mini": (0.15, 0.60), "gpt-4o": (2.50, 10.00)}
EMBED_PRICING = {"text-embedding-3-small": 0.02, "text-embedding-3-large": 0.13}


class UsageTracker:
    """Accumulates tokens and cost for every LLM call made in the current context."""

    def __init__(self):
        self.tokens = 0
        self.cost_usd = 0.0

    def add(self, tokens: int, cost: float):
        self.tokens += tokens
        self.cost_usd += cost


_current = contextvars.ContextVar("usage_tracker", default=None)


def start_tracking() -> UsageTracker:
    tracker = UsageTracker()
    _current.set(tracker)
    return tracker


def _record(tokens: int, cost: float):
    tracker = _current.get()
    if tracker:
        tracker.add(tokens, cost)


def estimate_chat_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    pin, pout = CHAT_PRICING.get(model, (0.0, 0.0))
    return (prompt_tokens * pin + completion_tokens * pout) / 1_000_000


class RateLimiter:
    """Spaces requests evenly so we stay under a requests-per-minute cap."""

    def __init__(self, rpm: int):
        self.interval = 60.0 / rpm if rpm > 0 else 0.0
        self._lock = asyncio.Lock()
        self._next = 0.0

    async def wait(self):
        if not self.interval:
            return
        async with self._lock:
            now = time.monotonic()
            start = max(now, self._next)
            self._next = start + self.interval
        if start > now:
            await asyncio.sleep(start - now)


_limiter = RateLimiter(settings.requests_per_minute)
_semaphore = asyncio.Semaphore(max(1, settings.max_concurrent_requests))


async def _with_retries(make_call):
    """Rate-limit, then retry on 429s, connection problems, 5xx errors and bad JSON.
    Auth errors and bad model names (other 4xx) fail immediately with a clear message."""
    retries = max(1, settings.llm_max_retries)
    for attempt in range(retries):
        async with _semaphore:
            await _limiter.wait()
            try:
                return await make_call()
            except (RateLimitError, APIConnectionError, ValueError) as e:
                err = e
            except APIStatusError as e:
                if e.status_code < 500:
                    raise
                err = e
        if attempt == retries - 1:
            raise err
        await asyncio.sleep(min(5 * 2 ** attempt, 60))


async def chat(system: str, user: str, json_mode: bool = False):
    """Returns (content, usage). One place for retries, rate limits and cost tracking."""
    kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}

    async def call():
        resp = await client.chat.completions.create(
            model=settings.chat_model,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
            timeout=120,
            **kwargs,
        )
        content = resp.choices[0].message.content or ""
        u = resp.usage
        prompt_t = (u.prompt_tokens or 0) if u else 0
        completion_t = (u.completion_tokens or 0) if u else 0
        tokens = (u.total_tokens or (prompt_t + completion_t)) if u else 0
        cost = estimate_chat_cost(settings.chat_model, prompt_t, completion_t)
        parsed = json.loads(content) if json_mode else content  # ValueError -> retried
        _record(tokens, cost)
        return parsed, {"tokens": tokens, "cost_usd": cost}

    return await _with_retries(call)


async def embed(texts: list):
    async def call():
        resp = await client.embeddings.create(model=settings.embed_model, input=texts)
        tokens = (resp.usage.total_tokens or 0) if resp.usage else 0
        _record(tokens, tokens * EMBED_PRICING.get(settings.embed_model, 0.0) / 1_000_000)
        return [d.embedding for d in resp.data]

    return await _with_retries(call)
