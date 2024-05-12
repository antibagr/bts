import typing

from app.dto import enums
from app.dto.entities.base import BaseModel


@typing.final
class Result(BaseModel):
    value: enums.ResultValue
