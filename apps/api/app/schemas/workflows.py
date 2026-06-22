from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class WorkflowModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


RunwayScenario = Literal["conservative", "base", "aggressive"]
ApplicationStatus = Literal[
    "saved",
    "applied",
    "recruiter",
    "tech",
    "system_design",
    "manager",
    "final",
    "offer",
    "rejected",
    "withdrawn",
]
ProofAssetType = Literal[
    "star_story",
    "case_study",
    "architecture_note",
    "github_readme",
    "linkedin_post",
    "portfolio_link",
]
ProofStatus = Literal["draft", "ready", "approved", "archived"]
InterviewType = Literal[
    "behavioral",
    "coding",
    "system_design",
    "ai_rag",
    "manager",
    "mixed",
]
InterviewStatus = Literal["planned", "scheduled", "completed", "cancelled"]


class RunwaySnapshotCreate(BaseModel):
    title: str = Field(default="Current runway", min_length=1, max_length=160)
    scenario: RunwayScenario = "base"
    risk_level: str = Field(default="unknown", max_length=40)
    monthly_expenses: float = Field(default=0, ge=0)
    savings_balance: float = Field(default=0, ge=0)
    severance_amount: float = Field(default=0, ge=0)
    unemployment_amount: float = Field(default=0, ge=0)
    target_months: float = Field(default=6, ge=0)
    assumptions_json: dict[str, Any] = Field(default_factory=dict)
    action_items_json: list[dict[str, Any] | str] = Field(default_factory=list)
    disclaimer_acknowledged: bool = False


class RunwaySnapshotUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    scenario: RunwayScenario | None = None
    risk_level: str | None = Field(default=None, max_length=40)
    monthly_expenses: float | None = Field(default=None, ge=0)
    savings_balance: float | None = Field(default=None, ge=0)
    severance_amount: float | None = Field(default=None, ge=0)
    unemployment_amount: float | None = Field(default=None, ge=0)
    target_months: float | None = Field(default=None, ge=0)
    assumptions_json: dict[str, Any] | None = None
    action_items_json: list[dict[str, Any] | str] | None = None
    disclaimer_acknowledged: bool | None = None


class RunwaySnapshotOut(WorkflowModel):
    id: str
    title: str
    scenario: str
    risk_level: str
    monthly_expenses: float
    savings_balance: float
    severance_amount: float
    unemployment_amount: float
    target_months: float
    assumptions_json: dict[str, Any] | None = None
    action_items_json: list[Any] | None = None
    disclaimer_acknowledged: bool
    created_at: datetime
    updated_at: datetime | None = None


class ApplicationCreate(BaseModel):
    company: str = Field(min_length=1, max_length=180)
    role: str = Field(min_length=1, max_length=180)
    status: ApplicationStatus = "saved"
    source_url: str | None = Field(default=None, max_length=4000)
    location: str | None = Field(default=None, max_length=180)
    salary_range: str | None = Field(default=None, max_length=180)
    resume_version_id: str | None = Field(default=None, max_length=36)
    jd_snapshot: str | None = Field(default=None, max_length=20000)
    notes: str | None = Field(default=None, max_length=8000)
    next_step: str | None = Field(default=None, max_length=180)
    next_step_at: datetime | None = None
    fit_score: float | None = Field(default=None, ge=0, le=100)
    sponsorship_signal: str | None = Field(default=None, max_length=80)
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class ApplicationUpdate(BaseModel):
    company: str | None = Field(default=None, min_length=1, max_length=180)
    role: str | None = Field(default=None, min_length=1, max_length=180)
    status: ApplicationStatus | None = None
    source_url: str | None = Field(default=None, max_length=4000)
    location: str | None = Field(default=None, max_length=180)
    salary_range: str | None = Field(default=None, max_length=180)
    resume_version_id: str | None = Field(default=None, max_length=36)
    jd_snapshot: str | None = Field(default=None, max_length=20000)
    notes: str | None = Field(default=None, max_length=8000)
    next_step: str | None = Field(default=None, max_length=180)
    next_step_at: datetime | None = None
    fit_score: float | None = Field(default=None, ge=0, le=100)
    sponsorship_signal: str | None = Field(default=None, max_length=80)
    metadata_json: dict[str, Any] | None = None


class ApplicationOut(WorkflowModel):
    id: str
    company: str
    role: str
    status: str
    source_url: str | None = None
    location: str | None = None
    salary_range: str | None = None
    resume_version_id: str | None = None
    jd_snapshot: str | None = None
    notes: str | None = None
    next_step: str | None = None
    next_step_at: datetime | None = None
    fit_score: float | None = None
    sponsorship_signal: str | None = None
    metadata_json: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime | None = None


class ProofAssetCreate(BaseModel):
    title: str = Field(min_length=1, max_length=220)
    asset_type: ProofAssetType
    status: ProofStatus = "draft"
    summary: str | None = Field(default=None, max_length=8000)
    content_json: dict[str, Any] = Field(default_factory=dict)
    citations_json: list[dict[str, Any] | str] = Field(default_factory=list)
    linked_application_id: str | None = Field(default=None, max_length=36)
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class ProofAssetUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=220)
    asset_type: ProofAssetType | None = None
    status: ProofStatus | None = None
    summary: str | None = Field(default=None, max_length=8000)
    content_json: dict[str, Any] | None = None
    citations_json: list[dict[str, Any] | str] | None = None
    linked_application_id: str | None = Field(default=None, max_length=36)
    metadata_json: dict[str, Any] | None = None


class ProofAssetOut(WorkflowModel):
    id: str
    title: str
    asset_type: str
    status: str
    summary: str | None = None
    content_json: dict[str, Any] | None = None
    citations_json: list[Any] | None = None
    linked_application_id: str | None = None
    metadata_json: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime | None = None


class InterviewSessionCreate(BaseModel):
    target_role: str = Field(min_length=1, max_length=180)
    company: str | None = Field(default=None, max_length=180)
    interview_type: InterviewType = "mixed"
    status: InterviewStatus = "planned"
    scheduled_at: datetime | None = None
    score: float | None = Field(default=None, ge=0, le=100)
    focus_areas_json: list[str] = Field(default_factory=list)
    question_log_json: list[dict[str, Any]] = Field(default_factory=list)
    feedback_json: dict[str, Any] = Field(default_factory=dict)
    linked_application_id: str | None = Field(default=None, max_length=36)
    metadata_json: dict[str, Any] = Field(default_factory=dict)


class InterviewSessionUpdate(BaseModel):
    target_role: str | None = Field(default=None, min_length=1, max_length=180)
    company: str | None = Field(default=None, max_length=180)
    interview_type: InterviewType | None = None
    status: InterviewStatus | None = None
    scheduled_at: datetime | None = None
    score: float | None = Field(default=None, ge=0, le=100)
    focus_areas_json: list[str] | None = None
    question_log_json: list[dict[str, Any]] | None = None
    feedback_json: dict[str, Any] | None = None
    linked_application_id: str | None = Field(default=None, max_length=36)
    metadata_json: dict[str, Any] | None = None


class InterviewSessionOut(WorkflowModel):
    id: str
    target_role: str
    company: str | None = None
    interview_type: str
    status: str
    scheduled_at: datetime | None = None
    score: float | None = None
    focus_areas_json: list[Any] | None = None
    question_log_json: list[Any] | None = None
    feedback_json: dict[str, Any] | None = None
    linked_application_id: str | None = None
    metadata_json: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime | None = None


class DeleteOut(BaseModel):
    ok: bool = True
    id: str
