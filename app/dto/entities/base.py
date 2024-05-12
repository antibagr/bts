from __future__ import annotations

import abc
import contextlib
import operator
import typing

import arrow
import pydantic
import pydantic.alias_generators
import pydantic.json_schema
import pydantic_core

from app.dto.annotations import GreaterEqualZero  # noqa: TCH001

T = typing.TypeVar("T")
C = typing.TypeVar("C")
TModel = typing.TypeVar("TModel", bound=pydantic.BaseModel)


class _ArrowTypeTimestampPydanticAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(  # noqa: PLW3201
        cls,
        _source_type: typing.Any,  # noqa: ANN401
        _handler: pydantic.GetCoreSchemaHandler,
    ) -> pydantic_core.core_schema.CoreSchema:
        def validate_from_int(value: int) -> arrow.Arrow:
            return arrow.get(value)

        from_int_schema = pydantic_core.core_schema.chain_schema([
            pydantic_core.core_schema.int_schema(),
            pydantic_core.core_schema.no_info_plain_validator_function(validate_from_int),
        ])

        return pydantic_core.core_schema.json_or_python_schema(
            json_schema=from_int_schema,
            python_schema=pydantic_core.core_schema.union_schema([
                pydantic_core.core_schema.is_instance_schema(arrow.Arrow),
                from_int_schema,
            ]),
            serialization=pydantic_core.core_schema.plain_serializer_function_ser_schema(
                lambda instance: instance.int_timestamp if isinstance(instance, arrow.Arrow) else arrow.get(instance)
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(  # noqa: PLW3201
        cls,
        _core_schema: pydantic_core.CoreSchema,
        handler: pydantic.GetJsonSchemaHandler,
    ) -> pydantic.json_schema.JsonSchemaValue:
        return handler(pydantic_core.core_schema.int_schema())


class _ArrowTypeIsoformatPydanticAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(  # noqa: PLW3201
        cls,
        _source_type: typing.Any,  # noqa: ANN401
        _handler: pydantic.GetCoreSchemaHandler,
    ) -> pydantic_core.core_schema.CoreSchema:
        def validate_from_str(value: str) -> arrow.Arrow:
            return arrow.get(value)

        from_str_schema = pydantic_core.core_schema.chain_schema([
            pydantic_core.core_schema.str_schema(),
            pydantic_core.core_schema.no_info_plain_validator_function(validate_from_str),
        ])

        return pydantic_core.core_schema.json_or_python_schema(
            json_schema=from_str_schema,
            python_schema=pydantic_core.core_schema.union_schema([
                pydantic_core.core_schema.is_instance_schema(arrow.Arrow),
                from_str_schema,
            ]),
            serialization=pydantic_core.core_schema.plain_serializer_function_ser_schema(
                operator.methodcaller("isoformat")
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(  # noqa: PLW3201
        cls,
        _core_schema: pydantic_core.CoreSchema,
        handler: pydantic.GetJsonSchemaHandler,
    ) -> pydantic.json_schema.JsonSchemaValue:
        return handler(pydantic_core.core_schema.str_schema())


ArrowType = typing.Annotated[arrow.Arrow, _ArrowTypeTimestampPydanticAnnotation]
ISOArrowType = typing.Annotated[arrow.Arrow, _ArrowTypeIsoformatPydanticAnnotation]


class BaseModel(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="forbid",
    )


class SchemeBaseModel(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        extra="allow",
        frozen=True,
        alias_generator=pydantic.alias_generators.to_camel,
    )


class APISchemeBaseModel(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        frozen=True,
        extra="forbid",
        alias_generator=pydantic.alias_generators.to_camel,
    )


class AbstractPage(BaseModel, typing.Generic[T], abc.ABC):
    __model_aliases__: typing.ClassVar[dict[str, str]] = {}
    __model_exclude__: typing.ClassVar[set[str]] = set()
    model_config = {
        "arbitrary_types_allowed": True,
        "from_attributes": True,
        "populate_by_name": True,
    }

    @classmethod
    @typing.no_type_check
    def __pydantic_init_subclass__(cls, **kwargs: typing.Any) -> None:  # noqa: PLW3201, ANN401
        super().__pydantic_init_subclass__(**kwargs)

        for exclude in cls.__model_exclude__:
            cls.model_fields[exclude].exclude = True
        for name, alias in cls.__model_aliases__.items():
            cls.model_fields[name].serialization_alias = alias

        # rebuild model only in case if customizations is present
        if cls.__model_exclude__ or cls.__model_aliases__:
            with contextlib.suppress(pydantic.PydanticUndefinedAnnotation):
                cls.model_rebuild(force=True)


class BasePage(AbstractPage[T], typing.Generic[T], abc.ABC):
    items: typing.Sequence[T]
    total: GreaterEqualZero


class Page(BasePage[T], typing.Generic[T]):
    items: typing.Sequence[T]
    total: GreaterEqualZero

    @classmethod
    def create(
        cls,
        items: typing.Sequence[T],
        **kwargs: typing.Any,  # noqa: ANN401
    ) -> Page[T]:
        return cls(items=items, total=len(items), **kwargs)
