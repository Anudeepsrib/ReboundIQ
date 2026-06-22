"""User action audit log for deterministic, non-AI product workflows."""

from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin, UserOwnedMixin


class ActionAuditLog(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "action_audit_logs"

    action: Mapped[str] = mapped_column(String(100), index=True)
    resource_type: Mapped[str] = mapped_column(String(100), index=True)
    resource_id: Mapped[str | None] = mapped_column(String(100), index=True)
    request_id: Mapped[str | None] = mapped_column(String(128), index=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, default=dict)
