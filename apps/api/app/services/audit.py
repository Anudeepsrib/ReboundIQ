from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.action_audit_logs import ActionAuditLog


async def log_action(
    db: AsyncSession,
    *,
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    request_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    commit: bool = False,
) -> None:
    db.add(
        ActionAuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            request_id=request_id,
            metadata_json=metadata or {},
        )
    )
    if commit:
        await db.commit()
