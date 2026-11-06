from django.conf import settings
from django.http import Http404, HttpResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from ai_engine import GenerationError, get_generator, testownik
from ai_engine.extraction import SUPPORTED_EXTENSIONS
from apps.generation import serializers as s
from apps.generation.store import Job, JobStage, JobStatus, Upload, jobs
from apps.generation.tasks import start_job


def _get_job_or_404(job_id: str) -> Job:
    job = jobs.get(job_id)
    if job is None:
        raise Http404("Job not found.")
    return job


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
        summary="Start reading files and generating questions (WF-01..WF-05)",
        tags=["jobs"],
    )
    def post(self, request):
        serializer = s.JobCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # Files are only read here; extracting their text (OCR) runs in the background job.
        uploads = [Upload(filename=f.name, data=f.read()) for f in data["files"]]
        job = Job(
            language=data["language"],
            question_count=data["question_count"],
            source_files=[upload.filename for upload in uploads],
            pasted_text=data["text"],
            uploads=uploads,
            stage=JobStage.READING if uploads else JobStage.GENERATING,
        )
        jobs.add(job)
        start_job(job)
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
        responses={
            200: s.QuestionSerializer,
            502: OpenApiResponse(description="The AI provider failed."),
        },
        summary="Regenerate a single question (PU-02)",
        tags=["questions"],
    )
    def post(self, request, job_id: str, question_id: str):
        job = _get_job_or_404(job_id)
        question = job.find_question(question_id)
        if question is None:
            raise Http404("Question not found.")
        others = [q.text for q in job.questions]
        try:
            [new_question, *_] = get_generator().generate(
                job.source_text, 1, job.language, avoid=others
            )
        except GenerationError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
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
