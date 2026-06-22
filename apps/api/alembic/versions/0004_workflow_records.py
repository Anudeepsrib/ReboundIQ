"""Add product workflow persistence tables

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    ]


def upgrade():
    # Align the active MemoryProvider model with the consolidated 0002 memory table.
    op.execute("ALTER TABLE memory_records ADD COLUMN IF NOT EXISTS key VARCHAR(128);")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_memory_records_key ON memory_records (key);"
    )
    op.execute(
        "ALTER TABLE memory_records ADD COLUMN IF NOT EXISTS consent_scope VARCHAR(50);"
    )

    op.create_table(
        "runway_snapshots",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(160), nullable=False),
        sa.Column("scenario", sa.String(40), nullable=False),
        sa.Column("risk_level", sa.String(40), nullable=False),
        sa.Column("monthly_expenses", sa.Float(), nullable=False),
        sa.Column("savings_balance", sa.Float(), nullable=False),
        sa.Column("severance_amount", sa.Float(), nullable=False),
        sa.Column("unemployment_amount", sa.Float(), nullable=False),
        sa.Column("target_months", sa.Float(), nullable=False),
        sa.Column("assumptions_json", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("action_items_json", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("disclaimer_acknowledged", sa.Boolean(), nullable=False, default=False),
        *_timestamps(),
    )
    op.create_index("ix_runway_snapshots_user_id", "runway_snapshots", ["user_id"])
    op.create_index(
        "ix_runway_snapshots_user_created",
        "runway_snapshots",
        ["user_id", "created_at"],
    )
    op.create_index(
        "ix_runway_snapshots_deleted_at", "runway_snapshots", ["deleted_at"]
    )

    op.create_table(
        "application_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("company", sa.String(180), nullable=False),
        sa.Column("role", sa.String(180), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("source_url", sa.Text()),
        sa.Column("location", sa.String(180)),
        sa.Column("salary_range", sa.String(180)),
        sa.Column(
            "resume_version_id",
            sa.String(36),
            sa.ForeignKey("resume_versions.id", ondelete="SET NULL"),
        ),
        sa.Column("jd_snapshot", sa.Text()),
        sa.Column("notes", sa.Text()),
        sa.Column("next_step", sa.String(180)),
        sa.Column("next_step_at", sa.DateTime(timezone=True)),
        sa.Column("fit_score", sa.Float()),
        sa.Column("sponsorship_signal", sa.String(80)),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text())),
        *_timestamps(),
    )
    op.create_index("ix_application_records_user_id", "application_records", ["user_id"])
    op.create_index("ix_application_records_status", "application_records", ["status"])
    op.create_index(
        "ix_application_records_resume_version_id",
        "application_records",
        ["resume_version_id"],
    )
    op.create_index(
        "ix_application_records_user_status",
        "application_records",
        ["user_id", "status"],
    )
    op.create_index(
        "ix_application_records_deleted_at", "application_records", ["deleted_at"]
    )

    op.create_table(
        "proof_assets",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(220), nullable=False),
        sa.Column("asset_type", sa.String(60), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("summary", sa.Text()),
        sa.Column("content_json", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("citations_json", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column(
            "linked_application_id",
            sa.String(36),
            sa.ForeignKey("application_records.id", ondelete="SET NULL"),
        ),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text())),
        *_timestamps(),
    )
    op.create_index("ix_proof_assets_user_id", "proof_assets", ["user_id"])
    op.create_index("ix_proof_assets_asset_type", "proof_assets", ["asset_type"])
    op.create_index("ix_proof_assets_status", "proof_assets", ["status"])
    op.create_index(
        "ix_proof_assets_linked_application_id",
        "proof_assets",
        ["linked_application_id"],
    )
    op.create_index(
        "ix_proof_assets_user_status", "proof_assets", ["user_id", "status"]
    )
    op.create_index("ix_proof_assets_deleted_at", "proof_assets", ["deleted_at"])

    op.create_table(
        "interview_sessions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("target_role", sa.String(180), nullable=False),
        sa.Column("company", sa.String(180)),
        sa.Column("interview_type", sa.String(80), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True)),
        sa.Column("score", sa.Float()),
        sa.Column("focus_areas_json", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("question_log_json", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("feedback_json", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column(
            "linked_application_id",
            sa.String(36),
            sa.ForeignKey("application_records.id", ondelete="SET NULL"),
        ),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text())),
        *_timestamps(),
    )
    op.create_index("ix_interview_sessions_user_id", "interview_sessions", ["user_id"])
    op.create_index(
        "ix_interview_sessions_interview_type",
        "interview_sessions",
        ["interview_type"],
    )
    op.create_index("ix_interview_sessions_status", "interview_sessions", ["status"])
    op.create_index(
        "ix_interview_sessions_linked_application_id",
        "interview_sessions",
        ["linked_application_id"],
    )
    op.create_index(
        "ix_interview_sessions_user_status",
        "interview_sessions",
        ["user_id", "status"],
    )
    op.create_index(
        "ix_interview_sessions_deleted_at", "interview_sessions", ["deleted_at"]
    )


def downgrade():
    op.drop_index("ix_interview_sessions_deleted_at", table_name="interview_sessions")
    op.drop_index("ix_interview_sessions_user_status", table_name="interview_sessions")
    op.drop_index(
        "ix_interview_sessions_linked_application_id", table_name="interview_sessions"
    )
    op.drop_index("ix_interview_sessions_status", table_name="interview_sessions")
    op.drop_index(
        "ix_interview_sessions_interview_type", table_name="interview_sessions"
    )
    op.drop_index("ix_interview_sessions_user_id", table_name="interview_sessions")
    op.drop_table("interview_sessions")

    op.drop_index("ix_proof_assets_deleted_at", table_name="proof_assets")
    op.drop_index("ix_proof_assets_user_status", table_name="proof_assets")
    op.drop_index("ix_proof_assets_linked_application_id", table_name="proof_assets")
    op.drop_index("ix_proof_assets_status", table_name="proof_assets")
    op.drop_index("ix_proof_assets_asset_type", table_name="proof_assets")
    op.drop_index("ix_proof_assets_user_id", table_name="proof_assets")
    op.drop_table("proof_assets")

    op.drop_index("ix_application_records_deleted_at", table_name="application_records")
    op.drop_index("ix_application_records_user_status", table_name="application_records")
    op.drop_index(
        "ix_application_records_resume_version_id", table_name="application_records"
    )
    op.drop_index("ix_application_records_status", table_name="application_records")
    op.drop_index("ix_application_records_user_id", table_name="application_records")
    op.drop_table("application_records")

    op.drop_index("ix_runway_snapshots_deleted_at", table_name="runway_snapshots")
    op.drop_index("ix_runway_snapshots_user_created", table_name="runway_snapshots")
    op.drop_index("ix_runway_snapshots_user_id", table_name="runway_snapshots")
    op.drop_table("runway_snapshots")

    op.execute("DROP INDEX IF EXISTS ix_memory_records_key;")
    op.execute("ALTER TABLE memory_records DROP COLUMN IF EXISTS consent_scope;")
    op.execute("ALTER TABLE memory_records DROP COLUMN IF EXISTS key;")
