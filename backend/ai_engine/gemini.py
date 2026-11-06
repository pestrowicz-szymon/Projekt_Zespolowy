"""Google Gemini provider (``AI_PROVIDER=gemini``).

Two steps, both through the official ``google-genai`` SDK:

* :class:`GeminiDocumentReader` turns uploaded PDF, DOCX, PPTX and image files
  into text (including OCR of scans and photos),
* :class:`GeminiQuestionGenerator` generates questions from that text with
  structured JSON output, validated against :class:`_QuestionOut`.
"""

import io
import logging
import time
from collections.abc import Sequence

from google import genai
from google.genai import errors, types
from pydantic import BaseModel, Field

from ai_engine.generator import GenerationError
from ai_engine.prompts import READ_DOCUMENT_PROMPT, SYSTEM_PROMPT, build_user_prompt
from ai_engine.schemas import Answer, Question

logger = logging.getLogger(__name__)


class _AnswerOut(BaseModel):
    text: str
    correct: bool


class _QuestionOut(BaseModel):
    question: str
    answers: list[_AnswerOut] = Field(min_length=4, max_length=4)


def _make_client(api_key: str) -> genai.Client:
    if not api_key:
        raise GenerationError("Brak klucza GEMINI_API_KEY w pliku backend/.env.")
    return genai.Client(api_key=api_key)


# Gemini limit for PDF files (inline and Files API alike).
MAX_DOCUMENT_BYTES = 50 * 1024 * 1024
# Larger files go through the Files API instead of being inlined in the request.
_INLINE_LIMIT_BYTES = 15 * 1024 * 1024
_FILE_READY_TIMEOUT_SECONDS = 60


class GeminiDocumentReader:
    """Reads a document with Gemini: native text, scans (OCR), images, slides."""

    def __init__(self, api_key: str, model: str) -> None:
        self.model = model
        self._client = _make_client(api_key)

    def read(self, filename: str, mime_type: str, data: bytes) -> str:
        if len(data) > MAX_DOCUMENT_BYTES:
            raise GenerationError(f"Plik {filename} jest za duży dla Gemini (limit 50 MB).")

        uploaded = None
        try:
            if len(data) <= _INLINE_LIMIT_BYTES:
                part = types.Part.from_bytes(data=data, mime_type=mime_type)
            else:
                uploaded = self._upload(filename, mime_type, data)
                part = types.Part.from_uri(file_uri=uploaded.uri, mime_type=mime_type)
            response = self._client.models.generate_content(
                model=self.model,
                contents=[part, READ_DOCUMENT_PROMPT],
                config=types.GenerateContentConfig(temperature=0),
            )
        except errors.APIError as exc:
            logger.warning(
                "Gemini API error %s while reading %s: %s", exc.code, filename, exc.message
            )
            raise GenerationError(_user_message(exc, self.model)) from exc
        finally:
            if uploaded is not None:
                self._delete(uploaded)

        text = _raw(response).strip()
        logger.debug(
            "Gemini read %s (%s, %d bytes): %s, %d chars\n--- text (start) ---\n%s\n--- end ---",
            filename,
            mime_type,
            len(data),
            _summary(response),
            len(text),
            text[:_PREVIEW_CHARS],
        )
        if _finish_reason(response) == "MAX_TOKENS":
            logger.warning("Text of %s was cut off at the model's output limit.", filename)
        if not text:
            logger.warning("Gemini read no text from %s (%s)", filename, _summary(response))
        return text

    def _upload(self, filename: str, mime_type: str, data: bytes) -> types.File:
        uploaded = self._client.files.upload(
            file=io.BytesIO(data), config={"mime_type": mime_type, "display_name": filename}
        )
        # Large files may need a moment of server-side processing before use.
        deadline = time.monotonic() + _FILE_READY_TIMEOUT_SECONDS
        while uploaded.state and uploaded.state.name == "PROCESSING":
            if time.monotonic() > deadline:
                self._delete(uploaded)
                raise GenerationError(f"Gemini zbyt długo przetwarza plik {filename}.")
            time.sleep(2)
            uploaded = self._client.files.get(name=uploaded.name)
        if uploaded.state and uploaded.state.name == "FAILED":
            self._delete(uploaded)
            raise GenerationError(f"Gemini nie zdołał przetworzyć pliku {filename}.")
        return uploaded

    def _delete(self, uploaded: types.File) -> None:
        # Stage 1 keeps documents only temporarily, so don't leave them on Google's side.
        try:
            self._client.files.delete(name=uploaded.name)
        except errors.APIError as exc:
            logger.warning("Could not delete uploaded file %s: %s", uploaded.name, exc.message)


