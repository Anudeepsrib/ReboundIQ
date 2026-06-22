"""
MemoryRecord model for private long-term memory + RAG evidence store (Postgres + pgvector).
Always user-isolated (filter by user_id in all queries).
Sensitivity + consent_scope filters on recall.
Content stored as-is (original); embeddings may be on redacted version only if external embedder used (with consent).
"""

from sqlalchemy import String, Text, DateTime, ForeignKey, func, JSON
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
import uuid
from .user import Base
from pgvector.sqlalchemy import Vector

# Fixed dim for the default local embedding model and consolidated migration.
EMBED_DIM: int = 768


class MemoryRecord(Base):
    __tablename__ = "memory_records"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )

    # Optional namespaced key for direct lookup/overwrite (e.g. "profile:current_role")
    key: Mapped[str | None] = mapped_column(String(128), index=True)

    content: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # original text; evidence only

    embedding: Mapped[list[float] | None] = mapped_column(Vector(EMBED_DIM))

    category: Mapped[str] = mapped_column(
        String(50), default="note", nullable=False, index=True
    )
    # low|medium|high ; recall filters by max allowed
    sensitivity: Mapped[str] = mapped_column(String(20), default="low", nullable=False)

    # e.g. "memory_basic", "hindsight", "profile" -- for consent gating on recall
    consent_scope: Mapped[str | None] = mapped_column(String(50))

    source: Mapped[str | None] = mapped_column(
        String(50)
    )  # "user", "reflect", "resume_import", "agent"

    metadata_json: Mapped[dict | None] = mapped_column(
        JSON
    )  # source refs, timestamps, etc. never secrets

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
