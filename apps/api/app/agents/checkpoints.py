from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator, Any

from langgraph.checkpoint.memory import InMemorySaver

from app.core.config import settings
from app.core.logging import logger

_memory_saver = InMemorySaver()


@asynccontextmanager
async def campaign_checkpointer() -> AsyncIterator[tuple[Any, str]]:
    """Yield a LangGraph checkpointer.

    Postgres checkpointing is available for production, while memory fallback
    keeps unit tests and local smoke runs from requiring checkpoint tables.
    """
    if settings.LANGGRAPH_CHECKPOINT_BACKEND == "postgres":
        try:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

            conn = settings.LANGGRAPH_CHECKPOINT_DATABASE_URL or settings.DATABASE_URL
            conn = conn.replace("postgresql+asyncpg://", "postgresql://", 1)
            async with AsyncPostgresSaver.from_conn_string(conn) as saver:
                if settings.LANGGRAPH_CHECKPOINT_SETUP:
                    await saver.setup()
                yield saver, "postgres"
                return
        except Exception as ex:
            logger.warning(
                "agent.checkpointer.postgres_fallback",
                extra={"error_type": type(ex).__name__, "error": str(ex)[:180]},
            )
    yield _memory_saver, "memory"

