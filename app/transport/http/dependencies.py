import typing
import uuid

import fastapi
import fastapi.security
import sqlalchemy.ext.asyncio

from app import models
from app.repository.db import DatabaseSessionManager, DB
from app.services.bets import BetsService
from app.services.liveness_probe import LivenessProbeSrv
from app.settings import Settings
from app.settings import settings as global_settings


def settings() -> Settings:
    return global_settings


async def session_manager(
    settings: typing.Annotated[Settings, fastapi.Depends(settings)],
) -> typing.AsyncGenerator[DatabaseSessionManager, None]:
    manager = DatabaseSessionManager()
    manager.initialize(
        url=str(settings.ASYNC_DATABASE_URI),
        echo=False,
        future=True,
    )
    yield manager
    await manager.close()


async def db_session(
    session_manager: typing.Annotated[DatabaseSessionManager, fastapi.Depends(session_manager)],
) -> typing.AsyncGenerator[sqlalchemy.ext.asyncio.AsyncSession, None]:
    async with (
        session_manager.bet() as bet,
        session_manager.session(conn=bet.connection) as _session,
    ):
        yield _session


def db(
    db_session: typing.Annotated[sqlalchemy.ext.asyncio.AsyncSession, fastapi.Depends(db_session)],
) -> DB:
    return DB(session=db_session)


def bets_service(
    db: typing.Annotated[DB, fastapi.Depends(db)],
) -> BetsService:
    return BetsService(bets_storage=db)


def liveness_resources() -> dict[str, typing.Any]:
    return {}


def liveness_probe_service(
    liveness_resources: typing.Annotated[dict[str, typing.Any], fastapi.Depends(liveness_resources)],
) -> LivenessProbeSrv:
    return LivenessProbeSrv(resources=liveness_resources)


def get_current_user() -> models.User:
    return models.User(
        id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
        email="test@mail.com",
        is_superuser=False,
    )
