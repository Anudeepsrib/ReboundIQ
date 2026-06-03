"""Async SQLAlchemy 2.0 session factory + deps.
- Lazy connect (engine created at import, first use connects).
- All queries in services/endpoints MUST filter by user_id for isolation.
- Used by resume service for Resume + DocumentChunk persistence in PR-7.
"""

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from contextlib import asynccontextmanager
from app.core.config import settings

# Note: DATABASE_URL must use +asyncpg (set in env/compose)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=(settings.ENV == "development"),
    pool_pre_ping=True,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """FastAPI Depends() generator for request-scoped sessions."""
    async with AsyncSessionLocal() as session:
        yield session


@asynccontextmanager
async def get_db_context():
    """Manual context for services / non-request code (e.g. background). Commits on success."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
