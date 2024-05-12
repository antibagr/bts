import collections
import logging
import logging.config
import typing

import pydantic
import sqlalchemy
import sqlalchemy.exc
import sqlalchemy.pool

import alembic
import alembic.autogenerate
import alembic.config
import alembic.context
import alembic.operations
import alembic.runtime.migration
import alembic.script

from .version_table import (
    CREATE_VERSION_TRIGGER_KEY,
    DELETE_VERSION_TRIGGER_KEY,
    RECREATE_VERSION_TRIGGER_KEY,
    SYSTEM_COLUMN,
)

logger = logging.getLogger(__name__)
config = alembic.context.config

writer_rename_migration = alembic.autogenerate.rewriter.Rewriter()
writer_add_version_trigger = alembic.autogenerate.rewriter.Rewriter()
writer_del_version_trigger = alembic.autogenerate.rewriter.Rewriter()

writer_chain = writer_rename_migration.chain(writer_add_version_trigger.chain(writer_del_version_trigger))

OPERATIONS_WITH_TRIGGER_RECREATION: typing.Final = (
    alembic.operations.ops.AddColumnOp,
    alembic.operations.ops.DropColumnOp,
)


@writer_rename_migration.rewrites(alembic.operations.ops.MigrationScript)
def rename_migration_script(
    migration_context: alembic.runtime.migration.MigrationContext,
    revision: str,  # noqa: ARG001
    migration_script: alembic.operations.ops.MigrationScript,
) -> alembic.operations.ops.MigrationScript:
    # extract current head revision
    head_revision = alembic.script.ScriptDirectory.from_config(
        typing.cast(alembic.config.Config, migration_context.config)
    ).get_current_head()
    if head_revision is None:
        # edge case with first migration
        new_rev_id = 1
    else:
        # default branch with incrementation
        last_rev_id = int(head_revision.lstrip("0"))
        new_rev_id = last_rev_id + 1
    # fill zeros up to 4 digits: 1 -> 0001
    migration_script.rev_id = f"{new_rev_id:04}"
    return migration_script


@writer_add_version_trigger.rewrites(alembic.operations.ops.CreateTableOp)
def add_version_trigger(
    migration_context: alembic.runtime.migration.MigrationContext,  # noqa: ARG001
    revision: str,  # noqa: ARG001
    create_table_op: alembic.operations.ops.CreateTableOp,
) -> (
    alembic.operations.ops.CreateTableOp
    | list[alembic.operations.ops.CreateTableOp | alembic.operations.ops.ExecuteSQLOp]
):
    if create_table_op.info.get(CREATE_VERSION_TRIGGER_KEY):
        create_trigger_op = alembic.operations.ops.ExecuteSQLOp(create_table_op.info[CREATE_VERSION_TRIGGER_KEY])
        return [create_table_op, create_trigger_op]
    return create_table_op


@writer_del_version_trigger.rewrites(alembic.operations.ops.DropTableOp)
def del_version_trigger(
    migration_context: alembic.runtime.migration.MigrationContext,  # noqa: ARG001
    revision: str,  # noqa: ARG001
    drop_table_op: alembic.operations.ops.DropTableOp,
) -> (
    alembic.operations.ops.DropTableOp | list[alembic.operations.ops.DropTableOp | alembic.operations.ops.ExecuteSQLOp]
):
    if drop_table_op.info.get(DELETE_VERSION_TRIGGER_KEY):
        del_trigger_op = alembic.operations.ops.ExecuteSQLOp(drop_table_op.info[DELETE_VERSION_TRIGGER_KEY])
        return [drop_table_op, del_trigger_op]
    return drop_table_op


