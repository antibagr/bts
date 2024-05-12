"""Commands are emitted by the application layer and are consumed by the domain layer.

A command is a way to encapsulate a request to perform an action or a change in the system.
Commands are used to communicate between the application layer and the domain layer.

Commands are immutable and should be serializable to JSON if needed.
"""

import decimal
import typing
import uuid

from app import models
from app.dto import enums
from app.dto.entities.base import BaseModel


@typing.final
class MakeBet(BaseModel):
    """Command emitted when we need to create a new bet."""

    user: models.User
    event_id: uuid.UUID
    amount: decimal.Decimal


@typing.final
class UpdateEvent(BaseModel):
    """Command emitted when we need to update an event."""

    event_id: uuid.UUID
    status: enums.EventStatus
