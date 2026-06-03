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
