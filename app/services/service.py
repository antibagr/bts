import contextlib
import typing

from app import logs
from app.repository.db import DatabaseSessionManager, DB
from app.services.bets import BetsService
from app.services.liveness_probe import LivenessProbeInterface, LivenessProbeSrv
from app.settings import settings

# Dependencies Layer
sessionmanager = DatabaseSessionManager()
sessionmanager.initialize(
    url=str(settings.ASYNC_DATABASE_URI),
    echo=True,
    future=True,
)
session = sessionmanager.create_session()
cache = settings.CACHE_TYPE()


# Repository Layer
db = DB(session=session)

# Service Layer
bets_service = BetsService(bets_storage=db)


liveness_probe_resources: typing.Mapping[str, LivenessProbeInterface] = {
    "db": db,
}
liveness_probe_service = LivenessProbeSrv(resources=liveness_probe_resources)


async def startup() -> None:
    logs.setup_logging()
    await session.begin()


async def shutdown() -> None:
    await cache.close()
    await session.close()
    await sessionmanager.close()


@contextlib.asynccontextmanager
async def application_dependencies() -> typing.AsyncGenerator[None, None]:
    await startup()
    try:
        yield
    finally:
        await shutdown()
