"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-07-05

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "magic_link_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_magic_link_tokens_user_id", "magic_link_tokens", ["user_id"])
    op.create_index(
        "ix_magic_link_tokens_token_hash", "magic_link_tokens", ["token_hash"], unique=True
    )

    # Not created explicitly here: create_table() below creates these enum
    # types itself as part of creating monitor_configs (the only table that
    # uses them). Creating them again explicitly caused a duplicate-type error.
    frequency_enum = postgresql.ENUM(
        "immediate", "daily", "weekly", name="frequency_enum"
    )
    status_enum = postgresql.ENUM("active", "paused", name="config_status_enum")

    op.create_table(
        "monitor_configs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("email_to_monitor", sa.String(320), nullable=False),
        sa.Column("imap_server", sa.String(255), nullable=False),
        sa.Column("imap_port", sa.Integer(), nullable=False, server_default="993"),
        sa.Column("imap_password_encrypted", sa.String(), nullable=False),
        sa.Column("report_destination_email", sa.String(320), nullable=False),
        sa.Column(
            "frequency",
            frequency_enum,
            nullable=False,
            server_default="immediate",
        ),
        sa.Column(
            "status",
            status_enum,
            nullable=False,
            server_default="active",
        ),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_seen_uid", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("last_seen_uidvalidity", sa.BigInteger(), nullable=True),
        sa.Column("last_error", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "email_analyses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "config_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("monitor_configs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("message_id", sa.String(998), nullable=False),
        sa.Column("imap_uid", sa.BigInteger(), nullable=False),
        sa.Column("sender", sa.String(320), nullable=False),
        sa.Column("subject", sa.String(998), nullable=False, server_default=""),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("mood_label", sa.String(32), nullable=False),
        sa.Column("mood_score", sa.Float(), nullable=False),
        sa.Column("mood_summary", sa.Text(), nullable=False, server_default=""),
        sa.Column("requires_attention", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("analysis_failed", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("report_sent", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("report_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("config_id", "message_id", name="uq_config_message"),
    )
    op.create_index("ix_email_analyses_config_id", "email_analyses", ["config_id"])


def downgrade() -> None:
    op.drop_index("ix_email_analyses_config_id", table_name="email_analyses")
    op.drop_table("email_analyses")
    # Dropping monitor_configs also drops frequency_enum/config_status_enum,
    # since they're only used by this table's columns.
    op.drop_table("monitor_configs")
    op.drop_index("ix_magic_link_tokens_token_hash", table_name="magic_link_tokens")
    op.drop_index("ix_magic_link_tokens_user_id", table_name="magic_link_tokens")
    op.drop_table("magic_link_tokens")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
