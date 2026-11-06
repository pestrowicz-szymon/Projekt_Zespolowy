from pathlib import Path

from django.conf import settings
from rest_framework import serializers

from ai_engine.extraction import SUPPORTED_EXTENSIONS

LANGUAGE_CHOICES = (("auto", "Language of the material"), ("pl", "Polish"), ("en", "English"))
MIN_QUESTIONS = 1
MAX_QUESTIONS = 100
DEFAULT_QUESTIONS = 20


class AnswerSerializer(serializers.Serializer):
    text = serializers.CharField()
    correct = serializers.BooleanField()


class QuestionSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    text = serializers.CharField()
    answers = AnswerSerializer(many=True)
    multiple_choice = serializers.BooleanField(read_only=True)


class JobSerializer(serializers.Serializer):
    id = serializers.CharField()
    status = serializers.ChoiceField(choices=("processing", "completed", "failed"))
    stage = serializers.ChoiceField(choices=("reading", "generating"))
    progress = serializers.IntegerField(min_value=0, max_value=100)
    language = serializers.CharField()
    question_count = serializers.IntegerField()
    source_files = serializers.ListField(child=serializers.CharField())
    error = serializers.CharField(allow_null=True)
    questions = serializers.SerializerMethodField()

    def get_questions(self, job) -> list[dict]:
        # Questions are only exposed once the (simulated) job has finished.
        if job.status != "completed":
            return []
        return QuestionSerializer(job.questions, many=True).data


class JobCreateSerializer(serializers.Serializer):
    files = serializers.ListField(child=serializers.FileField(), required=False, default=list)
    text = serializers.CharField(required=False, allow_blank=True, default="")
    language = serializers.ChoiceField(choices=LANGUAGE_CHOICES, default="auto")
    question_count = serializers.IntegerField(
        min_value=MIN_QUESTIONS, max_value=MAX_QUESTIONS, default=DEFAULT_QUESTIONS
    )

    def validate_files(self, files):
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        for upload in files:
            extension = Path(upload.name).suffix.lower()
            if extension not in SUPPORTED_EXTENSIONS:
                raise serializers.ValidationError(f"Nieobsługiwany format pliku: {upload.name}")
            if upload.size > max_bytes:
                raise serializers.ValidationError(
                    f"Plik {upload.name} przekracza limit {settings.MAX_UPLOAD_SIZE_MB} MB."
                )
        return files

    def validate(self, attrs):
        if not attrs["files"] and not attrs["text"].strip():
            raise serializers.ValidationError("Wgraj co najmniej jeden plik lub wklej tekst.")
        return attrs


class ConfigSerializer(serializers.Serializer):
    max_upload_size_mb = serializers.IntegerField()
    supported_extensions = serializers.ListField(child=serializers.CharField())
    languages = serializers.ListField(child=serializers.CharField())
    min_questions = serializers.IntegerField()
    max_questions = serializers.IntegerField()
    default_questions = serializers.IntegerField()
    ai_provider = serializers.CharField()
