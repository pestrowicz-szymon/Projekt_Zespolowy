from dataclasses import dataclass, field
from uuid import uuid4


@dataclass
class Answer:
    text: str
    correct: bool


@dataclass
class Question:
    text: str
    answers: list[Answer]
    id: str = field(default_factory=lambda: uuid4().hex)

    @property
    def multiple_choice(self) -> bool:
        return sum(answer.correct for answer in self.answers) > 1
