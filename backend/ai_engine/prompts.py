"""Prompts shared by LLM providers (Gemini now, Ollama later)."""

from collections.abc import Sequence

# Keeps a single request well inside free-tier token limits.
# TODO (WF-05): split long material into chunks instead of truncating.
MAX_SOURCE_CHARS = 200_000

_LANGUAGE_NAMES = {"pl": "Polish", "en": "English"}

SYSTEM_PROMPT = """\
You write exam questions for university students who study with Testownik.
Rules:
- Use only facts stated in the source material. Do not invent facts.
- Every question has exactly 4 answer options.
- Decide for each question how many options are correct (1 to 4). Use several correct
  options when the material naturally lists several valid items (e.g. "methods of X are
  a, b and c"); otherwise use exactly one.
- Wrong options must be plausible but clearly wrong according to the material.
- Do not use options like "all of the above" or "none of the above".
- Keep questions and options short, self-contained and unambiguous.
- Cover different parts of the material; do not repeat questions.
"""


READ_DOCUMENT_PROMPT = """\
Extract the complete content of this document as plain Markdown, for later use as study
material. Rules:
- Transcribe all text faithfully in its original language, including text in scans, photos,
  handwriting, slides and speaker notes. Do not translate, summarize or omit anything.
- Keep the structure: headings, lists, and tables as Markdown tables.
- For diagrams, charts and pictures that carry information, add a short factual description
  in square brackets, e.g. [Diagram: ...].
- Skip page numbers, repeated headers/footers and decorative elements.
- Output only the extracted content, with no introduction or comments.
"""


def build_user_prompt(text: str, count: int, language: str, avoid: Sequence[str] = ()) -> str:
    if language in _LANGUAGE_NAMES:
        language_rule = f"Write all questions and answers in {_LANGUAGE_NAMES[language]}."
    else:
        language_rule = "Write all questions and answers in the language of the source material."

    parts = [f"Generate {count} questions.", language_rule]
    if avoid:
        listed = "\n".join(f"- {question}" for question in avoid)
        parts.append(f"Do not repeat or rephrase these existing questions:\n{listed}")
    parts.append(f"Source material:\n<material>\n{text[:MAX_SOURCE_CHARS]}\n</material>")
    return "\n\n".join(parts)
