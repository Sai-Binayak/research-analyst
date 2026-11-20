import json
import os
import random
from pathlib import Path

from app.models import vector_store
from app.services import llm_service
from app.utils.prompts import QUESTION_GEN_SYSTEM, CROSS_QUESTION_SYSTEM
from app.utils.question_utils import (
    GENERIC_QUESTIONS, QUESTIONS_PATH, category_of, copies_ngram, is_duplicate,
    is_good_chunk, sample_chunks,
)

CROSS_COUNT = 5
MIN_WORDS = 5


def _clean(data) -> str:
    if not isinstance(data, dict) or data.get("skip"):
        return ""
    q = data.get("question")
    q = q.strip() if isinstance(q, str) else ""
    return q if len(q.split()) >= MIN_WORDS else ""


async def _specific(chunks: list, n: int, progress):
    """One LLM call per sampled chunk; the chunk id becomes the gold evidence."""
    out, errors, last_error = [], 0, None
    for c in chunks:
        if len(out) >= n:
            break
        try:
            data, _ = await llm_service.chat(QUESTION_GEN_SYSTEM, c["text"], json_mode=True)
        except Exception as e:
            errors += 1
            last_error = e
            continue
        q = _clean(data)
        if not q or copies_ngram(q, c["text"]) or is_duplicate(q, [x["question"] for x in out]):
            continue
        answer = data.get("answer")
        out.append({
            "question": q,
            "gold_answer": answer.strip() if isinstance(answer, str) else "",
            "gold_chunk_ids": [c["chunk_id"]],
            "gold_phrases": [],
            "category": "specific",
            "source": f"{c['meta']['filename']} p.{c['meta']['page']}",
        })
        progress(len(out))
    return out, errors, last_error


async def _cross(corpus: list, rng, existing: list) -> list:
    by_doc = {}
    for c in corpus:
        by_doc.setdefault(c["meta"]["doc_id"], []).append(c)
    doc_ids = list(by_doc)
    rng.shuffle(doc_ids)
    parts = []
    for d in doc_ids[:6]:
        picks = rng.sample(by_doc[d], min(2, len(by_doc[d])))
        body = "\n---\n".join(p["text"][:600] for p in picks)
        parts.append(f"## {picks[0]['meta']['filename']}\n{body}")
    user = f"Write {CROSS_COUNT} questions.\n\n" + "\n\n".join(parts)
    data, _ = await llm_service.chat(CROSS_QUESTION_SYSTEM, user, json_mode=True)
    raw = data.get("questions", []) if isinstance(data, dict) else []

    out = []
    for q in raw:
        if not isinstance(q, str) or len(q.split()) < MIN_WORDS:
            continue
        if is_duplicate(q, existing + [x["question"] for x in out]):
            continue
        out.append({"question": q.strip(), "gold_chunk_ids": [], "gold_phrases": [],
                    "category": "cross"})
    return out


def _write(path: Path, questions: list):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():  # keep the previous set so nothing is lost
        path.with_name("questions.backup.json").write_text(
            path.read_text(encoding="utf-8"), encoding="utf-8")
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(questions, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)


def summarize(questions: list) -> dict:
    by_cat = {}
    for q in questions:
        cat = category_of(q)
        by_cat[cat] = by_cat.get(cat, 0) + 1
    return {"total": len(questions), "by_category": by_cat}


def load_summary(path=QUESTIONS_PATH) -> dict:
    try:
        return summarize(json.loads(Path(path).read_text(encoding="utf-8")))
    except (OSError, ValueError):
        return {"total": 0, "by_category": {}}


async def generate(n_specific: int = 30, include_generic: bool = True, include_cross: bool = True,
                   doc_ids=None, on_progress=None, seed=None, path=QUESTIONS_PATH) -> dict:
    corpus = [c for c in vector_store.get_all(doc_ids) if is_good_chunk(c["text"])]
    if not corpus:
        raise ValueError("No usable text found. Upload a PDF with extractable text first.")

    rng = random.Random(seed)
    budget = n_specific + max(5, n_specific // 2)  # oversample: some chunks get skipped
    chunks = sample_chunks(corpus, budget, rng)

    do_cross = include_cross and len({c["meta"]["doc_id"] for c in corpus}) >= 2
    total = n_specific + (1 if do_cross else 0)

    def progress(done: int):
        if on_progress:
            on_progress(min(done, total), total)

    progress(0)
    specific, errors, last_error = await _specific(chunks, n_specific, progress)
    if not specific and errors:
        raise RuntimeError(f"Question generation failed: {last_error}")

    cross, cross_error = [], None
    if do_cross:
        try:
            cross = await _cross(corpus, rng, [q["question"] for q in specific])
        except Exception as e:
            cross_error = str(e)
        progress(total)

    generic = [{"question": q, "gold_chunk_ids": [], "gold_phrases": [], "category": "generic"}
               for q in GENERIC_QUESTIONS] if include_generic else []

    questions = specific + generic + cross
    _write(path, questions)
    result = summarize(questions)
    result.update(requested_specific=n_specific, llm_errors=errors, cross_error=cross_error)
    return result
