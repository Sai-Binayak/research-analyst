def _norm(s: str) -> str:
    return " ".join(s.lower().split())


def is_hit(passages: list, gold_ids: list, gold_phrases: list):
    """True/False if the retrieved passages contain the gold evidence.
    Returns None when the question has no gold info (skipped in averages)."""
    if not gold_ids and not gold_phrases:
        return None
    ids = {p["chunk_id"] for p in passages}
    if ids & set(gold_ids):
        return True
    blob = _norm(" \n ".join(p["text"] for p in passages))
    return any(_norm(ph) in blob for ph in gold_phrases)


def mean(xs: list) -> float:
    return sum(xs) / len(xs) if xs else 0.0
