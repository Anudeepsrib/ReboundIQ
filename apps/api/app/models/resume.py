from __future__ import annotations

from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base, IdMixin, TimestampMixin, UserOwnedMixin


class Resume(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "resumes"

    original_filename: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str] = mapped_column(String(512))  # never delete
    mime_type: Mapped[str]
    parsed_text: Mapped[str | None] = mapped_column(Text)
    parsed_json: Mapped[dict | None] = mapped_column(
        JSONB
    )  # structured name/skills/experience

    versions: Mapped[list["ResumeVersion"]] = relationship(
        back_populates="resume", cascade="all, delete-orphan"
    )
    user: Mapped["User"] = relationship(back_populates="resumes")  # noqa: F821


class ResumeVersion(Base, IdMixin, TimestampMixin):
    __tablename__ = "resume_versions"

<<<<<<< HEAD
=======
    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
>>>>>>> 4a0a2ac (PR-1: Monorepo bootstrap + core foundation (Order 1))
    resume_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("resumes.id"), index=True
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    version_name: Mapped[str] = mapped_column(String(100))  # e.g. "AI Engineer v2"
    target_role: Mapped[str | None]
    content_json: Mapped[dict] = mapped_column(JSONB)  # bullets, summary etc
    ats_score: Mapped[float | None]
    source_inputs: Mapped[dict | None] = mapped_column(
<<<<<<< HEAD
        JSONB
    )  # which JD/resume chunks used
=======
        JSON
    )  # which JD/resume chunks used
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
>>>>>>> 4a0a2ac (PR-1: Monorepo bootstrap + core foundation (Order 1))

    resume: Mapped["Resume"] = relationship(back_populates="versions")
    # user relation omitted for stub (use user_id directly; full joins via FK)
