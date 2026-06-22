from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, TypeVar

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resume import ResumeVersion
from app.models.workflows import (
    ApplicationRecord,
    InterviewSession,
    ProofAsset,
    RunwaySnapshot,
)
from app.services.audit import log_action

WorkflowRecord = TypeVar(
    "WorkflowRecord", RunwaySnapshot, ApplicationRecord, ProofAsset, InterviewSession
)


class WorkflowNotFound(ValueError):
    """Raised when a workflow record is absent or not owned by the user."""


def owned_active_stmt(
    model: type[WorkflowRecord], user_id: str, item_id: str | None = None
) -> Select[tuple[WorkflowRecord]]:
    stmt = select(model).where(model.user_id == user_id, model.deleted_at.is_(None))
    if item_id:
        stmt = stmt.where(model.id == item_id)
    return stmt


async def _get_owned(
    db: AsyncSession, model: type[WorkflowRecord], user_id: str, item_id: str
) -> WorkflowRecord:
    result = await db.execute(owned_active_stmt(model, user_id, item_id))
    item = result.scalar_one_or_none()
    if item is None:
        raise WorkflowNotFound(f"{model.__tablename__} record not found")
    return item


async def _list_owned(
    db: AsyncSession,
    model: type[WorkflowRecord],
    user_id: str,
    status: str | None = None,
) -> list[WorkflowRecord]:
    stmt = owned_active_stmt(model, user_id)
    if status and hasattr(model, "status"):
        stmt = stmt.where(model.status == status)
    stmt = stmt.order_by(model.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def _ensure_resume_version_owned(
    db: AsyncSession, user_id: str, resume_version_id: str | None
) -> None:
    if not resume_version_id:
        return
    result = await db.execute(
        select(ResumeVersion).where(
            ResumeVersion.id == resume_version_id,
            ResumeVersion.user_id == user_id,
            ResumeVersion.deleted_at.is_(None),
        )
    )
    if result.scalar_one_or_none() is None:
        raise WorkflowNotFound("resume version not found")


async def _ensure_application_owned(
    db: AsyncSession, user_id: str, application_id: str | None
) -> None:
    if not application_id:
        return
    await _get_owned(db, ApplicationRecord, user_id, application_id)


async def _create_record(
    db: AsyncSession,
    model: type[WorkflowRecord],
    user_id: str,
    payload: dict[str, Any],
    request_id: str | None = None,
) -> WorkflowRecord:
    item = model(user_id=user_id, **payload)
    db.add(item)
    await db.flush()
    await log_action(
        db,
        user_id=user_id,
        action="create",
        resource_type=model.__tablename__,
        resource_id=item.id,
        request_id=request_id,
        metadata={"fields": sorted(payload.keys())},
    )
    await db.commit()
    await db.refresh(item)
    return item


async def _update_record(
    db: AsyncSession,
    model: type[WorkflowRecord],
    user_id: str,
    item_id: str,
    payload: dict[str, Any],
    request_id: str | None = None,
) -> WorkflowRecord:
    item = await _get_owned(db, model, user_id, item_id)
    for key, value in payload.items():
        setattr(item, key, value)
    await log_action(
        db,
        user_id=user_id,
        action="update",
        resource_type=model.__tablename__,
        resource_id=item_id,
        request_id=request_id,
        metadata={"fields": sorted(payload.keys())},
    )
    await db.commit()
    await db.refresh(item)
    return item


async def _soft_delete(
    db: AsyncSession,
    model: type[WorkflowRecord],
    user_id: str,
    item_id: str,
    request_id: str | None = None,
) -> None:
    item = await _get_owned(db, model, user_id, item_id)
    item.deleted_at = datetime.now(timezone.utc)
    await log_action(
        db,
        user_id=user_id,
        action="delete",
        resource_type=model.__tablename__,
        resource_id=item_id,
        request_id=request_id,
    )
    await db.commit()


async def list_runway_snapshots(
    db: AsyncSession, user_id: str
) -> list[RunwaySnapshot]:
    return await _list_owned(db, RunwaySnapshot, user_id)


async def create_runway_snapshot(
    db: AsyncSession, user_id: str, payload: dict[str, Any], request_id: str | None = None
) -> RunwaySnapshot:
    return await _create_record(db, RunwaySnapshot, user_id, payload, request_id)


async def update_runway_snapshot(
    db: AsyncSession,
    user_id: str,
    snapshot_id: str,
    payload: dict[str, Any],
    request_id: str | None = None,
) -> RunwaySnapshot:
    return await _update_record(
        db, RunwaySnapshot, user_id, snapshot_id, payload, request_id
    )


async def delete_runway_snapshot(
    db: AsyncSession, user_id: str, snapshot_id: str, request_id: str | None = None
) -> None:
    await _soft_delete(db, RunwaySnapshot, user_id, snapshot_id, request_id)


async def list_applications(
    db: AsyncSession, user_id: str, status: str | None = None
) -> list[ApplicationRecord]:
    return await _list_owned(db, ApplicationRecord, user_id, status=status)


async def create_application(
    db: AsyncSession, user_id: str, payload: dict[str, Any], request_id: str | None = None
) -> ApplicationRecord:
    await _ensure_resume_version_owned(db, user_id, payload.get("resume_version_id"))
    return await _create_record(db, ApplicationRecord, user_id, payload, request_id)


async def update_application(
    db: AsyncSession,
    user_id: str,
    application_id: str,
    payload: dict[str, Any],
    request_id: str | None = None,
) -> ApplicationRecord:
    if "resume_version_id" in payload:
        await _ensure_resume_version_owned(db, user_id, payload.get("resume_version_id"))
    return await _update_record(
        db, ApplicationRecord, user_id, application_id, payload, request_id
    )


async def delete_application(
    db: AsyncSession, user_id: str, application_id: str, request_id: str | None = None
) -> None:
    await _soft_delete(db, ApplicationRecord, user_id, application_id, request_id)


async def list_proof_assets(
    db: AsyncSession, user_id: str, status: str | None = None
) -> list[ProofAsset]:
    return await _list_owned(db, ProofAsset, user_id, status=status)


async def create_proof_asset(
    db: AsyncSession, user_id: str, payload: dict[str, Any], request_id: str | None = None
) -> ProofAsset:
    await _ensure_application_owned(db, user_id, payload.get("linked_application_id"))
    return await _create_record(db, ProofAsset, user_id, payload, request_id)


async def update_proof_asset(
    db: AsyncSession,
    user_id: str,
    asset_id: str,
    payload: dict[str, Any],
    request_id: str | None = None,
) -> ProofAsset:
    if "linked_application_id" in payload:
        await _ensure_application_owned(db, user_id, payload.get("linked_application_id"))
    return await _update_record(db, ProofAsset, user_id, asset_id, payload, request_id)


async def delete_proof_asset(
    db: AsyncSession, user_id: str, asset_id: str, request_id: str | None = None
) -> None:
    await _soft_delete(db, ProofAsset, user_id, asset_id, request_id)


async def list_interview_sessions(
    db: AsyncSession, user_id: str, status: str | None = None
) -> list[InterviewSession]:
    return await _list_owned(db, InterviewSession, user_id, status=status)


async def create_interview_session(
    db: AsyncSession, user_id: str, payload: dict[str, Any], request_id: str | None = None
) -> InterviewSession:
    await _ensure_application_owned(db, user_id, payload.get("linked_application_id"))
    return await _create_record(db, InterviewSession, user_id, payload, request_id)


async def update_interview_session(
    db: AsyncSession,
    user_id: str,
    session_id: str,
    payload: dict[str, Any],
    request_id: str | None = None,
) -> InterviewSession:
    if "linked_application_id" in payload:
        await _ensure_application_owned(db, user_id, payload.get("linked_application_id"))
    return await _update_record(
        db, InterviewSession, user_id, session_id, payload, request_id
    )


async def delete_interview_session(
    db: AsyncSession, user_id: str, session_id: str, request_id: str | None = None
) -> None:
    await _soft_delete(db, InterviewSession, user_id, session_id, request_id)
