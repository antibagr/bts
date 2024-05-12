import decimal
import typing
import uuid

import sqlmodel

from app.dto import enums
from app.models.base import Base

if typing.TYPE_CHECKING:
    from app.models.users import User


@typing.final
class Bets(Base, table=True):
    """Represent a bet made by a user."""

    __tablename__ = "bets"
    __table_args__ = (sqlmodel.Index("ix_bets_user_id_event_id", "user_id", "event_id", unique=False),)

    event_id: uuid.UUID = sqlmodel.Field(index=True)
    user_id: uuid.UUID = sqlmodel.Field(foreign_key="users.id", index=True)

    amount: decimal.Decimal = sqlmodel.Field(
        sa_column=sqlmodel.Column(
            sqlmodel.Numeric(),
            nullable=False,
            comment="Amount of the bet",
        ),
        gt=0,
    )

    status: enums.BetStatus = sqlmodel.Field(
        sa_column=sqlmodel.Column(
            sqlmodel.Enum(enums.BetStatus, name="enum_bet_status"),
            nullable=False,
            default=enums.BetStatus.PENDING,
            comment="Status of the bet",
        ),
    )

    user: "User" = sqlmodel.Relationship(back_populates="bets")
