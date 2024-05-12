import typing
import uuid

import arrow
import sqlalchemy.ext.asyncio
import sqlalchemy.orm
import sqlalchemy_utils
import sqlmodel
import sqlmodel.ext.asyncio.session
from sqlmodel.main import get_sqlalchemy_type as orig_get_sqlalchemy_type

from app.dto.entities.base import ArrowType


def get_sqlalchemy_type(field: typing.Any) -> typing.Any:  # noqa: ANN401
    try:
        return orig_get_sqlalchemy_type(field)
    except ValueError:
        type_ = sqlmodel.main.get_type_from_field(field)  # type: ignore[attr-defined]
        if str(type_) == "<class 'arrow.arrow.Arrow'>":
            return sqlalchemy_utils.ArrowType()
        raise


ALEMBIC_VERSION_SCHEMA: typing.Final[str] = "bts_alembic"
METADATA: typing.Final[sqlmodel.MetaData] = sqlmodel.MetaData(schema="bts")
now_at_utc: typing.Final[sqlalchemy.sql.ClauseElement] = sqlalchemy.text("(now() at time zone 'utc')")
create_uuid: typing.Final[sqlalchemy.sql.ClauseElement] = sqlalchemy.text("uuid_generate_v4()")


# NOTE (rudiemeant@gmail.com): Monkey patch
# get_sqlalchemy_type to support ArrowType
# and metadata to support schema
sqlmodel.main.get_sqlalchemy_type = get_sqlalchemy_type
sqlmodel.SQLModel.metadata = METADATA


class Base(sqlmodel.SQLModel, table=False):
    """Base model with common attributes.

    Attributes
    ----------
        id (uuid.UUID): unique identifier
        created_at (arrow.Arrow): timestamp of creation
        updated_at (arrow.Arrow): timestamp of last update

    """

    id: uuid.UUID = sqlmodel.Field(
        default_factory=uuid.uuid4,
        primary_key=True,
        index=True,
        unique=True,
        sa_column_kwargs={"server_default": create_uuid},
    )
    created_at: ArrowType = sqlmodel.Field(
        default_factory=arrow.utcnow,
        sa_column_kwargs={"server_default": now_at_utc},
    )
    updated_at: ArrowType = sqlmodel.Field(
        default_factory=arrow.utcnow,
        sa_column_kwargs={"server_default": now_at_utc, "server_onupdate": now_at_utc},
    )
