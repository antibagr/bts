import os

from app import models
from app.models import *  # noqa: F403
from app.models.alembic_env import run_alembic
from app.settings import settings

run_alembic(
    sqlalchemy_url=os.getenv("TEST_DB_URL") or settings.DATABASE_URI,
    target_metadata=models.METADATA,
    version_table_schema=models.ALEMBIC_VERSION_SCHEMA,
)
