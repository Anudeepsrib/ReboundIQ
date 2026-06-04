"""Audit for all AI gateway calls (local + external when consented).

Per AGENTS: "Audit everything AI: ai_requests, agent_tool_calls, memory_*"
Redaction + consent recorded here. request_id for correlation.
"""

from __future__ import annotations

from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base, IdMixin, TimestampMixin, UserOwnedMixin


class AIRequest(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "ai_requests"

    request_id: Mapped[str | None] = mapped_column(String(128), index=True)
    provider: Mapped[str] = mapped_column(String(50), index=True)
    model: Mapped[str] = mapped_column(String(100))
    prompt_preview: Mapped[str | None] = mapped_column()  # redacted/truncated
    response_preview: Mapped[str | None] = mapped_column()
    usage_json: Mapped[dict | None] = mapped_column(JSONB)
    external: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    redacted: Mapped[bool] = mapped_column(Boolean, default=True)
    consent_id: Mapped[str | None] = mapped_column(
        String(36), index=True
    )  # links to consent_records
