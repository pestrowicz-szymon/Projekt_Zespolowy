"""Text extraction from uploaded documents.

Stage 1 TODO (AI module): PDF, DOCX and PPTX parsing and OCR for scans.
For now only plain-text formats are decoded; binary formats return a
placeholder so the rest of the pipeline can be developed end to end.
"""

from pathlib import Path
from typing import BinaryIO

SUPPORTED_EXTENSIONS = (".pdf", ".docx", ".pptx", ".txt", ".md")
_PLAIN_TEXT_EXTENSIONS = (".txt", ".md")


def extract_text(filename: str, stream: BinaryIO) -> str:
    extension = Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported file type: {extension or filename}")
    if extension in _PLAIN_TEXT_EXTENSIONS:
        return stream.read().decode("utf-8", errors="replace")
    # TODO: use a real parser (e.g. pypdf, python-docx, python-pptx, OCR).
    return f"[Extraction of {extension} files is not implemented yet: {filename}]"
