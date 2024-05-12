import fastapi
import fastapi.openapi
import fastapi.openapi.docs
import gunicorn.app.base
from loguru import logger

from app import logs
from app.services import service
from app.settings import settings
from app.transport import http


class StandaloneApplication(gunicorn.app.base.BaseApplication):  # type: ignore[misc]
    """Our Gunicorn application."""

    def __init__(self, app: fastapi.FastAPI, options=None, usage=None, prog=None) -> None:  # type: ignore[no-untyped-def] # noqa: ARG002
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self) -> None:
        config = {key: value for key, value in self.options.items() if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self) -> fastapi.FastAPI:
        return self.application


def register_bootstrap(_app: fastapi.FastAPI) -> None:
    _app.add_event_handler("startup", _startup)
    _app.add_event_handler("shutdown", _shutdown)


async def _startup() -> None:
    try:
        await service.startup()
    finally:
        logger.debug("web_server_startup")


async def _shutdown() -> None:
    try:
        await service.shutdown()
    finally:
        logger.debug("web_server_shutdown")


def get_app() -> fastapi.FastAPI:
    _app = fastapi.FastAPI(
        debug=settings.DEBUG,
        default_response_class=fastapi.responses.ORJSONResponse,
        title="Betting API",
        swagger_ui_parameters={
            "docExpansion": "list",
            "displayOperationId": False,
            "filter": True,
            "showExtensions": False,
            "tagsSorter": "alpha",
            "operationsSorter": "alpha",
            "deepLinking": False,
            "defaultModelsExpandDepth": -1,
            "tryItOutEnabled": True,
            "persistAuthorization": True,
        },
    )

    register_bootstrap(_app)
    http.setup_exception_handlers(_app)
    http.register_middlewares(_app)
    http.register_http_routes(_app)

    return _app


fastapi_app = get_app()
logs.setup_logging()


if __name__ == "__main__":
    options = {
        "bind": "0.0.0.0:8000",
        "workers": 1,
        "accesslog": "-",
        "errorlog": "-",
        "worker_class": "uvicorn.workers.UvicornWorker",
        "logger_class": logs.StubbedGunicornLogger,
    }

    StandaloneApplication(fastapi_app, options).run()
