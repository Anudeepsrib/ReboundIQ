from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import (
    decode_token,
    revoke_token,
    logout_user as security_logout,
)
from app.core.config import settings
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    RefreshRequest,
    UserMeResponse,
)
from app.services.auth import (
    create_user_with_profile,
    authenticate_user,
    issue_tokens_for_user,
    get_me,
)
from app.core.logging import logger
from app.core.security import (
    get_current_user as _get_current_user,
)  # re-export for other endpoints; noqa E402 not needed when at top

router = APIRouter()


def _cookie_secure() -> bool:
    return settings.ENV == "production"


def _set_auth_cookies(
    response: Response, access_token: str, refresh_token: str | None
) -> None:
    response.set_cookie(
        "access_token",
        access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=_cookie_secure(),
        samesite="lax",
        path="/",
    )
    if refresh_token:
        response.set_cookie(
            "refresh_token",
            refresh_token,
            max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            httponly=True,
            secure=_cookie_secure(),
            samesite="lax",
            path="/",
        )


def _clear_auth_cookies(response: Response) -> None:
    for name in ("access_token", "refresh_token"):
        response.delete_cookie(name, path="/", samesite="lax", secure=_cookie_secure())


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(
    req: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Register new user + default profile (consents false). Returns tokens for convenience."""
    user = await create_user_with_profile(db, req.email, req.password, req.full_name)
    access, refresh, user_out = await issue_tokens_for_user(db, user)
    _set_auth_cookies(response, access, refresh)
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "user": user_out,
    }


@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    user = await authenticate_user(db, req.email, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    access, refresh, user_out = await issue_tokens_for_user(db, user)
    _set_auth_cookies(response, access, refresh)
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
        "user": user_out,
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    req: RefreshRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Validate refresh token (body), issue new short-lived access. Optional: rotate."""
    try:
        payload = await decode_token(req.refresh_token)
    except HTTPException:
        raise
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not a refresh token"
        )
    user_id = payload["id"]
    user = await get_user_by_id_for_refresh(db, user_id)  # helper local
    if not user:
        raise HTTPException(401, "User inactive or not found")

    # Issue fresh access with current consents snapshot (no auto blacklist old access here)
    access, refresh_token, user_out = await issue_tokens_for_user(db, user)
    if payload.get("jti"):
        await revoke_token(
            payload["jti"],
            "refresh",
            settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        )
    _set_auth_cookies(response, access, refresh_token)
    return {
        "access_token": access,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user_out,
    }


# Local shim to avoid circular in this file (import inside func ok but for clarity)
async def get_user_by_id_for_refresh(db: AsyncSession, user_id: str):
    from app.models import User
    from sqlalchemy import select

    result = await db.execute(select(User).where(User.id == user_id))
    u = result.scalar_one_or_none()
    if u and getattr(u, "is_active", True):
        return u
    return None


@router.get("/me", response_model=UserMeResponse)
async def me(
    current_user: dict = Depends(_get_current_user), db: AsyncSession = Depends(get_db)
):
    """Return authenticated user + consent snapshot from profile (authoritative)."""
    user_id = current_user["id"]
    data = await get_me(db, user_id)
    return data


@router.post("/logout")
async def logout(
    response: Response,
    current_user: dict = Depends(_get_current_user),
    db: AsyncSession = Depends(get_db),  # not strictly needed but for future audit
):
    """Revoke current access (and optionally refresh if client sends). Blacklists via redis."""
    jti = current_user.get("jti")
    ttype = current_user.get("token_type", "access")
    if jti:
        # Short TTL sufficient for access (15m+), for refresh use longer if we had the jti
        ttl = 60 * 20 if ttype == "access" else 60 * 60 * 24 * 8
        await revoke_token(jti, ttype, ttl)
    await security_logout(current_user)
    _clear_auth_cookies(response)
    logger.info("auth.logged_out", extra={"user_id": current_user.get("id")})
    return {"ok": True, "message": "Logged out; token revoked"}


# For convenience, also support direct import of dep from endpoints.auth in other modules
get_current_user = _get_current_user
