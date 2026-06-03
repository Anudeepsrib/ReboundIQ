"""Candidates for memory extraction / hindsight (pre-reflection).

Used by memory layer to propose records before user consent + reflection.
"""

from __future__ import annotations

from sqlalchemy import String, Float, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector

from app.db.base import Base, IdMixin, TimestampMixin, UserOwnedMixin


class MemoryCandidate(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "memory_candidates"

    content: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(100), index=True)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768))
    score: Mapped[float | None] = mapped_column(Float)
    source_event: Mapped[str | None] = mapped_column(String(255))
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)
