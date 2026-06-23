from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_current_user
from app.db.session import get_db
from app.models.workflows import ApplicationRecord, InterviewSession, RunwaySnapshot
from app.services.dashboard import build_reminders

router = APIRouter()


@router.get("/")
async def list_reminders(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user_id = current_user["id"]
    applications = list(
        (
            await db.execute(
                select(ApplicationRecord).where(
                    ApplicationRecord.user_id == user_id,
                    ApplicationRecord.deleted_at.is_(None),
                )
            )
        )
        .scalars()
        .all()
    )
    interviews = list(
        (
            await db.execute(
                select(InterviewSession).where(
                    InterviewSession.user_id == user_id,
                    InterviewSession.deleted_at.is_(None),
                )
            )
        )
        .scalars()
        .all()
    )
    runway = (
        await db.execute(
            select(RunwaySnapshot)
            .where(RunwaySnapshot.user_id == user_id, RunwaySnapshot.deleted_at.is_(None))
            .order_by(RunwaySnapshot.updated_at.desc(), RunwaySnapshot.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    return {
        "delivery": "in_app",
        "reminders": build_reminders(
            applications=applications,
            interviews=interviews,
            runway=runway,
        ),
    }
