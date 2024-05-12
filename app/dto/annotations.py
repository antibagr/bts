import typing

import pydantic
import pydantic_core

T = typing.TypeVar("T")
P = typing.ParamSpec("P")
F = typing.Callable[P, typing.Awaitable[T]]


Json = dict[str, typing.Any]
Payload = Json | list[Json]
AttributeIds = dict[str, int]


HttpsUrl = typing.Annotated[pydantic_core.Url, pydantic.UrlConstraints(allowed_schemes=["https"])]


GreaterEqualZero = typing.Annotated[int, pydantic.conint(ge=0)]

String = typing.Annotated[
    str,
    pydantic.StringConstraints(
        strip_whitespace=True,
        min_length=1,
        max_length=256,
    ),
]
"""
String type with constraints for length and whitespace stripping.
"""
