"""In-memory store of generation jobs.

Stage 1 keeps no user data ("dokumenty przetwarzane są tymczasowo"), so jobs
live only in process memory and vanish on restart. This only works with a
single server process (``runserver``); replace with a database-backed task
queue before running several workers.
"""

import threading
import time
from dataclasses import dataclass, field
from enum import StrEnum
from uuid import uuid4

from ai_engine.schemas import Question


class JobStatus(StrEnum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobStage(StrEnum):
    READING = "reading"  # extracting text from uploaded files
    GENERATING = "generating"


@dataclass
class Upload:
    filename: str
    data: bytes


@dataclass
class Job:
    language: str
    question_count: int
    source_files: list[str]
    pasted_text: str = ""
    # Raw files, dropped as soon as their text has been extracted.
    uploads: list[Upload] = field(default_factory=list)
    source_text: str = ""
    stage: JobStage = JobStage.GENERATING
    # Rough guess of how long generation takes; drives the progress bar only.
    expected_seconds: float = 10.0
    questions: list[Question] = field(default_factory=list)
    error: str | None = None
    finished_at: float | None = None
    id: str = field(default_factory=lambda: uuid4().hex)
    created_at: float = field(default_factory=time.time)

    @property
    def status(self) -> JobStatus:
        if self.error:
            return JobStatus.FAILED
        return JobStatus.PROCESSING if self.finished_at is None else JobStatus.COMPLETED

    @property
    def progress(self) -> int:
        if self.finished_at is not None:
            return 100
        # A single LLM call reports no real progress, so estimate it and stop
        # short of 100 % until the job has actually finished.
        elapsed = time.time() - self.created_at
        return min(95, int(elapsed / max(self.expected_seconds, 0.1) * 100))

    def find_question(self, question_id: str) -> Question | None:
        return next((q for q in self.questions if q.id == question_id), None)


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def add(self, job: Job) -> Job:
        with self._lock:
            self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def delete(self, job_id: str) -> bool:
        with self._lock:
            return self._jobs.pop(job_id, None) is not None

    def clear(self) -> None:
        with self._lock:
            self._jobs.clear()


jobs = JobStore()
