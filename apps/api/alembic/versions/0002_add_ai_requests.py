"""Add ai_requests table for AIGateway audit (redaction, consent, full audit, request_id)

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-03
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "ai_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), index=True),
        sa.Column("request_id", sa.String(64), index=True),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("endpoint", sa.String(50), nullable=False),
        sa.Column("redacted", sa.Boolean(), nullable=False, default=False),
        sa.Column("consent_used", sa.Boolean(), nullable=False, default=False),
        sa.Column("usage", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("latency_ms", sa.Float()),
        sa.Column("cost_usd", sa.Float()),
        sa.Column("full_audit_jsonb", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )
    # Note: production would add RLS policies or app-level user_id filters.
    # Indexes on (user_id, created_at) etc added in follow-up if needed.


def downgrade():
    op.drop_table("ai_requests")
