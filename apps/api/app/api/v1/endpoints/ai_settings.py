from fastapi import APIRouter, Request
from pydantic import BaseModel
from app.core.config import settings
from app.ai.gateway import gateway

router = APIRouter()


class ConsentRequest(BaseModel):
    enable_external: bool
    consent_text: str  # user must acknowledge disclaimer


class ProviderStatus(BaseModel):
    provider: str
    chat_model: str
    embedding_model: str
    external_enabled: bool
    local_available: bool
    redaction_enabled: bool


@router.get("/status", response_model=ProviderStatus)
async def status():
    return {
        "provider": settings.AI_PROVIDER,
        "chat_model": settings.AI_CHAT_MODEL,
        "embedding_model": settings.AI_EMBEDDING_MODEL,
        "external_enabled": settings.ENABLE_EXTERNAL_AI,
        "local_available": True,  # would ping ollama /api/tags
        "redaction_enabled": True,
    }


@router.post("/consent/external-ai")
async def consent_external(req: ConsentRequest):
    if not req.consent_text or "I understand" not in req.consent_text:
        return {"ok": False, "error": "Must acknowledge disclaimer"}
    # In real: record in consent_records table for user, update session flag
    # For now just allow toggle in this process (not persisted)
    settings.ENABLE_EXTERNAL_AI = req.enable_external
    return {
        "ok": True,
        "external_now": settings.ENABLE_EXTERNAL_AI,
        "warning": "External calls will be redacted + audited. This is not stored persistently in demo slice.",
    }


@router.post("/test")
async def test_connection(request: Request):
    rid = getattr(request.state, "request_id", None)
    try:
        res = await gateway.chat(
            [{"role": "user", "content": "Reply with OK only."}],
            max_tokens=5,
            request_id=rid,
        )
        return {
            "ok": True,
            "provider": settings.AI_PROVIDER,
            "sample": res["content"][:50],
            "request_id": rid,
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "request_id": rid}
