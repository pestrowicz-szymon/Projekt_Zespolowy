import pytest

from apps.generation.store import jobs


@pytest.fixture(autouse=True)
def _instant_generation(settings):
    settings.MOCK_GENERATION_SECONDS = 0
    settings.AI_PROVIDER = "mock"
    yield
    jobs.clear()
