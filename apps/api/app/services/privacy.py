from __future__ import annotations

import base64
from datetime import date, datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.inspection import inspect as sa_inspect

from app.models import (
    ActionAuditLog,
    AgentApprovalRequest,
    AgentCampaign,
    AgentToolCall,
    AIRequest,
    ApplicationRecord,
    ConsentRecord,
    InterviewSession,
    MemoryCandidate,
    MemoryReflection,
    ProofAsset,
    Resume,
    ResumeVersion,
    RunwaySnapshot,
    User,
    UserProfile,
)
from app.models.memory_record import MemoryRecord
from app.models.resume import DocumentChunk
from app.services.audit import log_action
from app.services.storage import get_storage


EXPORT_MODELS = [
    UserProfile,
    Resume,
    ResumeVersion,
    DocumentChunk,
    AgentCampaign,
    AgentToolCall,
    AgentApprovalRequest,
    AIRequest,
    MemoryRecord,
    MemoryCandidate,
    MemoryReflection,
    ConsentRecord,
    RunwaySnapshot,
    ApplicationRecord,
    ProofAsset,
    InterviewSession,
    ActionAuditLog,
]


def _normalize(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    if isinstance(value, dict):
        return {key: _normalize(item) for key, item in value.items()}
    return value


def _row_to_dict(row: Any) -> dict[str, Any]:
    mapper = sa_inspect(row.__class__)
    return {
        column.key: _normalize(getattr(row, column.key))
        for column in mapper.column_attrs
    }


async def _rows_for_model(
    db: AsyncSession, model: type[Any], user_id: str
) -> list[dict[str, Any]]:
    result = await db.execute(select(model).where(model.user_id == user_id))
    return [_row_to_dict(row) for row in result.scalars().all()]


async def export_user_data(
    db: AsyncSession, user_id: str, request_id: str | None
) -> dict[str, Any]:
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise ValueError("User not found")

    export: dict[str, Any] = {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "user": _row_to_dict(user),
        "tables": {},
        "files": [],
        "notes": [
            "Planning guidance only; exported AI artifacts require human review.",
            "File payloads are base64 encoded where the configured storage backend can read them.",
        ],
    }

    for model in EXPORT_MODELS:
        export["tables"][model.__tablename__] = await _rows_for_model(
            db, model, user_id
        )

    storage = get_storage()
    resume_result = await db.execute(select(Resume).where(Resume.user_id == user_id))
    for resume in resume_result.scalars().all():
        try:
            data = await storage.get(resume.storage_key)
            export["files"].append(
                {
                    "resume_id": resume.id,
                    "filename": resume.original_filename,
                    "storage_key": resume.storage_key,
                    "mime_type": resume.mime_type,
                    "base64": base64.b64encode(data).decode("ascii"),
                }
            )
        except Exception as exc:
            export["files"].append(
                {
                    "resume_id": resume.id,
                    "filename": resume.original_filename,
                    "storage_key": resume.storage_key,
                    "error": f"{type(exc).__name__}: {str(exc)[:120]}",
                }
            )

    await log_action(
        db,
        user_id=user_id,
        action="export",
        resource_type="user_data",
        resource_id=user_id,
        request_id=request_id,
        metadata={"table_count": len(export["tables"]), "file_count": len(export["files"])},
        commit=True,
    )
    return export


async def delete_user_account(
    db: AsyncSession, user_id: str, request_id: str | None
) -> dict[str, Any]:
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise ValueError("User not found")

    await log_action(
        db,
        user_id=user_id,
        action="delete_account_requested",
        resource_type="user",
        resource_id=user_id,
        request_id=request_id,
    )
    storage = get_storage()
    deleted_files = await storage.delete_prefix(f"users/{user_id}")

    delete_order = [
        ActionAuditLog,
        AgentApprovalRequest,
        AgentToolCall,
        AgentCampaign,
        ProofAsset,
        InterviewSession,
        ApplicationRecord,
        DocumentChunk,
        ResumeVersion,
        Resume,
        AIRequest,
        MemoryRecord,
        MemoryCandidate,
        MemoryReflection,
        ConsentRecord,
        UserProfile,
    ]
    deleted_rows: dict[str, int] = {}
    for model in delete_order:
        result = await db.execute(delete(model).where(model.user_id == user_id))
        deleted_rows[model.__tablename__] = int(result.rowcount or 0)

    result = await db.execute(delete(User).where(User.id == user_id))
    deleted_rows["users"] = int(result.rowcount or 0)
    await db.commit()

    return {
        "ok": True,
        "user_id": user_id,
        "deleted_rows": deleted_rows,
        "deleted_files": deleted_files,
        "request_id": request_id,
    }
