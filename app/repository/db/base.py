from __future__ import annotations

import contextlib
import typing

import sqlalchemy.exc
import sqlalchemy.ext.asyncio
import sqlalchemy.sql.elements
import sqlmodel
import sqlmodel.sql.expression
from loguru import logger

from app.dto.exceptions import AlreadyExistsError, NotFoundError
from app.models.base import Base

T = typing.TypeVar("T", bound=Base)
_Tb = typing.TypeVar("_Tb", bound=sqlmodel.Table)
Filters = typing.Any


class NoTransactionError(Exception):
    """No bet error."""


class DatabaseSessionManager:
    _engine: sqlalchemy.ext.asyncio.AsyncEngine | None
    _sessionmaker: sqlalchemy.ext.asyncio.async_sessionmaker[sqlalchemy.ext.asyncio.AsyncSession] | None

    def __init__(self) -> None:
        self._engine = None
        self._sessionmaker = None

    def initialize(self, *, url: str, **kwargs: str | int) -> None:
        self._engine = sqlalchemy.ext.asyncio.create_async_engine(url=url, **kwargs)
        self._sessionmaker = sqlalchemy.ext.asyncio.async_sessionmaker(
            bind=self._engine,
            expire_on_commit=False,
            autoflush=False,
        )

    def _check_engine(self) -> None:
        if self._engine is None:
            raise NoTransactionError("DatabaseSessionManager is not initialized")

    async def close(self) -> None:
        self._check_engine()
        await self._engine.dispose()  # type: ignore[union-attr]

        self._engine = None
        self._sessionmaker = None

    def create_session(
        self,
        *,
        conn: sqlalchemy.ext.asyncio.AsyncConnection | None = None,
    ) -> sqlalchemy.ext.asyncio.AsyncSession:
        if self._sessionmaker is None:
            raise NoTransactionError("DatabaseSessionManager is not initialized")
        if conn is not None:
            return self._sessionmaker(bind=conn)
        return self._sessionmaker()

    @contextlib.asynccontextmanager
    async def connection(self) -> typing.AsyncIterator[sqlalchemy.ext.asyncio.AsyncConnection]:
        self._check_engine()

        async with self._engine.connect() as connection:  # type: ignore[union-attr]
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    @contextlib.asynccontextmanager
    async def session(
        self,
        *,
        conn: sqlalchemy.ext.asyncio.AsyncConnection | None = None,
    ) -> typing.AsyncIterator[sqlalchemy.ext.asyncio.AsyncSession]:
        async with self.create_session(conn=conn) as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    @contextlib.asynccontextmanager
    async def bet(self) -> typing.AsyncIterator[sqlalchemy.ext.asyncio.AsyncTransaction]:
        self._check_engine()
        async with self.connection() as connection, connection.begin() as bet:
            try:
                yield bet
            except Exception:
                await bet.rollback()
                raise


