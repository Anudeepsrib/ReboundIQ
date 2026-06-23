from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.profile import UserProfile

AI_PREF_KEY = "ai_settings"


def default_ai_preferences() -> dict[str, str]:
    return {
        "provider": "ollama",
        "chat_model": settings.AI_CHAT_MODEL,
        "embedding_model": settings.AI_EMBEDDING_MODEL,
        "base_url": settings.AI_BASE_URL,
    }


def _preferences_dict(profile: UserProfile | None) -> dict[str, Any]:
    value = getattr(profile, "preferences_json", None) or {}
    return value if isinstance(value, dict) else {}


async def get_or_create_profile(db: AsyncSession, user_id: str) -> UserProfile:
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    profile = result.scalar_one_or_none()
    if profile:
        return profile
    profile = UserProfile(user_id=user_id)
    db.add(profile)
    await db.flush()
    return profile


async def get_ai_preferences(
    db: AsyncSession | None, user_id: str | None
) -> dict[str, str]:
    prefs = default_ai_preferences()
    if not db or not user_id:
        return prefs
    profile = await get_or_create_profile(db, user_id)
    profile_prefs = _preferences_dict(profile).get(AI_PREF_KEY)
    if isinstance(profile_prefs, dict):
        for key in ("provider", "chat_model", "embedding_model", "base_url"):
            value = profile_prefs.get(key)
            if isinstance(value, str) and value.strip():
                prefs[key] = value.strip()
    prefs["provider"] = "ollama"
    return prefs


async def save_ai_preferences(
    db: AsyncSession,
    user_id: str,
    *,
    chat_model: str,
    embedding_model: str | None,
    base_url: str | None,
) -> dict[str, str]:
    profile = await get_or_create_profile(db, user_id)
    preferences = _preferences_dict(profile)
    next_prefs = {
        "provider": "ollama",
        "chat_model": chat_model.strip(),
        "embedding_model": (embedding_model or settings.AI_EMBEDDING_MODEL).strip(),
        "base_url": (base_url or settings.AI_BASE_URL).strip().rstrip("/"),
    }
    preferences[AI_PREF_KEY] = next_prefs
    profile.preferences_json = preferences
    await db.flush()
    return next_prefs
