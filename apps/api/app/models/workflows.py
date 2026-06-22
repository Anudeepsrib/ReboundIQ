"""Persistent deterministic workflow records for the ReboundIQ product surface.

These tables back the non-generative runway, application, proof, and interview
workflows. All access must be scoped by authenticated user_id in services.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, IdMixin, TimestampMixin, UserOwnedMixin


class RunwaySnapshot(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "runway_snapshots"

    title: Mapped[str] = mapped_column(String(160), default="Current runway")
    scenario: Mapped[str] = mapped_column(String(40), default="base", index=True)
    risk_level: Mapped[str] = mapped_column(String(40), default="unknown", index=True)
    monthly_expenses: Mapped[float] = mapped_column(Float, default=0.0)
    savings_balance: Mapped[float] = mapped_column(Float, default=0.0)
    severance_amount: Mapped[float] = mapped_column(Float, default=0.0)
    unemployment_amount: Mapped[float] = mapped_column(Float, default=0.0)
    target_months: Mapped[float] = mapped_column(Float, default=6.0)
    assumptions_json: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    action_items_json: Mapped[list | None] = mapped_column(JSONB, default=list)
    disclaimer_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)


class ApplicationRecord(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "application_records"

    company: Mapped[str] = mapped_column(String(180))
    role: Mapped[str] = mapped_column(String(180))
    status: Mapped[str] = mapped_column(String(50), default="saved", index=True)
    source_url: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(String(180))
    salary_range: Mapped[str | None] = mapped_column(String(180))
    resume_version_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("resume_versions.id", ondelete="SET NULL"), index=True
    )
    jd_snapshot: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    next_step: Mapped[str | None] = mapped_column(String(180))
    next_step_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fit_score: Mapped[float | None] = mapped_column(Float)
    sponsorship_signal: Mapped[str | None] = mapped_column(String(80))
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, default=dict)


class ProofAsset(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "proof_assets"

    title: Mapped[str] = mapped_column(String(220))
    asset_type: Mapped[str] = mapped_column(String(60), index=True)
    status: Mapped[str] = mapped_column(String(40), default="draft", index=True)
    summary: Mapped[str | None] = mapped_column(Text)
    content_json: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    citations_json: Mapped[list | None] = mapped_column(JSONB, default=list)
    linked_application_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("application_records.id", ondelete="SET NULL"), index=True
    )
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, default=dict)


class InterviewSession(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "interview_sessions"

    target_role: Mapped[str] = mapped_column(String(180))
    company: Mapped[str | None] = mapped_column(String(180))
    interview_type: Mapped[str] = mapped_column(String(80), default="mixed", index=True)
    status: Mapped[str] = mapped_column(String(40), default="planned", index=True)
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    score: Mapped[float | None] = mapped_column(Float)
    focus_areas_json: Mapped[list | None] = mapped_column(JSONB, default=list)
    question_log_json: Mapped[list | None] = mapped_column(JSONB, default=list)
    feedback_json: Mapped[dict | None] = mapped_column(JSONB, default=dict)
    linked_application_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("application_records.id", ondelete="SET NULL"), index=True
    )
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, default=dict)
