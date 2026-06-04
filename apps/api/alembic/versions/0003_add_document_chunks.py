"""Add document_chunks table for RAG (resume + future docs) with pgvector embeddings.
PR-7: resume upload/parse + storage + RAG chunk/embed for grounding.

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-03
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    # Raw SQL for vector type (pgvector extension already in init.sql; ARRAY would be wrong type)
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS document_chunks (
            id VARCHAR(36) PRIMARY KEY,
            user_id VARCHAR(36) NOT NULL REFERENCES users(id),
            resume_id VARCHAR(36) REFERENCES resumes(id),
            chunk_index INTEGER NOT NULL DEFAULT 0,
            text TEXT NOT NULL,
            embedding VECTOR(768),
            meta JSONB,
            created_at TIMESTAMPTZ DEFAULT now()
        );
        CREATE INDEX IF NOT EXISTS document_chunks_user_id_idx ON document_chunks (user_id);
        CREATE INDEX IF NOT EXISTS document_chunks_resume_id_idx ON document_chunks (resume_id);
        CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx ON document_chunks USING hnsw (embedding vector_cosine_ops);
        """
    )


def downgrade():
    op.execute("DROP INDEX IF EXISTS document_chunks_embedding_idx;")
    op.execute("DROP INDEX IF EXISTS document_chunks_resume_id_idx;")
    op.execute("DROP INDEX IF EXISTS document_chunks_user_id_idx;")
    op.drop_table("document_chunks")
