"""Add user profile consent and role columns

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-23
"""

from alembic import op
import sqlalchemy as sa


revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user_profiles",
        sa.Column(
            "consent_external_ai",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "user_profiles",
        sa.Column(
            "consent_memory_sensitive",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "user_profiles",
        sa.Column(
            "consent_visa_processing",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "user_profiles",
        sa.Column("role", sa.String(50), nullable=False, server_default="user"),
    )


def downgrade():
    op.drop_column("user_profiles", "role")
    op.drop_column("user_profiles", "consent_visa_processing")
    op.drop_column("user_profiles", "consent_memory_sensitive")
    op.drop_column("user_profiles", "consent_external_ai")
