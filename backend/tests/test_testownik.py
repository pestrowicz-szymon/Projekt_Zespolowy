import io
import zipfile

from ai_engine.schemas import Answer, Question
from ai_engine.testownik import build_zip, format_question


def _question() -> Question:
    return Question(
        text="Które są poprawne?",
        answers=[
            Answer("a", True),
            Answer("b", True),
            Answer("c", False),
            Answer("d", False),
        ],
    )


def test_format_question_matches_readme_example():
    assert format_question(_question()) == "X1100\nKtóre są poprawne?\na\nb\nc\nd\n"


def test_build_zip_numbers_files():
    archive = zipfile.ZipFile(io.BytesIO(build_zip([_question(), _question()])))
    assert archive.namelist() == ["001.txt", "002.txt"]
    assert archive.read("001.txt").decode().startswith("X1100\n")
