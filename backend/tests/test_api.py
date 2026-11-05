import io
import zipfile

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient


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


def test_export_before_completion_conflicts(client, settings):
    settings.MOCK_GENERATION_SECONDS = 60
    job = _create_job(client).json()
    assert job["status"] == "processing"
    assert job["questions"] == []
    assert client.get(f"/api/v1/jobs/{job['id']}/export/").status_code == 409


def test_delete_job(client):
    job = _create_job(client).json()
    assert client.delete(f"/api/v1/jobs/{job['id']}/").status_code == 204
    assert client.get(f"/api/v1/jobs/{job['id']}/").status_code == 404


def test_openapi_schema(client):
    assert client.get("/api/schema/").status_code == 200
