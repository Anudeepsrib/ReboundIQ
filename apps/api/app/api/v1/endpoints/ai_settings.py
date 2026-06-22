from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.security import get_current_user
from app.db.session import get_db
from app.ai.gateway import gateway
from app.ai.memory import (
    memory_provider,
)  # PR-6: basic retain/recall wired for RAG/services
from app.models.consent_records import ConsentRecord
from app.models.profile import UserProfile
from app.services.audit import log_action

router = APIRouter()


class ConsentRequest(BaseModel):
    enable_external: bool
    consent_text: str  # user must acknowledge disclaimer


class ProviderStatus(BaseModel):
    provider: str
    chat_model: str
    embedding_model: str
    local_base_url: str
    external_enabled: bool
    local_available: bool
    local_models: List[str]
    chat_model_present: bool
    embedding_model_present: bool
    redaction_enabled: bool
    memory_provider: str  # PR-6: "postgres+pgvector" | "inmem-fallback"


class LocalModelRequest(BaseModel):
    chat_model: str = Field(..., min_length=1, max_length=120)
    embedding_model: Optional[str] = Field(default=None, max_length=120)
    base_url: Optional[str] = Field(default=None, max_length=240)


class LocalModelResponse(BaseModel):
    ok: bool
    provider: str
    chat_model: str
    embedding_model: str
    local_base_url: str
    local_models: List[str]
    chat_model_present: bool
    embedding_model_present: bool
    warning: str


SUGGESTED_LOCAL_MODELS = [
    "llama3.2:1b",
    "llama3.2:3b",
    "gemma3:4b",
    "gemma2:9b",
    "mistral:7b",
    "qwen2.5:7b",
    "phi3:mini",
]


@router.get("/status", response_model=ProviderStatus)
async def status():
    local_available = False
    local_models: List[str] = []
    chat_model_present = False
    embedding_model_present = False
    if settings.AI_PROVIDER == "ollama":
        try:
            h = await gateway.local_health()
            local_available = bool(h.get("local") and not h.get("error"))
            local_models = h.get("models", []) or []
            chat_model_present = settings.AI_CHAT_MODEL in local_models
            embedding_model_present = settings.AI_EMBEDDING_MODEL in local_models
        except Exception:
            local_available = False
    mem_type = (
        "postgres+pgvector"
        if "Postgres" in type(memory_provider).__name__
        else "inmem-fallback"
    )
    return {
        "provider": settings.AI_PROVIDER,
        "chat_model": settings.AI_CHAT_MODEL,
        "embedding_model": settings.AI_EMBEDDING_MODEL,
        "local_base_url": settings.AI_BASE_URL,
        "external_enabled": settings.ENABLE_EXTERNAL_AI,
        "local_available": local_available,
        "local_models": local_models,
        "chat_model_present": chat_model_present,
        "embedding_model_present": embedding_model_present,
        "redaction_enabled": True,
        "memory_provider": mem_type,
    }


@router.get("/local-models")
async def local_models(request: Request):
    rid = getattr(request.state, "request_id", None)
    health = await gateway.local_health(request_id=rid)
    models = health.get("models", []) if health.get("local") and not health.get("error") else []
    return {
        "provider": "ollama",
        "base_url": settings.AI_BASE_URL,
        "chat_model": settings.AI_CHAT_MODEL,
        "embedding_model": settings.AI_EMBEDDING_MODEL,
        "installed_models": models,
        "suggested_models": SUGGESTED_LOCAL_MODELS,
        "request_id": rid,
        "warning": "Only local Ollama models are listed here. Pull models outside the app, then refresh.",
        "health": health,
    }


@router.post("/local-models/select", response_model=LocalModelResponse)
async def select_local_model(req: LocalModelRequest, request: Request):
    rid = getattr(request.state, "request_id", None)
    configured = gateway.configure_local_models(
        chat_model=req.chat_model,
        embedding_model=req.embedding_model or settings.AI_EMBEDDING_MODEL,
        base_url=req.base_url or settings.AI_BASE_URL,
    )
    health = await gateway.local_health(request_id=rid)
    local_models = health.get("models", []) if health.get("local") and not health.get("error") else []
    chat_model_present = configured["chat_model"] in local_models
    embedding_model_present = configured["embedding_model"] in local_models
    missing_warning = (
        "Selected model is not currently reported by Ollama. Pull it locally, then test the connection."
        if not chat_model_present
        else "Runtime local model selection updated for this API process. Persist to .env or user settings for production."
    )
    return {
        "ok": True,
        "provider": configured["provider"],
        "chat_model": configured["chat_model"],
        "embedding_model": configured["embedding_model"],
        "local_base_url": configured["base_url"],
        "local_models": local_models,
        "chat_model_present": chat_model_present,
        "embedding_model_present": embedding_model_present,
        "warning": missing_warning,
    }


@router.post("/consent/external-ai")
async def consent_external(
    req: ConsentRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if req.enable_external and (
        not req.consent_text or "I understand" not in req.consent_text
    ):
        raise HTTPException(status_code=400, detail="Must acknowledge disclaimer")

    user_id = current_user["id"]
    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = profile_result.scalar_one_or_none()
    if not profile:
        profile = UserProfile(user_id=user_id)
        db.add(profile)
        await db.flush()

    profile.consent_external_ai = req.enable_external
    consent = ConsentRecord(
        user_id=user_id,
        consent_type="external_ai",
        granted=req.enable_external,
        consent_text=req.consent_text,
        revoked_at=None if req.enable_external else datetime.now(timezone.utc),
    )
    db.add(consent)
    await log_action(
        db,
        user_id=user_id,
        action="consent_granted" if req.enable_external else "consent_revoked",
        resource_type="external_ai",
        resource_id=consent.id,
        request_id=getattr(request.state, "request_id", None),
        metadata={"enabled": req.enable_external},
    )

    settings.ENABLE_EXTERNAL_AI = req.enable_external
    gateway.enable_external = req.enable_external
    await db.commit()
    await db.refresh(consent)

    return {
        "ok": True,
        "external_now": settings.ENABLE_EXTERNAL_AI,
        "consent_id": consent.id,
        "warning": "External calls are redacted and audited. Refresh your session token to embed the latest consent snapshot.",
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
        # PR-6: also smoke memory retain/recall (uses inmem or pg; always user-isolated)
        mem_id = await memory_provider.retain(
            user_id="test-conn-user",
            content="Test memory for provider config: user prefers concise replies.",
            category="preference",
            sensitivity="low",
        )
        recalled = await memory_provider.recall(
            user_id="test-conn-user",
            query="prefers concise",
            top_k=1,
            sensitivity_max="low",
        )
        mem_ok = len(recalled) > 0 and "concise" in recalled[0]["content"].lower()
        return {
            "ok": True,
            "provider": settings.AI_PROVIDER,
            "chat_model": settings.AI_CHAT_MODEL,
            "sample": res["content"][:50],
            "request_id": rid,
            "memory_smoke": {
                "retained": bool(mem_id),
                "recalled": mem_ok,
                "count": len(recalled),
            },
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
            "chat_model": settings.AI_CHAT_MODEL,
            "health": h,
            "sample": sample,
            "request_id": rid,
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "request_id": rid}
