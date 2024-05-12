import typing
import uuid

import pytest
import sqlalchemy.event
import sqlalchemy.exc
import sqlalchemy.ext.asyncio
import sqlalchemy_utils

from app.models import *  # noqa: F403
from app.models import METADATA
from app.repository.db import DatabaseSessionManager, DB
from app.settings import settings


@pytest.fixture(scope="session")
def db_name(worker_id: str) -> str:
    return f"test_db_{worker_id}"


@pytest.fixture(scope="session")
def db_uri(db_name: str) -> str:
    return f"{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD.get_secret_value()}@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{db_name}"


@pytest.fixture(scope="session")
def db_url(db_uri: str) -> str:
    return f"postgresql+asyncpg://{db_uri}"


@pytest.fixture(scope="session")
def sync_db_url(db_uri: str) -> str:
    return f"postgresql://{db_uri}"


@pytest.fixture(scope="session", autouse=True)
def _setup_db(sync_db_url: str) -> typing.Generator[None, None, None]:
    """Setups the test database for each worker."""
    if sqlalchemy_utils.database_exists(sync_db_url):
        sqlalchemy_utils.drop_database(sync_db_url)
    sqlalchemy_utils.create_database(sync_db_url)

    assert sqlalchemy_utils.database_exists(sync_db_url)

    _engine = sqlalchemy.create_engine(sync_db_url, poolclass=sqlalchemy.pool.NullPool, echo=False, future=True)

    with _engine.connect() as conn:
        conn.execute(sqlalchemy.text("CREATE SCHEMA IF NOT EXISTS bts;"))
        conn.execute(sqlalchemy.text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
        conn.commit()
    METADATA.create_all(_engine)

    try:
        yield
    finally:
        sqlalchemy_utils.drop_database(sync_db_url)


@pytest.fixture(scope="session")
async def engine(db_url: str) -> sqlalchemy.ext.asyncio.AsyncEngine:
    return sqlalchemy.ext.asyncio.create_async_engine(
        db_url,
        future=True,
        echo=False,
        poolclass=sqlalchemy.pool.NullPool,
    )


@pytest.fixture(scope="session")
async def sessionmaker(
    engine: sqlalchemy.ext.asyncio.AsyncEngine,
) -> sqlalchemy.ext.asyncio.async_sessionmaker[sqlalchemy.ext.asyncio.AsyncSession]:
    return sqlalchemy.ext.asyncio.async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autoflush=False,
        class_=sqlalchemy.ext.asyncio.AsyncSession,
    )


@pytest.fixture(scope="session")
async def session_manager(
    engine: sqlalchemy.ext.asyncio.AsyncEngine,
    sessionmaker: sqlalchemy.ext.asyncio.async_sessionmaker[sqlalchemy.ext.asyncio.AsyncSession],
) -> typing.AsyncGenerator[DatabaseSessionManager, None]:
    try:
        manager = DatabaseSessionManager()
        manager._engine = engine  # noqa: SLF001
        manager._sessionmaker = sessionmaker  # noqa: SLF001
        yield manager
    finally:
        await manager.close()


@pytest.fixture()
async def db_session(
    session_manager: DatabaseSessionManager,
) -> typing.AsyncGenerator[sqlalchemy.ext.asyncio.AsyncSession, None]:
    async with (
        session_manager.bet() as bet,
        session_manager.session(conn=bet.connection) as _session,
    ):
        yield _session
        await bet.rollback()


@pytest.fixture()
async def db(db_session: sqlalchemy.ext.asyncio.AsyncSession) -> DB:
    return DB(db_session)


@pytest.fixture()
async def test_user_id() -> uuid.UUID:
    return uuid.UUID("00000000-0000-0000-0000-000000000001")
