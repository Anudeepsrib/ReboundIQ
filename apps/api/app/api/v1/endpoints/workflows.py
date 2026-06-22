from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import get_current_user
from app.schemas.workflows import (
    ApplicationCreate,
    ApplicationOut,
    ApplicationUpdate,
    DeleteOut,
    InterviewSessionCreate,
    InterviewSessionOut,
    InterviewSessionUpdate,
    ProofAssetCreate,
    ProofAssetOut,
    ProofAssetUpdate,
    RunwaySnapshotCreate,
    RunwaySnapshotOut,
    RunwaySnapshotUpdate,
)
from app.services import workflows
from app.services.workflows import WorkflowNotFound

router = APIRouter()


def _not_found(exc: WorkflowNotFound) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/runway/snapshots", response_model=list[RunwaySnapshotOut])
async def list_runway_snapshots(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await workflows.list_runway_snapshots(db, current_user["id"])


@router.post(
    "/runway/snapshots",
    response_model=RunwaySnapshotOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_runway_snapshot(
    payload: RunwaySnapshotCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await workflows.create_runway_snapshot(
        db,
        current_user["id"],
        payload.model_dump(),
        getattr(request.state, "request_id", None),
    )


@router.patch("/runway/snapshots/{snapshot_id}", response_model=RunwaySnapshotOut)
async def update_runway_snapshot(
    snapshot_id: str,
    payload: RunwaySnapshotUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        return await workflows.update_runway_snapshot(
            db,
            current_user["id"],
            snapshot_id,
            payload.model_dump(exclude_unset=True),
            getattr(request.state, "request_id", None),
        )
    except WorkflowNotFound as exc:
        raise _not_found(exc)


@router.delete("/runway/snapshots/{snapshot_id}", response_model=DeleteOut)
async def delete_runway_snapshot(
    snapshot_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        await workflows.delete_runway_snapshot(
            db,
            current_user["id"],
            snapshot_id,
            getattr(request.state, "request_id", None),
        )
    except WorkflowNotFound as exc:
        raise _not_found(exc)
    return DeleteOut(id=snapshot_id)


@router.get("/applications", response_model=list[ApplicationOut])
async def list_applications(
    status_filter: str | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await workflows.list_applications(
        db, current_user["id"], status=status_filter
    )


@router.post(
    "/applications", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED
)
async def create_application(
    payload: ApplicationCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        return await workflows.create_application(
            db,
            current_user["id"],
            payload.model_dump(),
            getattr(request.state, "request_id", None),
        )
    except WorkflowNotFound as exc:
        raise _not_found(exc)


@router.patch("/applications/{application_id}", response_model=ApplicationOut)
async def update_application(
    application_id: str,
    payload: ApplicationUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        return await workflows.update_application(
            db,
            current_user["id"],
            application_id,
            payload.model_dump(exclude_unset=True),
            getattr(request.state, "request_id", None),
        )
    except WorkflowNotFound as exc:
        raise _not_found(exc)


@router.delete("/applications/{application_id}", response_model=DeleteOut)
async def delete_application(
    application_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        await workflows.delete_application(
            db,
            current_user["id"],
            application_id,
            getattr(request.state, "request_id", None),
        )
    except WorkflowNotFound as exc:
        raise _not_found(exc)
    return DeleteOut(id=application_id)


@router.get("/proof/assets", response_model=list[ProofAssetOut])
async def list_proof_assets(
    status_filter: str | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await workflows.list_proof_assets(
        db, current_user["id"], status=status_filter
    )


@router.post(
    "/proof/assets", response_model=ProofAssetOut, status_code=status.HTTP_201_CREATED
)
async def create_proof_asset(
    payload: ProofAssetCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        return await workflows.create_proof_asset(
            db,
            current_user["id"],
            payload.model_dump(),
            getattr(request.state, "request_id", None),
        )
    except WorkflowNotFound as exc:
        raise _not_found(exc)


@router.patch("/proof/assets/{asset_id}", response_model=ProofAssetOut)
async def update_proof_asset(
    asset_id: str,
    payload: ProofAssetUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        return await workflows.update_proof_asset(
            db,
            current_user["id"],
            asset_id,
            payload.model_dump(exclude_unset=True),
            getattr(request.state, "request_id", None),
        )
    except WorkflowNotFound as exc:
        raise _not_found(exc)


@router.delete("/proof/assets/{asset_id}", response_model=DeleteOut)
async def delete_proof_asset(
    asset_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        await workflows.delete_proof_asset(
            db,
            current_user["id"],
            asset_id,
            getattr(request.state, "request_id", None),
        )
    except WorkflowNotFound as exc:
        raise _not_found(exc)
    return DeleteOut(id=asset_id)


@router.get("/interviews/sessions", response_model=list[InterviewSessionOut])
async def list_interview_sessions(
    status_filter: str | None = Query(default=None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await workflows.list_interview_sessions(
        db, current_user["id"], status=status_filter
    )


@router.post(
    "/interviews/sessions",
    response_model=InterviewSessionOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_interview_session(
    payload: InterviewSessionCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        return await workflows.create_interview_session(
            db,
            current_user["id"],
            payload.model_dump(),
            getattr(request.state, "request_id", None),
        )
    except WorkflowNotFound as exc:
        raise _not_found(exc)


@router.patch("/interviews/sessions/{session_id}", response_model=InterviewSessionOut)
async def update_interview_session(
    session_id: str,
    payload: InterviewSessionUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        return await workflows.update_interview_session(
            db,
            current_user["id"],
            session_id,
            payload.model_dump(exclude_unset=True),
            getattr(request.state, "request_id", None),
        )
    except WorkflowNotFound as exc:
        raise _not_found(exc)


@router.delete("/interviews/sessions/{session_id}", response_model=DeleteOut)
async def delete_interview_session(
    session_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    try:
        await workflows.delete_interview_session(
            db,
            current_user["id"],
            session_id,
            getattr(request.state, "request_id", None),
        )
    except WorkflowNotFound as exc:
        raise _not_found(exc)
    return DeleteOut(id=session_id)
