"""User profile model (core table per PR-2 / design).

Separate from resumes for preferences, headline, sensitive fields (later encrypted via service).
"""

from __future__ import annotations

from sqlalchemy import String, Text
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

    user: Mapped["User"] = relationship(back_populates="profile", uselist=False)  # noqa: F821
