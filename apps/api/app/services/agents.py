from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.checkpoints import campaign_checkpointer
from app.agents.deep_harness import deep_agent_capabilities
from app.agents.graph import build_campaign_graph
from app.agents.observability import configure_langsmith_env, graph_config
from app.agents.state import CampaignAgentState
from app.core.logging import logger
from app.models.agent_approval_requests import AgentApprovalRequest
from app.models.agent_campaigns import AgentCampaign
from app.models.workflows import InterviewSession, ProofAsset
from app.schemas.agents import CampaignCreateRequest, CampaignRunRequest
from app.services.audit import log_action


async def create_campaign(
    *,
    db: AsyncSession,
    user_id: str,
    payload: CampaignCreateRequest,
    request_id: str | None,
) -> tuple[AgentCampaign, dict[str, Any] | None]:
    metadata = {
        "target_roles": payload.target_roles,
        "constraints": payload.constraints,
        "thread_id": f"campaign-{uuid.uuid4().hex}",
        "request_id": request_id,
        "langsmith": configure_langsmith_env(),
        "deepagents": deep_agent_capabilities(),
    }
    campaign = AgentCampaign(
        user_id=user_id,
        goal=payload.goal,
        status="created",
        metadata_json=metadata,
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)

    run_result = None
    if payload.run_immediately:
        run_result = await run_campaign(
            db=db,
            user_id=user_id,
            campaign_id=campaign.id,
            payload=CampaignRunRequest(
                goal=payload.goal,
                target_roles=payload.target_roles,
                constraints=payload.constraints,
            ),
            request_id=request_id,
        )
        await db.refresh(campaign)
    return campaign, run_result


async def list_campaigns(db: AsyncSession, user_id: str) -> list[AgentCampaign]:
    res = await db.execute(
        select(AgentCampaign)
        .where(AgentCampaign.user_id == user_id, AgentCampaign.deleted_at.is_(None))
        .order_by(AgentCampaign.created_at.desc())
    )
    return list(res.scalars().all())


async def get_campaign(
    db: AsyncSession, user_id: str, campaign_id: str
) -> AgentCampaign | None:
    res = await db.execute(
        select(AgentCampaign).where(
            AgentCampaign.id == campaign_id,
            AgentCampaign.user_id == user_id,
            AgentCampaign.deleted_at.is_(None),
        )
    )
    return res.scalar_one_or_none()


