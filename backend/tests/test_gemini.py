from types import SimpleNamespace

import pytest
from google.genai import errors

from ai_engine.gemini import GeminiDocumentReader, GeminiQuestionGenerator, _AnswerOut, _QuestionOut
from ai_engine.generator import GenerationError
from ai_engine.prompts import build_user_prompt


def _question(text: str, correct: tuple[bool, ...]) -> _QuestionOut:
    return _QuestionOut(
        question=text,
        answers=[_AnswerOut(text=f"opt {i}", correct=c) for i, c in enumerate(correct)],
    )


class _FakeModels:
    def __init__(self, parsed=None, error=None, text="raw"):
        self.parsed, self.error, self.text, self.calls = parsed, error, text, []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise self.error
        return SimpleNamespace(
            parsed=self.parsed,
            text=self.text,
            candidates=[SimpleNamespace(finish_reason="STOP")],
            prompt_feedback=None,
            usage_metadata=SimpleNamespace(prompt_token_count=10, candidates_token_count=2),
        )


def _generator(models: _FakeModels) -> GeminiQuestionGenerator:
    generator = GeminiQuestionGenerator(api_key="test-key", model="gemini-test")
    generator._client = SimpleNamespace(models=models)
    return generator


def test_requires_api_key():
    with pytest.raises(GenerationError, match="GEMINI_API_KEY"):
        GeminiQuestionGenerator(api_key="", model="gemini-test")


def test_converts_structured_output_and_drops_invalid_questions():
    models = _FakeModels(
        parsed=[
            _question("Q1", (True, True, False, False)),
            _question("No correct answer", (False, False, False, False)),
            _question("Q2", (False, False, True, False)),
        ]
    )
    questions = _generator(models).generate("material", 5, "pl")

    assert [q.text for q in questions] == ["Q1", "Q2"]
    assert questions[0].multiple_choice and not questions[1].multiple_choice
    assert models.calls[0]["model"] == "gemini-test"


def test_trims_to_requested_count():
    models = _FakeModels(parsed=[_question(f"Q{i}", (True, False, False, False)) for i in range(3)])
    assert len(_generator(models).generate("material", 2, "en")) == 2


def test_empty_response_raises_and_logs_raw_output(caplog):
    with pytest.raises(GenerationError, match="wystarczająco dużo treści"):
        _generator(_FakeModels(parsed=[], text="[]")).generate("material", 3, "pl")
    assert "Raw response: '[]'" in caplog.text
    assert "finish_reason=STOP" in caplog.text


def test_debug_logs_material_and_response(caplog):
    models = _FakeModels(parsed=[_question("Q1", (True, False, False, False))], text='[{"q": 1}]')
    with caplog.at_level("DEBUG", logger="ai_engine"):
        _generator(models).generate("Photosynthesis needs light.", 1, "en")
    assert "Photosynthesis needs light." in caplog.text
    assert '[{"q": 1}]' in caplog.text


def test_rate_limit_is_reported_in_polish():
    error = errors.ClientError(429, {"error": {"message": "quota", "status": "RESOURCE_EXHAUSTED"}})
    with pytest.raises(GenerationError, match="limit"):
        _generator(_FakeModels(error=error)).generate("material", 3, "pl")


def test_prompt_mentions_language_and_avoided_questions():
    prompt = build_user_prompt("text", 3, "en", avoid=["Old question?"])
    assert "in English" in prompt
    assert "Old question?" in prompt
    assert "language of the source material" in build_user_prompt("text", 3, "auto")


def test_list_generation_models_filters_by_action(monkeypatch):
    from ai_engine import gemini

    listed = [
        SimpleNamespace(name="models/gemini-a", supported_actions=["generateContent"]),
        SimpleNamespace(name="models/embed", supported_actions=["embedContent"]),
    ]
    fake_client = SimpleNamespace(models=SimpleNamespace(list=lambda: listed))
    monkeypatch.setattr(gemini.genai, "Client", lambda api_key: fake_client)
    assert gemini.list_generation_models("key") == ["gemini-a"]


def test_missing_model_message_names_the_model():
    error = errors.ClientError(404, {"error": {"message": "not found", "status": "NOT_FOUND"}})
    with pytest.raises(GenerationError, match="gemini-test"):
        _generator(_FakeModels(error=error)).generate("material", 3, "pl")


class _FakeFiles:
    def __init__(self):
        self.uploaded, self.deleted = [], []

    def upload(self, file, config):
        self.uploaded.append(config)
        return SimpleNamespace(name="files/abc", uri="https://files/abc", state=None)

    def delete(self, name):
        self.deleted.append(name)


def _reader(models: _FakeModels, files: _FakeFiles | None = None) -> GeminiDocumentReader:
    reader = GeminiDocumentReader(api_key="test-key", model="gemini-test")
    reader._client = SimpleNamespace(models=models, files=files or _FakeFiles())
    return reader


def test_reader_sends_small_file_inline():
    models = _FakeModels(text="  Treść slajdu  ")
    assert _reader(models).read("deck.pdf", "application/pdf", b"%PDF") == "Treść slajdu"
    part, prompt = models.calls[0]["contents"]
    assert part.inline_data.mime_type == "application/pdf"
    assert "Transcribe" in prompt


def test_reader_uploads_large_file_and_deletes_it(monkeypatch):
    from ai_engine import gemini

    monkeypatch.setattr(gemini, "_INLINE_LIMIT_BYTES", 2)
    files = _FakeFiles()
    models = _FakeModels(text="text")
    _reader(models, files).read("big.pdf", "application/pdf", b"%PDF-big")

    assert files.uploaded[0]["mime_type"] == "application/pdf"
    assert files.deleted == ["files/abc"]
    assert models.calls[0]["contents"][0].file_data.file_uri == "https://files/abc"


def test_reader_deletes_upload_even_when_generation_fails(monkeypatch):
    from ai_engine import gemini

    monkeypatch.setattr(gemini, "_INLINE_LIMIT_BYTES", 2)
    files = _FakeFiles()
    error = errors.ClientError(429, {"error": {"message": "quota", "status": "RESOURCE_EXHAUSTED"}})
    with pytest.raises(GenerationError, match="limit"):
        _reader(_FakeModels(error=error), files).read("big.pdf", "application/pdf", b"%PDF-big")
    assert files.deleted == ["files/abc"]


def test_reader_rejects_files_over_gemini_limit(monkeypatch):
    from ai_engine import gemini

    monkeypatch.setattr(gemini, "MAX_DOCUMENT_BYTES", 3)
    with pytest.raises(GenerationError, match="50 MB"):
        _reader(_FakeModels()).read("huge.pdf", "application/pdf", b"%PDF")
