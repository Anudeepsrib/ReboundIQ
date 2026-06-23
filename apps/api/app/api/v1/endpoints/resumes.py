from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Request, Depends
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.resume import (
    upload_and_parse_resume,
    create_resume_version,
    list_user_resumes,
    list_user_resume_versions,
)
from app.core.security import get_current_user

router = APIRouter()


class ResumeOut(BaseModel):
    id: str
    original_filename: str
    created_at: datetime
    has_parsed: bool


class ResumeVersionOut(BaseModel):
    id: str
    resume_id: Optional[str] = None
    version_name: str
    target_role: Optional[str]
    content_json: dict
    source_inputs: Optional[dict] = None
    ats_score: Optional[float]
    created_at: datetime


class JDMatchRequest(BaseModel):
    jd_text: str
    resume_version_id: Optional[str] = None  # or latest


@router.post("/upload", response_model=ResumeOut)
async def upload_resume(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not file.filename:
        raise HTTPException(400, "No file")
    content = await file.read()
    rid = getattr(request.state, "request_id", None)
    try:
        data = await upload_and_parse_resume(
            db=db,
            file_bytes=content,
            filename=file.filename,
            user_id=current_user["id"],
            request_id=rid,
            content_type=file.content_type,
        )
        return {
            "id": data["id"],
            "original_filename": data["original_filename"],
            "created_at": data.get("created_at", datetime.utcnow()),
            "has_parsed": data["has_parsed"],
        }
    except ValueError as ve:
        raise HTTPException(400, str(ve))
    except Exception as e:
        # Do not leak internals; logged inside service via request_id
        raise HTTPException(400, f"resume upload failed: {type(e).__name__}")


@router.post("/{resume_id}/versions", response_model=ResumeVersionOut)
async def create_version(
    resume_id: str,
    request: Request,
    target_role: str = Form(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    rid = getattr(request.state, "request_id", None)
    try:
        v = await create_resume_version(
            db=db,
            resume_id=resume_id,
            target_role=target_role,
            user_id=current_user["id"],
            request_id=rid,
        )
        return v
    except ValueError as ve:
        raise HTTPException(404, str(ve))
    except Exception as e:
        raise HTTPException(400, f"version create failed: {type(e).__name__}")


@router.get("/", response_model=List[ResumeOut])
async def list_resumes(
    db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    items = await list_user_resumes(db, current_user["id"])
    return items


@router.get("/versions", response_model=List[ResumeVersionOut])
async def list_versions(
    db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)
):
    return await list_user_resume_versions(db, current_user["id"])


@router.get("/{resume_id}/versions", response_model=List[ResumeVersionOut])
async def list_versions_for_resume(
    resume_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return await list_user_resume_versions(db, current_user["id"], resume_id=resume_id)
