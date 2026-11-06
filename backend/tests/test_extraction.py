import pytest

from ai_engine.extraction import PlaceholderDocumentReader, extract_text, needs_reader
from ai_engine.generator import GenerationError


class _RecordingReader:
    def __init__(self):
        self.calls = []

    def read(self, filename, mime_type, data):
        self.calls.append((filename, mime_type, data))
        return "document text"


def test_plain_text_is_decoded_without_reader():
    assert extract_text("notes.md", "Zażółć".encode(), reader=None) == "Zażółć"


@pytest.mark.parametrize(
    ("filename", "mime_type"),
    [
        ("slides.PDF", "application/pdf"),
        (
            "lecture.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ),
        (
            "deck.pptx",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ),
        ("scan.jpg", "image/jpeg"),
    ],
)
def test_binary_documents_go_to_reader(filename, mime_type):
    reader = _RecordingReader()
    assert extract_text(filename, b"%PDF", reader) == "document text"
    assert reader.calls == [(filename, mime_type, b"%PDF")]
    assert needs_reader(filename)


def test_binary_document_without_reader_explains_requirement():
    with pytest.raises(GenerationError, match="AI_PROVIDER=gemini"):
        extract_text("scan.pdf", b"%PDF", reader=None)


def test_unsupported_extension_raises():
    with pytest.raises(ValueError):
        extract_text("virus.exe", b"MZ", reader=None)


def test_placeholder_reader_marks_file():
    assert "scan.pdf" in PlaceholderDocumentReader().read("scan.pdf", "application/pdf", b"")