@writer_add_version_trigger.rewrites(alembic.operations.ops.ModifyTableOps)
def check_modify_operations(
    migration_context: alembic.runtime.migration.MigrationContext,
    revision: str,  # noqa: ARG001
    modify_ops: alembic.operations.ops.ModifyTableOps,
) -> alembic.operations.ops.ModifyTableOps:
    recreate_trigger_op = None
    table_columns: dict[sqlalchemy.Table, list[str]] = collections.defaultdict(list)
    for operation in modify_ops.ops:
        if not isinstance(operation, OPERATIONS_WITH_TRIGGER_RECREATION):
            continue

        table = _get_table_from_migration_context(migration_context, operation.schema, operation.table_name)

        if table is None:
            logger.warning(f"Table {operation.table_name} not found in metadata. Probably model was deleted")
            continue

        recreate_func = table.info.get(RECREATE_VERSION_TRIGGER_KEY)

        if recreate_func:
            if not table_columns.get(table):
                table_columns[table] = [column.name for column in table.c if column.name != SYSTEM_COLUMN]

            if isinstance(operation, alembic.operations.ops.DropColumnOp):
                table_columns[table] = [
                    column_name
                    for column_name in table_columns[table]
                    if column_name not in {operation.column_name, SYSTEM_COLUMN}
                ]
            elif operation.column.name not in {*table_columns[table], SYSTEM_COLUMN}:
                table_columns[table].append(operation.column.name)

            recreate_trigger_op = alembic.operations.ops.ExecuteSQLOp(
                recreate_func(columns=table_columns[table]),
            )

    if recreate_trigger_op:
        modify_ops.ops.append(recreate_trigger_op)

    return modify_ops


def _get_table_from_migration_context(
    migration_context: alembic.runtime.migration.MigrationContext,
    schema: str | None,
    table_name: str,
) -> sqlalchemy.Table:
    """Get table from migration context.

    Getting from context useful for cases when alembic generates model without an info parameter.

    """
    table_key = f"{schema}.{table_name}"
    original_tables = migration_context.opts["target_metadata"].tables
    return typing.cast(sqlalchemy.Table, original_tables.get(table_key))


def run_migrations_offline(
    target_metadata: sqlalchemy.MetaData,
    version_table_schema: str | None,
) -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    alembic.context.configure(
        url=url,
        target_metadata=target_metadata,
        version_table_schema=version_table_schema,
        process_revision_directives=writer_chain,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with alembic.context.begin_transaction():
        alembic.context.execute("set enable_parallel_hash=off;")
        if version_table_schema:
            alembic.context.execute(f"CREATE SCHEMA IF NOT EXISTS {version_table_schema};")
            alembic.context.execute(f"SET search_path TO {version_table_schema}, public;")
        alembic.context.run_migrations()
        alembic.context.execute("set enable_parallel_hash=on;")


def run_migrations_online(
    target_metadata: sqlalchemy.MetaData,
    version_table_schema: str | None,
    *,
    is_local: bool,
) -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = sqlalchemy.engine_from_config(
        config.get_section(config.config_ini_section) or {},
        prefix="sqlalchemy.",
        poolclass=sqlalchemy.pool.NullPool,
    )

    with connectable.connect() as connection:
        alembic.context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=version_table_schema,
            process_revision_directives=writer_chain,
            include_schemas=True,
        )

        with alembic.context.begin_transaction():
            if is_local:
                alembic.context.execute("LOCK TABLE pg_catalog.pg_namespace;")
            if version_table_schema:
                alembic.context.execute(f"CREATE SCHEMA IF NOT EXISTS {version_table_schema};")
            alembic.context.run_migrations()


def run_alembic(
    sqlalchemy_url: str | pydantic.PostgresDsn,
    target_metadata: sqlalchemy.MetaData,
    version_table_schema: str | None = None,
    *,
    is_local: bool = False,
) -> None:
    logging.config.fileConfig(typing.cast(str, config.config_file_name))

    config.set_main_option("sqlalchemy.url", str(sqlalchemy_url))

    if alembic.context.is_offline_mode():
        run_migrations_offline(target_metadata, version_table_schema)
    else:
        run_migrations_online(target_metadata, version_table_schema, is_local=is_local)
