from app.utils.metrics import is_hit, mean

PASSAGES = [
    {"chunk_id": "d1-p1-c0", "text": "Transformers use self-attention."},
    {"chunk_id": "d1-p2-c1", "text": "RNNs process tokens sequentially."},
]


def test_hit_by_id():
    assert is_hit(PASSAGES, ["d1-p2-c1"], []) is True


def test_hit_by_phrase_is_case_and_whitespace_insensitive():
    assert is_hit(PASSAGES, [], ["SELF-ATTENTION"]) is True


def test_miss():
    assert is_hit(PASSAGES, ["d9-p9-c9"], ["nonexistent phrase"]) is False


def test_no_gold_returns_none():
    assert is_hit(PASSAGES, [], []) is None


def test_mean():
    assert mean([]) == 0.0
    assert mean([1, 0]) == 0.5
