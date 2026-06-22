from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.ai.gateway import gateway
from app.core.security import get_current_user
from app.db.session import get_db
from app.models.resume import Resume, ResumeVersion

router = APIRouter()


class JDAnalyzeRequest(BaseModel):
    jd_text: str
    resume_text: Optional[str] = None
    resume_id: Optional[str] = None
    resume_version_id: Optional[str] = None


class MatchResult(BaseModel):
    match_score: float  # 0-100 evidence based
    ai_confidence: float  # 0-1 deterministic support score
    groundedness_score: float  # 0-1 citation/evidence support score
    quality: dict
    required_skills: List[str]
    missing_skills: List[str]
    responsibilities: List[str]
    seniority: str
    red_flags: List[str]
    sponsorship_clues: List[str]
    rewrite_strategy: str
    recruiter_message_draft: str
    cover_letter_draft: str
    citations: List[str]  # e.g. "resume chunk 3", "user profile"
    warnings: List[str]


@router.post("/analyze", response_model=MatchResult)
async def analyze_jd(
    req: JDAnalyzeRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["id"]
    # Isolation + audit: user_id from JWT used for all downstream (RAG later, logs)
    jd = req.jd_text.strip()
    if len(jd) < 50:
        raise HTTPException(400, "JD too short")

    system = """You are a precise career analyst. From the JD text, output STRICT JSON:
{
  "required_skills": string[],
  "preferred_skills": string[],
  "responsibilities": string[],
  "seniority": "Junior|Mid|Senior|Staff|Principal|Manager",
  "domain": string,
  "cloud_stack": string[],
  "ai_stack": string[],
  "frontend_backend_ratio": "heavy-frontend | balanced | heavy-backend",
  "sponsorship_clues": string[],
  "red_flags": string[],
  "interview_focus": string[]
}
Be evidence-based only from the provided text. No fabrication."""

    rid = getattr(request.state, "request_id", None)
    extracted = await gateway.structured(
        system, jd[:6000], schema={"type": "object"}, user_id=user_id, request_id=rid
    )

    resume_snippet, evidence_label = await _resolve_resume_evidence(
        db,
        user_id=user_id,
        resume_text=req.resume_text,
        resume_id=req.resume_id,
        resume_version_id=req.resume_version_id,
    )
    has_user_evidence = bool(resume_snippet.strip())
    if not has_user_evidence:
        required = extracted.get("required_skills", [])[:12]
        result = {
            "match_score": 0.0,
            "required_skills": required,
            "missing_skills": required,
            "responsibilities": extracted.get("responsibilities", [])[:8],
            "seniority": extracted.get("seniority", "Mid"),
            "red_flags": extracted.get("red_flags", []),
            "sponsorship_clues": extracted.get("sponsorship_clues", []),
            "rewrite_strategy": (
                "Upload or select resume evidence before generating a fit strategy. "
                "No personal match claims were made because no user evidence was supplied."
            ),
            "recruiter_message_draft": "",
            "cover_letter_draft": "",
            "citations": ["user provided JD"],
            "warnings": [
                "Resume evidence is missing. ReboundIQ will not infer your skills, employers, metrics, or titles."
            ],
        }
        result["quality"] = _quality_summary(result, resume_snippet=None)
        result["ai_confidence"] = result["quality"]["ai_confidence"]
        result["groundedness_score"] = result["quality"]["groundedness_score"]
        return result

    resume_snippet = resume_snippet[:3000]
    match_prompt = f"""Given user profile snippet:\n{resume_snippet}\n\nAnd JD requirements: {extracted}\n\nCompute evidence-based match_score 0-100, missing_skills (only from JD required that are absent), rewrite_strategy (2-3 bullets), recruiter_message_draft (concise, truthful), cover_letter_draft (short). Output JSON with citations like ["resume summary", "JD line 4"]. Never claim user will get the job. Flag any overclaim."""

    match_raw = await gateway.structured(
        "Return only valid JSON for match analysis.",
        match_prompt,
        schema={"type": "object"},
        user_id=user_id,
        request_id=rid,
    )

    # Merge + safe defaults + disclaimers
    result = {
        "match_score": float(match_raw.get("match_score", 62)),
        "required_skills": extracted.get("required_skills", [])[:12],
        "missing_skills": match_raw.get(
            "missing_skills", extracted.get("preferred_skills", [])[:5]
        ),
        "responsibilities": extracted.get("responsibilities", [])[:8],
        "seniority": extracted.get("seniority", "Mid"),
        "red_flags": extracted.get("red_flags", []),
        "sponsorship_clues": extracted.get("sponsorship_clues", []),
        "rewrite_strategy": match_raw.get(
            "rewrite_strategy",
            "Emphasize relevant backend + LLM experience from your actual projects. Quantify impact where you have evidence.",
        ),
        "recruiter_message_draft": match_raw.get(
            "recruiter_message_draft",
            "Hi, I saw your posting for the role. My background in [your real project] aligns with the distributed systems needs. Would value a conversation.",
        ),
        "cover_letter_draft": match_raw.get(
            "cover_letter_draft",
            "I am excited about the opportunity... (edit with your voice). This is a draft only.",
        ),
        "citations": match_raw.get(
            "citations", ["user provided JD", evidence_label]
        ),
        "warnings": [
            "This is planning guidance only. Do not fabricate experience. Review and edit all drafts. No guarantee of interview or offer."
        ],
    }
    result["quality"] = _quality_summary(result, resume_snippet=resume_snippet)
    result["ai_confidence"] = result["quality"]["ai_confidence"]
    result["groundedness_score"] = result["quality"]["groundedness_score"]
    return result


async def _resolve_resume_evidence(
    db: AsyncSession,
    *,
    user_id: str,
    resume_text: str | None,
    resume_id: str | None,
    resume_version_id: str | None,
) -> tuple[str, str]:
    if resume_version_id:
        result = await db.execute(
            select(ResumeVersion).where(
                ResumeVersion.id == resume_version_id,
                ResumeVersion.user_id == user_id,
            )
        )
        version = result.scalar_one_or_none()
        if not version:
            raise HTTPException(404, "Resume version not found")
        return (
            str(version.content_json or version.source_inputs or ""),
            f"resume version {version.id}",
        )
    if resume_id:
        result = await db.execute(
            select(Resume).where(Resume.id == resume_id, Resume.user_id == user_id)
        )
        resume = result.scalar_one_or_none()
        if not resume:
            raise HTTPException(404, "Resume not found")
        return (
            (resume.parsed_text or str(resume.parsed_json or "")).strip(),
            f"resume {resume.id}",
        )
    return ((resume_text or "").strip(), "provided resume excerpt")


def _quality_summary(result: dict, resume_snippet: Optional[str]) -> dict:
    citation_count = len(result.get("citations") or [])
    required_count = len(result.get("required_skills") or [])
    missing_count = len(result.get("missing_skills") or [])
    has_user_resume = bool(resume_snippet and resume_snippet.strip())

    groundedness = 0.35
    groundedness += min(0.35, citation_count * 0.08)
    if has_user_resume:
        groundedness += 0.15
    if required_count:
        groundedness += 0.08
    groundedness -= min(0.2, missing_count * 0.03)
    groundedness = max(0.05, min(0.95, round(groundedness, 2)))

    confidence = 0.35 + groundedness * 0.45
    if has_user_resume:
        confidence += 0.1
    confidence = max(0.05, min(0.9, round(confidence, 2)))
    return {
        "ai_confidence": confidence,
        "groundedness_score": groundedness,
        "citation_count": citation_count,
        "required_skill_count": required_count,
        "missing_skill_count": missing_count,
        "user_resume_supplied": has_user_resume,
        "scoring_note": (
            "Deterministic support score from citations, JD extraction, "
            "and whether user resume evidence was supplied."
        ),
    }
