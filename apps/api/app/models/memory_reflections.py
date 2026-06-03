"""Reflections / retrospectives over memories (hindsight after real events).

Linked to memory_records via ids in json. Per design for "reflection after real events".
"""

from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base import Base, IdMixin, TimestampMixin, UserOwnedMixin


class MemoryReflection(Base, IdMixin, TimestampMixin, UserOwnedMixin):
    __tablename__ = "memory_reflections"

    reflection: Mapped[str] = mapped_column(Text)
    linked_record_ids: Mapped[list[str] | None] = mapped_column(
        JSONB
    )  # array of memory_record ids
    trigger_event: Mapped[str | None] = mapped_column(String(255))
    metadata_json: Mapped[dict | None] = mapped_column(JSONB)
