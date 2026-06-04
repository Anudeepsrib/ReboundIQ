"""Add memory_records table for MemoryProvider (pgvector semantic retain/recall/reflect)
User-isolated, sensitivity, consent_scope, category filters. Used for private RAG + agent evidence.

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-03
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector

# match model EMBED_DIM
EMBED_DIM = 1536

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "memory_records",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), nullable=False, index=True),
        sa.Column("key", sa.String(128), index=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(EMBED_DIM)),
        sa.Column("category", sa.String(50), nullable=False, index=True, server_default="note"),
        sa.Column("sensitivity", sa.String(20), nullable=False, server_default="low"),
        sa.Column("consent_scope", sa.String(50)),
        sa.Column("source", sa.String(50)),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text())),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    # Vector index for cosine similarity (common for embeddings). HNSW preferred in pgvector 0.5+
    # Note: in some envs may need to be created after data; safe for empty.
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_memory_records_embedding_cosine
        ON memory_records USING hnsw (embedding vector_cosine_ops)
        WHERE embedding IS NOT NULL;
        """
    )
    # Composite for common filtered recall
    op.create_index(
        "ix_memory_records_user_category_created",
        "memory_records",
        ["user_id", "category", "created_at"],
    )
    # Note: production would add RLS policies or app-level user_id filters on all queries.
    # Memory is evidence only; never auto-apply.


def downgrade():
    op.drop_index("ix_memory_records_user_category_created", table_name="memory_records")
    op.drop_index("ix_memory_records_embedding_cosine", table_name="memory_records")
    op.drop_table("memory_records")
