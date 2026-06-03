"""
Security: JWT with python-jose + passlib, HTTPBearer, consent snapshot in token,
redis blacklist for logout/revoke, owner checks, get_current_user dep.
Follows: short-lived access + refresh, parameterized (via decode), user isolation via sub.
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
import redis.asyncio as aioredis

from app.core.config import settings
from app.core.logging import logger

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Use HTTPBearer (not OAuth2PasswordBearer for pure bearer tokens)
bearer_scheme = HTTPBearer(auto_error=True)

# Redis client for blacklist (module singleton for simplicity; injected in prod if needed)
_redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.REDIS_URL, decode_responses=True, encoding="utf-8"
        )
    return _redis_client


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def _create_token(
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    now = datetime.now(timezone.utc)
    expire = now + expires_delta
    jti = str(uuid.uuid4())
    to_encode: Dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": jti,
        "type": token_type,
    }
    if extra_claims:
        to_encode.update(extra_claims)
    encoded = jwt.encode(
        to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )
    return encoded


def create_access_token(
    subject: str, extra_claims: Optional[Dict[str, Any]] = None
) -> str:
    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _create_token(subject, "access", expires, extra_claims)


def create_refresh_token(subject: str) -> str:
    expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return _create_token(subject, "refresh", expires)


async def _is_blacklisted(jti: Optional[str], token_type: str) -> bool:
    if not jti:
        return False
    r = await get_redis()
    key = f"blacklist:{token_type}:{jti}"
    val = await r.get(key)
    return val is not None


async def revoke_token(jti: str, token_type: str, ttl_seconds: int) -> None:
    """Blacklist a token (used on logout/refresh rotation)."""
    r = await get_redis()
    key = f"blacklist:{token_type}:{jti}"
    await r.setex(key, ttl_seconds, "1")


async def decode_token(token: str) -> Dict[str, Any]:
    """Core decode + blacklist check. Used by dep and by refresh (body token)."""
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError:
        logger.warning("auth.jwt_decode_failed")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id: Optional[str] = payload.get("sub")
    token_type: str = payload.get("type", "access")
    jti: Optional[str] = payload.get("jti")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject"
        )

    if await _is_blacklisted(jti, token_type):
        logger.info("auth.token_blacklisted", extra={"user_id": user_id, "jti": jti})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked"
        )

    consents = payload.get("consents", {}) or {}
    role = payload.get("role", "user")
    email = payload.get("email")

    return {
        "id": user_id,
        "email": email,
        "consents": consents,
        "role": role,
        "token_type": token_type,
        "jti": jti,
    }


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> Dict[str, Any]:
    """
    FastAPI dependency. Decodes JWT (via decode_token), enforces not blacklisted.
    Returns normalized user dict. All data queries MUST filter by user['id'].
    """
    token = credentials.credentials
    return await decode_token(token)


def check_owner(current_user: Dict[str, Any], resource_owner_id: str) -> None:
    """Owner check helper. Use in all services/endpoints for row-level isolation enforcement."""
    if not resource_owner_id or current_user.get("id") != resource_owner_id:
        logger.warning(
            "auth.owner_check_failed",
            extra={
                "current_user_id": current_user.get("id"),
                "resource_owner_id": resource_owner_id,
            },
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: you do not own this resource",
        )


async def logout_user(user: Dict[str, Any], access_token: Optional[str] = None) -> None:
    """Blacklist current tokens (call from logout endpoint). Short TTLs."""
    # Blacklist access if present (use remaining exp if possible; simple: 15min + margin)
    if user.get("jti") and user.get("token_type") == "access":
        await revoke_token(user["jti"], "access", 60 * 20)
    # For refresh, caller should pass or we don't have it here; endpoint handles both
    # Also support explicit token if provided (e.g. the one used)
    logger.info("auth.logout", extra={"user_id": user.get("id")})
