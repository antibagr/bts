import functools
import typing

import sqlalchemy

CREATE_VERSION_TRIGGER_KEY: typing.Final = "CREATE_VERSION_TRIGGER_KEY"
DELETE_VERSION_TRIGGER_KEY: typing.Final = "DELETE_VERSION_TRIGGER_KEY"
RECREATE_VERSION_TRIGGER_KEY: typing.Final = "RECREATE_VERSION_TRIGGER_KEY"
SYSTEM_COLUMN: typing.Final = "row_id"

_T = typing.TypeVar("_T")


def declare_version_table(table: sqlalchemy.Table, version_table_name: str) -> sqlalchemy.Table:
    """Declare new table for store historical data of original table
    :param table: Original table
    :param version_table_name: Name for new table
    :return: Table with same columns as `table` plus `version` integer column.
    """

    def _col_copy(col: sqlalchemy.Column[_T]) -> sqlalchemy.Column[_T]:
        col = col.copy()
        col.unique = False
        col.default = col.server_default = None
        col.autoincrement = False
        col.nullable = True
        col._user_defined_nullable = col.nullable  # noqa: SLF001
        col.primary_key = False
        return col

    return sqlalchemy.Table(
        version_table_name,
        table.metadata,
        sqlalchemy.Column(
            SYSTEM_COLUMN,
            sqlalchemy.BigInteger,
            sqlalchemy.Identity(always=True, start=1, cycle=False),
            primary_key=True,
            nullable=False,
        ),
        *[_col_copy(x) for x in table.columns],
        info={
            CREATE_VERSION_TRIGGER_KEY: get_create_version_trigger_sql(
                schema=table.schema,
                table_name=table.name,
                version_table_name=version_table_name,
                columns=[column.name for column in table.c],  # type: ignore[misc]
            ),
            DELETE_VERSION_TRIGGER_KEY: get_delete_version_trigger_sql(schema=table.schema, table_name=table.name),
            RECREATE_VERSION_TRIGGER_KEY: functools.partial(
                recreate_version_trigger_sql,
                schema=table.schema,
                table_name=table.name,
                version_table_name=version_table_name,
            ),
        },
    )


def generate_trigger_name(table_name: str) -> tuple[str, str]:
    trigger_name = f"tg_{table_name}_versions"
    function_name = f"process_{trigger_name}"
    return trigger_name, function_name


def get_create_version_trigger_sql(
    schema: str | None,
    table_name: str,
    version_table_name: str,
    columns: typing.Sequence[sqlalchemy.Column[str]] | None = None,
) -> str:
    trigger_name, function_name = generate_trigger_name(table_name)
    old_sql = f"""
       create or replace function {function_name}()
       returns trigger as ${trigger_name}$
       declare
       main_table_columns text;

       begin
           select  string_agg(column_name, ',')
           into    main_table_columns
           from information_schema.columns
           where table_schema = '{schema}'
             and table_name   = '{table_name}';

           execute format(
               'insert into {schema}.{version_table_name} ( %s ) VALUES ($1.*) ',
                main_table_columns
           ) using OLD;

           RETURN NEW;
       end;
       ${trigger_name}$ language plpgsql;


       create trigger {trigger_name}
       after update or delete on {schema}.{table_name}
       for each row execute procedure {function_name}();
    """  # noqa: S608  # nosec

    if columns:
        formatted_log_columns = ", ".join(columns)  # type: ignore[arg-type]
        formatted_old_columns = ", ".join(f"old.{column_name}" for column_name in columns)

        return f"""
           create or replace function {function_name}()
           returns trigger as ${trigger_name}$

           begin
               insert into {schema}.{version_table_name} ( {formatted_log_columns} )
               values ( {formatted_old_columns} );
               return NEW;
           end;
           ${trigger_name}$ language plpgsql;

           create trigger {trigger_name}
           after update or delete on {schema}.{table_name}
           for each row execute procedure {function_name}();
        """  # noqa: S608  # nosec

    return old_sql


def get_delete_version_trigger_sql(schema: str | None, table_name: str) -> str:
    trigger_name, function_name = generate_trigger_name(table_name)
    return (
        f"drop function if exists {function_name}() cascade; "
        f"drop trigger if exists  {trigger_name} on {schema}.{table_name};"
    )


def recreate_version_trigger_sql(
    schema: str | None,
    table_name: str,
    version_table_name: str,
    columns: typing.Sequence[str] | None = None,
) -> str:
    sql = get_delete_version_trigger_sql(schema, table_name)
    sql += get_create_version_trigger_sql(schema, table_name, version_table_name, columns)  # type: ignore[arg-type]
    return sql
