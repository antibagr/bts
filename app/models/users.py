import typing

import pydantic
import sqlmodel

from app.models.base import Base


@typing.final
class User(Base, table=True):
    """Represents a user in the system."""

    __tablename__ = "users"

    email: pydantic.EmailStr = sqlmodel.Field(sa_column=sqlmodel.Column("email", sqlmodel.VARCHAR, unique=True))
    is_superuser: bool = sqlmodel.Field(default=False)
