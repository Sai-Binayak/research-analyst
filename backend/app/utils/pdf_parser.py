from pypdf import PdfReader


def parse_pdf(path: str):
    """Return a list of (page_number, text)."""
    reader = PdfReader(path)
    return [(i + 1, page.extract_text() or "") for i, page in enumerate(reader.pages)]
