import pytest

from app.models import *  # noqa: F403
from app.settings import Settings


@pytest.fixture()
def test_bearer_token() -> str:
    return "test_bearer_token"


@pytest.fixture()
def settings() -> Settings:
    _settings = Settings()
    _settings.POSTGRES_NAME = "test_db"
    return _settings
