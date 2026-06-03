from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from pydantic import BaseModel
from typing import List, Optional
import uuid
import os
from datetime import datetime
from app.core.config import settings
from app.ai.gateway import gateway
from app.services.storage import LocalStorage  # simple impl below
import pdfplumber
from io import BytesIO

router = APIRouter()

storage = LocalStorage(root=settings.STORAGE_LOCAL_ROOT)

class ResumeOut(BaseModel):
    id: str
    original_filename: str
    created_at: datetime
    has_parsed: bool

class ResumeVersionOut(BaseModel):
    id: str
    version_name: str
    target_role: Optional[str]
    content_json: dict
    ats_score: Optional[float]
    created_at: datetime

class JDMatchRequest(BaseModel):
    jd_text: str
    resume_version_id: Optional[str] = None  # or latest

@router.post("/upload", response_model=ResumeOut)
async def upload_resume(file: UploadFile = File(...), user_id: str = "demo-user"):  # TODO: real auth
    if not file.filename:
        raise HTTPException(400, "No file")
    ext = file.filename.lower().split(".")[-1]
    if ext not in ("pdf", "docx", "txt"):
        raise HTTPException(400, "Supported: pdf, docx, txt")

    content = await file.read()
    key = f"users/{user_id}/resumes/{uuid.uuid4()}.{ext}"
    await storage.save(key, content, file.content_type or "application/octet-stream")

    # Minimal parse
    text = ""
    parsed = {}
    if ext == "pdf":
        try:
            with pdfplumber.open(BytesIO(content)) as pdf:
                text = "\n".join([p.extract_text() or "" for p in pdf.pages])
        except Exception:
            text = content.decode("utf-8", errors="ignore")
    elif ext == "txt":
        text = content.decode("utf-8", errors="ignore")
    else:
        text = "[DOCX parsed text would go here - stub for slice]"

    # Structured parse via gateway (local model)
    try:
        system = "Extract structured resume info as JSON: name, contact, summary, skills (list), experience (list of {company, title, bullets}), education, certifications, metrics. Be faithful to text. If unclear use null."
        parsed = await gateway.structured(system, text[:8000], schema={"type": "object"}, user_id=user_id)
    except Exception as e:
        parsed = {"error": str(e), "raw_text_excerpt": text[:500]}

    # In real: save to DB Resume + user
    rid = str(uuid.uuid4())
    # For demo in-memory stub (replace with DB in full)
    # Here we just return; persistence in later slice + Alembic applied

    return {
        "id": rid,
        "original_filename": file.filename,
        "created_at": datetime.utcnow(),
        "has_parsed": bool(parsed and not parsed.get("error"))
    }

@router.post("/{resume_id}/versions", response_model=ResumeVersionOut)
async def create_version(resume_id: str, target_role: str = Form(...), user_id: str = "demo-user"):
    # In full: load resume parsed, use gateway.structured to rewrite bullets for role, compute ATS heuristic
    # Stub: return example version
    version = {
        "id": str(uuid.uuid4()),
        "version_name": f"{target_role} Tailored",
        "target_role": target_role,
        "content_json": {
            "summary": f"Experienced professional targeting {target_role} roles. (Grounded in your uploaded resume.)",
            "bullets": [
                "Led X initiatives resulting in Y% improvement (from your experience).",
                "Built Z system using A, B, C stack."
            ],
            "skills": ["Python", "LLMs", "Distributed Systems"]  # would come from parsed + JD
        },
        "ats_score": 78.5,
        "created_at": datetime.utcnow()
    }
    return version

@router.get("/", response_model=List[ResumeOut])
async def list_resumes(user_id: str = "demo-user"):
    # Stub
    return []
