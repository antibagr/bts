"""The module patches the alembic script to use schema and custom migration name."""

from .env import run_alembic

__all__ = ["run_alembic"]
