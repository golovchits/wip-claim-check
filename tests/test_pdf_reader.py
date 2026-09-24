import io
from pathlib import Path

import pytest
from pypdf import PdfWriter

from app.pdf_reader import MAX_PASSAGE_CHARS, PDFError, ScannedPDFError, pack_sentences, read_passages

BRIEF = Path(__file__).parent / "Studio-WIP-Dev-Take-Home-Test.pdf"


# The brief PDF is kept out of the repo. Put it in tests/ to run this test.
@pytest.mark.skipif(not BRIEF.exists(), reason="WIP brief PDF not in tests/")
def test_brief_gives_numbered_passages_on_every_page():
    passages = read_passages(BRIEF.read_bytes())

    assert [p["id"] for p in passages] == list(range(1, len(passages) + 1))
    assert {p["page"] for p in passages} == {1, 2, 3, 4}
    # This sentence wraps across two lines in the PDF; it must land whole in one passage.
    sentence = "Keys come from the environment / a secret store — never committed, never baked into an image."
    assert any(sentence in p["text"] for p in passages)


def test_pack_keeps_sentences_whole_and_under_limit():
    sentences = ["A" * 300 + ".", "B" * 300 + ".", "C" * 100 + "."]

    passages = pack_sentences(sentences)

    assert passages == [sentences[0], sentences[1] + " " + sentences[2]]
    assert all(len(p) <= MAX_PASSAGE_CHARS for p in passages)


def test_pdf_without_text_is_detected_as_scanned():
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buffer = io.BytesIO()
    writer.write(buffer)

    with pytest.raises(ScannedPDFError):
        read_passages(buffer.getvalue())


def test_text_file_is_rejected():
    with pytest.raises(PDFError, match="not a PDF"):
        read_passages(b"just some text")


def test_too_many_pages_is_rejected():
    writer = PdfWriter()
    for _ in range(51):
        writer.add_blank_page(width=200, height=200)
    buffer = io.BytesIO()
    writer.write(buffer)

    with pytest.raises(PDFError, match="51 pages"):
        read_passages(buffer.getvalue())


def test_over_10_mb_is_rejected():
    with pytest.raises(PDFError, match="over 10 MB"):
        read_passages(b"%PDF-" + b"0" * (10 * 1024 * 1024))
