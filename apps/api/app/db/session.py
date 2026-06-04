"""Async SQLAlchemy session factory and FastAPI dependency.

Usage:
- from app.db.session import get_db
- async with session: ...

Models must be imported (side-effect registers with Base.metadata) before
using target_metadata in Alembic or creating tables.
"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import create_engine

from app.core.config import settings

# Ensure all models are registered with Base.metadata (import order matters)
# This side-effect populates metadata for Alembic env.py (which imports from app.models)
import app.models  # noqa: F401  # registers User, Resume*, AgentCampaign*, Memory* etc

from .base import Base  # re-export for convenience

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=(settings.ENV == "development"),
    pool_pre_ping=True,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


# FastAPI dependency
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


# Sync engine for Alembic (see alembic/env.py override) or one-off scripts
def get_sync_engine():
    url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
    return create_engine(url, future=True)


__all__ = [
    "Base",
    "engine",
    "AsyncSessionLocal",
    "get_db",
    "get_sync_engine",
]
