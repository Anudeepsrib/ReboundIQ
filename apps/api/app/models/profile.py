"""User profile model (core table per PR-2 / design).

Separate from resumes for preferences, headline, sensitive fields (later encrypted via service).
"""

from __future__ import annotations

from sqlalchemy import String, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base, IdMixin, TimestampMixin, UserOwnedMixin


class UserProfile(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "user_profiles"

    headline: Mapped[str | None] = mapped_column(String(255))
    summary: Mapped[str | None] = mapped_column(Text)
    skills_json: Mapped[dict | None] = mapped_column(JSONB)
    preferences_json: Mapped[dict | None] = mapped_column(
        JSONB
    )  # target roles, locations, constraints
    sensitive_json: Mapped[dict | None] = mapped_column(
        JSONB
    )  # H1B etc - handle via redaction/encryption in services

    # Consent flags (for snapshotting into JWT for memory/external/sensitive paths) [PR-3 auth/isolation]
    consent_external_ai: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_memory_sensitive: Mapped[bool] = mapped_column(Boolean, default=False)
    consent_visa_processing: Mapped[bool] = mapped_column(Boolean, default=False)
    # RBAC skeleton [PR-3]
    role: Mapped[str] = mapped_column(String(50), default="user")

    user: Mapped["User"] = relationship(back_populates="profile", uselist=False)  # noqa: F821
