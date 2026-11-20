import random

from app.utils.question_utils import (
    are_adjacent, category_of, copies_ngram, is_duplicate, is_good_chunk,
    sample_chunks, select_questions,
)

GOOD = ("Self attention relates different positions of a single sequence in order to compute a "
        "representation of the sequence. " * 4)


def chunk(doc, page, idx):
    return {"chunk_id": f"d{doc}-p{page}-c{idx}", "text": GOOD,
            "meta": {"doc_id": doc, "page": page, "filename": f"doc{doc}.pdf"}}


def test_is_good_chunk():
    assert is_good_chunk(GOOD)
    assert not is_good_chunk("short")
    assert not is_good_chunk("1 2 3 4 5 6 7 8 9 0 " * 30)
    assert not is_good_chunk(("Smith et al. arXiv preprint arXiv:1234 results here. " * 10))


def test_adjacent():
    assert are_adjacent("d1-p2-c3", "d1-p2-c4")
    assert not are_adjacent("d1-p2-c3", "d1-p2-c5")
    assert not are_adjacent("d1-p2-c3", "d1-p3-c4")


def test_copies_ngram():
    passage = "the quick brown fox jumps over the lazy dog near the river bank"
    assert copies_ngram("Why does the quick brown fox jumps over things?", passage)
    assert not copies_ngram("How does the fox behave near water?", passage)


def test_duplicates():
    assert is_duplicate("What is the main idea of attention?", ["What is the main idea of attention?"])
    assert not is_duplicate("How many heads are used?", ["What is the main idea of attention?"])


def test_sample_chunks_spreads_docs_and_skips_adjacent():
    corpus = [chunk(d, 1, i) for d in (1, 2) for i in range(10)]
    picked = sample_chunks(corpus, 6, random.Random(0))
    assert len({c["meta"]["doc_id"] for c in picked}) == 2
    ids = [c["chunk_id"] for c in picked]
    assert not any(are_adjacent(a, b) for a in ids for b in ids)


def test_category_and_selection():
    qs = [{"question": "a", "gold_phrases": ["x"]}, {"question": "b"},
          {"question": "c", "category": "cross"}, {"question": "d", "gold_phrases": ["y"]}]
    assert [category_of(q) for q in qs] == ["specific", "generic", "cross", "specific"]
    picked = select_questions(qs, 3)
    assert {category_of(q) for q in picked} == {"specific", "generic", "cross"}
    assert select_questions(qs, 0) == qs
