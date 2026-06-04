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
    local_available = False
    if settings.AI_PROVIDER == "ollama":
        try:
            h = await gateway.local_health()
            local_available = bool(h.get("local") and not h.get("error"))
        except Exception:
            local_available = False
    return {
        "provider": settings.AI_PROVIDER,
        "chat_model": settings.AI_CHAT_MODEL,
        "embedding_model": settings.AI_EMBEDDING_MODEL,
        "external_enabled": settings.ENABLE_EXTERNAL_AI,
        "local_available": local_available,
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


@router.get("/test-conn")
async def test_local_conn(request: Request):
    """Dedicated local connection test (ollama /api/tags + model presence + optional smoke).
    Use this for health dashboards and startup validation. Local-only path.
    """
    rid = getattr(request.state, "request_id", None)
    try:
        h = await gateway.local_health(request_id=rid)
        ok = bool(h.get("local") and not h.get("error"))
        sample = None
        if ok and h.get("model_present"):
            try:
                chat = await gateway.chat(
                    [{"role": "user", "content": "OK"}],
                    max_tokens=2,
                    request_id=rid,
                )
                sample = chat.get("content", "")[:30]
            except Exception as ch_e:
                sample = f"chat-err:{str(ch_e)[:60]}"
        return {
            "ok": ok,
            "provider": settings.AI_PROVIDER,
            "health": h,
            "sample": sample,
            "request_id": rid,
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "request_id": rid}
