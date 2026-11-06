import io
import zipfile

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from ai_engine import GenerationError
from apps.generation import tasks, views
from apps.generation.store import Job, jobs


class _FailingGenerator:
    def generate(self, text, count, language, avoid=()):
        raise GenerationError("limit")


@pytest.fixture
def client():
    return APIClient()


def _create_job(client, **data):
    payload = {"text": "Some study material.", "question_count": 3, **data}
    return client.post("/api/v1/jobs/", payload, format="multipart")


def test_health(client):
    assert client.get("/api/v1/health/").json() == {"status": "ok"}


def test_config_lists_supported_formats(client):
    body = client.get("/api/v1/config/").json()
    assert ".pdf" in body["supported_extensions"]
    assert body["max_upload_size_mb"] == 100


def test_create_job_from_text(client):
    response = _create_job(client)
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "completed"
    assert len(body["questions"]) == 3


def test_create_job_from_file(client):
    upload = SimpleUploadedFile("notes.md", b"# Notes", content_type="text/markdown")
    response = client.post("/api/v1/jobs/", {"files": [upload]}, format="multipart")
    assert response.status_code == 201
    assert response.json()["source_files"] == ["notes.md"]


def test_pdf_is_read_by_document_reader(client):
    upload = SimpleUploadedFile("scan.pdf", b"%PDF-1.7", content_type="application/pdf")
    body = client.post("/api/v1/jobs/", {"files": [upload]}, format="multipart").json()
    assert body["status"] == "completed"
    assert body["stage"] == "generating"
    assert jobs.get(body["id"]).uploads == []  # raw files are dropped after reading
    assert "scan.pdf" in jobs.get(body["id"]).source_text


def test_pdf_without_reader_fails_with_message(client, settings, monkeypatch):
    monkeypatch.setattr(tasks, "get_document_reader", lambda: None)
    upload = SimpleUploadedFile("scan.pdf", b"%PDF-1.7", content_type="application/pdf")
    body = client.post("/api/v1/jobs/", {"files": [upload]}, format="multipart").json()
    assert body["status"] == "failed"
    assert "AI_PROVIDER=gemini" in body["error"]


def test_create_job_requires_input(client):
    response = client.post("/api/v1/jobs/", {}, format="multipart")
    assert response.status_code == 400


def test_create_job_rejects_unsupported_format(client):
    upload = SimpleUploadedFile("virus.exe", b"MZ")
    response = client.post("/api/v1/jobs/", {"files": [upload]}, format="multipart")
    assert response.status_code == 400


def test_delete_and_regenerate_question(client):
    job = _create_job(client).json()
    first, second = job["questions"][0]["id"], job["questions"][1]["id"]

    assert client.delete(f"/api/v1/jobs/{job['id']}/questions/{first}/").status_code == 204
    regenerated = client.post(f"/api/v1/jobs/{job['id']}/questions/{second}/regenerate/")
    assert regenerated.status_code == 200
    assert regenerated.json()["id"] == second

    assert len(client.get(f"/api/v1/jobs/{job['id']}/").json()["questions"]) == 2


def test_export_zip(client):
    job = _create_job(client).json()
    response = client.get(f"/api/v1/jobs/{job['id']}/export/")
    assert response["Content-Type"] == "application/zip"
    assert len(zipfile.ZipFile(io.BytesIO(response.content)).namelist()) == 3


def test_export_before_completion_conflicts(client):
    job = jobs.add(Job(source_text="x", language="pl", question_count=3, source_files=[]))
    body = client.get(f"/api/v1/jobs/{job.id}/").json()
    assert body["status"] == "processing"
    assert body["questions"] == []
    assert client.get(f"/api/v1/jobs/{job.id}/export/").status_code == 409


def test_generation_error_marks_job_failed(client, monkeypatch):
    monkeypatch.setattr(tasks, "get_generator", lambda: _FailingGenerator())
    body = _create_job(client).json()
    assert body["status"] == "failed"
    assert body["error"] == "limit"


def test_regenerate_reports_provider_error(client, monkeypatch):
    job = _create_job(client).json()
    monkeypatch.setattr(views, "get_generator", lambda: _FailingGenerator())
    question_id = job["questions"][0]["id"]
    response = client.post(f"/api/v1/jobs/{job['id']}/questions/{question_id}/regenerate/")
    assert response.status_code == 502
    assert response.json()["detail"] == "limit"


def test_delete_job(client):
    job = _create_job(client).json()
    assert client.delete(f"/api/v1/jobs/{job['id']}/").status_code == 204
    assert client.get(f"/api/v1/jobs/{job['id']}/").status_code == 404


def test_openapi_schema(client):
    assert client.get("/api/schema/").status_code == 200
