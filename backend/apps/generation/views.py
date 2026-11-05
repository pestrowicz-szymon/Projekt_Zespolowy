from django.conf import settings
from django.http import Http404, HttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_engine import get_generator, testownik
from ai_engine.extraction import SUPPORTED_EXTENSIONS, extract_text
from apps.generation import serializers as s
from apps.generation.store import Job, JobStatus, jobs


def _get_job_or_404(job_id: str) -> Job:
    job = jobs.get(job_id)
    if job is None:
        raise Http404("Job not found.")
    return job


def _resolve_language(language: str) -> str:
    # TODO (AI module): detect the language of the material.
    return "pl" if language == "auto" else language


class HealthView(APIView):
    @extend_schema(
        responses=inline_serializer("Health", {"status": serializers.CharField()}),
        tags=["meta"],
    )
    def get(self, request):
        return Response({"status": "ok"})


class ConfigView(APIView):
    @extend_schema(responses=s.ConfigSerializer, tags=["meta"])
    def get(self, request):
        data = {
            "max_upload_size_mb": settings.MAX_UPLOAD_SIZE_MB,
            "supported_extensions": list(SUPPORTED_EXTENSIONS),
            "languages": [code for code, _ in s.LANGUAGE_CHOICES],
            "min_questions": s.MIN_QUESTIONS,
            "max_questions": s.MAX_QUESTIONS,
            "default_questions": s.DEFAULT_QUESTIONS,
            "ai_provider": settings.AI_PROVIDER,
        }
        return Response(s.ConfigSerializer(data).data)


class JobCreateView(APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    @extend_schema(
        request={"multipart/form-data": s.JobCreateSerializer},
        responses={201: s.JobSerializer},
        summary="Start generating questions from files and/or pasted text (WF-01..WF-05)",
        tags=["jobs"],
    )
    def post(self, request):
        serializer = s.JobCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        texts = [extract_text(f.name, f) for f in data["files"]]
        if data["text"].strip():
            texts.append(data["text"])
        job = Job(
            source_text="\n\n".join(texts),
            language=data["language"],
            question_count=data["question_count"],
            source_files=[f.name for f in data["files"]],
        )
        try:
            job.questions = get_generator().generate(
                job.source_text, job.question_count, _resolve_language(job.language)
            )
        except Exception as exc:  # noqa: BLE001 - surfaced to the user as a failed job
            job.error = str(exc) or exc.__class__.__name__
        jobs.add(job)
        return Response(s.JobSerializer(job).data, status=status.HTTP_201_CREATED)


class JobDetailView(APIView):
    @extend_schema(
        responses=s.JobSerializer, summary="Job status, progress and questions", tags=["jobs"]
    )
    def get(self, request, job_id: str):
        return Response(s.JobSerializer(_get_job_or_404(job_id)).data)

    @extend_schema(
        responses={204: None}, summary="End the session and discard the documents", tags=["jobs"]
    )
    def delete(self, request, job_id: str):
        if not jobs.delete(job_id):
            raise Http404("Job not found.")
        return Response(status=status.HTTP_204_NO_CONTENT)


class QuestionDetailView(APIView):
    @extend_schema(responses={204: None}, summary="Remove a question (PU-02)", tags=["questions"])
    def delete(self, request, job_id: str, question_id: str):
        job = _get_job_or_404(job_id)
        question = job.find_question(question_id)
        if question is None:
            raise Http404("Question not found.")
        job.questions.remove(question)
        return Response(status=status.HTTP_204_NO_CONTENT)


class QuestionRegenerateView(APIView):
    @extend_schema(
        request=None,
        responses=s.QuestionSerializer,
        summary="Regenerate a single question (PU-02)",
        tags=["questions"],
    )
    def post(self, request, job_id: str, question_id: str):
        job = _get_job_or_404(job_id)
        question = job.find_question(question_id)
        if question is None:
            raise Http404("Question not found.")
        [new_question] = get_generator().generate(
            job.source_text, 1, _resolve_language(job.language)
        )
        new_question.id = question.id
        job.questions[job.questions.index(question)] = new_question
        return Response(s.QuestionSerializer(new_question).data)


class JobExportView(APIView):
    @extend_schema(
        responses={
            (200, "application/zip"): OpenApiResponse(OpenApiTypes.BINARY),
            409: OpenApiResponse(description="Job has not finished yet."),
        },
        summary="Download questions as a Testownik ZIP archive (WF-07)",
        tags=["jobs"],
    )
    def get(self, request, job_id: str):
        job = _get_job_or_404(job_id)
        if job.status != JobStatus.COMPLETED:
            return Response(
                {"detail": "Generowanie nie zostało jeszcze zakończone."},
                status=status.HTTP_409_CONFLICT,
            )
        response = HttpResponse(testownik.build_zip(job.questions), content_type="application/zip")
        response["Content-Disposition"] = f'attachment; filename="testownik-{job.id[:8]}.zip"'
        return response
