from __future__ import annotations

import time
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.compliance import ComplianceReport, merge_reports, run_compliance_guard
from app.agents.state import AgentArtifact, CampaignTask, EvidenceItem
from app.ai.gateway import gateway
from app.ai.memory import memory_provider
from app.core.logging import logger
from app.models.agent_approval_requests import AgentApprovalRequest
from app.models.agent_tool_calls import AgentToolCall
from app.models.profile import UserProfile
from app.models.resume import Resume
from app.services.ai_preferences import get_ai_preferences
from app.services.resume import recall_similar_chunks


class RetrieveEvidenceInput(BaseModel):
    user_id: str
    campaign_id: str
    query: str
    top_k: int = 5


class RetrieveEvidenceOutput(BaseModel):
    evidence: list[EvidenceItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class GeneratePlanInput(BaseModel):
    user_id: str
    campaign_id: str
    request_id: str | None = None
    goal: str
    target_roles: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)


class GeneratePlanOutput(BaseModel):
    tasks: list[CampaignTask] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class DraftArtifactInput(BaseModel):
    user_id: str
    campaign_id: str
    request_id: str | None = None
    artifact_type: Literal[
        "resume_strategy",
        "jd_gap_analysis",
        "proof_plan",
        "outreach_email",
        "interview_plan",
    ]
    owner: str
    goal: str
    plan: list[CampaignTask]
    evidence: list[EvidenceItem] = Field(default_factory=list)


class DraftArtifactOutput(BaseModel):
    artifact: AgentArtifact
    warnings: list[str] = Field(default_factory=list)


class ComplianceToolInput(BaseModel):
    campaign_id: str
    artifacts: list[AgentArtifact]


class ComplianceToolOutput(BaseModel):
    report: ComplianceReport


class ApprovalToolInput(BaseModel):
    user_id: str
    campaign_id: str
    request_id: str | None = None
    plan: list[CampaignTask]
    artifacts: list[AgentArtifact]
    compliance: dict[str, Any]
    warnings: list[str] = Field(default_factory=list)


class ApprovalToolOutput(BaseModel):
    approval: dict[str, Any]


