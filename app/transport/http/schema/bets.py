import decimal
import typing
import uuid

import pydantic

from app.dto import enums
from app.dto.entities.base import APISchemeBaseModel, ISOArrowType


@typing.final
class MakeBetRequest(APISchemeBaseModel):
    event_id: uuid.UUID
    amount: typing.Annotated[
        decimal.Decimal,
        pydantic.Field(
            ge=0,
            max_digits=10,
            decimal_places=2,
            allow_inf_nan=False,
        ),
    ]
    value: typing.Literal[enums.ResultValue.HOME] = enums.ResultValue.HOME
    bet_type: typing.Annotated[typing.Literal[enums.BetType.RESULT], pydantic.Field(enums.BetType.RESULT, alias="type")]


@typing.final
class Bet(APISchemeBaseModel):
    id: uuid.UUID
    event_id: uuid.UUID
    amount: decimal.Decimal
    created_at: ISOArrowType
    updated_at: ISOArrowType
    status: enums.BetStatus

    value: typing.Literal[enums.ResultValue.HOME] = enums.ResultValue.HOME
    bet_type: typing.Annotated[
        typing.Literal[enums.BetType.RESULT],
        pydantic.Field(
            enums.BetType.RESULT,
            serialization_alias="type",
        ),
    ]
