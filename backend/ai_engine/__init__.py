"""AI module: text extraction, question generation and Testownik export.

This package is deliberately independent of Django REST Framework so the AI
provider can be swapped (README, "Wymienność dostawcy AI") without touching
the API layer.
"""

from ai_engine.generator import QuestionGenerator, get_generator
from ai_engine.schemas import Answer, Question

__all__ = ["Answer", "Question", "QuestionGenerator", "get_generator"]
