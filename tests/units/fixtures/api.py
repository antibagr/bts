import typing

import aioresponses
import fastapi
import fastapi.testclient
import httpx
import pytest
import sqlalchemy.ext.asyncio

from app import models
from app.asgi import get_app
from app.transport.http import dependencies


@pytest.fixture(scope="session")
async def app() -> fastapi.FastAPI:
    return get_app()


@pytest.fixture(autouse=True)
async def _override_app_dependencies(
    app: fastapi.FastAPI,
    db_session: sqlalchemy.ext.asyncio.AsyncSession,
) -> typing.AsyncGenerator[None, None]:
    try:
        app.dependency_overrides[dependencies.db_session] = lambda: db_session
        yield
    finally:
        app.dependency_overrides.clear()


@pytest.fixture()
async def client(app: fastapi.FastAPI) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url="http://test",
        transport=httpx.ASGITransport(app=app),  # type: ignore[arg-type]
    )


@pytest.fixture()
async def auth_client(
    app: fastapi.FastAPI,
    client: httpx.AsyncClient,
    user: models.User,
) -> typing.AsyncGenerator[httpx.AsyncClient, None]:
    async def _get_user() -> models.User:
        return user

    app.dependency_overrides[dependencies.get_current_user] = _get_user
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def mock_api_response() -> typing.Generator[aioresponses.aioresponses, None, None]:
    with aioresponses.aioresponses() as m:
        yield m
