from typing import Final

from fastapi import APIRouter, FastAPI

from app.settings import settings
from app.transport.http.api import public, service

API_PREFIX: Final = "/api"


def _service_api(app: FastAPI, router: APIRouter) -> None:
    app.include_router(
        router=router,
        tags=["service"],
        include_in_schema=settings.is_dev,
    )


def register_http_routes(app: FastAPI) -> None:
    _service_api(app=app, router=service.health.router)
    app.include_router(
        router=public.bets.router,
        prefix=API_PREFIX,
    )
