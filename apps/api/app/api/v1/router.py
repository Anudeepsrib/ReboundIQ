from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    resumes,
    jobs,
    health,
    ai_settings,
    agents,
    workflows,
    privacy,
    dashboard,
    reminders,
)

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(resumes.router, prefix="/resumes", tags=["resumes"])
api_router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
api_router.include_router(ai_settings.router, prefix="/ai", tags=["ai-providers"])
api_router.include_router(agents.router, prefix="/agents", tags=["agents"])
api_router.include_router(workflows.router, tags=["workflows"])
api_router.include_router(privacy.router, prefix="/privacy", tags=["privacy"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(reminders.router, prefix="/reminders", tags=["reminders"])
