import logging
import sys

import gunicorn.app.base
import gunicorn.glogging
from loguru import logger

from app.settings import settings


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:  # noqa: PLR6301
        # get corresponding loguru level if it exists
        level: str | int
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # find caller from where originated the logged message
        frame, depth = sys._getframe(6), 6  # noqa: SLF001
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # type: ignore[assignment]
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


class StubbedGunicornLogger(gunicorn.glogging.Logger):  # type: ignore[misc]
    def setup(self, cfg) -> None:  # type: ignore[no-untyped-def] # noqa: ARG002
        handler = logging.NullHandler()
        self.error_logger = logging.getLogger("gunicorn.error")
        self.error_logger.addHandler(handler)
        self.access_logger = logging.getLogger("gunicorn.access")
        self.access_logger.addHandler(handler)
        self.error_logger.setLevel(settings.LOGGING_LEVEL)
        self.access_logger.setLevel(settings.LOGGING_LEVEL)


class GunicornLogger(gunicorn.glogging.Logger):  # type: ignore[misc]
    def setup(self, cfg) -> None:  # type: ignore[no-untyped-def] # noqa: ARG002
        handler = InterceptHandler()

        # Add log handler to logger and set log level
        self.error_log.addHandler(handler)
        self.error_log.setLevel(settings.LOGGING_LEVEL)
        self.access_log.addHandler(handler)
        self.access_log.setLevel(settings.LOGGING_LEVEL)

        # Configure logger before gunicorn starts logging
        logger.configure(handlers=[{"sink": sys.stdout, "level": settings.LOGGING_LEVEL}])


def setup_logging() -> None:
    intercept_handler = InterceptHandler()
    logging.root.setLevel(settings.LOGGING_LEVEL)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("aiocache").setLevel(logging.WARNING)

    logger_names: set[str] = {
        name.split(".")[0]
        for name in [
            *logging.root.manager.loggerDict.keys(),
            "gunicorn",
            "gunicorn.access",
            "gunicorn.error",
            "uvicorn",
            "uvicorn.access",
            "uvicorn.error",
        ]
    }

    for name in logger_names:
        logging.getLogger(name).handlers = [intercept_handler]

    logger.configure(
        handlers=[
            {
                "sink": sys.stdout,
                "serialize": False,
                "backtrace": settings.DEBUG,
                "diagnose": settings.DEBUG,
                "level": settings.LOGGING_LEVEL,
            }
        ]
    )
