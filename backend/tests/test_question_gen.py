import asyncio
import json

from app.services import question_gen_service as qg
from app.utils.prompts import CROSS_QUESTION_SYSTEM, QUESTION_GEN_SYSTEM

TOPICS = ["alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "golf", "hotel"]


def make_corpus():
    corpus = []
    for doc in (1, 2):
        for i, topic in enumerate(TOPICS):
            text = (f"The {topic} mechanism in document {doc} stabilises training by adjusting "
                    f"internal representations across layers and reducing variance. " * 4)
            corpus.append({"chunk_id": f"d{doc}-p{i + 1}-c0", "text": text,
                           "meta": {"doc_id": doc, "page": i + 1, "filename": f"doc{doc}.pdf"}})
    return corpus


def install_fakes(monkeypatch, corpus):
    calls = {"n": 0}

    async def fake_chat(system, user, json_mode=False):
        if system == CROSS_QUESTION_SYSTEM:
            return {"questions": [
                "How do the two documents differ in their training stabilisation approaches?",
                "Which document reports stronger evidence for its central mechanism?",
                "What assumptions underlie the methods compared across both documents?",
                "Do the conclusions of the documents agree about variance reduction?",
                "How does each document justify its choice of internal representations?",
            ]}, {}
        assert system == QUESTION_GEN_SYSTEM
        calls["n"] += 1
        if calls["n"] == 1:
            return {"skip": True}, {}  # boilerplate chunk is skipped
        if calls["n"] == 2:  # copies a 5+ word run from the passage -> must be rejected
            return {"skip": False,
                    "question": "why does stabilises training by adjusting internal representations matter"}, {}
        return {"skip": False, "question": f"What does mechanism variant {calls['n']} change about training?",
                "answer": "It stabilises training."}, {}

    monkeypatch.setattr(qg.vector_store, "get_all", lambda doc_ids=None: corpus)
    monkeypatch.setattr(qg.llm_service, "chat", fake_chat)


def test_generate_builds_all_categories(monkeypatch, tmp_path):
    corpus = make_corpus()
    install_fakes(monkeypatch, corpus)
    path = tmp_path / "questions.json"
    progress = []

    result = asyncio.run(qg.generate(
        n_specific=4, path=path, seed=1, on_progress=lambda d, t: progress.append((d, t))))

    questions = json.loads(path.read_text(encoding="utf-8"))
    cats = {}
    for q in questions:
        cats.setdefault(q["category"], []).append(q)

    assert len(cats["specific"]) == 4          # skipped + copied chunks were replaced
    assert len(cats["generic"]) == 6
    assert len(cats["cross"]) == 5             # two documents -> cross questions generated
    assert result["total"] == 15

    valid_ids = {c["chunk_id"] for c in corpus}
    for q in cats["specific"]:
        assert q["gold_chunk_ids"] and q["gold_chunk_ids"][0] in valid_ids
        assert "stabilises training by adjusting internal" not in q["question"]
    assert all(not q["gold_chunk_ids"] and not q["gold_phrases"] for q in cats["generic"] + cats["cross"])
    assert len({q["question"] for q in questions}) == len(questions)   # no duplicates

    dones = [d for d, _ in progress]
    assert dones == sorted(dones) and progress[-1][0] == progress[-1][1]


def test_single_document_skips_cross_and_second_run_keeps_backup(monkeypatch, tmp_path):
    corpus = [c for c in make_corpus() if c["meta"]["doc_id"] == 1]
    install_fakes(monkeypatch, corpus)
    path = tmp_path / "questions.json"

    first = asyncio.run(qg.generate(n_specific=3, path=path, seed=2, include_generic=False))
    assert "cross" not in first["by_category"]
    assert first["by_category"]["specific"] == 3

    asyncio.run(qg.generate(n_specific=2, path=path, seed=3))
    backup = tmp_path / "questions.backup.json"
    assert backup.exists() and len(json.loads(backup.read_text(encoding="utf-8"))) == 3


def test_no_usable_text_raises(monkeypatch, tmp_path):
    install_fakes(monkeypatch, [])
    try:
        asyncio.run(qg.generate(n_specific=2, path=tmp_path / "q.json"))
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
