from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict


CampaignStatus = Literal[
    "created",
    "running",
    "awaiting_approval",
    "blocked",
    "completed",
    "failed",
]


class EvidenceItem(TypedDict):
    source: str
    citation: str
    text: str
    validated: bool


class CampaignTask(TypedDict):
    id: str
    title: str
    owner: str
    description: str
    status: Literal["pending", "in_progress", "completed", "blocked"]
    citations: list[str]


class AgentArtifact(TypedDict):
    artifact_type: str
    title: str
    content: dict[str, Any]
    citations: list[str]
    ai_confidence: float
    groundedness_score: float
    quality_signals: dict[str, Any]
    requires_human_approval: bool


class CampaignAgentState(TypedDict):
    user_id: str
    campaign_id: str
    thread_id: str
    request_id: str | None
    goal: str
    target_roles: list[str]
    constraints: list[str]
    status: CampaignStatus
    evidence: list[EvidenceItem]
    plan: list[CampaignTask]
    artifacts: list[AgentArtifact]
    approvals: list[dict[str, Any]]
    compliance: dict[str, Any]
    warnings: list[str]
    errors: list[str]
    next_actions: list[str]
    subagent_reports: dict[str, Any]
    checkpoint_backend: NotRequired[str]
    langsmith: NotRequired[dict[str, Any]]
