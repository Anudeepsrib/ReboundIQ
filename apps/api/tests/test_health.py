import os
import pytest
from httpx import ASGITransport, AsyncClient

# Provide required settings for test collection / import (pydantic validates at import time)
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/testdb")
os.environ.setdefault(
    "JWT_SECRET", "test-jwt-secret-that-is-at-least-32-chars-long-for-tests"
)
os.environ.setdefault("ENCRYPTION_KEY", "test-fernet-key-32-bytes-exactly!!")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from app.main import app


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        r = await ac.get("/health")
        assert r.status_code == 200
        assert "version" in r.json()


# PR-3: basic auth + isolation tests (no live DB/redis required for these units)
def test_auth_security_and_isolation_helpers():
    from app.core.security import (
        create_access_token,
        create_refresh_token,
        get_password_hash,
        verify_password,
        check_owner,
    )
    from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
    from fastapi import HTTPException

    # password
    hp = get_password_hash("s3cr3t-pass")
    assert verify_password("s3cr3t-pass", hp)
    assert not verify_password("wrong", hp)

    # tokens (sync create)
    tok = create_access_token(
        "user-123",
        extra_claims={
            "email": "t@e.com",
            "consents": {"memory_sensitive": False},
            "role": "user",
        },
    )
    assert isinstance(tok, str) and len(tok) > 20
    ref = create_refresh_token("user-123")
    assert isinstance(ref, str)

    # owner check (isolation helper)
    check_owner({"id": "user-123"}, "user-123")  # ok, no raise
    with pytest.raises(HTTPException) as exc:
        check_owner({"id": "user-123"}, "other-user")
    assert exc.value.status_code == 403

    # schemas
    lr = LoginRequest(email="a@b.com", password="longenough")
    assert lr.email == "a@b.com"
    rr = RegisterRequest(email="c@d.com", password="longenough")
    assert rr.full_name is None
    tr = TokenResponse(access_token="x", user={"id": "u"})
    assert tr.token_type == "bearer"

    # Note: full decode_token requires redis + valid signed token + no blacklist; tested in integration with services
    # Here we just ensure no import/syntax error and basic helpers for isolation


@pytest.mark.asyncio
async def test_auth_endpoints_import_and_router():
    # Ensures /auth routes are registered without crashing on import (real flows need DB)
    from app.api.v1.endpoints.auth import router as auth_router, get_current_user

    assert auth_router is not None
    assert get_current_user is not None
    # routes include register/login/refresh/me/logout
    paths = [r.path for r in auth_router.routes]
    assert "/register" in paths
    assert "/login" in paths
    assert "/refresh" in paths
    assert "/me" in paths
    assert "/logout" in paths
