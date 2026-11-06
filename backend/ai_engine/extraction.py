"""Text extraction from uploaded documents.

Plain-text formats are decoded locally. Everything else (PDF, DOCX, PPTX and
images, including scans that need OCR) goes to a :class:`DocumentReader`
supplied by the AI provider; see ``get_document_reader()``.
"""

from pathlib import Path
from typing import Protocol

from ai_engine.generator import GenerationError

_PLAIN_TEXT_EXTENSIONS = (".txt", ".md")
_READER_MIME_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
}
SUPPORTED_EXTENSIONS = (*_READER_MIME_TYPES, *_PLAIN_TEXT_EXTENSIONS)


class DocumentReader(Protocol):
    def read(self, filename: str, mime_type: str, data: bytes) -> str:
        """Return the text content of a binary document (OCR where needed)."""
        ...


class PlaceholderDocumentReader:
    """Used with the mock provider: no AI call, just a marker in the material."""

    def read(self, filename: str, mime_type: str, data: bytes) -> str:
        return f"[Mock: treść pliku {filename} nie została odczytana]"


def needs_reader(filename: str) -> bool:
    return Path(filename).suffix.lower() in _READER_MIME_TYPES


def extract_text(filename: str, data: bytes, reader: DocumentReader | None) -> str:
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {extension or filename}")
    if extension in _PLAIN_TEXT_EXTENSIONS:
        return data.decode("utf-8", errors="replace")
    if reader is None:
        raise GenerationError(
            f"Odczyt plików {extension} wymaga AI_PROVIDER=gemini. Wklej tekst albo użyj .txt/.md."
        )
    return reader.read(filename, _READER_MIME_TYPES[extension], data)


def get_document_reader() -> DocumentReader | None:
    from django.conf import settings

    if settings.AI_PROVIDER == "gemini":
        from ai_engine.gemini import GeminiDocumentReader

        return GeminiDocumentReader(settings.GEMINI_API_KEY, settings.GEMINI_MODEL)
    if settings.AI_PROVIDER == "mock":
        return PlaceholderDocumentReader()
    # TODO (AI module): local extraction for Ollama (e.g. pypdf, python-docx, OCR).
    return None
