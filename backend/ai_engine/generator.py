"""Question generators.

Every provider implements :class:`QuestionGenerator`. ``get_generator()``
picks one based on the ``AI_PROVIDER`` setting.
"""

import random
from collections.abc import Sequence
from typing import Protocol

from ai_engine.schemas import Answer, Question


class GenerationError(Exception):
    """A provider failed in a way that should be shown to the user."""


class QuestionGenerator(Protocol):
    def generate(
        self, text: str, count: int, language: str, avoid: Sequence[str] = ()
    ) -> list[Question]:
        """Generate up to ``count`` questions from ``text``.

        ``language`` is ``"pl"``, ``"en"`` or ``"auto"`` (language of the material).
        ``avoid`` lists existing question texts that must not be repeated.
        The model decides per question whether it has one or more correct answers.
        """
        ...


class MockQuestionGenerator:
    """Returns deterministic-looking fake questions; no model required."""

    _TEMPLATES = {
        "pl": ("Przykładowe pytanie nr {n} wygenerowane z materiału?", "Odpowiedź"),
        "en": ("Sample question no. {n} generated from the material?", "Answer"),
    }

    def generate(
        self, text: str, count: int, language: str, avoid: Sequence[str] = ()
    ) -> list[Question]:
        question_tpl, answer_word = self._TEMPLATES.get(language, self._TEMPLATES["pl"])
        questions = []
        for n in range(1, count + 1):
            correct = set(random.sample(range(4), k=random.choice((1, 1, 2, 3))))
            answers = [
                Answer(text=f"{answer_word} {'abcd'[i]}", correct=i in correct) for i in range(4)
            ]
            questions.append(Question(text=question_tpl.format(n=n), answers=answers))
        return questions


class OllamaQuestionGenerator:
    """Stage 1 TODO (AI module): call the Ollama HTTP API (``/api/chat``)."""

    def __init__(self, base_url: str, model: str) -> None:
        self.base_url = base_url
        self.model = model

    def generate(
        self, text: str, count: int, language: str, avoid: Sequence[str] = ()
    ) -> list[Question]:
        raise GenerationError("Integracja z Ollama nie jest jeszcze gotowa.")


def get_generator() -> QuestionGenerator:
    from django.conf import settings

    if settings.AI_PROVIDER == "ollama":
        return OllamaQuestionGenerator(settings.OLLAMA_BASE_URL, settings.OLLAMA_MODEL)
    if settings.AI_PROVIDER == "gemini":
        from ai_engine.gemini import GeminiQuestionGenerator

        return GeminiQuestionGenerator(settings.GEMINI_API_KEY, settings.GEMINI_MODEL)
    return MockQuestionGenerator()