class CampaignToolbelt:
    """Typed deterministic tools used by CareerCampaignAgent graph nodes."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def retrieve_evidence(
        self, payload: RetrieveEvidenceInput
    ) -> RetrieveEvidenceOutput:
        start = time.perf_counter()
        warnings: list[str] = []
        evidence: list[EvidenceItem] = []
        try:
            res = await self.db.execute(
                select(Resume)
                .where(Resume.user_id == payload.user_id)
                .order_by(Resume.created_at.desc())
                .limit(1)
            )
            resume = res.scalar_one_or_none()
            if resume and resume.parsed_text:
                evidence.append(
                    {
                        "source": f"resume:{resume.id}",
                        "citation": f"resume:{resume.id}:latest",
                        "text": resume.parsed_text[:900],
                        "validated": True,
                    }
                )
        except Exception as ex:
            warnings.append(f"resume evidence unavailable: {type(ex).__name__}")

        try:
            chunks = await recall_similar_chunks(
                self.db, payload.user_id, payload.query, k=min(payload.top_k, 3)
            )
            for index, chunk in enumerate(chunks):
                evidence.append(
                    {
                        "source": "document_chunk",
                        "citation": f"resume_chunk:{index + 1}",
                        "text": chunk[:700],
                        "validated": True,
                    }
                )
        except Exception as ex:
            warnings.append(f"document chunk recall unavailable: {type(ex).__name__}")

        try:
            profile = await self.db.scalar(
                select(UserProfile).where(UserProfile.user_id == payload.user_id)
            )
            allow_sensitive_memory = bool(
                getattr(profile, "consent_memory_sensitive", False)
            )
            if not allow_sensitive_memory:
                warnings.append("sensitive memory skipped: consent not granted")
            memories = await memory_provider.recall(
                user_id=payload.user_id,
                query=payload.query,
                top_k=min(payload.top_k, 3),
                sensitivity_max="medium" if allow_sensitive_memory else "low",
                consent_scope="memory_sensitive" if allow_sensitive_memory else None,
                min_created_at=datetime.now(timezone.utc) - timedelta(days=365),
            )
            for mem in memories:
                content = str(mem.get("content") or "")
                if _looks_like_prompt_injection(content):
                    warnings.append(f"memory skipped for unsafe instructions: {mem.get('id')}")
                    continue
                evidence.append(
                    {
                        "source": f"memory:{mem.get('id')}",
                        "citation": f"memory:{mem.get('id')}",
                        "text": content[:700],
                        "validated": True,
                    }
                )
        except Exception as ex:
            warnings.append(f"memory recall unavailable: {type(ex).__name__}")

        if not evidence:
            warnings.append("No user evidence found; outputs must ask for missing data.")

        output = RetrieveEvidenceOutput(evidence=evidence[: payload.top_k], warnings=warnings)
        await self._log_tool_call(
            payload.user_id,
            payload.campaign_id,
            "retrieve_user_documents",
            payload.model_dump(),
            output.model_dump(),
            start,
            None,
        )
        return output

    async def generate_campaign_plan(
        self, payload: GeneratePlanInput
    ) -> GeneratePlanOutput:
        start = time.perf_counter()
        citations = [item["citation"] for item in payload.evidence]
        warnings: list[str] = []
        parsed: dict[str, Any] = {}
        try:
            prefs = await get_ai_preferences(self.db, payload.user_id)
            parsed = await gateway.structured(
                _PLAN_SYSTEM,
                _plan_user_prompt(payload),
                schema={"type": "object"},
                model=prefs["chat_model"],
                user_id=payload.user_id,
                request_id=payload.request_id,
                metadata={
                    "campaign_id": payload.campaign_id,
                    "agent": "planner_deep",
                },
            )
        except Exception as ex:
            warnings.append(f"local planner model unavailable: {type(ex).__name__}")

        tasks = _normalize_tasks(parsed.get("tasks"), citations)
        if not tasks:
            tasks = _fallback_tasks(payload.goal, citations)
        next_actions = [
            a
            for a in parsed.get("next_actions", [])
            if isinstance(a, str) and a.strip()
        ][:5]
        if not next_actions:
            next_actions = [
                "Review the generated campaign plan.",
                "Add missing evidence before approving user-facing drafts.",
                "Approve, edit, or reject the pending campaign checkpoint.",
            ]
        output = GeneratePlanOutput(
            tasks=tasks,
            next_actions=next_actions,
            warnings=warnings,
        )
        await self._log_tool_call(
            payload.user_id,
            payload.campaign_id,
            "generate_campaign_plan",
            payload.model_dump(),
            output.model_dump(),
            start,
            payload.request_id,
        )
        return output

    async def draft_artifact(self, payload: DraftArtifactInput) -> DraftArtifactOutput:
        start = time.perf_counter()
        warnings: list[str] = []
        parsed: dict[str, Any] = {}
        try:
            prefs = await get_ai_preferences(self.db, payload.user_id)
            parsed = await gateway.structured(
                _DRAFT_SYSTEM,
                _draft_user_prompt(payload),
                schema={"type": "object"},
                model=prefs["chat_model"],
                user_id=payload.user_id,
                request_id=payload.request_id,
                metadata={
                    "campaign_id": payload.campaign_id,
                    "agent": payload.owner,
                    "artifact_type": payload.artifact_type,
                },
            )
        except Exception as ex:
            warnings.append(f"local draft model unavailable: {type(ex).__name__}")

        citations = _artifact_citations(parsed, payload.evidence)
        content = parsed.get("content") if isinstance(parsed.get("content"), dict) else {}
        if not content:
            content = _fallback_artifact_content(payload)
        quality = _quality_scores(content, citations, payload.evidence)

        artifact: AgentArtifact = {
            "artifact_type": payload.artifact_type,
            "title": str(parsed.get("title") or _artifact_title(payload.artifact_type)),
            "content": {
                **content,
                "manual_review_required": True,
                "planning_guidance_only": True,
            },
            "citations": citations,
            "ai_confidence": quality["ai_confidence"],
            "groundedness_score": quality["groundedness_score"],
            "quality_signals": quality,
            "requires_human_approval": True,
        }
        output = DraftArtifactOutput(artifact=artifact, warnings=warnings)
        await self._log_tool_call(
            payload.user_id,
            payload.campaign_id,
            f"{payload.owner}.draft_artifact",
            payload.model_dump(),
            output.model_dump(),
            start,
            payload.request_id,
        )
        return output

    async def run_compliance_check(
        self, payload: ComplianceToolInput, user_id: str, request_id: str | None
    ) -> ComplianceToolOutput:
        start = time.perf_counter()
        reports = [
            run_compliance_guard(
                artifact_type=a["artifact_type"],
                content=a["content"],
                citations=a.get("citations", []),
                requires_human_approval=a.get("requires_human_approval", False),
            )
            for a in payload.artifacts
        ]
        output = ComplianceToolOutput(report=merge_reports(reports))
        await self._log_tool_call(
            user_id,
            payload.campaign_id,
            "compliance_guard.run",
            payload.model_dump(),
            output.model_dump(),
            start,
            request_id,
        )
        return output

    async def request_human_approval(
        self, payload: ApprovalToolInput
    ) -> ApprovalToolOutput:
        start = time.perf_counter()
        approval = AgentApprovalRequest(
            user_id=payload.user_id,
            campaign_id=payload.campaign_id,
            artifact_type="campaign_checkpoint",
            artifact_json={
                "plan": payload.plan,
                "artifacts": payload.artifacts,
                "compliance": payload.compliance,
                "warnings": payload.warnings,
                "manual_action_only": True,
            },
            artifact_ref=None,
            status="pending",
            notes=None,
        )
        self.db.add(approval)
        await self.db.flush()
        out = {
            "id": approval.id,
            "campaign_id": approval.campaign_id,
            "artifact_type": approval.artifact_type,
            "status": approval.status,
        }
        output = ApprovalToolOutput(approval=out)
        await self._log_tool_call(
            payload.user_id,
            payload.campaign_id,
            "request_human_approval",
            payload.model_dump(),
            output.model_dump(),
            start,
            payload.request_id,
        )
        return output

    async def _log_tool_call(
        self,
        user_id: str,
        campaign_id: str,
        tool_name: str,
        input_json: dict[str, Any],
        output_json: dict[str, Any],
        start: float,
        request_id: str | None,
    ) -> None:
        latency_ms = int((time.perf_counter() - start) * 1000)
        self.db.add(
            AgentToolCall(
                user_id=user_id,
                campaign_id=campaign_id,
                tool_name=tool_name,
                input_json=input_json,
                output_json=output_json,
                request_id=request_id,
                latency_ms=latency_ms,
            )
        )
        await self.db.flush()
        logger.info(
            "agent.tool_call",
            extra={
                "user_id": user_id,
                "campaign_id": campaign_id,
                "tool_name": tool_name,
                "latency_ms": latency_ms,
                "request_id": request_id,
            },
        )


_PLAN_SYSTEM = (
    "You are PlannerDeepAgent for ReboundIQ. Build a truthful career campaign "
    "plan using only provided evidence. Never fabricate employment history, "
    "metrics, titles, employers, or hiring outcomes. Return JSON with keys "
    "tasks (array of {title, owner, description, citations}) and next_actions."
)

_DRAFT_SYSTEM = (
    "You are a ReboundIQ specialized deep subagent. Draft planning artifacts only. "
    "Use citations for personal claims. If evidence is missing, say what is missing. "
    "Never auto-send, auto-apply, or provide legal/immigration/financial/tax/medical advice. "
    "Return JSON with title, content object, and citations."
)


def _plan_user_prompt(payload: GeneratePlanInput) -> str:
    evidence = "\n".join(
        f"- {item['citation']}: {item['text'][:500]}" for item in payload.evidence
    )
    return (
        f"GOAL: {payload.goal}\n"
        f"TARGET ROLES: {payload.target_roles or ['unspecified']}\n"
        f"CONSTRAINTS: {payload.constraints or ['none provided']}\n"
        f"EVIDENCE:\n{evidence or '- no evidence found'}\n\n"
        "Create a 5-7 step campaign plan with owners from: planner_deep, "
        "resume_deep, jd_deep, proof_deep, outreach_deep, interview_deep, "
        "compliance_guard. Every task needs citations or a missing-data note."
    )


def _draft_user_prompt(payload: DraftArtifactInput) -> str:
    evidence = "\n".join(
        f"- {item['citation']}: {item['text'][:500]}" for item in payload.evidence
    )
    tasks = "\n".join(f"- {t['title']} ({t['owner']})" for t in payload.plan)
    return (
        f"ARTIFACT TYPE: {payload.artifact_type}\n"
        f"OWNER: {payload.owner}\n"
        f"GOAL: {payload.goal}\n"
        f"PLAN:\n{tasks}\n"
        f"EVIDENCE:\n{evidence or '- no evidence found'}\n\n"
        "Draft a compact artifact. Include missing_evidence if needed. "
        "Keep it user-review-only."
    )


def _normalize_tasks(raw: Any, citations: list[str]) -> list[CampaignTask]:
    if not isinstance(raw, list):
        return []
    tasks: list[CampaignTask] = []
    for index, item in enumerate(raw[:7]):
        if not isinstance(item, dict):
            continue
        title = str(item.get("title") or "").strip()
        if not title:
            continue
        owner = str(item.get("owner") or "planner_deep").strip()
        item_citations = [
            c for c in item.get("citations", []) if isinstance(c, str) and c.strip()
        ]
        tasks.append(
            {
                "id": f"task-{index + 1}",
                "title": title[:140],
                "owner": owner,
                "description": str(item.get("description") or title)[:600],
                "status": "pending",
                "citations": item_citations or citations[:3],
            }
        )
    return tasks


def _fallback_tasks(goal: str, citations: list[str]) -> list[CampaignTask]:
    owners = [
        ("planner_deep", "Clarify campaign goal and missing evidence"),
        ("resume_deep", "Review resume positioning against target roles"),
        ("jd_deep", "Analyze role requirements and visible gaps"),
        ("proof_deep", "Plan proof assets that substantiate claims"),
        ("outreach_deep", "Draft manual-review outreach variants"),
        ("interview_deep", "Build interview practice from real evidence"),
        ("compliance_guard", "Run safety, citation, and approval checks"),
    ]
    return [
        {
            "id": f"task-{index + 1}",
            "title": title,
            "owner": owner,
            "description": f"{title} for goal: {goal[:160]}",
            "status": "pending",
            "citations": citations[:3],
        }
        for index, (owner, title) in enumerate(owners)
    ]


def _fallback_artifact_content(payload: DraftArtifactInput) -> dict[str, Any]:
    citations = [e["citation"] for e in payload.evidence][:4]
    missing = [] if citations else ["Upload or select resume/JD evidence before approval."]
    return {
        "summary": (
            f"{payload.owner} prepared a conservative {payload.artifact_type} "
            f"for: {payload.goal[:180]}"
        ),
        "recommendations": [
            "Keep claims tied to cited user evidence.",
            "Replace placeholders with user-confirmed facts before use.",
            "Treat this as planning guidance, not a final external message.",
        ],
        "missing_evidence": missing,
    }


def _artifact_title(artifact_type: str) -> str:
    return artifact_type.replace("_", " ").title()


def _artifact_citations(parsed: dict[str, Any], evidence: list[EvidenceItem]) -> list[str]:
    raw = parsed.get("citations") if isinstance(parsed, dict) else None
    citations = [c for c in (raw or []) if isinstance(c, str) and c.strip()]
    if citations:
        return citations[:6]
    return [item["citation"] for item in evidence[:4]]


def _quality_scores(
    content: dict[str, Any], citations: list[str], evidence: list[EvidenceItem]
) -> dict[str, Any]:
    evidence_count = len(evidence)
    citation_count = len(citations)
    missing_count = _missing_evidence_count(content)
    groundedness = 0.25
    if evidence_count:
        groundedness += 0.35
    groundedness += min(0.3, citation_count * 0.08)
    groundedness -= min(0.25, missing_count * 0.08)
    groundedness = max(0.05, min(0.95, round(groundedness, 2)))

    confidence = 0.35 + (groundedness * 0.45)
    if evidence_count >= 2:
        confidence += 0.1
    if missing_count:
        confidence -= min(0.2, missing_count * 0.05)
    confidence = max(0.05, min(0.9, round(confidence, 2)))
    return {
        "ai_confidence": confidence,
        "groundedness_score": groundedness,
        "evidence_count": evidence_count,
        "citation_count": citation_count,
        "missing_evidence_count": missing_count,
        "scoring_note": (
            "Deterministic support score from citations, evidence coverage, "
            "missing-evidence flags, and compliance gates."
        ),
    }


def _missing_evidence_count(content: dict[str, Any]) -> int:
    raw = content.get("missing_evidence")
    if isinstance(raw, list):
        return len([item for item in raw if str(item).strip()])
    if isinstance(raw, str) and raw.strip():
        return 1
    return 0


def _looks_like_prompt_injection(text: str) -> bool:
    lowered = text.lower()
    return any(
        phrase in lowered
        for phrase in (
            "ignore previous",
            "ignore all previous",
            "system prompt",
            "developer message",
            "override safety",
            "bypass compliance",
        )
    )
