from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class CampaignCreateRequest(BaseModel):
    goal: str = Field(min_length=10, max_length=4000)
    target_roles: list[str] = Field(default_factory=list, max_length=8)
    constraints: list[str] = Field(default_factory=list, max_length=12)
    run_immediately: bool = True


class CampaignRunRequest(BaseModel):
    goal: str | None = Field(default=None, min_length=10, max_length=4000)
    target_roles: list[str] | None = None
    constraints: list[str] | None = None


class CampaignOut(BaseModel):
    id: str
    goal: str
    status: str
    metadata_json: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime | None = None


class CampaignRunOut(BaseModel):
    campaign_id: str
    status: str
    thread_id: str
    checkpoint_backend: str
    plan: list[dict[str, Any]] = Field(default_factory=list)
    artifacts: list[dict[str, Any]] = Field(default_factory=list)
    approvals: list[dict[str, Any]] = Field(default_factory=list)
    compliance: dict[str, Any] = Field(default_factory=dict)
    evidence: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    langsmith: dict[str, Any] = Field(default_factory=dict)
    deepagents: dict[str, Any] = Field(default_factory=dict)


class ApprovalOut(BaseModel):
    id: str
    campaign_id: str
    artifact_type: str
    artifact_json: dict[str, Any] | None = None
    status: str
    notes: str | None = None
    responded_at: datetime | None = None
    created_at: datetime


class ApprovalDecisionRequest(BaseModel):
    status: Literal["approved", "rejected"]
    notes: str | None = Field(default=None, max_length=2000)

