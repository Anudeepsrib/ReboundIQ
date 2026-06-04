"""Consent records for sensitive actions (external AI, memory categories, etc).

Per non-negotiables + AGENTS: explicit consent + PII redaction before external.
User can export/delete; consent respected, never override.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin, UserOwnedMixin


class ConsentRecord(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "consent_records"

    consent_type: Mapped[str] = mapped_column(String(100), index=True)
    # e.g. "external_ai", "memory_category:visa", "memory_category:financial"

    granted: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    consent_text: Mapped[str] = mapped_column(
        Text
    )  # the exact text user acknowledged e.g. "I understand..."

    revoked_at: Mapped[datetime | None] = mapped_column(nullable=True)
    # version or source_ip_hash could be added later
