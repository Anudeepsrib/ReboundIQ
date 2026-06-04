"""
MemoryProvider ABC + PostgresMemoryProvider (pgvector) + InMemory fallback for tests/smoke.
Per AGENTS.md + PR-6: retain/recall/reflect basic ops.
- All queries MUST filter by user_id (row-level isolation).
- Recall applies sensitivity + consent_scope pre-filters (evidence only).
- Embeddings for semantic: via AIGateway (respects local-default + redaction if external).
- Never auto-apply memories; caller (RAG, agents) must validate + cite.
- Hindsight opt-in via settings later.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.logging import logger

# Avoid top-level circulars: gateway imported lazily inside methods that need embed.
# Model imported inside methods too for safety during partial startup.


class MemoryProvider(ABC):
    """Abstract base for memory backends. Default impl is Postgres + pgvector."""

    @abstractmethod
    async def retain(
        self,
        user_id: str,
        content: str,
        category: str = "note",
        sensitivity: str = "low",
        consent_scope: Optional[str] = None,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
        key: Optional[str] = None,
    ) -> str:
        """Store a memory record (original content). Returns record id.
        If embedding None, will compute via gateway.embed (local preferred).
        """
        ...

    @abstractmethod
    async def recall(
        self,
        user_id: str,
        query: str,
        category: Optional[str] = None,
        top_k: int = 5,
        sensitivity_max: str = "medium",
        consent_scope: Optional[str] = None,
        min_created_at: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """Semantic (or lexical fallback) recall filtered by user, sens, consent.
        Returns list of dicts with id, content, category, sensitivity, metadata, created_at, score?
        Memories are EVIDENCE ONLY; caller must cross-check against current user input, cite sources.
        """
        ...

    @abstractmethod
    async def reflect(
        self,
        user_id: str,
        event: str,
        category: str = "reflection",
        sensitivity: str = "low",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Basic reflection: synthesize/store insight from event (e.g. post-outcome).
        For skeleton: just retains a derived memory. Full: may call gateway.structured on recent recalls.
        Returns the id of the reflection record.
        """
        ...

    async def close(self) -> None:
        """Optional cleanup."""
        pass


