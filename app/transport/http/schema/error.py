import typing

import fastapi
import pydantic


@typing.final
class APIErrorResponseProtocol(pydantic.BaseModel):
    code: str
    detail: str


Responses: dict[int | str, dict[str, typing.Any]] = {
    _status: {"model": APIErrorResponseProtocol}
    for _status in (
        fastapi.status.HTTP_400_BAD_REQUEST,
        fastapi.status.HTTP_401_UNAUTHORIZED,
        fastapi.status.HTTP_403_FORBIDDEN,
        fastapi.status.HTTP_404_NOT_FOUND,
        fastapi.status.HTTP_422_UNPROCESSABLE_ENTITY,
        fastapi.status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
}
