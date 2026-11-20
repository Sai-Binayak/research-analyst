from app.utils.chunking import chunk_text


def test_chunk_overlap():
    text = "word " * 1000
    chunks = chunk_text(text, size=200, overlap=40)
    assert len(chunks) > 1
    assert all(len(c) <= 200 for c in chunks)


def test_empty():
    assert chunk_text("") == []
