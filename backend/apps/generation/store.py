"""In-memory store of generation jobs.

MOCK: Stage 1 keeps no user data ("dokumenty przetwarzane są tymczasowo"),
so jobs live only in process memory and vanish on restart. Generation runs
synchronously and progress is simulated from elapsed time. Replace with a
real task queue (e.g. Celery / Django tasks) once the AI module is ready.
"""

import threading
import time
from dataclasses import dataclass, field
from enum import StrEnum
from uuid import uuid4

from django.conf import settings

from ai_engine.schemas import Question


class JobStatus(StrEnum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Job:
    source_text: str
    language: str
    question_count: int
    source_files: list[str]
    questions: list[Question] = field(default_factory=list)
    error: str | None = None
    id: str = field(default_factory=lambda: uuid4().hex)
    created_at: float = field(default_factory=time.time)

    @property
    def progress(self) -> int:
        if self.error:
            return 100
        duration = settings.MOCK_GENERATION_SECONDS
        if duration <= 0:
            return 100
        return min(100, int((time.time() - self.created_at) / duration * 100))

    @property
    def status(self) -> JobStatus:
        if self.error:
            return JobStatus.FAILED
        return JobStatus.COMPLETED if self.progress >= 100 else JobStatus.PROCESSING

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
