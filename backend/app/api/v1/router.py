from fastapi import APIRouter
from app.api.v1.endpoints import assistant

api_router = APIRouter()
api_router.include_router(assistant.router, prefix="/assistant", tags=["assistant"])
