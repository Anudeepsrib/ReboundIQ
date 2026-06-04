"""Add common fields (updated_at/deleted_at to prior tables for consistency) +
initial agent/memory tables (PR-2 / Order 1-2).

Tables added (stubs with proper columns/indexes/FKs/JSONB/vector):
- user_profiles
- agent_campaigns (goal, status)
- memory_records (category, sensitivity, consent_id, embedding:vector)
- agent_tool_calls
- agent_approval_requests
- memory_candidates (with embedding)
- memory_reflections
- ai_requests
- consent_records

Also adds deleted_at (soft delete) + missing updated_at to users/resumes/resume_versions.
Per design: user_id on owned tables, pgvector for memory, JSONB for structured data.

Revision ID: 0002
Revises: 0001
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    # --- Common fields for consistency (soft delete everywhere appropriate) ---
    # users already had updated_at in 0001; add deleted_at
    op.add_column(
        "users",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_users_deleted_at", "users", ["deleted_at"])

    # resumes: add updated_at + deleted_at (0001 had only created_at)
    op.add_column(
        "resumes",
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )
    op.add_column(
        "resumes",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_resumes_deleted_at", "resumes", ["deleted_at"])

    # resume_versions: add updated_at + deleted_at
    op.add_column(
        "resume_versions",
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )
    op.add_column(
        "resume_versions",
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_resume_versions_deleted_at", "resume_versions", ["deleted_at"])

    # --- New core: profile ---
    op.create_table(
        "user_profiles",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("headline", sa.String(255)),
        sa.Column("summary", sa.Text()),
        sa.Column("skills_json", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("preferences_json", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("sensitive_json", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_user_profiles_deleted_at", "user_profiles", ["deleted_at"])

    # --- Agent / memory tables (stubs) ---
    op.create_table(
        "agent_campaigns",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("goal", sa.Text(), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, index=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_agent_campaigns_user_status",
        "agent_campaigns",
        ["user_id", "status"],
    )
    op.create_index("ix_agent_campaigns_deleted_at", "agent_campaigns", ["deleted_at"])

    op.create_table(
        "consent_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("consent_type", sa.String(100), nullable=False, index=True),
        sa.Column("granted", sa.Boolean(), nullable=False, default=False),
        sa.Column("consent_text", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_consent_records_deleted_at", "consent_records", ["deleted_at"])

    op.create_table(
        "memory_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("category", sa.String(100), nullable=False, index=True),
        sa.Column("sensitivity", sa.String(20), nullable=False, index=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(768)),
        sa.Column("source", sa.String(255)),
        sa.Column(
            "consent_id",
            sa.String(36),
            sa.ForeignKey("consent_records.id"),
            nullable=True,
            index=True,
        ),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_memory_records_deleted_at", "memory_records", ["deleted_at"])
    # Vector similarity index (hnsw recommended for pgvector >=0.5)
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_memory_records_embedding "
        "ON memory_records USING hnsw (embedding vector_cosine_ops)"
    )

    op.create_table(
        "agent_tool_calls",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "campaign_id",
            sa.String(36),
            sa.ForeignKey("agent_campaigns.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("tool_name", sa.String(100), nullable=False, index=True),
        sa.Column("input_json", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("output_json", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("request_id", sa.String(128), index=True),
        sa.Column("latency_ms", sa.Integer()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_agent_tool_calls_deleted_at", "agent_tool_calls", ["deleted_at"]
    )

    op.create_table(
        "agent_approval_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "campaign_id",
            sa.String(36),
            sa.ForeignKey("agent_campaigns.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("artifact_type", sa.String(50), nullable=False, index=True),
        sa.Column("artifact_json", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("artifact_ref", sa.String(255)),
        sa.Column("status", sa.String(20), nullable=False, index=True),
        sa.Column("notes", sa.Text()),
        sa.Column("responded_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_agent_approval_requests_deleted_at",
        "agent_approval_requests",
        ["deleted_at"],
    )

    op.create_table(
        "memory_candidates",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category", sa.String(100), nullable=False, index=True),
        sa.Column("embedding", Vector(768)),
        sa.Column("score", sa.Float()),
        sa.Column("source_event", sa.String(255)),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_memory_candidates_deleted_at", "memory_candidates", ["deleted_at"]
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_memory_candidates_embedding "
        "ON memory_candidates USING hnsw (embedding vector_cosine_ops)"
    )

    op.create_table(
        "memory_reflections",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("reflection", sa.Text(), nullable=False),
        sa.Column("linked_record_ids", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("trigger_event", sa.String(255)),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_memory_reflections_deleted_at", "memory_reflections", ["deleted_at"]
    )

    op.create_table(
        "ai_requests",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("request_id", sa.String(128), index=True),
        sa.Column("provider", sa.String(50), nullable=False, index=True),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("prompt_preview", sa.Text()),
        sa.Column("response_preview", sa.Text()),
        sa.Column("usage_json", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column("external", sa.Boolean(), nullable=False, default=False),
        sa.Column("redacted", sa.Boolean(), nullable=False, default=True),
        sa.Column(
            "consent_id",
            sa.String(36),
            sa.ForeignKey("consent_records.id"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_ai_requests_deleted_at", "ai_requests", ["deleted_at"])


def downgrade():
    # Drop in reverse FK order
    op.drop_index("ix_ai_requests_deleted_at", table_name="ai_requests")
    op.drop_table("ai_requests")

    op.drop_index("ix_memory_reflections_deleted_at", table_name="memory_reflections")
    op.drop_table("memory_reflections")

    op.execute("DROP INDEX IF EXISTS idx_memory_candidates_embedding")
    op.drop_index("ix_memory_candidates_deleted_at", table_name="memory_candidates")
    op.drop_table("memory_candidates")

    op.drop_index(
        "ix_agent_approval_requests_deleted_at", table_name="agent_approval_requests"
    )
    op.drop_table("agent_approval_requests")

    op.drop_index("ix_agent_tool_calls_deleted_at", table_name="agent_tool_calls")
    op.drop_table("agent_tool_calls")

    op.execute("DROP INDEX IF EXISTS idx_memory_records_embedding")
    op.drop_index("ix_memory_records_deleted_at", table_name="memory_records")
    op.drop_table("memory_records")

    op.drop_index("ix_consent_records_deleted_at", table_name="consent_records")
    op.drop_table("consent_records")

    op.drop_index("ix_agent_campaigns_deleted_at", table_name="agent_campaigns")
    op.drop_index("ix_agent_campaigns_user_status", table_name="agent_campaigns")
    op.drop_table("agent_campaigns")

    op.drop_index("ix_user_profiles_deleted_at", table_name="user_profiles")
    op.drop_table("user_profiles")

    # Remove added columns (reverse of upgrade)
    op.drop_index("ix_resume_versions_deleted_at", table_name="resume_versions")
    op.drop_column("resume_versions", "deleted_at")
    op.drop_column("resume_versions", "updated_at")

    op.drop_index("ix_resumes_deleted_at", table_name="resumes")
    op.drop_column("resumes", "deleted_at")
    op.drop_column("resumes", "updated_at")

    op.drop_index("ix_users_deleted_at", table_name="users")
    op.drop_column("users", "deleted_at")
