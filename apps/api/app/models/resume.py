from sqlalchemy import String, Text, DateTime, ForeignKey, func, JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import uuid
from .user import Base

# pgvector support (for RAG embeddings on resume chunks etc). Dim 768 for nomic-embed-text default.
try:
    from pgvector.sqlalchemy import Vector
except ImportError:  # fallback for type/lint in partial envs
    Vector = list  # type: ignore[misc,assignment]


class Resume(Base):
    __tablename__ = "resumes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    original_filename: Mapped[str] = mapped_column(String(255))
    storage_key: Mapped[str] = mapped_column(String(512))  # never delete
    mime_type: Mapped[str]
    parsed_text: Mapped[str | None] = mapped_column(Text)
    parsed_json: Mapped[dict | None] = mapped_column(
        JSON
    )  # structured name/skills/experience
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    versions: Mapped[list["ResumeVersion"]] = relationship(
        back_populates="resume", cascade="all, delete-orphan"
    )


class ResumeVersion(Base):
    __tablename__ = "resume_versions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    resume_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("resumes.id"), index=True
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    version_name: Mapped[str] = mapped_column(String(100))  # e.g. "AI Engineer v2"
    target_role: Mapped[str | None]
    content_json: Mapped[dict] = mapped_column(JSON)  # bullets, summary etc
    ats_score: Mapped[float | None]
    source_inputs: Mapped[dict | None] = mapped_column(
        JSON
    )  # which JD/resume chunks used
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    resume: Mapped["Resume"] = relationship(back_populates="versions")


class DocumentChunk(Base):
    """RAG chunks + embeddings for resumes (and future docs). Stored immutable.
    Used for grounded recall in parse/versioning/generation. User-isolated.
    """

    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    resume_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("resumes.id"), index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer, default=0)
    text: Mapped[str] = mapped_column(Text)
    # 768 for default nomic-embed-text; queries use cosine via pgvector
    embedding: Mapped[list[float] | None] = mapped_column(Vector(768))
    meta: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
