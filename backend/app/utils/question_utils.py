import re
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2]
QUESTIONS_PATH = BACKEND_DIR / "eval_data" / "questions.json"

# Work on any paper, so they only measure faithfulness (no gold evidence needed).
GENERIC_QUESTIONS = [
    "What problem does this work address, and why does it matter?",
    "What is the main contribution or key idea of this work?",
    "Which datasets or benchmarks were used in the experiments?",
    "What are the main results reported?",
    "What limitations or weaknesses do the authors acknowledge?",
    "What future work do the authors suggest?",
]

_WORD = re.compile(r"\w+")
_CHUNK_ID = re.compile(r"^d(\d+)-p(\d+)-c(\d+)$")


def category_of(q: dict) -> str:
    """specific = has gold evidence, generic/cross = scored on faithfulness only."""
    if q.get("category"):
        return q["category"]
    return "specific" if (q.get("gold_chunk_ids") or q.get("gold_phrases")) else "generic"


def select_questions(questions: list, limit: int) -> list:
    """Take up to `limit` questions, interleaving categories so small runs stay representative."""
    if not limit or limit >= len(questions):
        return questions
    groups = {}
    for q in questions:
        groups.setdefault(category_of(q), []).append(q)
    out = []
    while len(out) < limit and any(groups.values()):
        for g in groups.values():
            if g and len(out) < limit:
                out.append(g.pop(0))
    return out


def is_good_chunk(text: str) -> bool:
    """Filter out chunks that make poor question sources (references, tables, headers)."""
    if len(text) < 350:
        return False
    letters = sum(ch.isalpha() for ch in text) / len(text)
    digits = sum(ch.isdigit() for ch in text) / len(text)
    if letters < 0.6 or digits > 0.2:
        return False
    lower = text.lower()
    if lower.count("arxiv") >= 2 or lower.count("et al") >= 3:
        return False
    return True


def parse_chunk_id(cid: str):
    m = _CHUNK_ID.match(cid)
    return tuple(int(x) for x in m.groups()) if m else None


def are_adjacent(a: str, b: str) -> bool:
    """Neighbouring chunks on the same page share overlapping text."""
    pa, pb = parse_chunk_id(a), parse_chunk_id(b)
    return bool(pa and pb and pa[:2] == pb[:2] and abs(pa[2] - pb[2]) == 1)


def copies_ngram(question: str, passage: str, n: int = 5) -> bool:
    """True if the question reuses a run of n consecutive words from the passage.
    Copied wording would inflate keyword-search scores."""
    qw = [w.lower() for w in _WORD.findall(question)]
    pw = [w.lower() for w in _WORD.findall(passage)]
    if len(qw) < n or len(pw) < n:
        return False
    grams = {tuple(pw[i:i + n]) for i in range(len(pw) - n + 1)}
    return any(tuple(qw[i:i + n]) in grams for i in range(len(qw) - n + 1))


def is_duplicate(question: str, existing: list, threshold: float = 0.8) -> bool:
    a = {w.lower() for w in _WORD.findall(question)}
    for other in existing:
        b = {w.lower() for w in _WORD.findall(other)}
        if a and b and len(a & b) / len(a | b) >= threshold:
            return True
    return False


def sample_chunks(corpus: list, k: int, rng) -> list:
    """Pick up to k chunks, round-robin across documents, skipping adjacent chunks."""
    groups = {}
    for c in corpus:
        groups.setdefault(c["meta"]["doc_id"], []).append(c)
    for g in groups.values():
        rng.shuffle(g)
    order = list(groups)
    rng.shuffle(order)

    chosen = []
    while len(chosen) < k and any(groups.values()):
        for d in order:
            g = groups[d]
            while g:
                c = g.pop()
                if not any(are_adjacent(c["chunk_id"], x["chunk_id"]) for x in chosen):
                    chosen.append(c)
                    break
            if len(chosen) >= k:
                break
    return chosen
