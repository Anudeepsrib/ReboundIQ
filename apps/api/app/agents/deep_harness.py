from __future__ import annotations

from typing import Any

from app.agents.local_model import GatewayChatModel


CAREER_SUBAGENTS: list[dict[str, str]] = [
    {
        "name": "resume_deep",
        "description": "Produces truthful, cited resume positioning recommendations.",
        "system_prompt": "Use only provided evidence. Never invent metrics, employers, or titles.",
    },
    {
        "name": "jd_deep",
        "description": "Extracts JD signals, gaps, and grounded role-fit strategy.",
        "system_prompt": "Be evidence-based. Missing data must be called missing.",
    },
    {
        "name": "proof_deep",
        "description": "Plans proof assets and portfolio evidence for target roles.",
        "system_prompt": "Recommend proof work only as planning guidance.",
    },
    {
        "name": "outreach_deep",
        "description": "Drafts manual-review outreach variants with citations.",
        "system_prompt": "Never auto-send. Drafts require human approval.",
    },
    {
        "name": "interview_deep",
        "description": "Creates interview practice from resume and JD evidence.",
        "system_prompt": "Do not fabricate experience. Ask for missing evidence.",
    },
    {
        "name": "planner_deep",
        "description": "Maintains campaign plans, dependencies, and next actions.",
        "system_prompt": "Coordinate deterministic tools and human checkpoints.",
    },
    {
        "name": "compliance_guard",
        "description": "Blocks unsafe advice, fabrication, missing citations, and auto-actions.",
        "system_prompt": "Safety checks are authoritative and must not be bypassed.",
    },
]


def deep_agent_capabilities() -> dict[str, Any]:
    """Lightweight runtime capability check for LangChain Deep Agents."""
    try:
        from deepagents import create_deep_agent

        return {
            "available": True,
            "factory": f"{create_deep_agent.__module__}.create_deep_agent",
            "subagents": [s["name"] for s in CAREER_SUBAGENTS],
        }
    except Exception as ex:
        return {
            "available": False,
            "error_type": type(ex).__name__,
            "subagents": [s["name"] for s in CAREER_SUBAGENTS],
        }


def build_deep_agent_harness(
    *,
    user_id: str | None = None,
    request_id: str | None = None,
    checkpointer: Any | None = None,
) -> Any:
    """Build a LangChain Deep Agents harness over ReboundIQ's gateway model.

    The service graph below is the production execution path because it keeps
    deterministic tools authoritative. This factory is kept for interactive
    harness experimentation without allowing direct provider calls.
    """
    from deepagents import create_deep_agent

    model = GatewayChatModel().bind_request(
        user_id=user_id,
        request_id=request_id,
        metadata={"component": "deepagents_harness"},
    )
    return create_deep_agent(
        model=model,
        tools=[],
        subagents=CAREER_SUBAGENTS,
        system_prompt=(
            "You are ReboundIQ CareerCampaignAgent. Orchestrate only. "
            "Use deterministic tools/services for business logic, require citations "
            "for personal claims, and require human approval for artifacts."
        ),
        checkpointer=checkpointer,
        name="CareerCampaignAgent",
    )

