"""
Async DB session dependency for FastAPI + SQLAlchemy 2.0.
Use: user_id filters in all queries for isolation.
"""

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)
from app.core.config import settings

# Echo only in dev for debug (never log secrets)
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=(settings.ENV == "development"),
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine, expire_on_commit=False, autoflush=False
)


async def get_db() -> AsyncSession:
    """Yield async session. Always scope to request; caller does commits."""
    async with AsyncSessionLocal() as session:
        yield session
