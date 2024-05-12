"""init.

Revision ID: 0001
Revises:
Create Date: 2024-05-12 21:44:40.366844

"""

import sqlalchemy as sa
import sqlalchemy_utils
import sqlmodel.sql.sqltypes

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS bts;")
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    op.create_table(
        "users",
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column(
            "created_at",
            sqlalchemy_utils.types.arrow.ArrowType(),
            server_default=sa.text("(now() at time zone 'utc')"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sqlalchemy_utils.types.arrow.ArrowType(),
            server_default=sa.text("(now() at time zone 'utc')"),
            server_onupdate=sa.text("(now() at time zone 'utc')"),
            nullable=False,
        ),
        sa.Column("email", sqlalchemy_utils.types.email.EmailType(length=255), nullable=True),
        sa.Column("is_superuser", sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        schema="bts",
    )
    op.create_index(op.f("ix_bts_users_id"), "users", ["id"], unique=True, schema="bts")
    op.create_table(
        "bets",
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column(
            "created_at",
            sqlalchemy_utils.types.arrow.ArrowType(),
            server_default=sa.text("(now() at time zone 'utc')"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sqlalchemy_utils.types.arrow.ArrowType(),
            server_default=sa.text("(now() at time zone 'utc')"),
            server_onupdate=sa.text("(now() at time zone 'utc')"),
            nullable=False,
        ),
        sa.Column("event_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("user_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column(
            "amount",
            sa.Numeric(),
            nullable=False,
            comment="Amount of the bet",
        ),
        sa.Column(
            "status",
            sa.Enum("PENDING", "WON", "LOST", name="enum_bet_status"),
            nullable=False,
            comment="Status of the bet",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["bts.users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        schema="bts",
    )
    op.create_index("ix_bets_user_id_event_id", "bets", ["user_id", "event_id"], unique=True, schema="bts")
    op.create_index(op.f("ix_bts_bets_event_id"), "bets", ["event_id"], unique=False, schema="bts")
    op.create_index(op.f("ix_bts_bets_id"), "bets", ["id"], unique=True, schema="bts")
    op.create_index(op.f("ix_bts_bets_user_id"), "bets", ["user_id"], unique=False, schema="bts")
    # ### end Alembic commands ###


def downgrade() -> None:
    op.execute("DROP SCHEMA IF EXISTS bts CASCADE;")
    op.execute("DROP TYPE IF EXISTS enum_bet_status;")
