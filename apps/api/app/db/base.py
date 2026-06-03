"""SQLAlchemy 2.0 declarative Base + common mixins.

Per design + AGENTS.md:
- id (uuid str)
- user_id on all user-owned tables (row-level isolation)
- created_at / updated_at / deleted_at (soft delete via deleted_at IS NULL)
- Alembic ONLY for schema changes (never edit models standalone)
- JSONB for structured, Vector for pgvector memory embeddings
"""

from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import String, DateTime, func, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Root declarative base for all models. Metadata collected here for Alembic."""

    pass


class IdMixin:
    """Common primary key."""

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )


class TimestampMixin:
    """Common audit + soft delete timestamps.

    Soft delete: filter deleted_at.is_(None) in queries/services.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )


class UserOwnedMixin:
    """Mixin for tables that must be filtered by authenticated user_id (per AGENTS)."""

    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False, index=True
    )
