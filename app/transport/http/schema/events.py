import typing
import uuid

from app.dto import enums
from app.dto.entities.base import APISchemeBaseModel


@typing.final
class UpdateEventRequest(APISchemeBaseModel):
    status: enums.EventStatus


@typing.final
class Event(APISchemeBaseModel):
    id: uuid.UUID
    status: enums.EventStatus
