"""Agent campaign model stub (for CareerCampaignAgent + subagents).

Per PR-2 / design: goal + status, human approval checkpoints via related approval_requests.
Audit via tool_calls. Soft delete + user_id isolation.
"""

from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base, IdMixin, TimestampMixin, UserOwnedMixin


class AgentCampaign(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "agent_campaigns"

    goal: Mapped[str] = mapped_column(
        Text
    )  # user goal e.g. "land senior backend role in 90 days"
    status: Mapped[str] = mapped_column(String(50), default="active", index=True)
    # active | paused | completed | aborted | blocked

    metadata_json: Mapped[dict | None] = mapped_column(
        JSONB
    )  # steps, config, last_state etc

    # Relationships for audit / checkpoints (populated in full agent impl)
    tool_calls: Mapped[list["AgentToolCall"]] = relationship(  # noqa: F821
        back_populates="campaign", cascade="all, delete-orphan"
    )
    approval_requests: Mapped[list["AgentApprovalRequest"]] = relationship(  # noqa: F821
        back_populates="campaign", cascade="all, delete-orphan"
    )
