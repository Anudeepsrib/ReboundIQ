"""Audit log for agent tool invocations (per AGENTS: audit everything AI).

Linked to campaign. Immutable-ish (soft delete for GDPR export/delete cascade).
"""

from __future__ import annotations

from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base, IdMixin, TimestampMixin, UserOwnedMixin


class AgentToolCall(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "agent_tool_calls"

    campaign_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )  # FK to agent_campaigns (enforced in migration)

    tool_name: Mapped[str] = mapped_column(String(100), index=True)
    input_json: Mapped[dict | None] = mapped_column(JSONB)
    output_json: Mapped[dict | None] = mapped_column(JSONB)
    request_id: Mapped[str | None] = mapped_column(String(128), index=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer)

    campaign: Mapped["AgentCampaign"] = relationship(back_populates="tool_calls")  # noqa: F821
