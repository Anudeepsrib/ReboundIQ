from __future__ import annotations

from collections.abc import Callable
from typing import Any

from langgraph.graph import END, START, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.state import CampaignAgentState
from app.agents.tools import (
    ApprovalToolInput,
    CampaignToolbelt,
    ComplianceToolInput,
    DraftArtifactInput,
    GeneratePlanInput,
    RetrieveEvidenceInput,
)


def build_campaign_graph(db: AsyncSession) -> StateGraph:
    toolbelt = CampaignToolbelt(db)
    builder = StateGraph(CampaignAgentState)

    builder.add_node("retrieve_evidence", _retrieve_evidence(toolbelt))
    builder.add_node("planner_deep", _planner_deep(toolbelt))
    builder.add_node("resume_deep", _draft_deep(toolbelt, "resume_deep", "resume_strategy"))
    builder.add_node("jd_deep", _draft_deep(toolbelt, "jd_deep", "jd_gap_analysis"))
    builder.add_node("proof_deep", _draft_deep(toolbelt, "proof_deep", "proof_plan"))
    builder.add_node(
        "outreach_deep", _draft_deep(toolbelt, "outreach_deep", "outreach_email")
    )
    builder.add_node(
        "interview_deep", _draft_deep(toolbelt, "interview_deep", "interview_plan")
    )
    builder.add_node("compliance_guard", _compliance_guard(toolbelt))
    builder.add_node("approval_checkpoint", _approval_checkpoint(toolbelt))
    builder.add_node("blocked", _blocked_node)

    builder.add_edge(START, "retrieve_evidence")
    builder.add_edge("retrieve_evidence", "planner_deep")
    builder.add_edge("planner_deep", "resume_deep")
    builder.add_edge("resume_deep", "jd_deep")
    builder.add_edge("jd_deep", "proof_deep")
    builder.add_edge("proof_deep", "outreach_deep")
    builder.add_edge("outreach_deep", "interview_deep")
    builder.add_edge("interview_deep", "compliance_guard")
    builder.add_conditional_edges(
        "compliance_guard",
        _route_after_compliance,
        {"approval": "approval_checkpoint", "blocked": "blocked"},
    )
    builder.add_edge("approval_checkpoint", END)
    builder.add_edge("blocked", END)
    return builder


def _retrieve_evidence(
    toolbelt: CampaignToolbelt,
) -> Callable[[CampaignAgentState], Any]:
    async def node(state: CampaignAgentState) -> dict[str, Any]:
        out = await toolbelt.retrieve_evidence(
            RetrieveEvidenceInput(
                user_id=state["user_id"],
                campaign_id=state["campaign_id"],
                query=state["goal"],
                top_k=6,
            )
        )
        return {
            "status": "running",
            "evidence": out.evidence,
            "warnings": [*state.get("warnings", []), *out.warnings],
            "subagent_reports": {
                **state.get("subagent_reports", {}),
                "retrieve_evidence": {"evidence_count": len(out.evidence)},
            },
        }

    return node


def _planner_deep(toolbelt: CampaignToolbelt) -> Callable[[CampaignAgentState], Any]:
    async def node(state: CampaignAgentState) -> dict[str, Any]:
        out = await toolbelt.generate_campaign_plan(
            GeneratePlanInput(
                user_id=state["user_id"],
                campaign_id=state["campaign_id"],
                request_id=state.get("request_id"),
                goal=state["goal"],
                target_roles=state.get("target_roles", []),
                constraints=state.get("constraints", []),
                evidence=state.get("evidence", []),
            )
        )
        return {
            "plan": out.tasks,
            "next_actions": out.next_actions,
            "warnings": [*state.get("warnings", []), *out.warnings],
            "subagent_reports": {
                **state.get("subagent_reports", {}),
                "planner_deep": {"tasks": len(out.tasks)},
            },
        }

    return node


def _draft_deep(
    toolbelt: CampaignToolbelt,
    owner: str,
    artifact_type: str,
) -> Callable[[CampaignAgentState], Any]:
    async def node(state: CampaignAgentState) -> dict[str, Any]:
        out = await toolbelt.draft_artifact(
            DraftArtifactInput(
                user_id=state["user_id"],
                campaign_id=state["campaign_id"],
                request_id=state.get("request_id"),
                artifact_type=artifact_type,  # type: ignore[arg-type]
                owner=owner,
                goal=state["goal"],
                plan=state.get("plan", []),
                evidence=state.get("evidence", []),
            )
        )
        artifacts = [*state.get("artifacts", []), out.artifact]
        return {
            "artifacts": artifacts,
            "warnings": [*state.get("warnings", []), *out.warnings],
            "subagent_reports": {
                **state.get("subagent_reports", {}),
                owner: {"artifact_type": artifact_type, "drafted": True},
            },
        }

    return node


def _compliance_guard(
    toolbelt: CampaignToolbelt,
) -> Callable[[CampaignAgentState], Any]:
    async def node(state: CampaignAgentState) -> dict[str, Any]:
        out = await toolbelt.run_compliance_check(
            ComplianceToolInput(
                campaign_id=state["campaign_id"],
                artifacts=state.get("artifacts", []),
            ),
            user_id=state["user_id"],
            request_id=state.get("request_id"),
        )
        report = out.report.model_dump()
        return {
            "compliance": report,
            "status": "running" if report["passed"] else "blocked",
            "subagent_reports": {
                **state.get("subagent_reports", {}),
                "compliance_guard": report,
            },
        }

    return node


def _approval_checkpoint(
    toolbelt: CampaignToolbelt,
) -> Callable[[CampaignAgentState], Any]:
    async def node(state: CampaignAgentState) -> dict[str, Any]:
        out = await toolbelt.request_human_approval(
            ApprovalToolInput(
                user_id=state["user_id"],
                campaign_id=state["campaign_id"],
                request_id=state.get("request_id"),
                plan=state.get("plan", []),
                artifacts=state.get("artifacts", []),
                compliance=state.get("compliance", {}),
                warnings=state.get("warnings", []),
            )
        )
        return {
            "status": "awaiting_approval",
            "approvals": [*state.get("approvals", []), out.approval],
            "next_actions": [
                "Review the pending campaign checkpoint.",
                "Edit, approve, or reject each artifact before any external use.",
                *state.get("next_actions", []),
            ][:6],
        }

    return node


async def _blocked_node(state: CampaignAgentState) -> dict[str, Any]:
    findings = state.get("compliance", {}).get("findings", [])
    return {
        "status": "blocked",
        "next_actions": [
            "Resolve ComplianceGuard findings before approval.",
            "Remove unsupported claims or add citations from user-provided evidence.",
            *state.get("next_actions", []),
        ][:6],
        "errors": [
            *state.get("errors", []),
            f"Compliance blocked campaign checkpoint with {len(findings)} finding(s).",
        ],
    }


def _route_after_compliance(state: CampaignAgentState) -> str:
    return "approval" if state.get("compliance", {}).get("passed", False) else "blocked"

