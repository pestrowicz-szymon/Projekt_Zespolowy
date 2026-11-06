"""Runs generation jobs outside the request (WF-06).

Jobs run in a daemon thread so ``POST /jobs/`` returns immediately and the
frontend can poll for progress. Tests set ``GENERATION_RUN_IN_BACKGROUND``
to ``False`` to run jobs inline.
"""

import logging
import threading
import time

from django.conf import settings

from ai_engine import GenerationError, get_generator
from ai_engine.extraction import extract_text, get_document_reader, needs_reader
from apps.generation.store import Job, JobStage

logger = logging.getLogger(__name__)

# Rough timings for real models; only used for the progress estimate.
_SECONDS_PER_QUESTION = 1.5
_SECONDS_PER_DOCUMENT = 20


def start_job(job: Job) -> None:
    if settings.AI_PROVIDER == "mock":
        job.expected_seconds = settings.MOCK_GENERATION_SECONDS
    else:
        documents = sum(needs_reader(upload.filename) for upload in job.uploads)
        job.expected_seconds = (
            5 + job.question_count * _SECONDS_PER_QUESTION + documents * _SECONDS_PER_DOCUMENT
        )

    if settings.GENERATION_RUN_IN_BACKGROUND:
        threading.Thread(target=run_job, args=(job,), daemon=True).start()
    else:
        run_job(job)


def run_job(job: Job) -> None:
    try:
        if settings.AI_PROVIDER == "mock":
            # Pretend to work so the progress bar can be developed against the mock.
            time.sleep(settings.MOCK_GENERATION_SECONDS)
        job.source_text = _read_sources(job)
        job.stage = JobStage.GENERATING
        job.questions = get_generator().generate(job.source_text, job.question_count, job.language)
    except GenerationError as exc:
        job.error = str(exc)
    except Exception:
        logger.exception("Generation job %s crashed", job.id)
        job.error = "Nieoczekiwany błąd serwera podczas generowania."
    finally:
        job.uploads = []
        job.finished_at = time.time()


def _read_sources(job: Job) -> str:
    reader = get_document_reader() if any(needs_reader(u.filename) for u in job.uploads) else None
    texts = []
    for upload in job.uploads:
        text = extract_text(upload.filename, upload.data, reader).strip()
        if text:
            texts.append(f"## {upload.filename}\n\n{text}")
    if job.pasted_text.strip():
        texts.append(job.pasted_text.strip())
    if not texts:
        raise GenerationError("Nie udało się odczytać żadnego tekstu z przesłanych plików.")
    return "\n\n".join(texts)