class GeminiQuestionGenerator:
    def __init__(self, api_key: str, model: str) -> None:
        self.model = model
        self._client = _make_client(api_key)

    def generate(
        self, text: str, count: int, language: str, avoid: Sequence[str] = ()
    ) -> list[Question]:
        prompt = build_user_prompt(text, count, language, avoid)
        logger.debug(
            "Gemini request: model=%s count=%s language=%s material=%d chars\n"
            "--- material (start) ---\n%s\n--- end ---",
            self.model,
            count,
            language,
            len(text),
            text[:_PREVIEW_CHARS],
        )
        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=list[_QuestionOut],
                    temperature=0.7,
                ),
            )
        except errors.APIError as exc:
            logger.warning("Gemini API error %s: %s", exc.code, exc.message)
            raise GenerationError(_user_message(exc, self.model)) from exc

        logger.debug(
            "Gemini response: %s\n--- raw ---\n%s\n--- end ---", _summary(response), _raw(response)
        )

        questions = [_to_question(q) for q in response.parsed or [] if _is_valid(q)]
        if not questions:
            logger.warning(
                "Gemini returned no usable questions (%s, material=%d chars). Raw response: %r. "
                "Set AI_LOG_LEVEL=DEBUG to log the material that was sent.",
                _summary(response),
                len(text),
                _raw(response)[:_PREVIEW_CHARS],
            )
            raise GenerationError(
                "Model nie zwrócił żadnych pytań. Sprawdź, czy materiał zawiera wystarczająco "
                "dużo treści, i spróbuj ponownie."
            )
        return questions[:count]


_PREVIEW_CHARS = 1000


def _raw(response: types.GenerateContentResponse) -> str:
    try:
        return response.text or ""
    except ValueError:  # e.g. the response was blocked and has no text part
        return ""


def _finish_reason(response: types.GenerateContentResponse) -> str | None:
    candidate = response.candidates[0] if response.candidates else None
    reason = candidate.finish_reason if candidate else None
    return getattr(reason, "name", reason)


def _summary(response: types.GenerateContentResponse) -> str:
    feedback = response.prompt_feedback
    usage = response.usage_metadata
    parts = [
        f"finish_reason={_finish_reason(response)}",
        f"block_reason={feedback.block_reason if feedback else None}",
    ]
    if usage:
        parts.append(f"tokens in={usage.prompt_token_count} out={usage.candidates_token_count}")
    return ", ".join(parts)


def _is_valid(question: _QuestionOut) -> bool:
    return bool(question.question.strip()) and any(a.correct for a in question.answers)


def _to_question(question: _QuestionOut) -> Question:
    return Question(
        text=question.question.strip(),
        answers=[Answer(text=a.text.strip(), correct=a.correct) for a in question.answers],
    )


def list_generation_models(api_key: str) -> list[str]:
    """Model IDs this API key can use with ``generateContent``."""
    client = genai.Client(api_key=api_key)
    return sorted(
        model.name.removeprefix("models/")
        for model in client.models.list()
        if model.name and "generateContent" in (model.supported_actions or [])
    )


def _user_message(exc: errors.APIError, model: str) -> str:
    if exc.code == 429:
        return "Przekroczono limit zapytań do Gemini (darmowy plan). Spróbuj za chwilę."
    if exc.code in (401, 403):
        return "Klucz GEMINI_API_KEY jest nieprawidłowy lub nie ma dostępu do modelu."
    if exc.code == 404:
        return (
            f"Model Gemini „{model}” nie jest dostępny. Zmień GEMINI_MODEL w backend/.env "
            "(listę modeli pokaże: python manage.py gemini_models)."
        )
    return f"Błąd Gemini API ({exc.code}): {exc.message}"
