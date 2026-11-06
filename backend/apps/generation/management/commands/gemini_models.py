from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from google.genai import errors

from ai_engine.gemini import list_generation_models


class Command(BaseCommand):
    help = "List Gemini models your GEMINI_API_KEY can use for question generation."

    def handle(self, *args, **options):
        if not settings.GEMINI_API_KEY:
            raise CommandError("GEMINI_API_KEY is not set in backend/.env.")
        try:
            models = list_generation_models(settings.GEMINI_API_KEY)
        except errors.APIError as exc:
            raise CommandError(f"Gemini API error {exc.code}: {exc.message}") from exc

        for model in models:
            marker = "  <- GEMINI_MODEL" if model == settings.GEMINI_MODEL else ""
            self.stdout.write(f"{model}{marker}")
        self.stdout.write(f"\nCurrent GEMINI_MODEL: {settings.GEMINI_MODEL}")
