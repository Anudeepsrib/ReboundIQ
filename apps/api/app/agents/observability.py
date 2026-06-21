from __future__ import annotations

import os
from typing import Any

from app.core.config import settings


def configure_langsmith_env() -> dict[str, Any]:
    """Configure LangSmith from settings without requiring secrets in code."""
    if settings.LANGSMITH_PROJECT:
        os.environ.setdefault("LANGSMITH_PROJECT", settings.LANGSMITH_PROJECT)
    if settings.LANGSMITH_ENDPOINT:
        os.environ.setdefault("LANGSMITH_ENDPOINT", settings.LANGSMITH_ENDPOINT)
    os.environ.setdefault(
        "LANGSMITH_TRACING", "true" if settings.LANGSMITH_TRACING else "false"
    )
    return {
        "tracing": settings.LANGSMITH_TRACING,
        "project": settings.LANGSMITH_PROJECT,
        "endpoint_configured": bool(settings.LANGSMITH_ENDPOINT),
    }


def graph_config(
    *,
    thread_id: str,
    user_id: str,
    campaign_id: str,
    request_id: str | None,
) -> dict[str, Any]:
    langsmith = configure_langsmith_env()
    return {
        "configurable": {"thread_id": thread_id},
        "metadata": {
            "user_id": user_id,
            "campaign_id": campaign_id,
            "request_id": request_id,
            "langsmith_project": langsmith["project"],
        },
        "tags": [
            "reboundiq",
            "career-campaign",
            f"provider:{settings.AI_PROVIDER}",
        ],
        "run_name": "CareerCampaignAgent",
    }