class EntityDB:
    session: sqlalchemy.ext.asyncio.AsyncSession

    @staticmethod
    def _get_filter_bool_expression(
        *,
        model: _Tb,
        filter_name: str,
        filter_value: Filters,
        query: sqlmodel.sql.expression.Select[_Tb] | None = None,
    ) -> sqlalchemy.sql.elements.ColumnElement[bool]:
        """Create filter expression for query from filter name and value.

        The filter name should be in the format of `column_name_sign`, where:
        - `column_name` is the name of the column to filter by
        - `sign` is the sign of the comparison operation to perform

        The filter value should be the value to compare the column to.

        The following signs are supported:
        - `lt` - less than
        - `le` - less than or equal to
        - `gt` - greater than
        - `ge` - greater than or equal to
        - `ne` - not equal to
        - `in` - in list
        - `notin` - not in list
        - `is` - is
        - `isnot` - is not
        - `like` - like
        - `ilike` - ilike

        Example:
        -------
        - `id_lt` - id less than
        - `name_like` - name like
        - `is_active` - is active
        - `is_active_is` - is active is
        - `payment_system_in` - payment system in list
        - `status_ne` - status not equal to

        """
        if query is not None and filter_name in (dict(query.subquery().columns).keys() | model.model_fields.keys()):  # type: ignore[attr-defined]
            return sqlmodel.column(filter_name).__eq__(filter_value)  # noqa: PLC2801
        if query is None and filter_name in model.columns:
            return model.columns[filter_name].__eq__(filter_value)  # noqa: PLC2801

        split_by_underscore = filter_name.split("_")
        sign = split_by_underscore.pop()
        col_name = "_".join(split_by_underscore)
        col = sqlmodel.column(col_name) if query is not None else model.columns[col_name]

        match sign:
            case "lt" | "le" | "gt" | "ge" | "ne":
                expr = getattr(col, f"__{sign}__")(filter_value)
            case "in":
                expr = col.in_(filter_value)
            case "notin":
                expr = ~col.in_(filter_value)
            case "is":
                expr = col.is_(filter_value)
            case "isnot":
                expr = col.is_not(filter_value)
            case "like":
                expr = col.like(filter_value)
            case "ilike":
                expr = col.ilike(filter_value)
            case _:
                raise ValueError(f"Unknown filter name ({filter_name})")

        return typing.cast(sqlalchemy.sql.elements.ColumnElement[bool], expr)

    def _apply_filters(
        self,
        *,
        model: type[T],
        query: sqlmodel.sql.expression.SelectOfScalar[T],
        **filters: Filters,
    ) -> sqlmodel.sql.expression.SelectOfScalar[T]:
        for filter_name, filter_value in filters.items():
            query = query.where(
                self._get_filter_bool_expression(
                    model=model,  # type: ignore[type-var]
                    filter_name=filter_name,
                    filter_value=filter_value,
                    query=query,  # type: ignore[arg-type]
                )
            )
        return query

    async def create(self, model: T, /) -> T:
        try:
            self.session.add(model)
            await self.session.commit()
        except sqlalchemy.exc.IntegrityError as exc:
            if "duplicate key value violates unique constraint" in str(exc):
                raise AlreadyExistsError(
                    f"Entity {model.__class__.__name__} with id {model.id} already exists"
                ) from exc
            raise
        await self.session.refresh(model)
        return model

    async def update(self, model: T, /) -> T:
        self.session.add(model)
        await self.session.commit()
        return model

    async def get(self, model: type[T], /, **filters: Filters) -> T:
        query = self._apply_filters(model=model, query=sqlmodel.select(model), **filters)
        rows = await self.session.execute(query)
        result = rows.scalars().first()
        if result is None:
            raise NotFoundError(f"Entity {model.__name__} with filters {filters} not found")
        return result

    async def get_many(
        self,
        model: type[T],
        /,
        **filters: Filters,
    ) -> list[T]:
        query = self._apply_filters(model=model, query=sqlmodel.select(model), **filters)
        rows = await self.session.execute(query.order_by(sqlmodel.col(model.created_at).desc()))
        return typing.cast(list[T], rows.scalars().all())

    async def get_or_create(
        self,
        model: type[T],
        /,
        **filters: Filters,
    ) -> typing.Annotated[tuple[T, bool], "Tuple[Entity, is_created]"]:
        entities = await self.get_many(model, **filters)
        if len(entities) > 1:
            raise AlreadyExistsError(f"Multiple entities {model.__name__} with filters {filters} found")
        if entities:
            return entities[0], False
        return await self.create(model(**filters)), True

    async def count(self, model: type[T], /, **filters: Filters) -> int:
        query = self._apply_filters(  # type: ignore[misc]
            model=model,
            query=sqlmodel.select(sqlmodel.func.count(model.id)),  # type: ignore[arg-type]
            **filters,
        )
        rows = await self.session.execute(query)
        return typing.cast(int, rows.scalar())

    async def close(self) -> None:
        await self.session.close()


class BaseDB(EntityDB):
    def __init__(self, session: sqlalchemy.ext.asyncio.AsyncSession) -> None:
        self.session = session

    async def is_alive(self) -> bool:
        try:
            await self.session.execute(sqlalchemy.text("SELECT 1"))
        except sqlalchemy.exc.DBAPIError as exc:
            logger.exception(exc)
            return False
        return True
