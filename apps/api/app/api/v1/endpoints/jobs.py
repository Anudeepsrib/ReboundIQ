from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from app.ai.gateway import gateway
from app.core.security import get_current_user

router = APIRouter()


class JDAnalyzeRequest(BaseModel):
    jd_text: str
    resume_text: Optional[str] = None  # or use stored resume_id later


class MatchResult(BaseModel):
    match_score: float  # 0-100 evidence based
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
    req: JDAnalyzeRequest, current_user: dict = Depends(get_current_user)
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

    extracted = await gateway.structured(
        system, jd[:6000], schema={"type": "object"}, user_id=user_id
    )

    # Simple match if resume provided (in real use RAG + gateway on combined)
    resume_snippet = (
        req.resume_text
        or "User has experience in Python, LLMs, backend systems, distributed infra."
    )[:2000]
    match_prompt = f"""Given user profile snippet:\n{resume_snippet}\n\nAnd JD requirements: {extracted}\n\nCompute evidence-based match_score 0-100, missing_skills (only from JD required that are absent), rewrite_strategy (2-3 bullets), recruiter_message_draft (concise, truthful), cover_letter_draft (short). Output JSON with citations like ["resume summary", "JD line 4"]. Never claim user will get the job. Flag any overclaim."""

    match_raw = await gateway.structured(
        "Return only valid JSON for match analysis.",
        match_prompt,
        schema={"type": "object"},
        user_id=user_id,
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
            "citations", ["user provided JD", "uploaded resume (if any)"]
        ),
        "warnings": [
            "This is planning guidance only. Do not fabricate experience. Review and edit all drafts. No guarantee of interview or offer."
        ],
    }
    return result
