"""
Auth service: register, login, refresh, me.
All queries filter by user (for login by email unique; for others by id from token).
Uses owner checks via security helper where resource access.
Never auto anything; explicit.
"""

from typing import Optional, Tuple, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models import User, UserProfile
from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    check_owner,
)
from app.core.logging import logger


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Parameterized query."""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_profile(db: AsyncSession, user_id: str) -> Optional[UserProfile]:
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))
    return result.scalar_one_or_none()


async def create_user_with_profile(
    db: AsyncSession, email: str, password: str, full_name: Optional[str] = None
) -> User:
    existing = await get_user_by_email(db, email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )
    hashed = get_password_hash(password)
    user = User(
        email=email,
        hashed_password=hashed,
        full_name=full_name,
        is_active=True,
    )
    db.add(user)
    await db.flush()  # obtain id before profile

    profile = UserProfile(user_id=user.id)  # defaults: consents=false, role=user
    db.add(profile)
    await db.commit()
    await db.refresh(user)
    logger.info("auth.user_registered", extra={"user_id": user.id, "email": email})
    return user


async def authenticate_user(
    db: AsyncSession, email: str, password: str
) -> Optional[User]:
    user = await get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not getattr(user, "is_active", True):
        return None
    return user


def _build_token_claims(user: User, profile: Optional[UserProfile]) -> Dict[str, Any]:
    consents = {
        "external_ai": bool(getattr(profile, "consent_external_ai", False)),
        "memory_sensitive": bool(getattr(profile, "consent_memory_sensitive", False)),
        "visa_processing": bool(getattr(profile, "consent_visa_processing", False)),
    }
    role = getattr(profile, "role", "user") or "user"
    return {
        "email": user.email,
        "consents": consents,
        "role": role,
        "full_name": user.full_name,
    }


async def issue_tokens_for_user(
    db: AsyncSession, user: User
) -> Tuple[str, str, Dict[str, Any]]:
    """Create access (with consent snapshot) + refresh. Return for response."""
    profile = await get_user_profile(db, user.id)
    claims = _build_token_claims(user, profile)
    access_token = create_access_token(subject=user.id, extra_claims=claims)
    refresh_token = create_refresh_token(subject=user.id)
    user_out = {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": claims["role"],
        "consents": claims["consents"],
    }
    logger.info(
        "auth.tokens_issued",
        extra={"user_id": user.id, "has_refresh": True},
    )
    return access_token, refresh_token, user_out


async def refresh_access_token(
    db: AsyncSession, refresh_token: str
) -> Tuple[str, Dict[str, Any]]:
    """
    Decode/validate refresh (done in endpoint via get_current but type=refresh),
    issue fresh access with up-to-date consents snapshot.
    (Blacklist of old not auto here; endpoint can revoke on rotation if desired.)
    """
    # Note: actual JWT validation + blacklist + type check done in get_current_user dep (called with refresh)
    # Here we just re-fetch user and issue.
    # For minimal, the caller passes the validated user_id from dep.
    # We overload: this is called after dep validated the refresh token.
    # To get user, we need the sub; but since dep returns the dict, use that.
    # Signature kept for clarity; impl in endpoint for this slice.
    raise NotImplementedError("Use endpoint logic for refresh with dep")


async def get_me(db: AsyncSession, user_id: str) -> Dict[str, Any]:
    user = await get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    profile = await get_user_profile(db, user_id)
    consents = {
        "external_ai": bool(getattr(profile, "consent_external_ai", False)),
        "memory_sensitive": bool(getattr(profile, "consent_memory_sensitive", False)),
        "visa_processing": bool(getattr(profile, "consent_visa_processing", False)),
    }
    role = getattr(profile, "role", "user") or "user"
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": role,
        "consents": consents,
    }


# Helper usable by other services: ensure caller owns the resource
def ensure_owner(current_user: Dict[str, Any], owner_id: str) -> None:
    check_owner(current_user, owner_id)