async def run_campaign(
    *,
    db: AsyncSession,
    user_id: str,
    campaign_id: str,
    payload: CampaignRunRequest,
    request_id: str | None,
) -> dict[str, Any]:
    campaign = await get_campaign(db, user_id, campaign_id)
    if not campaign:
        raise ValueError("Campaign not found or access denied")

    metadata = dict(campaign.metadata_json or {})
    goal = payload.goal or campaign.goal
    target_roles = (
        payload.target_roles
        if payload.target_roles is not None
        else metadata.get("target_roles", [])
    )
    constraints = (
        payload.constraints
        if payload.constraints is not None
        else metadata.get("constraints", [])
    )
    thread_id = str(metadata.get("thread_id") or f"campaign-{campaign.id}")

    campaign.status = "running"
    campaign.goal = goal
    metadata.update(
        {
            "target_roles": target_roles or [],
            "constraints": constraints or [],
            "thread_id": thread_id,
            "last_request_id": request_id,
            "langsmith": configure_langsmith_env(),
            "deepagents": deep_agent_capabilities(),
        }
    )
    campaign.metadata_json = metadata
    await db.commit()

    initial_state: CampaignAgentState = {
        "user_id": user_id,
        "campaign_id": campaign.id,
        "thread_id": thread_id,
        "request_id": request_id,
        "goal": goal,
        "target_roles": list(target_roles or []),
        "constraints": list(constraints or []),
        "status": "running",
        "evidence": [],
        "plan": [],
        "artifacts": [],
        "approvals": [],
        "compliance": {},
        "warnings": [],
        "errors": [],
        "next_actions": [],
        "subagent_reports": {},
    }

    async with campaign_checkpointer() as (checkpointer, checkpoint_backend):
        graph = build_campaign_graph(db).compile(checkpointer=checkpointer)
        config = graph_config(
            thread_id=thread_id,
            user_id=user_id,
            campaign_id=campaign.id,
            request_id=request_id,
        )
        try:
            final_state = await graph.ainvoke(initial_state, config=config)
        except Exception as ex:
            logger.exception(
                "agent.campaign_run_failed",
                extra={
                    "user_id": user_id,
                    "campaign_id": campaign.id,
                    "request_id": request_id,
                    "error_type": type(ex).__name__,
                },
            )
            final_state = {
                **initial_state,
                "status": "failed",
                "errors": [f"Agent run failed: {type(ex).__name__}"],
            }

    final_state["checkpoint_backend"] = checkpoint_backend
    final_state["langsmith"] = metadata.get("langsmith", {})
    result = _run_response(final_state, metadata.get("deepagents", {}))

    campaign.status = result["status"]
    campaign.metadata_json = {
        **metadata,
        "last_state": _metadata_state(final_state),
        "checkpoint_backend": checkpoint_backend,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.commit()
    await db.refresh(campaign)
    return result


async def list_approvals(
    db: AsyncSession, user_id: str, campaign_id: str | None = None
) -> list[AgentApprovalRequest]:
    stmt = select(AgentApprovalRequest).where(
        AgentApprovalRequest.user_id == user_id,
        AgentApprovalRequest.deleted_at.is_(None),
    )
    if campaign_id:
        stmt = stmt.where(AgentApprovalRequest.campaign_id == campaign_id)
    stmt = stmt.order_by(AgentApprovalRequest.created_at.desc())
    res = await db.execute(stmt)
    return list(res.scalars().all())


async def decide_approval(
    *,
    db: AsyncSession,
    user_id: str,
    approval_id: str,
    status: str,
    notes: str | None,
) -> AgentApprovalRequest:
    res = await db.execute(
        select(AgentApprovalRequest).where(
            AgentApprovalRequest.id == approval_id,
            AgentApprovalRequest.user_id == user_id,
            AgentApprovalRequest.deleted_at.is_(None),
        )
    )
    approval = res.scalar_one_or_none()
    if not approval:
        raise ValueError("Approval not found or access denied")
    if approval.status != "pending":
        raise ValueError("Approval has already been decided")

    approval.status = status
    approval.notes = notes
    approval.responded_at = datetime.now(timezone.utc)

    campaign = await get_campaign(db, user_id, approval.campaign_id)
    if campaign:
        metadata = dict(campaign.metadata_json or {})
        metadata["last_approval_decision"] = {
            "approval_id": approval.id,
            "status": status,
            "notes": notes,
            "responded_at": approval.responded_at.isoformat(),
        }
        campaign.metadata_json = metadata
        campaign.status = "completed" if status == "approved" else "blocked"
        if status == "approved":
            await _promote_approved_checkpoint(
                db=db,
                user_id=user_id,
                campaign=campaign,
                approval=approval,
            )

    await db.commit()
    await db.refresh(approval)
    return approval


async def _promote_approved_checkpoint(
    *,
    db: AsyncSession,
    user_id: str,
    campaign: AgentCampaign,
    approval: AgentApprovalRequest,
) -> None:
    payload = approval.artifact_json or {}
    artifacts = payload.get("artifacts") if isinstance(payload, dict) else []
    if not isinstance(artifacts, list):
        return
    target_roles = (campaign.metadata_json or {}).get("target_roles") or []
    target_role = str(target_roles[0]) if target_roles else "Target role"

    promoted: list[dict[str, Any]] = []
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            continue
        artifact_type = str(artifact.get("artifact_type") or "proof_plan")
        title = str(artifact.get("title") or artifact_type.replace("_", " ").title())
        content = artifact.get("content") if isinstance(artifact.get("content"), dict) else {}
        citations = artifact.get("citations") if isinstance(artifact.get("citations"), list) else []
        common_meta = {
            "source": "campaign_approval",
            "campaign_id": campaign.id,
            "approval_id": approval.id,
            "artifact_type": artifact_type,
        }
        if artifact_type == "interview_plan":
            session = InterviewSession(
                user_id=user_id,
                target_role=target_role,
                company=None,
                interview_type="mixed",
                status="planned",
                focus_areas_json=["behavioral", "system_design", "ai_rag"],
                question_log_json=[],
                feedback_json=content,
                metadata_json=common_meta,
            )
            db.add(session)
            await db.flush()
            promoted.append({"type": "interview_session", "id": session.id})
            await log_action(
                db,
                user_id=user_id,
                action="promote_campaign_artifact",
                resource_type="interview_sessions",
                resource_id=session.id,
                metadata=common_meta,
            )
        else:
            asset = ProofAsset(
                user_id=user_id,
                title=title[:220],
                asset_type=_proof_asset_type(artifact_type),
                status="approved",
                summary=str(content.get("summary") or content.get("draft") or "")[:4000],
                content_json=content,
                citations_json=citations,
                metadata_json=common_meta,
            )
            db.add(asset)
            await db.flush()
            promoted.append({"type": "proof_asset", "id": asset.id})
            await log_action(
                db,
                user_id=user_id,
                action="promote_campaign_artifact",
                resource_type="proof_assets",
                resource_id=asset.id,
                metadata=common_meta,
            )

    metadata = dict(campaign.metadata_json or {})
    metadata["last_promotion"] = {
        "approval_id": approval.id,
        "promoted": promoted,
        "promoted_at": datetime.now(timezone.utc).isoformat(),
    }
    campaign.metadata_json = metadata


def _proof_asset_type(artifact_type: str) -> str:
    mapping = {
        "proof_plan": "case_study",
        "resume_strategy": "architecture_note",
        "jd_gap_analysis": "architecture_note",
        "outreach_email": "linkedin_post",
    }
    return mapping.get(artifact_type, "case_study")


def _run_response(
    state: CampaignAgentState, deepagents: dict[str, Any]
) -> dict[str, Any]:
    quality = _campaign_quality(state)
    return {
        "campaign_id": state["campaign_id"],
        "status": state.get("status", "failed"),
        "thread_id": state["thread_id"],
        "checkpoint_backend": state.get("checkpoint_backend", "memory"),
        "ai_confidence": quality["ai_confidence"],
        "groundedness_score": quality["groundedness_score"],
        "quality": quality,
        "plan": state.get("plan", []),
        "artifacts": state.get("artifacts", []),
        "approvals": state.get("approvals", []),
        "compliance": state.get("compliance", {}),
        "evidence": state.get("evidence", []),
        "warnings": state.get("warnings", []),
        "errors": state.get("errors", []),
        "next_actions": state.get("next_actions", []),
        "langsmith": state.get("langsmith", {}),
        "deepagents": deepagents,
    }


def _metadata_state(state: CampaignAgentState) -> dict[str, Any]:
    quality = _campaign_quality(state)
    return {
        "status": state.get("status"),
        "thread_id": state.get("thread_id"),
        "ai_confidence": quality["ai_confidence"],
        "groundedness_score": quality["groundedness_score"],
        "quality": quality,
        "plan": state.get("plan", []),
        "artifacts": state.get("artifacts", []),
        "approvals": state.get("approvals", []),
        "compliance": state.get("compliance", {}),
        "evidence": state.get("evidence", []),
        "warnings": state.get("warnings", []),
        "errors": state.get("errors", []),
        "next_actions": state.get("next_actions", []),
        "subagent_reports": state.get("subagent_reports", {}),
    }


def _campaign_quality(state: CampaignAgentState) -> dict[str, Any]:
    artifacts = state.get("artifacts", [])
    evidence = state.get("evidence", [])
    compliance = state.get("compliance", {})
    citation_count = sum(len(a.get("citations", [])) for a in artifacts)
    missing_count = sum(
        int(a.get("quality_signals", {}).get("missing_evidence_count", 0))
        for a in artifacts
    )
    if artifacts:
        avg_confidence = sum(float(a.get("ai_confidence", 0.0)) for a in artifacts) / len(
            artifacts
        )
        avg_groundedness = sum(
            float(a.get("groundedness_score", 0.0)) for a in artifacts
        ) / len(artifacts)
    else:
        avg_confidence = 0.0
        avg_groundedness = 0.0

    if not compliance.get("passed", False):
        avg_confidence = min(avg_confidence, 0.35)
        avg_groundedness = min(avg_groundedness, 0.45)

    return {
        "ai_confidence": round(avg_confidence, 2),
        "groundedness_score": round(avg_groundedness, 2),
        "evidence_count": len(evidence),
        "citation_count": citation_count,
        "missing_evidence_count": missing_count,
        "compliance_passed": bool(compliance.get("passed", False)),
        "approval_required": True,
        "scoring_note": (
            "Confidence and groundedness are deterministic support scores, "
            "not guarantees of outcome or factual completeness."
        ),
    }
