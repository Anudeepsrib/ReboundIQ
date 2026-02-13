from fastapi import APIRouter, Depends, HTTPException
from app.schemas.job import RecruiterMessageRequest, JobResponse
from app.services.orchestrator import orchestrator
from app.core.security import get_api_key

router = APIRouter()

@router.post("/analyze_message", response_model=JobResponse)
async def analyze_message(
    request: RecruiterMessageRequest,
    api_key: str = Depends(get_api_key)
):
    """
    Analyzes a recruiter's message, performs company research, and suggests a reply.
    """
    try:
        response = await orchestrator.process_recruiter_message(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
