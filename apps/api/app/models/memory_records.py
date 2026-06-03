"""Memory records (Hindsight / Postgres+pgvector default).

Per AGENTS + design:
- category, sensitivity, consent gating for high-sens
- embedding for similarity search (nomic-embed-text = 768)
- user_id isolation, soft delete, audit
- Memory is EVIDENCE ONLY; never auto overrides; pre-use validation required.
"""

from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector

from app.db.base import Base, IdMixin, TimestampMixin, UserOwnedMixin


class MemoryRecord(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "memory_records"

    category: Mapped[str] = mapped_column(String(100), index=True)
    # e.g. experience, skill, preference, event, reflection, visa, financial, health (sensitive)

    sensitivity: Mapped[str] = mapped_column(String(20), default="low", index=True)
    # low | medium | high  (high requires explicit consent per category)

    content: Mapped[str] = mapped_column(Text)  # grounded fact / note
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768))
    # 768 for nomic-embed-text; cosine for search

    source: Mapped[str | None] = mapped_column(
        String(255)
    )  # e.g. "resume:abc123", "user_input:note-4", "reflection:.."

    consent_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True
    )  # FK to consent_records (added in migration)

    metadata_json: Mapped[dict | None] = mapped_column(JSONB)
    # e.g. {"valid_from": "...", "tags": [...], "confidence": 0.9}