class InMemoryMemoryProvider(MemoryProvider):
    """Pure-python fallback for unit tests, evals smoke, and when DB unavailable.
    Uses substring match + recency for "semantic"; sufficient for golden/eval without pg.
    Never used in prod (see get_memory_provider).
    """

    def __init__(self) -> None:
        self._by_user: Dict[str, List[Dict[str, Any]]] = {}

    async def retain(
        self,
        user_id: str,
        content: str,
        category: str = "note",
        sensitivity: str = "low",
        consent_scope: Optional[str] = None,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
        key: Optional[str] = None,
    ) -> str:
        if not user_id or not content:
            raise ValueError("user_id and content required")
        rec_id = str(uuid.uuid4())
        rec = {
            "id": rec_id,
            "user_id": user_id,
            "key": key,
            "content": content,
            "embedding": embedding or [],
            "category": category,
            "sensitivity": sensitivity,
            "consent_scope": consent_scope,
            "source": source,
            "metadata_json": metadata or {},
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        self._by_user.setdefault(user_id, []).append(rec)
        # keep only last N per user for test bloat
        if len(self._by_user[user_id]) > 100:
            self._by_user[user_id] = self._by_user[user_id][-100:]
        logger.info(
            "memory.retain.inmem",
            extra={"user_id": user_id, "category": category, "id": rec_id[:8]},
        )
        return rec_id

    async def recall(
        self,
        user_id: str,
        query: str,
        category: Optional[str] = None,
        top_k: int = 5,
        sensitivity_max: str = "medium",
        consent_scope: Optional[str] = None,
        min_created_at: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        items = list(self._by_user.get(user_id, []))
        # sens filter
        allowed_sens = self._allowed_sensitivities(sensitivity_max)
        items = [i for i in items if i["sensitivity"] in allowed_sens]
        if consent_scope:
            items = [
                i
                for i in items
                if not i.get("consent_scope") or i.get("consent_scope") == consent_scope
            ]
        if category:
            items = [i for i in items if i["category"] == category]
        if min_created_at:
            items = [i for i in items if i["created_at"] >= min_created_at]
        # fake semantic: prefer exact substring, else recency
        q = (query or "").lower().strip()
        scored: List[tuple[float, Dict[str, Any]]] = []
        for it in items:
            c = (it["content"] or "").lower()
            score = 1.0 if q and q in c else 0.5
            # recency boost
            age_days = (datetime.utcnow() - it["created_at"]).total_seconds() / 86400.0
            score += max(0.0, 0.3 - min(age_days / 30.0, 0.3))
            scored.append((score, it))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for score, it in scored[:top_k]:
            results.append(
                {
                    "id": it["id"],
                    "content": it["content"],
                    "category": it["category"],
                    "sensitivity": it["sensitivity"],
                    "metadata": it["metadata_json"],
                    "created_at": it["created_at"].isoformat() + "Z",
                    "score": round(score, 4),
                    "key": it.get("key"),
                }
            )
        logger.info(
            "memory.recall.inmem",
            extra={
                "user_id": user_id,
                "query_len": len(query),
                "returned": len(results),
            },
        )
        return results

    async def reflect(
        self,
        user_id: str,
        event: str,
        category: str = "reflection",
        sensitivity: str = "low",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        content = f"[REFLECTION] {event}"
        return await self.retain(
            user_id=user_id,
            content=content,
            category=category,
            sensitivity=sensitivity,
            source="reflect",
            metadata=metadata or {"synthetic": True},
        )

    def _allowed_sensitivities(self, max_sens: str) -> List[str]:
        order = ["low", "medium", "high"]
        try:
            idx = order.index(max_sens.lower())
        except ValueError:
            idx = 1
        return order[: idx + 1]


class PostgresMemoryProvider(MemoryProvider):
    """Production default. Requires pgvector extension (in init.sql + compose).
    Uses AIGateway for embeddings (local-first, redaction on external path only).
    All access gated by user_id.
    """

    def __init__(self) -> None:
        self._session_factory = None
        self._engine = None

    def _get_session_factory(self):
        if self._session_factory is None:
            # Import here to avoid requiring DB at module import time for non-pg paths.
            from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

            db_url = settings.DATABASE_URL
            if not db_url:
                raise RuntimeError("DATABASE_URL required for PostgresMemoryProvider")
            # ensure asyncpg driver for runtime
            if "postgresql://" in db_url and "+asyncpg" not in db_url:
                db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            self._engine = create_async_engine(
                db_url, echo=(settings.ENV == "development"), pool_pre_ping=True
            )
            self._session_factory = async_sessionmaker(
                self._engine, expire_on_commit=False
            )
            logger.info("memory.postgres.engine_created")
        return self._session_factory

    async def _embed_for_memory(self, text: str, user_id: str) -> List[float]:
        """Get embedding via gateway (respects AI_PROVIDER, ENABLE_EXTERNAL_AI + redaction)."""
        # Lazy import to prevent cycles (gateway may be extended to use memory in future RAG)
        from app.ai.gateway import gateway

        try:
            emb = await gateway.embed(
                text=text[:8192],  # safety truncate
                user_id=user_id,
                request_id=f"mem-embed-{uuid.uuid4().hex[:8]}",
            )
            vec = emb if isinstance(emb, list) else list(emb)
            # pad/truncate to EMBED_DIM
            from app.models.memory_record import EMBED_DIM

            if len(vec) < EMBED_DIM:
                vec = vec + [0.0] * (EMBED_DIM - len(vec))
            elif len(vec) > EMBED_DIM:
                vec = vec[:EMBED_DIM]
            return vec
        except Exception as ex:
            logger.warning(
                "memory.embed_via_gateway.fail",
                extra={"user_id": user_id, "err": str(ex)[:120]},
            )
            # Return zero vec as last resort (recall will be poor but no crash)
            from app.models.memory_record import EMBED_DIM

            return [0.0] * EMBED_DIM

    async def retain(
        self,
        user_id: str,
        content: str,
        category: str = "note",
        sensitivity: str = "low",
        consent_scope: Optional[str] = None,
        source: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
        key: Optional[str] = None,
    ) -> str:
        if not user_id or not content or not isinstance(content, str):
            raise ValueError("user_id and non-empty content required for retain")
        from app.models.memory_record import MemoryRecord

        if embedding is None:
            embedding = await self._embed_for_memory(content, user_id)

        rec = MemoryRecord(
            user_id=user_id,
            key=key,
            content=content,
            embedding=embedding,
            category=category,
            sensitivity=sensitivity,
            consent_scope=consent_scope,
            source=source,
            metadata_json=metadata or {},
        )
        sess_factory = self._get_session_factory()
        async with sess_factory() as session:
            session.add(rec)
            await session.commit()
            await session.refresh(rec)
        rid = rec.id
        logger.info(
            "memory.retain.pg",
            extra={
                "user_id": user_id,
                "id": rid[:8],
                "category": category,
                "sens": sensitivity,
                "len": len(content),
            },
        )
        return rid

    async def recall(
        self,
        user_id: str,
        query: str,
        category: Optional[str] = None,
        top_k: int = 5,
        sensitivity_max: str = "medium",
        consent_scope: Optional[str] = None,
        min_created_at: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        from app.models.memory_record import MemoryRecord
        from sqlalchemy import select

        allowed = self._allowed_sensitivities(sensitivity_max)
        sess_factory = self._get_session_factory()
        async with sess_factory() as session:
            stmt = select(MemoryRecord).where(MemoryRecord.user_id == user_id)
            stmt = stmt.where(MemoryRecord.sensitivity.in_(allowed))
            if consent_scope:
                stmt = stmt.where(
                    (MemoryRecord.consent_scope == consent_scope)
                    | (MemoryRecord.consent_scope.is_(None))
                )
            if category:
                stmt = stmt.where(MemoryRecord.category == category)
            if min_created_at:
                stmt = stmt.where(MemoryRecord.created_at >= min_created_at)

            # If we have query, embed and order by cosine distance (smaller better)
            q = (query or "").strip()
            if q:
                q_vec = await self._embed_for_memory(q, user_id)
                # pgvector: cosine_distance returns dist (0 best); order asc
                stmt = stmt.order_by(MemoryRecord.embedding.cosine_distance(q_vec))
            else:
                stmt = stmt.order_by(MemoryRecord.created_at.desc())

            stmt = stmt.limit(top_k)
            res = await session.execute(stmt)
            rows: List[MemoryRecord] = res.scalars().all()

        out: List[Dict[str, Any]] = []
        for r in rows:
            out.append(
                {
                    "id": r.id,
                    "content": r.content,
                    "category": r.category,
                    "sensitivity": r.sensitivity,
                    "metadata": r.metadata_json or {},
                    "created_at": r.created_at.isoformat() + "Z"
                    if r.created_at
                    else None,
                    "key": r.key,
                    "source": r.source,
                    # score omitted for pg (would need .label or separate query); caller treats as ordered
                }
            )
        logger.info(
            "memory.recall.pg",
            extra={
                "user_id": user_id,
                "query_len": len(query),
                "returned": len(out),
                "category": category,
            },
        )
        return out

    async def reflect(
        self,
        user_id: str,
        event: str,
        category: str = "reflection",
        sensitivity: str = "low",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        # Basic: retain the event as reflection record. (Full version could recall recent + gateway.structured to distill)
        content = f"[REFLECTION] {event}"
        meta = dict(metadata or {})
        meta.setdefault("reflected_at", datetime.utcnow().isoformat())
        return await self.retain(
            user_id=user_id,
            content=content,
            category=category,
            sensitivity=sensitivity,
            source="reflect",
            metadata=meta,
        )

    def _allowed_sensitivities(self, max_sens: str) -> List[str]:
        order = ["low", "medium", "high"]
        try:
            idx = order.index((max_sens or "medium").lower())
        except ValueError:
            idx = 1
        return order[: idx + 1]


def get_memory_provider() -> MemoryProvider:
    """Factory. Prefers PostgresMemoryProvider when DATABASE_URL looks like postgres.
    Falls back to InMemoryMemoryProvider (for smoke/eval without live pg).
    """
    db_url = getattr(settings, "DATABASE_URL", "") or ""
    if "postgres" in db_url.lower():
        try:
            return PostgresMemoryProvider()
        except Exception as ex:  # e.g. during import before full env
            logger.warning(
                "memory.provider.pg_fallback_to_inmem",
                extra={"reason": str(ex)[:80]},
            )
    return InMemoryMemoryProvider()


# Singleton for easy import/use in services/RAG/agents (still per-user filtered)
memory_provider: MemoryProvider = get_memory_provider()
