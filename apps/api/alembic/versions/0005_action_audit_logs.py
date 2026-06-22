"""Add deterministic action audit logs

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "action_audit_logs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("resource_type", sa.String(100), nullable=False),
        sa.Column("resource_id", sa.String(100)),
        sa.Column("request_id", sa.String(128)),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_action_audit_logs_user_id", "action_audit_logs", ["user_id"])
    op.create_index("ix_action_audit_logs_action", "action_audit_logs", ["action"])
    op.create_index(
        "ix_action_audit_logs_resource_type",
        "action_audit_logs",
        ["resource_type"],
    )
    op.create_index(
        "ix_action_audit_logs_resource_id", "action_audit_logs", ["resource_id"]
    )
    op.create_index(
        "ix_action_audit_logs_request_id", "action_audit_logs", ["request_id"]
    )
    op.create_index(
        "ix_action_audit_logs_user_created",
        "action_audit_logs",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_action_audit_logs_deleted_at", "action_audit_logs", ["deleted_at"]
    )


def downgrade():
    op.drop_index("ix_action_audit_logs_deleted_at", table_name="action_audit_logs")
    op.drop_index("ix_action_audit_logs_user_created", table_name="action_audit_logs")
    op.drop_index("ix_action_audit_logs_request_id", table_name="action_audit_logs")
    op.drop_index("ix_action_audit_logs_resource_id", table_name="action_audit_logs")
    op.drop_index("ix_action_audit_logs_resource_type", table_name="action_audit_logs")
    op.drop_index("ix_action_audit_logs_action", table_name="action_audit_logs")
    op.drop_index("ix_action_audit_logs_user_id", table_name="action_audit_logs")
    op.drop_table("action_audit_logs")
