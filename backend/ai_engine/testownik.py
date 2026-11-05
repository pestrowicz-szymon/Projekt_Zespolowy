"""Export to the Testownik format (README, section 2.1).

Each question becomes ``001.txt``, ``002.txt``, ... inside a ZIP archive::

    X1100
    Question text
    answer a
    answer b
    ...
"""

import io
import zipfile
from collections.abc import Iterable

from ai_engine.schemas import Question


def format_question(question: Question) -> str:
    key = "X" + "".join("1" if answer.correct else "0" for answer in question.answers)
    lines = [key, question.text, *(answer.text for answer in question.answers)]
    return "\n".join(lines) + "\n"


def build_zip(questions: Iterable[Question]) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for index, question in enumerate(questions, start=1):
            archive.writestr(f"{index:03d}.txt", format_question(question))
    return buffer.getvalue()
