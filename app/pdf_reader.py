import io
import re

from pypdf import PdfReader
from pypdf.errors import PyPdfError

MAX_PASSAGE_CHARS = 500
MAX_BYTES = 10 * 1024 * 1024
MAX_PAGES = 50


class PDFError(Exception):
    """The upload can't be checked. The message is shown to the user as is."""


class ScannedPDFError(PDFError):
    pass


def split_sentences(text):
    # Cut after ". ", "? " or "! ", and just before each bullet "•".
    parts = re.split(r"(?<=[.?!]) |(?=•)", text)
    return [part.strip() for part in parts if part.strip()]


def pack_sentences(sentences):
    # Add whole sentences to a passage until the next one would push it past the limit.
    # A single sentence longer than the limit becomes its own passage, never cut.
    passages = []
    current = ""
    for sentence in sentences:
        if current and len(current) + 1 + len(sentence) > MAX_PASSAGE_CHARS:
            passages.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        passages.append(current)
    return passages


def read_passages(pdf_bytes):
    # Every real PDF starts with "%PDF-", whatever the file is called.
    if not pdf_bytes.startswith(b"%PDF-"):
        raise PDFError("This file is not a PDF.")
    if len(pdf_bytes) > MAX_BYTES:
        raise PDFError("This PDF is over 10 MB, please upload a smaller one.")
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        if len(reader.pages) > MAX_PAGES:
            raise PDFError(f"This PDF has {len(reader.pages)} pages, the limit is {MAX_PAGES}.")
        passages = []
        for page_number, page in enumerate(reader.pages, start=1):
            # Join the wrapped lines and collapse every run of whitespace into one space.
            text = " ".join(page.extract_text().split())
            for chunk in pack_sentences(split_sentences(text)):
                passages.append({"id": len(passages) + 1, "page": page_number, "text": chunk})
    except PyPdfError:
        # Damaged or password-protected files.
        raise PDFError("This PDF could not be read. It may be damaged or password-protected.")
    if not passages:
        raise ScannedPDFError("Looks like a scanned PDF, not supported yet")
    return passages
