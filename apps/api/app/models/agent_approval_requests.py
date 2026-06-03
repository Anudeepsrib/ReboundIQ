"""Human approval checkpoint requests for agent artifacts.

Per AGENTS: "request human approval for artifacts, never auto-apply, never auto-send".
Status drives LangGraph interrupt / resume.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base, IdMixin, TimestampMixin, UserOwnedMixin


class AgentApprovalRequest(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "agent_approval_requests"

    campaign_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    artifact_type: Mapped[str] = mapped_column(String(50), index=True)
    # e.g. "outreach_email", "resume_version", "cover_letter", "plan", "message"

    artifact_json: Mapped[dict | None] = mapped_column(
        JSONB
    )  # the proposed artifact (redacted if needed)
    artifact_ref: Mapped[str | None] = mapped_column(
        String(255)
    )  # e.g. storage key or version id

    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    # pending | approved | rejected | expired

    notes: Mapped[str | None] = mapped_column(Text)  # approver feedback

    responded_at: Mapped[datetime | None] = mapped_column(nullable=True)

    campaign: Mapped["AgentCampaign"] = relationship(back_populates="approval_requests")  # noqa: F821
