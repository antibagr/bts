import typing

import fastapi
import fastapi.encoders
import starlette.types

from app.dto.exceptions import (
    AlreadyExistsError,
    AuthenticationError,
    ClientError,
    ErrorProtocol,
    NotFoundError,
)


async def validation_error_handler(
    _: fastapi.Request,
    exc: fastapi.exceptions.RequestValidationError,
) -> fastapi.responses.ORJSONResponse:
    return fastapi.responses.ORJSONResponse(
        status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=fastapi.encoders.jsonable_encoder({"detail": str(exc), "code": "validation_error"}),
    )


async def assertion_error_handler(_: fastapi.Request, exc: AssertionError) -> fastapi.responses.ORJSONResponse:
    return fastapi.responses.ORJSONResponse(
        status_code=fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=fastapi.encoders.jsonable_encoder({"detail": str(exc), "code": "validation_error"}),
    )


def add_business_logic_error_handler(app: fastapi.FastAPI, exc: type[ErrorProtocol], status_code: int) -> None:
    async def error_handler(_request: fastapi.Request, ex: ErrorProtocol) -> fastapi.responses.ORJSONResponse:
        return fastapi.responses.ORJSONResponse(status_code=status_code, content={"detail": ex.detail, "code": ex.code})

    app.add_exception_handler(
        exc_class_or_status_code=typing.cast(type[Exception], exc),
        handler=typing.cast(starlette.types.ExceptionHandler, error_handler),
    )


def setup_exception_handlers(app: fastapi.FastAPI) -> None:
    app.add_exception_handler(
        exc_class_or_status_code=AssertionError,
        handler=typing.cast(starlette.types.ExceptionHandler, assertion_error_handler),
    )
    app.add_exception_handler(
        exc_class_or_status_code=fastapi.exceptions.RequestValidationError,
        handler=typing.cast(starlette.types.ExceptionHandler, validation_error_handler),
    )

    # business-logic exceptions
    for error, status_code in ERROR_MAP.items():
        add_business_logic_error_handler(app, error, status_code)


ERROR_MAP: typing.Mapping[type[ErrorProtocol], int] = {
    NotFoundError: fastapi.status.HTTP_404_NOT_FOUND,
    AlreadyExistsError: fastapi.status.HTTP_409_CONFLICT,
    ClientError: fastapi.status.HTTP_400_BAD_REQUEST,
    AuthenticationError: fastapi.status.HTTP_401_UNAUTHORIZED,
}


__all__ = [
    "setup_exception_handlers",
]
