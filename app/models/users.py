import typing

import pydantic
import sqlalchemy_utils
import sqlmodel

from app.models.base import Base

if typing.TYPE_CHECKING:
    from app.models.bets import Bets


@typing.final
class User(Base, table=True):
    """Represents a user in the system."""

    __tablename__ = "users"

    email: pydantic.EmailStr = sqlmodel.Field(sa_column=sqlmodel.Column(sqlalchemy_utils.EmailType, unique=True))
    is_superuser: bool = sqlmodel.Field(default=False)

    bets: list["Bets"] = sqlmodel.Relationship(back_populates="user")
